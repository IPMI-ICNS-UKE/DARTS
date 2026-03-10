import logging
import math
import json
import skimage.io as io
import numpy as np
import skimage.measure
from skimage.morphology import binary_erosion
from skimage.transform import probabilistic_hough_line
from alive_progress import alive_bar
import time
import pandas as pd
import os
import timeit
from datetime import datetime
import shutil
from stardist.models import StarDist2D
import matplotlib.pyplot as plt

from src.general.cell import CellImage, ChannelImage
from src.postprocessing.segmentation import SegmentationSD
from src.postprocessing.CellTracker_ROI import CellTracker
from src.postprocessing.deconvolution import TDEDeconvolution, LRDeconvolution, BaseDecon, LWDeconvolution
from src.postprocessing.registration import Registration_SITK, Registration_SR
from src.analysis import HotSpotDetection
from src.shapenormalization.shapenormalization import ShapeNormalization
from src.analysis.Dartboard import DartboardGenerator
from src.postprocessing.Bleaching import BleachingAdditiveNoFit, BleachingMultiplicativeSimple, BleachingBiexponentialFitAdditive
from src.general.RatioToConcentrationConverter import RatioConverter
from src.postprocessing.BackgroundSubtraction import BackgroundSubtractorMasked, WaveletBackgroundSubtractor
from src.postprocessing.upsampling import BaseUpsample, FourierUpsampling, SpatialUpsampling
from src.postprocessing.denoising import SparseHessian
from src.general.load_data import load_data
from scipy.signal import savgol_filter
from src.analysis.GUInoBeads_local import GUInoBeads_local

try:
    import SimpleITK as sitk
except ImportError:
    print("SimpleITK cannot be loaded")
    sitk = None

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def convert_ms_to_smh(millis):
    seconds = int(millis / 1000) % 60
    minutes = int(millis / (1000 * 60)) % 60
    hours = int(millis / (1000 * 60 * 60)) % 24
    return seconds, minutes, hours


def cut_image_frames(image, start, end):
    maxt = image.shape[0]
    if image.ndim == 3:
        if end > maxt and start >= maxt:
            return image
        elif end > maxt and start < maxt:
            return image[start:]
        elif end <= maxt and start < maxt:
            return image[start:end]
        else:
            return image
    else:
        return image


