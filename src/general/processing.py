import logging
import math
import skimage.io as io
import numpy as np
import skimage.measure
from alive_progress import alive_bar
import time
import pandas as pd
import os
import timeit
from stardist.models import StarDist2D
import matplotlib.pyplot as plt

from src.general.cell import CellImage, ChannelImage
from src.postprocessing.segmentation import SegmentationSD
from src.postprocessing.CellTracker_ROI import CellTracker
from src.postprocessing.deconvolution import TDEDeconvolution, LRDeconvolution, BaseDecon
from src.postprocessing.registration import Registration_SITK, Registration_SR
from src.analysis import HotSpotDetection
from src.shapenormalization.shapenormalization import ShapeNormalization
from src.analysis.Dartboard import DartboardGenerator
from src.postprocessing.Bleaching import BleachingAdditiveNoFit, BleachingMultiplicativeSimple, BleachingBiexponentialFitAdditive
from src.general.RatioToConcentrationConverter import RatioConverter
from src.postprocessing.BackgroundSubtraction import BackgroundSubtractor

from src.general.load_data import load_data
from scipy.signal import savgol_filter

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
        self.segmentation_result_dict = {}
        self.deconvolution_result_dict = {}
        self.cell_list_for_processing = self.cell_list
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

        # cell tracking & segmentation
        self.scale_pixels_per_micron = self.parameters["properties_of_measurement"]["scale"]
        self.cell_tracker = CellTracker(self.scale_pixels_per_micron)
        self.model = StarDist2D.from_pretrained('2D_versatile_fluo')
        self.segmentation = SegmentationSD(self.model)

        # background subtraction
        self.background_subtractor = BackgroundSubtractor(self.segmentation)
        # deconvolution
        # self.deconvolution_parameters = self.parameters["deconvolution"]
        if self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_algorithm"] == "TDE":
            self.deconvolution = TDEDeconvolution()
        elif self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_algorithm"] == "LR":
            self.deconvolution = LRDeconvolution()
        else:
            self.deconvolution = BaseDecon()
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
        # self.measurement_name = self.day_of_measurement + '_' + self.experiment_name
        self.measurement_name = self.day_of_measurement + '_' + self.experiment_name + '_' + self.file_name
        self.results_folder = self.parameters["input_output"]["results_dir"]
        self.save_path = self.results_folder + '/' + self.measurement_name
        self.frame_number = len(self.channel1)
        self.cell_type = self.parameters["properties_of_measurement"]["cell_type"]
        self.spotHeight = None
        if self.cell_type == 'primary':
            self.spotHeight = 112.5  # [Ca2+] = 112.5 nM
        elif self.cell_type == 'jurkat':
            self.spotHeight = 72
        elif self.cell_type == 'NK':
            self.spotHeight = 72  # needs to be checked
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
            try:
                channel1 = load_data(filename, channel_format)
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
            for cell in self.cell_list_for_processing:
                roi_channel1, roi_channel2 = cell.channel1.image, cell.channel2.image

                roi_channel1_decon, roi_channel2_decon = self.deconvolution.execute(roi_channel1, roi_channel2,
                                                                                    self.parameters)

                cell.set_image_channel1(roi_channel1_decon)
                cell.set_image_channel2(roi_channel2_decon)

                bar()


    def clear_outside_of_cells(self):
        self.background_subtractor.clear_outside_of_cells(self.cell_list_for_processing)

    def background_subtraction(self, channel_1, channel_2):
        print("\nBackground subtraction: ")
        with alive_bar(1, force_tty=True) as bar:
            time.sleep(.005)
            # background_label_first_frame = self.segmentation.stardist_segmentation_in_frame(channel_2[0])
            channel_1_background_subtracted = self.background_subtractor.subtract_background(channel_1)
            channel_2_background_subtracted = self.background_subtractor.subtract_background(channel_2)
            bar()
        return channel_1_background_subtracted, channel_2_background_subtracted

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
                bar()

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
        # -- PROCESSING OF WHOLE IMAGE CHANNELS --
        # channel registration
        if self.parameters["processing_pipeline"]["postprocessing"]["channel_alignment_in_pipeline"]:
            self.channel2 = self.registration.channel_registration(self.channel1, self.channel2,
                                                                   self.parameters["processing_pipeline"]["postprocessing"]["channel_alignment_each_frame"])

        # background subtraction
        if self.parameters["processing_pipeline"]["postprocessing"]["background_sub_in_pipeline"]:
            self.channel1, self.channel2 = self.background_subtraction(self.channel1, self.channel2)

        # segmentation of cells, tracking
        self.segmentation_result_dict = self.select_rois()

        # cell images
        self.create_cell_images(self.segmentation_result_dict)

        # -- PROCESSING OF CELL IMAGES --
        if self.parameters["properties_of_measurement"]["bead_contact"]:  # if "bead contacts" was elected in the GUI
            # assign bead contacts to cells
            self.assign_bead_contacts_to_cells()
        else:
            if self.parameters["properties_of_measurement"]["imaging_local_or_global"] == 'global':
                for i, cell in enumerate(self.cell_list):
                    cell.starting_point = self.time_of_addition

        # deconvolution
        if self.parameters["processing_pipeline"]["postprocessing"]["deconvolution_in_pipeline"]:
            self.deconvolve_cell_images()

        # bleaching correction
        if self.parameters["processing_pipeline"]["postprocessing"]["bleaching_correction_in_pipeline"]:
            self.bleaching_correction()

        # first median filter
        if self.deconvolution.give_name() != "TDE Deconvolution":
            self.medianfilter("channels")

        # generation of ratio images
        self.generate_ratio_images()

        # second median filter
        if self.deconvolution.give_name() != "TDE Deconvolution":
            self.medianfilter("ratio")

        # clear area outside the cells
        self.clear_outside_of_cells()

        # save ratio images of the cells
        self.save_ratio_images()

        # measure mean ratio values in all frames
        for cell in self.cell_list_for_processing:
            cell.mean_ratio_list = cell.measure_mean_ratio_in_all_frames()

        # determine starting points for local imaging, if no beads
        if not self.parameters["properties_of_measurement"]["bead_contact"] and self.parameters["properties_of_measurement"]["imaging_local_or_global"] == 'local':
            self.determine_starting_points_local_no_beads()

    def bleaching_correction(self):
        print("\n" + self.bleaching.give_name() + ": ")
        with alive_bar(len(self.cell_list_for_processing), force_tty=True) as bar:
            for cell in self.cell_list_for_processing:
                time.sleep(.005)

                if self.bleaching is not None:
                    self.bleaching.run(cell, self.parameters, self.model)

                bar()

    def generate_ratio_images(self):
        for i, cell in enumerate(self.cell_list_for_processing):
            cell.generate_ratio_image_series()
            cell.set_ratio_range(self.min_ratio, self.max_ratio)

    def save_ratio_images(self):
        savepath = self.save_path + '/ratio/'
        os.makedirs(savepath, exist_ok=True)

        for i, cell in enumerate(self.cell_list_for_processing):
            io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", cell.ratio)

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
            for cell in self.cell_list_for_processing:
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
                bar()


    def return_ratios(self):
        for cell in self.cell_list:
            self.ratio_list.append(cell.calculate_ratio())
        return self.ratio_list


    #----------------------------- Hotspots & Dartboard -------------------------


    def determine_starting_points_local_no_beads(self):
        # Specify the desired slope threshold per unit change in frame rate
        slope_threshold_per_fps = 0.0025

        # Get the actual frame rate
        actual_fps = self.frames_per_second

        # Adjust the slope threshold based on the actual frame rate
        slope_threshold = 0.25*slope_threshold_per_fps * (40.0/actual_fps)


        for i, cell in enumerate(self.cell_list_for_processing):
            cell.starting_point = 0
            """"
            time_points = np.arange(cell.frame_number)
            global_signal = np.array(cell.mean_ratio_list)

            # Smooth the global signal
            smoothed_global_signal = savgol_filter(global_signal, window_length=15, polyorder=3)

            # Calculate the first derivative (slope)
            slope = np.gradient(smoothed_global_signal)

            # Smooth the slope using a Savitzky-Golay filter
            smoothed_slope = savgol_filter(slope, window_length=15, polyorder=3)

            # Find the point where the slope surpasses the threshold
            transition_point = 0

            # Specify the consecutive frames threshold
            consecutive_frames_threshold = self.frames_per_second

            # Check if the slope exceeds the threshold for at least x frames
            for t in range(len(time_points)-int(consecutive_frames_threshold)):
                if np.all(smoothed_slope[t:t+int(consecutive_frames_threshold)] > slope_threshold):
                    transition_point = t
                    break

            # Plot the original data, smoothed data, and the slope
            
            # plt.plot(time_points, global_signal, label='Original Data')
            # plt.plot(time_points, smoothed_global_signal, label='Smoothed Data')
            # plt.plot(time_points, slope, label='Slope')
            # plt.axvline(x=transition_point, color='r', linestyle='--', label='Transition Point')
            # plt.xlabel('Time Points')
            # plt.ylabel('Global Signal')
            # plt.legend()
            # plt.show()

            # print("Transition Point:", transition_point)
            
            if transition_point > 0:
                cell.starting_point = transition_point  # individual starting point
            else:
                cell.starting_point = -1  # no individual starting point

        # A. some cells have a starting point > 0, see above. Other cells don't have a starting point (=-1).
        # B. First, the mean starting point of cells with starting point > 0 is calculated.
        # C. Next, the starting points of the cells without a useful starting point (=-1) are set to the mean starting
        #    point of  A.
        individual_starting_points = [cell.starting_point for cell in self.cell_list_for_processing if cell.starting_point > 0]
        mean_individual_starting_point = sum(individual_starting_points)/len(individual_starting_points)
        cells_without_individual_starting_point = [cell for cell in self.cell_list_for_processing if cell.starting_point == -1]
        for cell in cells_without_individual_starting_point:
            cell.starting_point = int(mean_individual_starting_point)
        """



    def assign_bead_contacts_to_cells(self):
        for bead_contact in self.list_of_bead_contacts:
            bead_contact_position = bead_contact.return_bead_contact_position()
            bead_contact_xpos = bead_contact_position[0]
            bead_contact_ypos = bead_contact_position[1]

            starting_point = bead_contact.return_time_of_bead_contact()
            selected_position_inside_cell = bead_contact.return_selected_position_inside_cell()
            selected_x_position_inside_cell, selected_y_position_inside_cell = selected_position_inside_cell[0], selected_position_inside_cell[1]

            for cell in self.cell_list:
                dataframe = cell.cell_image_data_channel_2
                cell_data_for_frame = dataframe.loc[dataframe['frame'] == starting_point]
                bbox_for_frame = cell_data_for_frame['bbox'].values.tolist()[0]
                min_row, min_col, max_row, max_col = bbox_for_frame

                if min_row <= selected_y_position_inside_cell <= max_row and min_col <= selected_x_position_inside_cell <= max_col:  # if bead contact inside bounding box of the cell
                    cell.starting_point = starting_point
                    centroid_x_coord_cell = cell_data_for_frame['x'].values.tolist()[0]
                    centroid_y_coord_cell = cell_data_for_frame['y'].values.tolist()[0]
                    location_on_clock = bead_contact.calculate_contact_position(bead_contact_xpos,
                                                                                bead_contact_ypos,
                                                                                centroid_x_coord_cell,
                                                                                centroid_y_coord_cell,
                                                                                self.dartboard_number_of_sections)
                    cell.bead_contact_site = location_on_clock
                    cell.has_bead_contact = True

        self.cell_list_for_processing = [cell for cell in self.cell_list if cell.has_bead_contact]

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


        
    