class ImageProcessor:

    # ------------------------------------- initialization ----------------------------------

    def __init__(self, image_ch1, image_ch2, parameterdict, logger=None, time_of_addition=None):
        self.parameters = parameterdict
        self.file_name = self.parameters["input_output"]["filename"]
        self.channel1 = image_ch1
        self.channel2 = image_ch2
        self.logger = logger
        self.time_of_addition = time_of_addition

        # self.list_of_bead_contacts = self.parameters["properties_of_measurement"]["list_of_bead_contacts"]

        self.wl1 = self.parameters["properties_of_measurement"]["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["properties_of_measurement"]["wavelength_2"]  # wavelength channel2
        if self.channel1.ndim == 3:
            self.t_max, self.y_max, self.x_max = self.channel1.shape
        elif self.channel1.ndim == 2:
            self.y_max, self.x_max = self.channel1.shape

        # self.file_name = filename  # ntpath.basename(self.parameters["inputoutput"]["path_to_input_combined"

        # self.image = cut_image_frames(self.image, self.start_frame, self.end_frame)

        self.cell_list = []
        self.cell_list_uncentered = []
        self.cell_list_stable_bbox = []
        self.cell_list_stable_bbox_centered = []
        self.segmentation_result_dict = {}
        self.deconvolution_result_dict = {}
        self.cell_list_for_processing = self.cell_list
        self.cell_list_for_processing_uncentered = self.cell_list_uncentered
        self.cell_list_for_processing_stable_bbox = self.cell_list_stable_bbox
        self.cell_list_for_processing_stable_bbox_centered = self.cell_list_stable_bbox_centered
        self.excluded_cells_list = []

        self.ratio_list = []
        self.nb_rois = None

        # ------------------------ setup methods postprocessing ----------------------------
        # registration
        if self.parameters["processing_pipeline"]["postprocessing"]["channel_alignment_in_pipeline"]:
            if self.parameters["processing_pipeline"]["postprocessing"]["registration_method"] == "SITK" and sitk is not None:
                self.registration = Registration_SITK()
            else:
                self.registration = Registration_SR()
        else:
            self.registration = None

        # bleaching correction
        if self.parameters["processing_pipeline"]["postprocessing"]["bleaching_correction_in_pipeline"]:
            if self.parameters["processing_pipeline"]["postprocessing"]["bleaching_correction_algorithm"] == "additiv no fit":
                self.bleaching = BleachingAdditiveNoFit()
            elif self.parameters["processing_pipeline"]["postprocessing"]["bleaching_correction_algorithm"] == "multiplicative simple ratio":
                self.bleaching = BleachingMultiplicativeSimple()
            elif self.parameters["processing_pipeline"]["postprocessing"]["bleaching_correction_algorithm"] == "biexponential fit additiv":
                self.bleaching = BleachingBiexponentialFitAdditive()
            # further bleaching correction alternatives here...

            else:
                self.bleaching = None
        else:
            self.bleaching = None
        # ratio converter
        self.ratio_converter = RatioConverter(self.parameters["properties_of_measurement"]["calibration_parameters_cell_types"])
        self.median_filter_kernel = self.parameters["processing_pipeline"]["postprocessing"]["median_filter_kernel"]

        # ------------------------ setup methods hotspots & dartboard ----------------------------

        self.microdomains_timelines_dict = {}
        self.experiment_name = self.parameters["properties_of_measurement"]["experiment_name"]
        self.day_of_measurement = self.parameters["properties_of_measurement"]["day_of_measurement"]
        self.run_datetime = self.parameters["properties_of_measurement"].get("run_datetime")
        # prefer run timestamp (date + time) if provided, else fall back to configured day
        measurement_prefix = self.run_datetime if self.run_datetime else self.day_of_measurement
        self.measurement_name = measurement_prefix + '_' + self.experiment_name + '_' + self.file_name
        self.results_folder = self.parameters["input_output"]["results_dir"]
        self.save_path = os.path.join(self.results_folder, self.measurement_name)
        self.time_of_finished_processing = None
        self._resumed_from_checkpoint = False
        self.frame_number = len(self.channel1)
        self.cell_type = self.parameters["properties_of_measurement"]["cell_type"]

        # cell tracking & segmentation
        self.scale_pixels_per_micron = self.parameters["properties_of_measurement"]["scale"]
        self.cell_tracker = CellTracker(self.scale_pixels_per_micron)
        # give tracker access to results path for debug overlays
        self.cell_tracker.save_path = self.save_path
        self.model = StarDist2D.from_pretrained('2D_versatile_fluo')
        self.segmentation = SegmentationSD(self.model)

        # background subtraction
        self.background_subtractor = None
        if self.parameters["processing_pipeline"]["postprocessing"]["background_sub_in_pipeline"]:
            if self.parameters["processing_pipeline"]["postprocessing"]["background_subtractor_algorithm"] == "Masked":
                self.background_subtractor = BackgroundSubtractorMasked(self.segmentation)
            elif self.parameters["processing_pipeline"]["postprocessing"]["background_subtractor_algorithm"] == "Wavelet":
                self.background_subtractor = WaveletBackgroundSubtractor()
        # UpSampling
        if self.parameters["processing_pipeline"]["postprocessing"]["upsampling_in_pipeline"]:
            if self.parameters["processing_pipeline"]["postprocessing"]["upsampling_algorithm"] == "Spatial":
                self.upsample = SpatialUpsampling()
            elif self.parameters["processing_pipeline"]["postprocessing"]["upsampling_algorithm"] == "Fourier":
                self.upsample = FourierUpsampling()

        # denoising_utils SPARSE
        if self.parameters["processing_pipeline"]["postprocessing"]["denoising_in_pipeline"]:
            if self.parameters["processing_pipeline"]["postprocessing"]["denoising_algorithm"].lower() == "sparsehessian":
                self.denoise = SparseHessian()

        # deconvolution
        if self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_algorithm"] == "TDE":
            self.deconvolution = TDEDeconvolution()
        elif self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_algorithm"] == "LR":
            self.deconvolution = LRDeconvolution()
        elif self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_algorithm"] == "LW":
            self.deconvolution = LWDeconvolution()
        else:
            self.deconvolution = BaseDecon()

        self.spotHeight = None
        if self.cell_type == 'primary':
            self.spotHeight = 112.5  # [Ca2+] = 112.5 nM
        elif self.cell_type == 'jurkat':
            self.spotHeight = 72
        elif self.cell_type == 'NK':
            self.spotHeight = 72  # needs to be checked
        elif self.cell_type == "NK_human":
            self.spotHeight = 72 # Platzhalter
        if self.parameters["properties_of_measurement"]["bead_contact"]:
            self.list_of_bead_contacts = self.parameters["properties_of_measurement"]["list_of_bead_contacts"]
        # self.selected_dartboard_areas = self.parameters["properties"]["selected_dartboard_areas_for_timeline"]
        self.dartboard_number_of_sections = 12 # self.parameters["properties"]["dartboard_number_of_sections"]
        self.dartboard_number_of_areas_per_section = 8 # self.parameters["properties"]["dartboard_number_of_areas_per_section"]

        self.frames_per_second = self.parameters["properties_of_measurement"]["frame_rate"]
        self.time_of_measurement_before_starting_point = self.parameters["properties_of_measurement"]["time_of_measurement_before_starting_point"]
        self.time_of_measurement_after_starting_point = self.parameters["properties_of_measurement"]["time_of_measurement_after_starting_point"]
        self.duration_of_measurement = self.parameters["properties_of_measurement"]["duration_of_measurement"]

        self.minimum_spotsize = 4
        self.min_ratio = 0.1
        self.max_ratio = 2.0
        # self.microdomain_signal_threshold = self.parameters["properties"]["microdomain_signal_threshold"]
        self.excel_filename_general = self.parameters["input_output"]["excel_filename_microdomain_data"]
        self.excel_filename_one_measurement = self.measurement_name + '_microdomain_data'
        self.hotspotdetector = HotSpotDetection.HotSpotDetector(self.save_path,
                                                                self.results_folder,
                                                                self.excel_filename_one_measurement,
                                                                self.excel_filename_general,
                                                                self.frames_per_second,
                                                                self.ratio_converter,
                                                                self.file_name,
                                                                self.scale_pixels_per_micron)

        self.dartboard_generator = DartboardGenerator(self.save_path,
                                                      self.frames_per_second,
                                                      self.measurement_name,
                                                      self.experiment_name,
                                                      self.results_folder)
    # ------------------------ alternative constructors --------------------------------
    # alternative constructor to define image processor with filename
    @classmethod
    def fromfilename(cls, filename, parameterdict, logger=None, time_of_addition = None):
        end = parameterdict["input_output"]["end_frame"]
        channel_format = parameterdict["input_output"]["image_conf"]
        if channel_format == "single":
            name, ext = os.path.splitext(filename)
            if name.endswith("_1"):
                name2 = name[:-2] + "_2"
                filename2 = name2 + ext
                filename1 = filename
            elif name.endswith("_2"):
                name1 = name[:-2]
                filename1 = name1 + ext
                filename2 = filename
            else:
                filename1 = filename
                filename2 = name + "_2" + ext
            try:
                channel1 = load_data(filename1, channel_format)
                channel2 = load_data(filename2, channel_format)
            except Exception as E:
                print(E)
                print("Error loading image ", filename)
                return
        else:
            try:
                channel1, channel2 = load_data(filename, channel_format, channel="both")
            except Exception as E:
                print(E)
                print("Error loading image ", filename)
                return
        if not end is None: # if "no bead contacts" was elected in the GUI
            channel1 = cut_image_frames(channel1, 0, end)
            channel2 = cut_image_frames(channel2, 0, end)
        return cls(channel1, channel2, parameterdict, logger, time_of_addition)

    @classmethod
    def fromfilename_split(cls, filename, parameterdict, logger=None):
        end = parameterdict["input_output"]["end_frame"]
        # !! for now, images need to start at 0 because of bleaching correction !!
        image = cut_image_frames(io.imread(filename), 0, end)
        # separate image into 2 channels: left half and right half
        channel1 = None
        channel2 = None
        if image.ndim == 3:  # for time series
            channel1, channel2 = np.split(image, 2, axis=2)
        elif image.ndim == 2:  # for static images
            channel1, channel2 = np.split(image, 2, axis=1)
        return cls(channel1, channel2, parameterdict, logger)

    @classmethod
    def fromfilename_combine(cls, filename_ch1, filename_ch2, parameterdict, logger=None):
        end = parameterdict["input_output"]["end_frame"]
        # !! for now, images need to start at 0 because of bleaching correction !!
        channel1 = cut_image_frames(io.imread(filename_ch1), 0, end)
        channel2 = cut_image_frames(io.imread(filename_ch2), 0, end)
        return cls(channel1, channel2, parameterdict, logger)

    # alternative constructor to define image processor with image object
    @classmethod
    def fromimage(cls, image_ch1, image_ch2, parameterdict, logger=None):
        return cls(image_ch1, image_ch2, parameterdict, logger)


    #------------------------------------- post processing methods ----------------------------------

    def select_rois(self):
        roi_before_backgroundcor_dict = self.cell_tracker.give_rois(self.channel1, self.channel2, self.model)
        return roi_before_backgroundcor_dict


    def deconvolve_cell_images(self):

        print("\n"+ self.deconvolution.give_name() + ": ")
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            time.sleep(.005)
            for idx, cell in enumerate(self.cell_list_for_processing):
                roi_channel1, roi_channel2 = cell.channel1.image, cell.channel2.image

                roi_channel1_decon, roi_channel2_decon = self.deconvolution.execute(roi_channel1, roi_channel2,
                                                                                    self.parameters)

                cell.set_image_channel1(roi_channel1_decon)
                cell.set_image_channel2(roi_channel2_decon)

                if idx < len(self.cell_list_for_processing_uncentered):
                    cell_uncentered = self.cell_list_for_processing_uncentered[idx]
                    roi_channel1_uncentered, roi_channel2_uncentered = cell_uncentered.channel1.image, cell_uncentered.channel2.image
                    roi_channel1_uncentered_decon, roi_channel2_uncentered_decon = self.deconvolution.execute(
                        roi_channel1_uncentered,
                        roi_channel2_uncentered,
                        self.parameters,
                    )
                    cell_uncentered.set_image_channel1(roi_channel1_uncentered_decon)
                    cell_uncentered.set_image_channel2(roi_channel2_uncentered_decon)
                if idx < len(self.cell_list_for_processing_stable_bbox):
                    cell_stable_bbox = self.cell_list_for_processing_stable_bbox[idx]
                    roi_channel1_stable_bbox, roi_channel2_stable_bbox = cell_stable_bbox.channel1.image, cell_stable_bbox.channel2.image
                    roi_channel1_stable_bbox_decon, roi_channel2_stable_bbox_decon = self.deconvolution.execute(
                        roi_channel1_stable_bbox,
                        roi_channel2_stable_bbox,
                        self.parameters,
                    )
                    cell_stable_bbox.set_image_channel1(roi_channel1_stable_bbox_decon)
                    cell_stable_bbox.set_image_channel2(roi_channel2_stable_bbox_decon)
                if idx < len(self.cell_list_for_processing_stable_bbox_centered):
                    cell_stable_bbox_centered = self.cell_list_for_processing_stable_bbox_centered[idx]
                    roi_channel1_stable_bbox_centered, roi_channel2_stable_bbox_centered = cell_stable_bbox_centered.channel1.image, cell_stable_bbox_centered.channel2.image
                    roi_channel1_stable_bbox_centered_decon, roi_channel2_stable_bbox_centered_decon = self.deconvolution.execute(
                        roi_channel1_stable_bbox_centered,
                        roi_channel2_stable_bbox_centered,
                        self.parameters,
                    )
                    cell_stable_bbox_centered.set_image_channel1(roi_channel1_stable_bbox_centered_decon)
                    cell_stable_bbox_centered.set_image_channel2(roi_channel2_stable_bbox_centered_decon)

                bar()


    def clear_outside_of_cells(self):
        if self.background_subtractor is None:
            return
        self.background_subtractor.clear_outside_of_cells(self.cell_list_for_processing)
        self.background_subtractor.clear_outside_of_cells(self.cell_list_for_processing_uncentered)
        self.background_subtractor.clear_outside_of_cells(self.cell_list_for_processing_stable_bbox)
        self.background_subtractor.clear_outside_of_cells(self.cell_list_for_processing_stable_bbox_centered)


    def background_subtraction(self, channel_1, channel_2):
        print("\n" + self.background_subtractor.give_name() + ": ")
        with alive_bar(1, force_tty=True) as bar:
            time.sleep(.005)
            # background_label_first_frame = self.segmentation.stardist_segmentation_in_frame(channel_2[0])
            channel_1_background_subtracted = self.background_subtractor.execute(channel_1, self.parameters)
            channel_2_background_subtracted = self.background_subtractor.execute(channel_2, self.parameters)
            bar()
        return channel_1_background_subtracted, channel_2_background_subtracted

    # TODO matching denoise Method
    def denoise_cell_images(self, channel_1, channel_2):
        print("\n"+ self.denoise.give_name() + ": ")
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            time.sleep(.005)
            channel_1_denoised, channel_2_denoised = self.denoise.execute(channel_1, channel_2, self.parameters)
            bar()
        return channel_1_denoised, channel_2_denoised

    def create_cell_images(self, segmentation_result_dict):
        self.nb_rois = len(segmentation_result_dict)
        print("\nCreating cell images: ")
        key_set = segmentation_result_dict.keys()
        with alive_bar(len(key_set), force_tty=True) as bar:
            time.sleep(.005)
            for i in key_set:
                if i in segmentation_result_dict:
                    self.cell_list.append(CellImage(ChannelImage(segmentation_result_dict[i][0], self.wl1),
                                                    ChannelImage(segmentation_result_dict[i][1], self.wl2),
                                                    self.x_max,
                                                    segmentation_result_dict[i][2],
                                                    segmentation_result_dict[i][3])
                                          )
                    if len(segmentation_result_dict[i]) >= 7:
                        self.cell_list_uncentered.append(CellImage(ChannelImage(segmentation_result_dict[i][4], self.wl1),
                                                                   ChannelImage(segmentation_result_dict[i][5], self.wl2),
                                                                   self.x_max,
                                                                   segmentation_result_dict[i][2],
                                                                   segmentation_result_dict[i][6])
                                                        )
                    if len(segmentation_result_dict[i]) >= 10:
                        self.cell_list_stable_bbox.append(CellImage(ChannelImage(segmentation_result_dict[i][7], self.wl1),
                                                                   ChannelImage(segmentation_result_dict[i][8], self.wl2),
                                                                   self.x_max,
                                                                   segmentation_result_dict[i][2],
                                                                   segmentation_result_dict[i][9])
                                                        )
                    if len(segmentation_result_dict[i]) >= 13:
                        self.cell_list_stable_bbox_centered.append(CellImage(ChannelImage(segmentation_result_dict[i][10], self.wl1),
                                                                            ChannelImage(segmentation_result_dict[i][11], self.wl2),
                                                                            self.x_max,
                                                                            segmentation_result_dict[i][2],
                                                                            segmentation_result_dict[i][12])
                                                                 )
                bar()
        self.cell_list_for_processing_uncentered = self.cell_list_uncentered
        self.cell_list_for_processing_stable_bbox = self.cell_list_stable_bbox
        self.cell_list_for_processing_stable_bbox_centered = self.cell_list_stable_bbox_centered

    def correct_coordinates(self, ymin, ymax, xmin, xmax):
        ymin_corrected = ymin
        ymax_corrected = ymax
        xmin_corrected = xmin
        xmax_corrected = xmax

        if (ymin < 0):
            ymin_corrected = 0
        if (ymax < 0):
            ymax_corrected = 0
        if (xmin < 0):
            xmin_corrected = 0
        if (xmax < 0):
            xmax_corrected = 0
        return ymin_corrected, ymax_corrected, xmin_corrected, xmax_corrected

    def start_postprocessing(self):
        resumed_from_checkpoint = False
        if self.should_load_preprocessing_checkpoint():
            resumed_from_checkpoint = self.load_preprocessing_checkpoint()

        self._resumed_from_checkpoint = resumed_from_checkpoint

        if not resumed_from_checkpoint:
            self._run_pre_checkpoint_pipeline()

        self._run_post_checkpoint_steps()

    def _run_pre_checkpoint_pipeline(self):
        # -- PROCESSING OF WHOLE IMAGE CHANNELS --
        if self.parameters["processing_pipeline"]["postprocessing"]["channel_alignment_in_pipeline"]:
            self.channel2 = self.registration.channel_registration(self.channel1, self.channel2,
                                                                   self.parameters["processing_pipeline"]["postprocessing"]["channel_alignment_each_frame"])

        if self.parameters["processing_pipeline"]["postprocessing"]["background_sub_in_pipeline"]:
            self.channel1, self.channel2 = self.background_subtraction(self.channel1, self.channel2)

        # Todo Denoise method

        if self.parameters["processing_pipeline"]["postprocessing"]["denoising_in_pipeline"]:
            self.channel1, self.channel2 = self.denoise_cell_images(self.channel1, self.channel2) #todo


        # segmentation of cells, tracking
        self.segmentation_result_dict = self.select_rois()
        self.create_cell_images(self.segmentation_result_dict)

        if not self.parameters["properties_of_measurement"]["bead_contact"]:
            self.filter_partial_cells(edge_margin=0, frames_to_check=3, required_fraction=0.66)

        if self.parameters["properties_of_measurement"]["bead_contact"]:
            self.assign_bead_contacts_to_cells()
        else:
            if self.parameters["properties_of_measurement"]["imaging_local_or_global"] == 'global':
                for idx, cell in enumerate(self.cell_list):
                    cell_uncentered = self.cell_list_uncentered[idx]
                    cell.starting_point = self.time_of_addition
                    cell_uncentered.starting_point = self.time_of_addition
                    if idx < len(self.cell_list_stable_bbox):
                        self.cell_list_stable_bbox[idx].starting_point = self.time_of_addition
                    if idx < len(self.cell_list_stable_bbox_centered):
                        self.cell_list_stable_bbox_centered[idx].starting_point = self.time_of_addition

        if self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_in_pipeline"]:
            self.deconvolve_cell_images()

        if self.parameters["processing_pipeline"]["postprocessing"]["bleaching_correction_in_pipeline"]:
            self.bleaching_correction()

        if self.deconvolution.give_name() != "TDE Deconvolution":
            self.medianfilter("channels")

        self.generate_ratio_images()

        if self.deconvolution.give_name() != "TDE Deconvolution":
            self.medianfilter("ratio")

        # Preserve the processed ratio stacks before outside-cell masking so
        # we can save full-ROI reference movies with background context.
        for cell in self.cell_list_for_processing:
            if cell.ratio is not None:
                cell.ratio_centered_unmasked = cell.ratio.copy()
        for cell_uncentered in self.cell_list_for_processing_uncentered:
            if cell_uncentered.ratio is not None:
                cell_uncentered.ratio_unmasked = cell_uncentered.ratio.copy()
        for cell_stable_bbox in self.cell_list_for_processing_stable_bbox:
            if cell_stable_bbox.ratio is not None:
                cell_stable_bbox.ratio_stable_bbox_unmasked = cell_stable_bbox.ratio.copy()
        for cell_stable_bbox_centered in self.cell_list_for_processing_stable_bbox_centered:
            if cell_stable_bbox_centered.ratio is not None:
                cell_stable_bbox_centered.ratio_centered_unmasked = cell_stable_bbox_centered.ratio.copy()

        self.clear_outside_of_cells()
        self.save_preprocessing_checkpoint()

    def _run_post_checkpoint_steps(self):
        if not self.parameters["properties_of_measurement"]["bead_contact"]:
            try:
                filtering_cfg = self.parameters.get("processing_pipeline", {}).get("filtering", {})
                preact_threshold = filtering_cfg.get("preactivation_ratio_threshold", 1.0)
            except Exception:
                preact_threshold = 1.0
            self.filter_preactivated_cells(preact_threshold)

        self.finalize_output_directory()

        self.save_ratio_images()
        self.save_centered_unmasked_ratio_images()
        self.save_uncentered_ratio_images()
        self.save_uncentered_unmasked_ratio_images()
        self.save_stable_bbox_masked_ratio_images()
        self.save_stable_bbox_ratio_images()
        self.save_stable_bbox_centered_ratio_images()
        self.save_stable_bbox_centered_unmasked_ratio_images()
        print(f"Final results saved to: {self.save_path}")

        for cell in self.cell_list_for_processing:
            cell.mean_ratio_list = cell.measure_mean_ratio_in_all_frames()

        if not self.parameters["properties_of_measurement"]["bead_contact"] and self.parameters["properties_of_measurement"]["imaging_local_or_global"] == 'local':
            self.determine_starting_points_local_no_beads()

    def finalize_output_directory(self):
        # Keep the original run-time folder so outputs stay with debug PNGs.
        if self.run_datetime:
            return
        if getattr(self, "_resumed_from_checkpoint", False):
            return

        finish_time = datetime.now().strftime("%H-%M-%S")
        self.time_of_finished_processing = finish_time
        new_measurement_name = f"{self.day_of_measurement}_{finish_time}_{self.experiment_name}_{self.file_name}"

        if new_measurement_name == self.measurement_name:
            return

        current_path = self.save_path
        target_path = os.path.join(self.results_folder, new_measurement_name)
        os.makedirs(self.results_folder, exist_ok=True)

        destination = target_path
        suffix = 1
        while os.path.exists(destination):
            destination = f"{target_path}_{suffix:02d}"
            suffix += 1

        try:
            if os.path.isdir(current_path) and current_path != destination:
                shutil.move(current_path, destination)
            else:
                os.makedirs(destination, exist_ok=True)
        except Exception as exc:
            message = ("Could not move output folder to include processing finish time. "
                       f"Reason: {exc}")
            try:
                if getattr(self, "logger", None) is not None:
                    self.logger.log_and_print(message=message,
                                              level=logging.WARNING,
                                              logger=self.logger)
                else:
                    print(message)
            except Exception:
                print(message)
            return

        self.save_path = destination
        self.measurement_name = os.path.basename(self.save_path)
        self.excel_filename_one_measurement = self.measurement_name + '_microdomain_data'

        if getattr(self, "hotspotdetector", None) is not None:
            self.hotspotdetector.save_path = self.save_path
            self.hotspotdetector.excel_filename_one_measurement = self.excel_filename_one_measurement

        if getattr(self, "dartboard_generator", None) is not None:
            self.dartboard_generator.save_path = self.save_path
            self.dartboard_generator.measurement_name = self.measurement_name

        self._update_checkpoint_manifest_measurement()

    def _update_checkpoint_manifest_measurement(self):
        checkpoint_dir = os.path.join(self.save_path, "checkpoints", "pre_start")
        manifest_path = os.path.join(checkpoint_dir, "manifest.json")

        if not os.path.isfile(manifest_path):
            return

        try:
            with open(manifest_path, "r+", encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)
                manifest["measurement"] = self.measurement_name
                manifest_file.seek(0)
                json.dump(manifest, manifest_file, indent=2)
                manifest_file.truncate()
        except Exception as exc:
            message = f"Could not update checkpoint manifest after renaming output folder: {exc}"
            try:
                if getattr(self, "logger", None) is not None:
                    self.logger.log_and_print(message=message,
                                              level=logging.WARNING,
                                              logger=self.logger)
                else:
                    print(message)
            except Exception:
                print(message)

    def filter_preactivated_cells(self, threshold: float):
        """Remove cells that are preactivated (mean ratio in frame 0 > threshold).

        Applies after ratio generation and masking, before saving/GUI steps.
        Updates both self.cell_list and self.cell_list_for_processing to keep them in sync.
        """
        kept = []
        kept_uncentered = []
        kept_stable_bbox = []
        kept_stable_bbox_centered = []
        removed = 0
        for idx, cell in enumerate(list(self.cell_list_for_processing)):
            cell_uncentered = self.cell_list_for_processing_uncentered[idx]
            try:
                if cell.is_preactivated(threshold):
                    removed += 1
                    continue
            except Exception as E:
                # If anything goes wrong with the check, keep the cell and continue
                print(E)
            kept.append(cell)
            kept_uncentered.append(cell_uncentered)
            if idx < len(self.cell_list_for_processing_stable_bbox):
                kept_stable_bbox.append(self.cell_list_for_processing_stable_bbox[idx])
            if idx < len(self.cell_list_for_processing_stable_bbox_centered):
                kept_stable_bbox_centered.append(self.cell_list_for_processing_stable_bbox_centered[idx])

        # Update lists consistently so later steps (including GUIs) only see kept cells
        self.cell_list_for_processing = kept
        self.cell_list = kept
        self.cell_list_for_processing_uncentered = kept_uncentered
        self.cell_list_uncentered = kept_uncentered
        self.cell_list_for_processing_stable_bbox = kept_stable_bbox
        self.cell_list_stable_bbox = kept_stable_bbox
        self.cell_list_for_processing_stable_bbox_centered = kept_stable_bbox_centered
        self.cell_list_stable_bbox_centered = kept_stable_bbox_centered
        if removed > 0:
            try:
                self.logger.log_and_print(
                    message=f"Filtered {removed} preactivated cell(s) (threshold={threshold}).",
                    level=logging.INFO,
                    logger=self.logger)
            except Exception:
                pass

    def _mask_touches_border(self, mask_frame, edge_margin=0):
        """Return True if the (inside-cell) mask touches any image border.

        mask_frame should be a boolean mask where True marks the cell area.
        """
        if mask_frame is None or not np.any(mask_frame):
            return False
        y_max, x_max = mask_frame.shape
        # Quick edge checks with optional margin
        if np.any(mask_frame[0:max(1, 1+edge_margin), :]):
            return True
        if np.any(mask_frame[y_max-1-edge_margin:y_max, :]):
            return True
        if np.any(mask_frame[:, 0:max(1, 1+edge_margin)]):
            return True
        if np.any(mask_frame[:, x_max-1-edge_margin:x_max]):
            return True
        return False

    def filter_partial_cells(self, edge_margin=0, frames_to_check=3, required_fraction=0.66):
        """Remove cells whose masks touch ROI borders (likely partial/cut cells).

        - edge_margin: allow tolerance from the border
        - frames_to_check: number of initial frames to test
        - required_fraction: fraction of tested frames that must touch a border to drop the cell
        """
        kept = []
        kept_uncentered = []
        kept_stable_bbox = []
        kept_stable_bbox_centered = []
        removed = 0
        for idx, cell in enumerate(list(self.cell_list)):
            cell_uncentered = self.cell_list_uncentered[idx]
            try:
                n_frames = min(frames_to_check, cell.frame_number)
                hits = 0
                checked = 0
                for f in range(n_frames):
                    # frame_masks True=outside; invert to get inside-cell mask
                    inside_mask = np.invert(cell.frame_masks[f])
                    if inside_mask is None:
                        continue
                    checked += 1
                    # Border contact OR internal straight edge
                    if (self._mask_touches_border(inside_mask, edge_margin=edge_margin)
                        or self._has_internal_straight_edge(inside_mask)):
                        hits += 1
                if checked > 0 and (hits / checked) >= required_fraction:
                    removed += 1
                    continue
            except Exception as E:
                # If in doubt, keep the cell to avoid false negatives
                print(E)
            kept.append(cell)
            kept_uncentered.append(cell_uncentered)
            if idx < len(self.cell_list_stable_bbox):
                kept_stable_bbox.append(self.cell_list_stable_bbox[idx])
            if idx < len(self.cell_list_stable_bbox_centered):
                kept_stable_bbox_centered.append(self.cell_list_stable_bbox_centered[idx])

        self.cell_list = kept
        self.cell_list_for_processing = kept
        self.cell_list_uncentered = kept_uncentered
        self.cell_list_for_processing_uncentered = kept_uncentered
        self.cell_list_stable_bbox = kept_stable_bbox
        self.cell_list_for_processing_stable_bbox = kept_stable_bbox
        self.cell_list_stable_bbox_centered = kept_stable_bbox_centered
        self.cell_list_for_processing_stable_bbox_centered = kept_stable_bbox_centered
        if removed > 0:
            try:
                self.logger.log_and_print(
                    message=f"Filtered {removed} partial cell(s) touching ROI borders.",
                    level=logging.INFO,
                    logger=self.logger)
            except Exception:
                pass

    def _has_internal_straight_edge(self, inside_mask: np.ndarray,
                                     min_rel_length: float = 0.6,
                                     min_abs_len_px: int = 10,
                                     threshold: int = 10,
                                     line_gap: int = 2) -> bool:
        """Detects a long straight segment on the cell boundary (a chord),
        which is characteristic for cut/partial cells.

        - inside_mask: boolean mask (True = cell)
        - min_rel_length: minimum line length relative to estimated diameter
        - min_abs_len_px: absolute minimum length in pixels
        - threshold, line_gap: parameters for probabilistic Hough transform
        """
        try:
            area = int(np.sum(inside_mask))
            if area <= 0:
                return False
            # Estimate diameter from area assuming roughly circular cell
            diameter_est = 2.0 * np.sqrt(area / np.pi)
            target_len = max(min_rel_length * diameter_est, float(min_abs_len_px))

            # Extract 1-pixel boundary of the mask
            boundary = np.logical_and(inside_mask, np.logical_not(binary_erosion(inside_mask)))

            # Detect line segments on the boundary
            # Use a conservative minimal length to propose segments; verify length below
            min_len_param = max(5, int(target_len * 0.7))
            lines = probabilistic_hough_line(boundary.astype(np.uint8),
                                             threshold=threshold,
                                             line_length=min_len_param,
                                             line_gap=line_gap)
            if not lines:
                return False
            # Check if any segment is long enough
            for (x0, y0), (x1, y1) in lines:
                seg_len = float(np.hypot(x1 - x0, y1 - y0))
                if seg_len >= target_len:
                    return True
            return False
        except Exception as E:
            # On any error, be conservative and return False
            print(E)
            return False

    def bleaching_correction(self):
        print("\n" + self.bleaching.give_name() + ": ")
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            for idx, cell in enumerate(self.cell_list_for_processing):
                time.sleep(.005)

                if self.bleaching is not None:
                    self.bleaching.run(cell, self.parameters, self.model)
                    if idx < len(self.cell_list_for_processing_uncentered):
                        self.bleaching.run(self.cell_list_for_processing_uncentered[idx], self.parameters, self.model)
                    if idx < len(self.cell_list_for_processing_stable_bbox):
                        self.bleaching.run(self.cell_list_for_processing_stable_bbox[idx], self.parameters, self.model)
                    if idx < len(self.cell_list_for_processing_stable_bbox_centered):
                        self.bleaching.run(self.cell_list_for_processing_stable_bbox_centered[idx], self.parameters, self.model)

                bar()

    def generate_ratio_images(self):
        for idx, cell in enumerate(self.cell_list_for_processing):
            cell.generate_ratio_image_series()
            cell.set_ratio_range(self.min_ratio, self.max_ratio)
            if idx < len(self.cell_list_for_processing_uncentered):
                cell_uncentered = self.cell_list_for_processing_uncentered[idx]
                cell_uncentered.generate_ratio_image_series()
                cell_uncentered.set_ratio_range(self.min_ratio, self.max_ratio)
            if idx < len(self.cell_list_for_processing_stable_bbox):
                cell_stable_bbox = self.cell_list_for_processing_stable_bbox[idx]
                cell_stable_bbox.generate_ratio_image_series()
                cell_stable_bbox.set_ratio_range(self.min_ratio, self.max_ratio)
            if idx < len(self.cell_list_for_processing_stable_bbox_centered):
                cell_stable_bbox_centered = self.cell_list_for_processing_stable_bbox_centered[idx]
                cell_stable_bbox_centered.generate_ratio_image_series()
                cell_stable_bbox_centered.set_ratio_range(self.min_ratio, self.max_ratio)

    def save_ratio_images(self):
        savepath = self.save_path + '/ratio/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", cell.ratio)

    def save_uncentered_ratio_images(self):
        if not self.cell_list_for_processing_uncentered:
            return

        savepath = self.save_path + '/ratio_uncentered/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if i >= len(self.cell_list_for_processing_uncentered):
                break
            cell_uncentered = self.cell_list_for_processing_uncentered[i]
            io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", cell_uncentered.ratio)

    def save_centered_unmasked_ratio_images(self):
        savepath = self.save_path + '/ratio_centered_unmasked/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if cell.ratio_centered_unmasked is None:
                continue
            io.imsave(
                savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif",
                cell.ratio_centered_unmasked,
            )

    def save_uncentered_unmasked_ratio_images(self):
        if not self.cell_list_for_processing_uncentered:
            return

        savepath = self.save_path + '/ratio_uncentered_unmasked/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if i >= len(self.cell_list_for_processing_uncentered):
                break
            cell_uncentered = self.cell_list_for_processing_uncentered[i]
            if cell_uncentered.ratio_unmasked is None:
                continue
            io.imsave(
                savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif",
                cell_uncentered.ratio_unmasked,
            )

    def save_stable_bbox_masked_ratio_images(self):
        if not self.cell_list_for_processing_stable_bbox:
            return

        savepath = self.save_path + '/ratio_stable_bbox/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if i >= len(self.cell_list_for_processing_stable_bbox):
                break
            cell_stable_bbox = self.cell_list_for_processing_stable_bbox[i]
            io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", cell_stable_bbox.ratio)

    def save_stable_bbox_ratio_images(self):
        if not self.cell_list_for_processing_stable_bbox:
            return

        savepath = self.save_path + '/ratio_stable_bbox_unmasked/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if i >= len(self.cell_list_for_processing_stable_bbox):
                break
            cell_stable_bbox = self.cell_list_for_processing_stable_bbox[i]
            if cell_stable_bbox.ratio_stable_bbox_unmasked is None:
                continue
            io.imsave(
                savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif",
                cell_stable_bbox.ratio_stable_bbox_unmasked,
            )

    def save_stable_bbox_centered_ratio_images(self):
        if not self.cell_list_for_processing_stable_bbox_centered:
            return

        savepath = self.save_path + '/ratio_stable_bbox_centered/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if i >= len(self.cell_list_for_processing_stable_bbox_centered):
                break
            cell_stable_bbox_centered = self.cell_list_for_processing_stable_bbox_centered[i]
            io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", cell_stable_bbox_centered.ratio)

    def save_stable_bbox_centered_unmasked_ratio_images(self):
        if not self.cell_list_for_processing_stable_bbox_centered:
            return

        savepath = self.save_path + '/ratio_stable_bbox_centered_unmasked/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            if i >= len(self.cell_list_for_processing_stable_bbox_centered):
                break
            cell_stable_bbox_centered = self.cell_list_for_processing_stable_bbox_centered[i]
            if cell_stable_bbox_centered.ratio_centered_unmasked is None:
                continue
            io.imsave(
                savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif",
                cell_stable_bbox_centered.ratio_centered_unmasked,
            )

    def save_preprocessing_checkpoint(self):
        """Persist intermediate data before trimming by time windows."""
        checkpoints_cfg = (self.parameters.get("processing_pipeline", {})
                           .get("checkpoints", {}))
        enabled = bool(checkpoints_cfg.get("save_pre_start", False))

        status_message = f"save_pre_start flag set to {enabled}."
        try:
            if getattr(self, "logger", None) is not None:
                self.logger.log_and_print(message=status_message,
                                          level=logging.INFO,
                                          logger=self.logger)
            else:
                print(status_message)
        except Exception:
            print(status_message)

        if not enabled:
            return

        checkpoint_dir = os.path.join(self.save_path, "checkpoints", "pre_start")
        os.makedirs(checkpoint_dir, exist_ok=True)

        manifest_entries = []
        for idx, cell in enumerate(self.cell_list_for_processing):
            cell_label = f"cell_{idx:04d}"

            ratio_filename = f"{cell_label}_ratio.tif"
            ratio_path = os.path.join(checkpoint_dir, ratio_filename)
            if cell.ratio is None:
                continue
            io.imsave(ratio_path, cell.ratio.astype(np.float32))

            channel1_filename = f"{cell_label}_channel1.npy"
            channel1_path = os.path.join(checkpoint_dir, channel1_filename)
            np.save(channel1_path, cell.give_image_channel1().astype(np.float32))

            channel2_filename = f"{cell_label}_channel2.npy"
            channel2_path = os.path.join(checkpoint_dir, channel2_filename)
            np.save(channel2_path, cell.give_image_channel2().astype(np.float32))

            cell_dataframe_filename = None
            if getattr(cell, "cell_image_data_channel_2", None) is not None:
                cell_dataframe_filename = f"{cell_label}_cell_data.pkl"
                cell_dataframe_path = os.path.join(checkpoint_dir, cell_dataframe_filename)
                cell.cell_image_data_channel_2.to_pickle(cell_dataframe_path)

            mask_filename = None
            if cell.frame_masks is not None:
                mask_filename = f"{cell_label}_frame_masks.npy"
                mask_path = os.path.join(checkpoint_dir, mask_filename)
                np.save(mask_path, cell.frame_masks)

            manifest_entries.append({
                "cell_index": idx,
                "ratio_file": ratio_filename,
                "mask_file": mask_filename,
                "channel1_file": channel1_filename,
                "channel2_file": channel2_filename,
                "cell_dataframe": cell_dataframe_filename,
                "frame_number": int(cell.frame_number),
                "starting_point": int(getattr(cell, "starting_point", 0)),
                "starting_point_auto": int(getattr(cell, "starting_point_auto", -1))
                if hasattr(cell, "starting_point_auto") else None,
            })

        manifest = {
            "measurement": self.measurement_name,
            "frame_rate": self.frames_per_second,
            "time_before_start": self.parameters["properties_of_measurement"].get(
                "time_of_measurement_before_starting_point"),
            "time_after_start": self.parameters["properties_of_measurement"].get(
                "time_of_measurement_after_starting_point"),
            "raw_image_shape": list(self.channel1.shape) if getattr(self, "channel1", None) is not None else None,
            "image_width": int(getattr(self, "x_max", 0)) if getattr(self, "x_max", None) is not None else None,
            "cells": manifest_entries,
        }

        manifest_path = os.path.join(checkpoint_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as manifest_file:
            json.dump(manifest, manifest_file, indent=2)

        message = (f"Saved preprocessing checkpoint with {len(manifest_entries)} cell(s) to "
                   f"{checkpoint_dir}.")
        try:
            if getattr(self, "logger", None) is not None:
                self.logger.log_and_print(message=message,
                                          level=logging.INFO,
                                          logger=self.logger)
            else:
                print(message)
        except Exception:
            print(message)

    def should_load_preprocessing_checkpoint(self) -> bool:
        checkpoints_cfg = (self.parameters.get("processing_pipeline", {})
                           .get("checkpoints", {}))
        return bool(checkpoints_cfg.get("load_pre_start", False))

    def load_preprocessing_checkpoint(self) -> bool:
        checkpoints_cfg = (self.parameters.get("processing_pipeline", {})
                           .get("checkpoints", {}))

        source_hint = str(checkpoints_cfg.get("source_dir", "")) or ""
        candidate_dirs = []

        if source_hint:
            expanded = os.path.expanduser(source_hint)
            if not os.path.isabs(expanded):
                expanded = os.path.join(self.results_folder, expanded)
            expanded = os.path.abspath(expanded)

            if os.path.isfile(expanded):
                if expanded.lower().endswith(".json"):
                    candidate_dirs.append(os.path.dirname(expanded))
            elif os.path.isdir(expanded):
                possible_dirs = [
                    expanded,
                    os.path.join(expanded, "checkpoints"),
                    os.path.join(expanded, "pre_start"),
                    os.path.join(expanded, "checkpoints", "pre_start"),
                ]
                for candidate in possible_dirs:
                    if os.path.isdir(candidate) and candidate not in candidate_dirs:
                        candidate_dirs.append(candidate)

        default_dir = os.path.join(self.save_path, "checkpoints", "pre_start")
        candidate_dirs.append(default_dir)

        checkpoint_dir = None
        manifest_path = None
        for candidate in candidate_dirs:
            if not candidate:
                continue
            candidate_manifest = os.path.join(candidate, "manifest.json")
            if os.path.isfile(candidate_manifest):
                checkpoint_dir = candidate
                manifest_path = candidate_manifest
                break

        if checkpoint_dir is None or manifest_path is None:
            msg = ("No preprocessing checkpoint manifest found. "
                   "Falling back to full preprocessing pipeline.")
            try:
                if getattr(self, "logger", None) is not None:
                    self.logger.log_and_print(message=msg,
                                              level=logging.WARNING,
                                              logger=self.logger)
                else:
                    print(msg)
            except Exception:
                print(msg)
            return False

        measurement_dir = os.path.dirname(checkpoint_dir)
        if os.path.basename(checkpoint_dir) != "pre_start":
            measurement_dir = checkpoint_dir
        elif os.path.basename(measurement_dir) == "checkpoints":
            measurement_dir = os.path.dirname(measurement_dir)

        with open(manifest_path, "r", encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)

        manifest_measurement = manifest.get("measurement")
        if manifest_measurement:
            self.measurement_name = manifest_measurement
            self.save_path = os.path.join(self.results_folder, self.measurement_name)

        if os.path.isdir(measurement_dir):
            self.save_path = measurement_dir

        raw_shape = manifest.get("raw_image_shape")
        if raw_shape:
            try:
                if len(raw_shape) == 3:
                    self.t_max, self.y_max, self.x_max = raw_shape
                elif len(raw_shape) == 2:
                    self.y_max, self.x_max = raw_shape
            except Exception:
                pass

        image_width = manifest.get("image_width", getattr(self, "x_max", None))

        cells_loaded = []
        for entry in manifest.get("cells", []):
            try:
                ratio_file = entry.get("ratio_file")
                if not ratio_file:
                    continue
                ratio_path = os.path.join(checkpoint_dir, ratio_file)
                if not os.path.isfile(ratio_path):
                    continue
                ratio = io.imread(ratio_path).astype(np.float32)

                channel1_path = entry.get("channel1_file")
                if channel1_path:
                    channel1_abs = os.path.join(checkpoint_dir, channel1_path)
                    if os.path.isfile(channel1_abs):
                        channel1_array = np.load(channel1_abs)
                    else:
                        continue
                else:
                    continue

                channel2_path = entry.get("channel2_file")
                if channel2_path:
                    channel2_abs = os.path.join(checkpoint_dir, channel2_path)
                    if os.path.isfile(channel2_abs):
                        channel2_array = np.load(channel2_abs)
                    else:
                        continue
                else:
                    continue

                mask_array = None
                mask_path = entry.get("mask_file")
                if mask_path:
                    mask_abs = os.path.join(checkpoint_dir, mask_path)
                    if os.path.isfile(mask_abs):
                        mask_array = np.load(mask_abs, allow_pickle=True)

                cell_dataframe = None
                df_path = entry.get("cell_dataframe")
                if df_path:
                    df_abs = os.path.join(checkpoint_dir, df_path)
                    if os.path.isfile(df_abs):
                        cell_dataframe = pd.read_pickle(df_abs)

                channel1_image = ChannelImage(channel1_array, self.wl1)
                channel2_image = ChannelImage(channel2_array, self.wl2)
                cell_obj = CellImage(channel1_image,
                                     channel2_image,
                                     image_width if image_width is not None else channel1_array.shape[-1],
                                     cell_dataframe,
                                     mask_array)

                cell_obj.ratio = ratio
                cell_obj.frame_number = int(entry.get("frame_number", ratio.shape[0]))
                cell_obj.starting_point = int(entry.get("starting_point", 0))
                if entry.get("starting_point_auto") is not None:
                    cell_obj.starting_point_auto = int(entry.get("starting_point_auto"))

                cells_loaded.append(cell_obj)
            except Exception as exc:
                warning = f"Failed to load cell from checkpoint: {exc}"
                try:
                    if getattr(self, "logger", None) is not None:
                        self.logger.log_and_print(message=warning,
                                                  level=logging.WARNING,
                                                  logger=self.logger)
                    else:
                        print(warning)
                except Exception:
                    print(warning)
                continue

        if not cells_loaded:
            msg = "Checkpoint manifest could not be loaded or contained no cells."
            try:
                if getattr(self, "logger", None) is not None:
                    self.logger.log_and_print(message=msg,
                                              level=logging.WARNING,
                                              logger=self.logger)
                else:
                    print(msg)
            except Exception:
                print(msg)
            return False

        self.cell_list = cells_loaded
        self.cell_list_for_processing = self.cell_list
        self.cell_list_uncentered = []
        self.cell_list_for_processing_uncentered = []
        self.cell_list_stable_bbox = []
        self.cell_list_for_processing_stable_bbox = []
        self.cell_list_stable_bbox_centered = []
        self.cell_list_for_processing_stable_bbox_centered = []
        self.nb_rois = len(self.cell_list)

        info_message = (f"Loaded preprocessing checkpoint with {len(self.cell_list)} cell(s) "
                        f"from {checkpoint_dir}.")
        try:
            if getattr(self, "logger", None) is not None:
                self.logger.log_and_print(message=info_message,
                                          level=logging.INFO,
                                          logger=self.logger)
            else:
                print(info_message)
        except Exception:
            print(info_message)

        return True

    def global_measurement(self, info_saver):
        global_dataframe = info_saver.global_data
        for i, cell in enumerate(self.cell_list_for_processing):
            cell_global_data = pd.DataFrame()
            starting_point_cell = cell.starting_point
            list_of_time_points = []

            for frame in range(cell.frame_number):
                time_in_seconds = (frame - starting_point_cell) / self.frames_per_second
                list_of_time_points.append(time_in_seconds)

            mean_ratio_value_list = cell.mean_ratio_list
            cell_global_data['time_in_seconds'] = list_of_time_points
            cell_global_data[self.file_name + "_cell_" + str(i)] = mean_ratio_value_list

            global_dataframe = pd.merge(global_dataframe, cell_global_data, on='time_in_seconds', how='left')
        info_saver.global_data = global_dataframe

    def medianfilter(self, channel):
        """"
         Apply a medianfilter on either the channels or the ratio image;
         Pixelvalues of zeroes are excluded in median calculation
         """
        print("\n Medianfilter " + channel + ": ")
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            for idx, cell in enumerate(self.cell_list_for_processing):
                if channel == "channels":
                    window = np.ones([int(self.median_filter_kernel), int(self.median_filter_kernel)])
                    filtered_image_list = []
                    channel_image_list = [cell.give_image_channel1(), cell.give_image_channel2()]
                    for channel_image in channel_image_list:
                        filtered_image = np.empty_like(channel_image)
                        for frame in range(channel_image.shape[0]):
                            filtered_image[frame] = skimage.filters.median(channel_image[frame], footprint=window)
                        filtered_image_list.append(filtered_image)
                    cell.set_image_channel1(filtered_image_list[0])
                    cell.set_image_channel2(filtered_image_list[1])
                    if idx < len(self.cell_list_for_processing_uncentered):
                        cell_uncentered = self.cell_list_for_processing_uncentered[idx]
                        filtered_image_list_uncentered = []
                        channel_image_list_uncentered = [cell_uncentered.give_image_channel1(), cell_uncentered.give_image_channel2()]
                        for channel_image in channel_image_list_uncentered:
                            filtered_image = np.empty_like(channel_image)
                            for frame in range(channel_image.shape[0]):
                                filtered_image[frame] = skimage.filters.median(channel_image[frame], footprint=window)
                            filtered_image_list_uncentered.append(filtered_image)
                        cell_uncentered.set_image_channel1(filtered_image_list_uncentered[0])
                        cell_uncentered.set_image_channel2(filtered_image_list_uncentered[1])
                    if idx < len(self.cell_list_for_processing_stable_bbox):
                        cell_stable_bbox = self.cell_list_for_processing_stable_bbox[idx]
                        filtered_image_list_stable_bbox = []
                        channel_image_list_stable_bbox = [cell_stable_bbox.give_image_channel1(), cell_stable_bbox.give_image_channel2()]
                        for channel_image in channel_image_list_stable_bbox:
                            filtered_image = np.empty_like(channel_image)
                            for frame in range(channel_image.shape[0]):
                                filtered_image[frame] = skimage.filters.median(channel_image[frame], footprint=window)
                            filtered_image_list_stable_bbox.append(filtered_image)
                        cell_stable_bbox.set_image_channel1(filtered_image_list_stable_bbox[0])
                        cell_stable_bbox.set_image_channel2(filtered_image_list_stable_bbox[1])
                    if idx < len(self.cell_list_for_processing_stable_bbox_centered):
                        cell_stable_bbox_centered = self.cell_list_for_processing_stable_bbox_centered[idx]
                        filtered_image_list_stable_bbox_centered = []
                        channel_image_list_stable_bbox_centered = [cell_stable_bbox_centered.give_image_channel1(), cell_stable_bbox_centered.give_image_channel2()]
                        for channel_image in channel_image_list_stable_bbox_centered:
                            filtered_image = np.empty_like(channel_image)
                            for frame in range(channel_image.shape[0]):
                                filtered_image[frame] = skimage.filters.median(channel_image[frame], footprint=window)
                            filtered_image_list_stable_bbox_centered.append(filtered_image)
                        cell_stable_bbox_centered.set_image_channel1(filtered_image_list_stable_bbox_centered[0])
                        cell_stable_bbox_centered.set_image_channel2(filtered_image_list_stable_bbox_centered[1])
                elif channel == 'ratio':
                    window = np.ones([int(self.median_filter_kernel), int(self.median_filter_kernel)])
                    filtered_image_list = []
                    ratio_image_list = [cell.ratio]
                    for ratio_image in ratio_image_list:
                        filtered_image = np.empty_like(ratio_image)
                        for frame in range(ratio_image.shape[0]):
                            filtered_image[frame] = skimage.filters.median(ratio_image[frame], footprint=window)
                        filtered_image_list.append(filtered_image)
                    cell.ratio = filtered_image_list[0]
                    if idx < len(self.cell_list_for_processing_uncentered):
                        cell_uncentered = self.cell_list_for_processing_uncentered[idx]
                        filtered_image = np.empty_like(cell_uncentered.ratio)
                        for frame in range(cell_uncentered.ratio.shape[0]):
                            filtered_image[frame] = skimage.filters.median(cell_uncentered.ratio[frame], footprint=window)
                        cell_uncentered.ratio = filtered_image
                    if idx < len(self.cell_list_for_processing_stable_bbox):
                        cell_stable_bbox = self.cell_list_for_processing_stable_bbox[idx]
                        filtered_image = np.empty_like(cell_stable_bbox.ratio)
                        for frame in range(cell_stable_bbox.ratio.shape[0]):
                            filtered_image[frame] = skimage.filters.median(cell_stable_bbox.ratio[frame], footprint=window)
                        cell_stable_bbox.ratio = filtered_image
                    if idx < len(self.cell_list_for_processing_stable_bbox_centered):
                        cell_stable_bbox_centered = self.cell_list_for_processing_stable_bbox_centered[idx]
                        filtered_image = np.empty_like(cell_stable_bbox_centered.ratio)
                        for frame in range(cell_stable_bbox_centered.ratio.shape[0]):
                            filtered_image[frame] = skimage.filters.median(cell_stable_bbox_centered.ratio[frame], footprint=window)
                        cell_stable_bbox_centered.ratio = filtered_image
                bar()

 
    def return_ratios(self):
        for cell in self.cell_list:
            self.ratio_list.append(cell.calculate_ratio())
        return self.ratio_list


    #----------------------------- Hotspots & Dartboard -------------------------


    def determine_starting_points_local_no_beads(self):

        for i, cell in enumerate(self.cell_list):
            cell.starting_point_auto = self.automated_starting_point(cell)


        for i, cell in enumerate(self.cell_list):
            cell_GUI_no_beads_local = GUInoBeads_local(cell, i, self.parameters,self.ratio_converter, self)
            cell_GUI_no_beads_local.run_main_loop()
            manual_starting_frame = cell_GUI_no_beads_local.starting_frame
            cell_denied = cell_GUI_no_beads_local.cell_denied_flag

            del cell_GUI_no_beads_local

            if cell_denied:
                self.cell_list.remove(cell)
                continue

        # A. some cells have a starting point > 0, see above. Other cells don't have a starting point (=-1).
        # B. First, the mean starting point of cells with starting point > 0 is calculated.
        # C. Next, the starting points of the cells without a useful starting point (=-1) are set to the mean starting
        #    point of  A.

        try:
            individual_valid_starting_points = [cell.starting_point for cell in self.cell_list_for_processing if
                                                cell.starting_point > 0]
            mean_individual_starting_point = sum(individual_valid_starting_points) / len(individual_valid_starting_points)
            cells_without_individual_starting_point = [cell for cell in self.cell_list_for_processing if cell.starting_point == -1]
            for cell in cells_without_individual_starting_point:
                cell.starting_point = int(mean_individual_starting_point)
        except Exception as E:
            print(E)
            self.logger.log_and_print(message="Exception occurred: Error in starting point definition !",
                                      level=logging.ERROR, logger=self.logger)


    def automated_starting_point(self, cell):

        # Specify the desired slope threshold per unit change in frame rate
        slope_threshold_per_fps = 0.0025
        # test

        slope_threshold_per_second = slope_threshold_per_fps * self.frames_per_second

        # Adjust the slope threshold based on the actual frame rate, 40.0
        # slope_threshold = 0.25*slope_threshold_per_fps * (40.0/actual_fps)

        cell.starting_point = 0

        time_points = np.arange(cell.frame_number)
        global_signal = np.array(cell.mean_ratio_list)

        # Smooth the global signal
        smoothed_global_signal = savgol_filter(global_signal, window_length=5, polyorder=3)

        # Calculate the first derivative (slope)
        slope = np.gradient(smoothed_global_signal)

        # Smooth the slope using a Savitzky-Golay filter
        smoothed_slope = savgol_filter(slope, window_length=5, polyorder=3)

        # Find the point where the slope surpasses the threshold
        transition_point = []

        # Specify the consecutive frames threshold
        consecutive_frames_threshold = 15

        # Check if the slope exceeds the threshold for at least x frames
        for t in range(len(time_points) - int(consecutive_frames_threshold)):
            if np.all(smoothed_slope[t:t + int(consecutive_frames_threshold)] > slope_threshold_per_fps):
                transition_point.append(t)
                break

        # Plot the original data, smoothed data, and the slope
        # plt.plot(time_points, global_signal, label='Original Data')
        #plt.plot(time_points, smoothed_global_signal, label='Smoothed Data')
        #plt.plot(time_points, slope, label='Slope')
        #for tp in transition_point:
        #    plt.axvline(x=tp, color='r', linestyle='--', label='Transition Point')
        #plt.xlabel('Time Points')
        #plt.ylabel('Global Signal')
        #plt.legend()
        # plt.show()

            if len(transition_point) > 0 and transition_point[0]>0:
                cell.starting_point = transition_point[0]  # individual starting point
            else:
                cell.starting_point = -1  # no individual starting point
            
            return cell.starting_point
        
        # A. some cells have a starting point > 0, see above. Other cells don't have a starting point (=-1).
        # B. First, the mean starting point of cells with starting point > 0 is calculated.
        # C. Next, the starting points of the cells without a useful starting point (=-1) are set to the mean starting
        #    point of  A.
        individual_starting_points = [cell.starting_point for cell in self.cell_list_for_processing if cell.starting_point > 0]
        if not individual_starting_points:
            return

        mean_individual_starting_point = sum(individual_starting_points)/len(individual_starting_points)
        cells_without_individual_starting_point = [cell for cell in self.cell_list_for_processing if cell.starting_point == -1]
        for cell in cells_without_individual_starting_point:
            cell.starting_point = int(mean_individual_starting_point)

        if len(transition_point) > 0 and transition_point[0]>0:
            cell.starting_point = transition_point[0]  # individual starting point
        else:
            cell.starting_point = -1  # no individual starting point

        return cell.starting_point
# Matlab version
    def find_exp_start(self, cell, tol=0.1, av_factor=0.05, show_plot=False, debug=True):
        """
        Alternative starting point detection method based on exponential signal onset.
        Python port of findExpStart.m

        Parameters
        ----------
        cell : CellImage
            Cell object containing the data to analyze
        tol : float, default 0.1
            Tolerance (in log-intensity units) for declaring onset:
            first frame where |log(I) - linear_continuation| < tol.
        av_factor : float, default 0.05
            Moving-average window as a fraction of total frames.
        show_plot : bool, default False
            If True, show the diagnostic plot.
        debug : bool, default True
            If True, print debugging information to terminal.

        Returns
        -------
        start_frame : int
            Index of the detected start frame (0-based) or -1 if not found.
        """

        # Get data from cell
        img_m = np.array(cell.mean_ratio_list)
        N = img_m.size
        
        if debug:
            print(f"[DEBUG] find_exp_start: Starting analysis with {N} frames")
            print(f"[DEBUG] Signal range: {np.min(img_m):.4f} to {np.max(img_m):.4f}")
        
        if N < 5:
            if debug:
                print(f"[DEBUG] FAILURE: Time series too short ({N} frames, need at least 5)")
            if show_plot:
                print("Warning: Time series too short.")
            # Store failure diagnostics in cell object
            if hasattr(cell, 'exp_start_diagnostics'):
                cell.exp_start_diagnostics = {"reason": "time_series_too_short"}
            return -1

        # ---- 1) Smoothing and log ----
        def movmean(x, w):
            w = max(1, int(w))
            if w == 1:
                return x.copy()
            k = np.ones(w, dtype=float) / w
            return np.convolve(x, k, mode="same")

        av = max(1, int(np.floor(av_factor * N)))
        img_ms = movmean(img_m, av)

        eps = np.finfo(float).eps
        img_ms_log = np.log(np.maximum(img_ms, eps))
        img_g = np.gradient(img_ms_log)
        
        if debug:
            print(f"[DEBUG] Smoothing: window size = {av} frames")
            print(f"[DEBUG] Log signal range: {np.min(img_ms_log):.4f} to {np.max(img_ms_log):.4f}")

        # ---- 2) Zero-crossings of smoothed derivative ----
        zc = np.where(np.diff(np.sign(movmean(img_g, av))) != 0)[0]
        number_frames = img_ms_log.size
        zc = np.r_[0, zc, number_frames - 1]
        if debug:
            print(f"[DEBUG] Found {zc.size} zero-crossings (extrema)")
            if zc.size > 0:
                print(f"[DEBUG] Zero-crossing positions: {zc}")
        
        if zc.size < 2:
            # Not enough extrema to define a segment
            if debug:
                print(f"[DEBUG] FAILURE: Not enough extrema ({zc.size} found, need at least 2)")
            if show_plot:
                print("Warning: not enough extrema; no fit can be found.")
            # Store failure diagnostics in cell object
            if hasattr(cell, 'exp_start_diagnostics'):
                cell.exp_start_diagnostics = {"reason": "not_enough_extrema"}
            return -1

        # ---- 3) Pick relevant rising segment (≥ 30% total log range) ----
        total_range = float(np.max(img_ms_log) - np.min(img_ms_log))
        if debug:
            print(f"[DEBUG] Total log range: {total_range:.4f}")
            print(f"[DEBUG] Looking for segments with ≥30% rise (≥{0.3 * total_range:.4f})")
        
        if total_range <= 0:
            if debug:
                print(f"[DEBUG] FAILURE: Non-positive total range ({total_range:.4f})")
            if show_plot:
                print("Warning: non-positive total range; no fit can be found.")
            # Store failure diagnostics in cell object
            if hasattr(cell, 'exp_start_diagnostics'):
                cell.exp_start_diagnostics = {"reason": "non_positive_total_range"}
            return -1

        # Sort extrema by their log value (desc) and walk down until a valid rise is found
        order = np.argsort(img_ms_log[zc])[::-1]  # indices into zc
        x1 = x2 = None
        range_size = None

        if debug:
            print(f"[DEBUG] Checking {len(order)} extrema pairs for valid rising segments...")

        for ord_idx in order:
            if ord_idx < 1:
                continue
            I = ord_idx
            x1_candidate = int(zc[I - 1])
            x2_candidate = int(zc[I])
            y1 = img_ms_log[x1_candidate]
            y2 = img_ms_log[x2_candidate]
            rise = y2 - y1
            if debug:
                print(f"[DEBUG] Segment {x1_candidate}-{x2_candidate}: rise={rise:.4f} (need ≥{0.3 * total_range:.4f})")
            if rise >= 0.3 * total_range:
                x1, x2 = x1_candidate, x2_candidate
                range_size = rise
                if debug:
                    print(f"[DEBUG] SUCCESS: Found valid segment {x1}-{x2} with rise={rise:.4f}")
                break

        if x1 is None or x2 is None or range_size is None:
            if debug:
                print(f"[DEBUG] FAILURE: No segment found with ≥30% rise (threshold: {0.3 * total_range:.4f})")
            if show_plot:
                print("Warning: no fit can be found (no segment with ≥30% rise).")
            # Store failure diagnostics in cell object
            if hasattr(cell, 'exp_start_diagnostics'):
                cell.exp_start_diagnostics = {"reason": "no_segment_meets_30pct_threshold"}
            return -1

        # ---- 4) Find the linear ascending sub-segment and fit it ----
        # Approximation of MATLAB ischange(...,'linear'): find the steepest
        # m-length window in [x1, x2] by linear regression slope.
        seg_len = x2 - x1 + 1
        if debug:
            print(f"[DEBUG] Chosen segment length: {seg_len} frames")
        
        if seg_len < 5:
            if debug:
                print(f"[DEBUG] FAILURE: Chosen segment too short ({seg_len} frames, need at least 5)")
            if show_plot:
                print("Warning: chosen segment too short.")
            # Store failure diagnostics in cell object
            if hasattr(cell, 'exp_start_diagnostics'):
                cell.exp_start_diagnostics = {"reason": "segment_too_short", "x1": x1, "x2": x2}
            return -1

        m = max(10, int(0.2 * seg_len))
        m = min(m, seg_len)  # clamp

        if debug:
            print(f"[DEBUG] Linear fit window size: {m} frames")
            print(f"[DEBUG] Searching for steepest slope in segment {x1}-{x2}...")

        best_slope = -np.inf
        lin_start = x1
        for s in range(x1, x2 - m + 2):
            y = img_ms_log[s : s + m]
            x = np.arange(m, dtype=float)
            # linear least squares
            A = np.vstack([x, np.ones_like(x)]).T
            slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
            if slope > best_slope:
                best_slope = slope
                lin_start = s
                lin_intercept = intercept

        if debug:
            print(f"[DEBUG] Best linear fit: start={lin_start}, slope={best_slope:.6f}")

        lin_end = lin_start + m - 1
        x = np.arange(m, dtype=float)
        # final fit on chosen window
        A = np.vstack([x, np.ones_like(x)]).T
        slope, intercept = np.linalg.lstsq(A, img_ms_log[lin_start : lin_end + 1], rcond=None)[0]

        # ---- 5) Extend the fitted line across all frames ----
        # Align so that at frame = lin_start, line equals the first point of that window
        t = np.arange(N, dtype=float)
        lin_cont = slope * (t - lin_start) + intercept

        # ---- 6) First frame within tolerance -> start_frame ----
        d = np.abs(img_ms_log - lin_cont)
        hits = np.where(d < tol)[0]
        start_frame = int(hits[0]) if hits.size else -1
        
        if debug:
            print(f"[DEBUG] Tolerance check: tol={tol}")
            print(f"[DEBUG] Found {hits.size} frames within tolerance")
            if hits.size > 0:
                print(f"[DEBUG] First hit at frame: {start_frame}")
            else:
                print(f"[DEBUG] FAILURE: No frames found within tolerance {tol}")
                print(f"[DEBUG] Minimum deviation: {np.min(d):.6f}")

        # ---- 7) Plot (optional) ----
        if show_plot:
            plt.figure(figsize=(9, 5))
            plt.plot(t, img_ms_log, label="Smoothed log-intensity")
            plt.plot(t, lin_cont, "--", label="Linear fit continuation")
            plt.axvspan(x1, x2, alpha=0.15, label="Chosen rising interval")
            plt.plot(t, lin_cont + tol, ":", label="+tol")
            plt.plot(t, lin_cont - tol, ":", label="-tol")
            if start_frame >= 0:
                plt.plot(start_frame, img_ms_log[start_frame], "D", label=f"Start: {start_frame}")
            plt.title(f"Cell {cell} — start detection")
            plt.xlabel("frames")
            plt.ylabel("log(I)")
            plt.legend()
            plt.tight_layout()
            plt.show()

        diagnostics = {
            "x1": x1,
            "x2": x2,
            "range_size": range_size,
            "total_range": total_range,
            "lin_start": lin_start,
            "lin_end": lin_end,
            "slope": float(slope),
            "intercept": float(intercept),
        }
        
        # Store diagnostics in cell object for debugging if needed
        if hasattr(cell, 'exp_start_diagnostics'):
            cell.exp_start_diagnostics = diagnostics
        
        # Return only the starting frame to match the interface of automated_starting_point()
        if debug:
            if start_frame >= 0:
                print(f"[DEBUG] SUCCESS: Starting point found at frame {start_frame}")
            else:
                print(f"[DEBUG] FAILURE: No starting point found")
        
        return start_frame

    def assign_bead_contacts_to_cells(self):
        for bead_contact in self.list_of_bead_contacts:
            bead_contact_position = bead_contact.return_bead_contact_position()
            bead_contact_xpos = bead_contact_position[0]
            bead_contact_ypos = bead_contact_position[1]

            starting_point = bead_contact.return_time_of_bead_contact()
            selected_position_inside_cell = bead_contact.return_selected_position_inside_cell()
            selected_x_position_inside_cell, selected_y_position_inside_cell = selected_position_inside_cell[0], selected_position_inside_cell[1]

            for idx, cell in enumerate(self.cell_list):
                cell_uncentered = self.cell_list_uncentered[idx]
                dataframe = cell.cell_image_data_channel_2
                cell_data_for_frame = dataframe.loc[dataframe['frame'] == starting_point]
                if cell_data_for_frame.empty:
                    available_frames = dataframe['frame'].values.tolist()
                    print(
                        f"No tracked frame {starting_point} for this cell; "
                        f"available frames: {available_frames}"
                    )
                bbox_for_frame = cell_data_for_frame['bbox'].values.tolist()[0]
                min_row, min_col, max_row, max_col = bbox_for_frame

                if min_row <= selected_y_position_inside_cell <= max_row and min_col <= selected_x_position_inside_cell <= max_col:  # if bead contact inside bounding box of the cell
                    cell.starting_point = starting_point
                    cell_uncentered.starting_point = starting_point
                    if idx < len(self.cell_list_stable_bbox):
                        self.cell_list_stable_bbox[idx].starting_point = starting_point
                    if idx < len(self.cell_list_stable_bbox_centered):
                        self.cell_list_stable_bbox_centered[idx].starting_point = starting_point
                    centroid_x_coord_cell = cell_data_for_frame['x'].values.tolist()[0]
                    centroid_y_coord_cell = cell_data_for_frame['y'].values.tolist()[0]
                    location_on_clock = bead_contact.calculate_contact_position(bead_contact_xpos,
                                                                                bead_contact_ypos,
                                                                                centroid_x_coord_cell,
                                                                                centroid_y_coord_cell,
                                                                                self.dartboard_number_of_sections)
                    cell.bead_contact_site = location_on_clock
                    cell_uncentered.bead_contact_site = location_on_clock
                    cell.has_bead_contact = True
                    cell_uncentered.has_bead_contact = True
                    if idx < len(self.cell_list_stable_bbox):
                        self.cell_list_stable_bbox[idx].bead_contact_site = location_on_clock
                        self.cell_list_stable_bbox[idx].has_bead_contact = True
                    if idx < len(self.cell_list_stable_bbox_centered):
                        self.cell_list_stable_bbox_centered[idx].bead_contact_site = location_on_clock
                        self.cell_list_stable_bbox_centered[idx].has_bead_contact = True

        self.cell_list_for_processing = [cell for cell in self.cell_list if cell.has_bead_contact]
        self.cell_list_for_processing_uncentered = [cell for cell in self.cell_list_uncentered if cell.has_bead_contact]
        self.cell_list_for_processing_stable_bbox = [cell for cell in self.cell_list_stable_bbox if cell.has_bead_contact]
        self.cell_list_for_processing_stable_bbox_centered = [cell for cell in self.cell_list_stable_bbox_centered if cell.has_bead_contact]

    def hotspot_detection(self, cells_dict):
        number_of_analyzed_cells = 0
        number_of_responding_cells = 0

        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            for i, cell in enumerate(self.cell_list_for_processing):
                try:
                    number_of_analyzed_cells += 1
                    hd_start = timeit.default_timer()
                    ratio = cells_dict[cell][0]
                    mean_ratio_value_list = cells_dict[cell][1]

                    start_frame, end_frame, cell_has_hotspots_after_bead_contact, frames_before_starting_point = self.detect_hotspots(ratio, mean_ratio_value_list, cell, i)
                    if cell_has_hotspots_after_bead_contact:
                        number_of_responding_cells += 1
                    hd_took = (timeit.default_timer() - hd_start) * 1000.0
                    hd_sec, hd_min, hd_hour = convert_ms_to_smh(int(hd_took))
                    self.logger.log_and_print(message=f"Hotspot detection of cell {i} "
                                                      f"took: {hd_hour:02d} h: {hd_min:02d} m: {hd_sec:02d} s :{int(hd_took):02d} ms",
                                              level=logging.INFO, logger=self.logger)
                except Exception as E:
                    print(E)
                    self.logger.log_and_print(message="Exception occurred: Error in Hotspot Detection !",
                                              level=logging.ERROR, logger=self.logger)
                    continue

                try:
                    microdomains_in_each_frame = self.save_measurements(i, cell.signal_data, start_frame, end_frame, frames_before_starting_point)
                    self.microdomains_timelines_dict[(self.file_name, i)] = microdomains_in_each_frame

                except Exception as E:
                    print(E)
                    self.logger.log_and_print(message="Exception occurred: Error in saving measurements",
                                              level=logging.ERROR, logger=self.logger)
                    continue

                bar()
        return number_of_analyzed_cells, number_of_responding_cells, self.microdomains_timelines_dict

    def give_frame_information_cell(self, cell):
        frames_before_starting_point = self.time_of_measurement_before_starting_point * self.frames_per_second
        start_frame = int(cell.starting_point - frames_before_starting_point)

        if start_frame < 0:
            frames_before_starting_point += start_frame
            start_frame = 0

        frame_number_cell = cell.frame_number

        if start_frame + self.duration_of_measurement >= frame_number_cell:
            end_frame = frame_number_cell - 1
        else:
            end_frame = int(
                start_frame + frames_before_starting_point + self.time_of_measurement_after_starting_point * self.frames_per_second)
        return start_frame, end_frame, frames_before_starting_point

    def detect_hotspots(self, ratio_image, mean_ratio_value_list, cell, i):
        start_frame, end_frame, frames_before_starting_point = self.give_frame_information_cell(cell)
        mean_ratio_value_list_short = mean_ratio_value_list[start_frame:end_frame]

        measurement_microdomains = self.hotspotdetector.measure_microdomains(ratio_image,
                                                                             start_frame,
                                                                             end_frame,
                                                                             mean_ratio_value_list_short,
                                                                             self.spotHeight,
                                                                             self.minimum_spotsize,  # lower area limit in pixels
                                                                             20,  # upper area limit in pixels
                                                                             self.cell_type,
                                                                             frames_before_starting_point)
        cell.signal_data = measurement_microdomains
        # number_of_analyzed_frames = end_frame - start_frame
        if not measurement_microdomains.empty:
            dataframe_after_bead_contact = measurement_microdomains.loc[
                measurement_microdomains['frame'] > (int(start_frame + frames_before_starting_point))].copy()
        else:
            dataframe_after_bead_contact = pd.DataFrame()
        cell_has_hotspots_after_bead_contact = not dataframe_after_bead_contact.empty
        return start_frame, end_frame, cell_has_hotspots_after_bead_contact, frames_before_starting_point

    def save_measurements(self, i, cell_signal_data, start_frame, end_frame, frames_before_starting_point):
        microdomains_in_each_frame = self.hotspotdetector.save_dataframes(self.file_name,
                                                                          i,
                                                                          cell_signal_data,
                                                                          start_frame,
                                                                          end_frame,
                                                                          self.duration_of_measurement,
                                                                          frames_before_starting_point,
                                                                          self.time_of_measurement_after_starting_point)
        return microdomains_in_each_frame

    def dartboard(self, normalized_cells_dict, info_saver):
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            for i, cell in enumerate(self.cell_list_for_processing):
                try:
                    db_start = timeit.default_timer()

                    centroid_coords_list = normalized_cells_dict[cell][3]
                    radii_after_normalization = normalized_cells_dict[cell][2]
                    start_frame, end_frame, frames_before_starting_point = self.give_frame_information_cell(cell)

                    self.generate_dartboard_data_single_cell(centroid_coords_list,
                                                             cell,
                                                             radii_after_normalization,
                                                             i,
                                                             start_frame,
                                                             end_frame,
                                                             self.file_name,
                                                             frames_before_starting_point)
                    db_took = (timeit.default_timer() - db_start) * 1000.0
                    db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
                    self.logger.log_and_print(message=f"Dartboard analysis of cell {i} "
                                                      f"took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms",
                                              level=logging.INFO, logger=self.logger)

                except Exception as E:
                    print(E)
                    self.logger.log_and_print(message="Exception occurred: Error in Dartboard (single cell)",
                                              level=logging.ERROR, logger=self.logger)
                    continue

                bar()

    def save_dartboard_data_single_cell(self, dartboard_data, cell_index, cell):
        dartboard_data_filename = self.file_name + '_dartboard_data_cell_' + str(cell_index)
        self.dartboard_generator.save_dartboard_data_for_single_cell(dartboard_data_filename, dartboard_data, cell)

    def generate_dartboard_data_single_cell(self, centroid_coords_list, cell, radii_after_normalization, cell_index, start_frame, end_frame, filename, frames_before_starting_point):

        # create new dataframe for single cell
        column_names = ['frame', 'time in seconds', '1 outer', '1 middle', '1 inner',
                        '2 outer', '2 middle', '2 inner',
                        '3 outer', '3 middle', '3 inner',
                        '4 outer', '4 middle', '4 inner',
                        '5 outer', '5 middle', '5 inner',
                        '6 outer', '6 middle', '6 inner',
                        '7 outer', '7 middle', '7 inner',
                        '8 outer', '8 middle', '8 inner',
                        '9 outer', '9 middle', '9 inner',
                        '10 outer', '10 middle', '10 inner',
                        '11 outer', '11 middle', '11 inner',
                        '12 outer', '12 middle', '12 inner',
                        'bulls eye']

        normalized_dartboard_data_table_single_cell = pd.DataFrame(0, index=np.arange(0, end_frame-start_frame), columns=column_names)
        normalized_dartboard_data_table_single_cell['time in seconds'] = normalized_dartboard_data_table_single_cell['time in seconds'].astype('float')

        for frame in range(start_frame, end_frame):
            normalized_frame = frame - start_frame
            normalized_time_in_sec = (normalized_frame-frames_before_starting_point)/self.frames_per_second
            normalized_dartboard_data_table_single_cell = self.dartboard_generator.append_normalized_frame_data(frame, normalized_frame, normalized_time_in_sec, normalized_dartboard_data_table_single_cell, centroid_coords_list[frame], radii_after_normalization[frame] + 2, cell_index, column_names, cell.signal_data, cell)

        cell.normalized_dartboard_data_table = normalized_dartboard_data_table_single_cell

        os.makedirs(self.save_path + '/Dartboards/Dartboard_data', exist_ok=True)
        with pd.ExcelWriter(self.save_path + '/Dartboards/Dartboard_data/' + filename + 'normalized_dartboard_data_table_cell_' + str(cell_index) + ".xlsx") as writer:
            normalized_dartboard_data_table_single_cell.to_excel(writer, index=False)

        os.makedirs(self.results_folder + '/Dartboards/Dartboard_data', exist_ok=True)
        with pd.ExcelWriter(self.results_folder + '/Dartboards/Dartboard_data/' + filename + 'normalized_dartboard_data_table_cell_' + str(cell_index) + ".xlsx") as writer:
            normalized_dartboard_data_table_single_cell.to_excel(writer, index=False)


    def normalize_average_dartboard_data_one_cell(self, average_dartboard_data, real_bead_contact_site,
                                                  normalized_bead_contact_site):
        return self.dartboard_generator.normalize_dartboard_data_to_bead_contact(average_dartboard_data,
                                                                                 real_bead_contact_site,
                                                                                 normalized_bead_contact_site)

    def generate_average_and_save_dartboard_multiple_cells(self, number_of_cells, dartboard_data_multiple_cells,
                                                           filename):
        average_dartboard_data_multiple_cells = self.dartboard_generator.calculate_mean_dartboard_multiple_cells(
            number_of_cells,
            dartboard_data_multiple_cells,
            self.dartboard_number_of_sections,
            self.dartboard_number_of_areas_per_section,
            filename)

        self.dartboard_generator.save_dartboard_plot(average_dartboard_data_multiple_cells,
                                                     len(dartboard_data_multiple_cells),
                                                     self.dartboard_number_of_sections,
                                                     self.dartboard_number_of_areas_per_section)
        return average_dartboard_data_multiple_cells

    # ------------------------------------------ Generation of cells_dict ------------------------------------

    def generate_cell_dict_without_shape_normalization(self):
        cells_dict = {}
        for i, cell in enumerate(self.cell_list_for_processing):
            time.sleep(.005)
            ratio = cell.give_ratio_image()
            # mean_ratio_value_list, _ = self.extract_mean_ratio_and_radii(ratio)
            cells_dict[cell] = (ratio, cell.mean_ratio_list)
        return cells_dict
    # ------------------------------------------ Shape Normalization ------------------------------------

    def apply_shape_normalization(self):
        savepath = self.save_path + '/normalization/'
        os.makedirs(savepath, exist_ok=True)

        normalized_cells_dict = {}

        print("\n")
        self.logger.log_and_print(message="Processing now continues with: ", level=logging.INFO, logger=self.logger)
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            for i, cell in enumerate(self.cell_list_for_processing):
                time.sleep(.005)
                # ratio = cell.give_ratio_image()
                try:
                    sh_start = timeit.default_timer()
                    normalized_ratio, centroid_coords_list = self.normalize_cell_shape(cell)
                    mean_ratio_value_list, radii_after_normalization = self.extract_mean_ratio_and_radii(
                        normalized_ratio)
                    normalized_cells_dict[cell] = (normalized_ratio, mean_ratio_value_list, radii_after_normalization, centroid_coords_list)

                    cell.mean_ratio_list = mean_ratio_value_list

                    sh_took = (timeit.default_timer() - sh_start) * 1000.0
                    sh_sec, sh_min, sh_hour = convert_ms_to_smh(int(sh_took))
                    self.logger.log_and_print(message=f"Shape normalization of cell {i} "
                                                      f"took: {sh_hour:02d} h: {sh_min:02d} m: {sh_sec:02d} s :{int(sh_took):02d} ms",
                                              level=logging.INFO, logger=self.logger)
                except Exception as E:
                    print(E)
                    self.logger.log_and_print(message="Exception occurred: Error in shape normalization",
                                              level=logging.ERROR, logger=self.logger)
                    continue

                # io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", ratio)
                io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio_normalized' + ".tif",
                          normalized_ratio)

                bar()
        return normalized_cells_dict

    def normalize_cell_shape(self, cell):
        df = cell.cell_image_data_channel_2
        shifted_edge_x = df['edge_x'] + df['xshift']
        shifted_edge_y = df['edge_y'] + df['yshift']
        shifted_centroid_x = df["x_centroid_minus_bbox"] + df['xshift']
        shifted_centroid_y = df["y_centroid_minus_bbox"] + df['yshift']
        edge_list = []
        centroid_list = []
        for i in range(len(shifted_edge_x)):
            e = np.vstack((shifted_edge_x[i], shifted_edge_y[i]))
            c = np.vstack((shifted_centroid_x[i], shifted_centroid_y[i]))
            edge_list.append(e)
            centroid_list.append(c)
        SN = ShapeNormalization(cell.ratio, cell.channel1.image, cell.channel2.image, self.model,
                                edge_list, centroid_list)

        cell.normalized_ratio_image = SN.apply_shape_normalization()
        centroid_coords_list = SN.get_centroid_coords_list()
        return cell.normalized_ratio_image, centroid_coords_list

    def extract_mean_ratio_and_radii(self, image_series):
        mean_ratio_value_list = []
        radii_list = []
        frame_number = len(image_series)

        for frame in range(frame_number):
            current_frame = image_series[frame]
            thresholded_image = current_frame > 0.01  # exclude background from measurement
            # io.imshow(thresholded_image)
            # plt.show()
            label = skimage.measure.label(thresholded_image)
            regions = skimage.measure.regionprops(label_image=label, intensity_image=current_frame)
            # print("frame :" + str(frame))
            largest_region, largest_area = self.give_largest_region(regions)  # largest area in pixels
            mean_ratio_value_of_largest_area = largest_region.intensity_mean
            mean_ratio_value_list.append(mean_ratio_value_of_largest_area)

            current_radius = math.sqrt(largest_area / math.pi)  # Area = r**2 * math.pi
            radii_list.append(current_radius)

        return mean_ratio_value_list, radii_list

    def give_largest_region(self, regions):
        areas = []
        for region in regions:
            area = region.area
            areas.append(area)
        index_largest_area = areas.index(max(areas))
        return regions[index_largest_area], areas[index_largest_area]

    def give_mean_amplitude_list(self):
        mean_amplitude_list_of_cells = []
        for i, cell in enumerate(self.cell_list_for_processing):
            cell_mean_signal_amplitude = cell.calculate_mean_amplitude_of_signals_after_bead_contact()
            if cell_mean_signal_amplitude is not None:
                mean_amplitude_list_of_cells.append((self.file_name,i,cell_mean_signal_amplitude))
        return mean_amplitude_list_of_cells



    # --------------------------- saving results -----------------------------------------

    def save_image_files(self):
        """
        Saves the image files within the cells of the cell list
        """
        for i, cell in enumerate(self.cell_list_for_processing):
            save_path = self.save_path + '/cell_image_processed_files/'
            os.makedirs(save_path, exist_ok=True)
            io.imsave(save_path + '/' + self.measurement_name + cell.to_string(i) + '_channel_1' + '.tif',
                      cell.give_image_channel1(),
                      check_contrast=False)

            io.imsave(save_path + '/' + self.measurement_name + cell.to_string(i) + '_channel_2' + '.tif',
                      cell.give_image_channel2(),
                      check_contrast=False)

    def save_ratio_image_files(self):
        save_path = self.save_path + '/cell_image_ratio_files/'
        os.makedirs(save_path, exist_ok=True)
        for i, cell in enumerate(self.cell_list_for_processing):
            io.imsave(save_path + '/'+ self.measurement_name + cell.to_string(i) + '_ratio_image' + '.tif', cell.give_ratio_image(), check_contrast=False)
