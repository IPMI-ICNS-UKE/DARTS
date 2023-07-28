import logging
import math
import skimage.io as io
import numpy as np
import skimage.measure
from alive_progress import alive_bar
import time
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
import pandas as pd
import os
import timeit
from stardist.models import StarDist2D

from general.cell import CellImage, ChannelImage
from postprocessing.segmentation import SegmentationSD
from postprocessing.CellTracker_ROI import CellTracker
from postprocessing.deconvolution import TDEDeconvolution, LRDeconvolution, BaseDecon
from postprocessing.registration import Registration_SITK, Registration_SR
from analysis import HotSpotDetection
from shapenormalization.shapenormalization import ShapeNormalization
from analysis.Dartboard import DartboardGenerator
from postprocessing.Bleaching import BleachingAdditiveNoFit
from general.RatioToConcentrationConverter import RatioConverter
from postprocessing.BackgroundSubtraction import BackgroundSubtractor

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

    def __init__(self, image_ch1, image_ch2, parameterdict, logger=None):
        self.parameters = parameterdict
        self.channel1 = image_ch1
        self.channel2 = image_ch2
        self.logger = logger
        self.list_of_bead_contacts = self.parameters["properties"]["list_of_bead_contacts"]

        self.duration_of_measurement = 600  # from bead contact + maximum 600 frames (40fps and 600 frames => 15sec)
        latest_time_of_bead_contact = max([bead_contact.time_of_bead_contact for bead_contact in self.list_of_bead_contacts])
        end_frame = latest_time_of_bead_contact + self.duration_of_measurement  + 1  # not all frames need to be processed

        self.wl1 = self.parameters["properties"]["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["properties"]["wavelength_2"]  # wavelength channel2
        if self.channel1.ndim == 3:
            self.t_max, self.y_max, self.x_max = self.channel1.shape
        elif self.channel1.ndim == 2:
            self.y_max, self.x_max = self.channel1.shape
          
       # self.file_name = filename  # ntpath.basename(self.parameters["inputoutput"]["path_to_input_combined"

        self.cell_list = []
        self.segmentation_result_dict = {}
        self.deconvolution_result_dict = {}
              self.cells_with_bead_contact = None
        self.excluded_cells_list = []

        self.ratio_list = []
        self.nb_rois = None

        # ------------------------ setup methods postprocessing ----------------------------
        # registration
        if self.parameters["properties"]["registration_method"] == "SITK" and sitk is not None:
            self.registration = Registration_SITK()
        else:
            self.registration = Registration_SR()
        # cell tracking & segmentation
        self.scale_pixels_per_micron = self.parameters["properties"]["scale_pixels_per_micron"]
        self.cell_tracker = CellTracker(self.scale_pixels_per_micron)
        self.model = StarDist2D.from_pretrained('2D_versatile_fluo')
        self.segmentation = SegmentationSD(self.model)

        # background subtraction
        self.background_subtractor = BackgroundSubtractor(self.segmentation)
        # deconvolution
        self.deconvolution_parameters = self.parameters["deconvolution"]
        if self.deconvolution_parameters["decon"] == "TDE":
            self.deconvolution = TDEDeconvolution()
        elif self.deconvolution_parameters["decon"] == "LR":
            self.deconvolution = LRDeconvolution()
        else:
            self.deconvolution = BaseDecon()
        # bleaching correction
        if self.parameters["properties"]["bleaching_correction_in_pipeline"]:
            if self.parameters["properties"]["bleaching_correction_algorithm"] == "additiv no fit":
                self.bleaching = BleachingAdditiveNoFit()
            else:
                self.bleaching = None
        else:
            self.bleaching = None
        # ratio converter
        self.ratio_converter = RatioConverter()
        self.median_filter_kernel = self.parameters["properties"]["median_filter_kernel"]

        # ------------------------ setup methods hotspots & dartboard ----------------------------

        self.microdomains_timelines_dict = {}
        self.experiment_name = self.parameters["inputoutput"]["experiment_name"]
        self.day_of_measurement = self.parameters["properties"]["day_of_measurement"]
        self.measurement_name = self.day_of_measurement + '_' + self.experiment_name
        #self.measurement_name = self.day_of_measurement + '_' + self.experiment_name + '_' + self.file_name
        self.results_folder = self.parameters["inputoutput"]["path_to_output"]
        self.save_path = self.results_folder + '/' + self.measurement_name
        self.frame_number = len(self.channel1)
        self.estimated_cell_diameter_in_pixels = self.parameters["properties"]["estimated_cell_diameter_in_pixels"]
        self.estimated_cell_area = round((0.5 * self.estimated_cell_diameter_in_pixels) ** 2 * math.pi)
        self.cell_type = self.parameters["properties"]["cell_type"]
        self.spotHeight = None
        if self.cell_type == 'primary':
            self.spotHeight = 112.5  # [Ca2+] = 112.5 nM
        elif self.cell_type == 'jurkat':
            self.spotHeight = 72
        elif self.cell_type == 'NK':
            self.spotHeight = 72  # needs to be checked
        self.list_of_bead_contacts = self.parameters["properties"]["list_of_bead_contacts"]

        self.dartboard_number_of_sections = self.parameters["properties"]["dartboard_number_of_sections"]
        self.dartboard_number_of_areas_per_section = self.parameters["properties"][
            "dartboard_number_of_areas_per_section"]

        self.frames_per_second = self.parameters["properties"]["frames_per_second"]
        self.ratio_converter = RatioConverter()
        self.minimum_spotsize = 4
        self.duration_of_measurement = 600  # from bead contact + maximum 600 frames (40fps and 600 frames => 15sec)
        self.min_ratio = 0.1
        self.max_ratio = 2.0
        # self.microdomain_signal_threshold = self.parameters["properties"]["microdomain_signal_threshold"]
        self.excel_filename_general = self.parameters["inputoutput"]["excel_filename_all_cells"]
        self.excel_filename_one_measurement = self.measurement_name + '_' + self.excel_filename_general
        self.file_name = None
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
    def fromfilename(cls, filename, parameterdict, logger=None):
        start = parameterdict["inputoutput"]["start_frame"]
        end = parameterdict["inputoutput"]["end_frame"]
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
            with alive_bar(len(self.cells_with_bead_contact), force_tty=True) as bar:
                time.sleep(.005)
                for cell in self.cells_with_bead_contact:
                    roi_channel1, roi_channel2 = cell.channel1.image, cell.channel2.image

                    roi_channel1_decon, roi_channel2_decon = self.deconvolution.execute(roi_channel1, roi_channel2,
                                                                                        self.parameters)

                    cell.set_image_channel1(roi_channel1_decon)
                    cell.set_image_channel2(roi_channel2_decon)

                    bar()


    def clear_outside_of_cells(self):
        self.background_subtractor.clear_outside_of_cells(self.cells_with_bead_contact)

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
        self.channel2 = self.registration.channel_registration(self.channel1, self.channel2,
                                                               self.parameters["properties"][
                                                                   "registration_framebyframe"])

        # background subtraction
        self.channel1, self.channel2 = self.background_subtraction(self.channel1, self.channel2)

        # segmentation of cells, tracking
        self.segmentation_result_dict = self.select_rois()

        # cell images
        self.create_cell_images(self.segmentation_result_dict)

        # -- PROCESSING OF CELL IMAGES --
        # assign bead contacts to cells
        self.assign_bead_contacts_to_cells()

        # deconvolution
        self.deconvolve_cell_images()

        # bleaching correction
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

    def bleaching_correction(self):
        print("\n" + self.bleaching.give_name() + ": ")
        with alive_bar(len(self.cells_with_bead_contact), force_tty=True) as bar:
            for cell in self.cells_with_bead_contact:
                time.sleep(.005)

                if self.bleaching is not None:
                    self.bleaching.run(cell, self.parameters, self.model)

                bar()

    def generate_ratio_images(self):
        for cell in self.cells_with_bead_contact:
            cell.generate_ratio_image_series()
            cell.set_ratio_range(self.min_ratio, self.max_ratio)

def medianfilter(self, channel):
       """"
        Apply a medianfilter on either the channels or the ratio image;
        Pixelvalues of zeroes are excluded in median calculation
        """

       print("\n Medianfilter " + channel + ": ")
       with alive_bar(len(self.cells_with_bead_contact), force_tty=True) as bar:
           for cell in self.cells_with_bead_contact:
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


    def assign_bead_contacts_to_cells(self):
        for bead_contact in self.list_of_bead_contacts:
            bead_contact_position = bead_contact.return_bead_contact_position()
            bead_contact_xpos = bead_contact_position[0]
            bead_contact_ypos = bead_contact_position[1]

            time_of_bead_contact = bead_contact.return_time_of_bead_contact()
            selected_position_inside_cell = bead_contact.return_selected_position_inside_cell()
            selected_x_position_inside_cell = selected_position_inside_cell[0]
            selected_y_position_inside_cell = selected_position_inside_cell[1]

            for cell in self.cell_list:
                dataframe = cell.cell_image_data_channel_2
                cell_data_for_frame = dataframe.loc[dataframe['frame'] == time_of_bead_contact]
                bbox_for_frame = cell_data_for_frame['bbox'].values.tolist()[0]
                min_row, min_col, max_row, max_col = bbox_for_frame

                if min_row <= selected_y_position_inside_cell <= max_row and min_col <= selected_x_position_inside_cell <= max_col:
                    cell.time_of_bead_contact = time_of_bead_contact
                    centroid_x_coord_cell = cell_data_for_frame['x'].values.tolist()[0]
                    centroid_y_coord_cell = cell_data_for_frame['y'].values.tolist()[0]
                    location_on_clock = bead_contact.calculate_contact_position(bead_contact_xpos,
                                                                                bead_contact_ypos,
                                                                                centroid_x_coord_cell,
                                                                                centroid_y_coord_cell,
                                                                                self.dartboard_number_of_sections)
                    cell.bead_contact_site = location_on_clock
                    cell.has_bead_contact = True

        self.cells_with_bead_contact = [cell for cell in self.cell_list if cell.has_bead_contact]

    def hotspot_detection(self, normalized_cells_dict):
        number_of_analyzed_cells = 0
        number_of_cells_with_hotspots = 0

        with alive_bar(len(self.cells_with_bead_contact), force_tty=True) as bar:
            for i, cell in enumerate(self.cells_with_bead_contact):
                try:
                    number_of_analyzed_cells += 1
                    hd_start = timeit.default_timer()
                    normalized_ratio = normalized_cells_dict[cell][0]
                    mean_ratio_value_list = normalized_cells_dict[cell][1]

                    number_of_frames, time_before_bead_contact, time_after_bead_contact, cell_has_hotspots_after_bead_contact = self.detect_hotspots(normalized_ratio, mean_ratio_value_list, cell, i)
                    if cell_has_hotspots_after_bead_contact:
                        number_of_cells_with_hotspots += 1
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
                    microdomains_timeline_for_cell = self.save_measurements(i, cell.signal_data, number_of_frames, time_before_bead_contact)
                    self.microdomains_timelines_dict[(self.file_name, i)] = microdomains_timeline_for_cell

                except Exception as E:
                    print(E)
                    self.logger.log_and_print(message="Exception occurred: Error in saving measurements",
                                  level=logging.ERROR, logger=self.logger)
                    continue

                bar()
        return number_of_analyzed_cells, number_of_cells_with_hotspots, self.microdomains_timelines_dict

    def detect_hotspots(self, ratio_image, mean_ratio_value_list, cell, i):
        if cell.has_bead_contact:  # if user defined a bead contact site (in the range from 1 to 12)
            start_frame = int(cell.time_of_bead_contact - self.frames_per_second)
            if start_frame < 0:
                start_frame = 0
            time_before_bead_contact = cell.time_of_bead_contact - start_frame
            frame_number_cell = cell.frame_number

            if start_frame + time_before_bead_contact + self.duration_of_measurement >= frame_number_cell:
                end_frame = frame_number_cell - 1
            else:
                end_frame = start_frame + time_before_bead_contact + self.duration_of_measurement
            time_after_bead_contact = end_frame - cell.time_of_bead_contact
            mean_ratio_value_list_short = mean_ratio_value_list[start_frame:end_frame]

            measurement_microdomains = self.hotspotdetector.measure_microdomains(ratio_image,
                                                                                 start_frame,
                                                                                 end_frame,
                                                                                 mean_ratio_value_list_short,
                                                                                 self.spotHeight,
                                                                                 self.minimum_spotsize,
                                                                                 # lower area limit in pixels
                                                                                 20,  # upper area limit in pixels
                                                                                 self.cell_type,
                                                                                 time_before_bead_contact)
            cell.signal_data = measurement_microdomains
            number_of_analyzed_frames = end_frame - start_frame
            if not measurement_microdomains.empty:
                dataframe_after_bead_contact = measurement_microdomains.loc[
                    measurement_microdomains['frame'] > 0].copy()
            else:
                dataframe_after_bead_contact = pd.DataFrame()
            cell_has_hotspots_after_bead_contact = not dataframe_after_bead_contact.empty
            return number_of_analyzed_frames, time_before_bead_contact, time_after_bead_contact, cell_has_hotspots_after_bead_contact

    def save_measurements(self, i, cell_signal_data, number_of_frames, time_before_bead_contact):
        microdomains_timeline_for_cell = self.hotspotdetector.save_dataframes(self.file_name, i, cell_signal_data,
                                                                              number_of_frames,
                                                                              time_before_bead_contact)
        return microdomains_timeline_for_cell

    def dartboard(self, normalized_cells_dict):
        normalized_dartboard_data_multiple_cells = []

        with alive_bar(len(self.cells_with_bead_contact), force_tty=True) as bar:
            for i, cell in enumerate(self.cells_with_bead_contact):
                try:
                    db_start = timeit.default_timer()

                    centroid_coords_list = normalized_cells_dict[cell][3]
                    radii_after_normalization = normalized_cells_dict[cell][2]

                    start_frame = int(cell.time_of_bead_contact - self.frames_per_second)  # also measure hotspots before bead contacts, if 40fps then 40 frames
                    if start_frame < 0:
                        start_frame = 0
                    time_before_bead_contact = cell.time_of_bead_contact - start_frame
                    frame_number_cell = cell.frame_number

                    if start_frame + time_before_bead_contact + self.duration_of_measurement >= frame_number_cell:
                        end_frame = frame_number_cell - 1
                    else:
                        end_frame = start_frame + time_before_bead_contact + self.duration_of_measurement

                    average_dartboard_data_single_cell = self.generate_average_dartboard_data_single_cell(
                        centroid_coords_list,
                        cell,
                        radii_after_normalization,
                        i,
                        cell.time_of_bead_contact,
                        end_frame)
                    normalized_dartboard_data_single_cell = self.normalize_average_dartboard_data_one_cell(
                        average_dartboard_data_single_cell,
                        cell.bead_contact_site,
                        2)

                    self.save_dartboard_data_single_cell(normalized_dartboard_data_single_cell, i)

                    normalized_dartboard_data_multiple_cells.append(normalized_dartboard_data_single_cell)

                    db_took = (timeit.default_timer() - db_start) * 1000.0
                    db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
                    self.logger.log_and_print(message=f"Dartboard analysis of cell {i} "
                                          f"took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms",
                                  level=logging.INFO, logger=self.logger)
                    """
                    else:
                        log_and_print(message=f"No Dartboard analysis of cell {i} ",
                                      level=logging.WARNING, logger=logger)
                    """
                except Exception as E:
                    print(E)
                    self.logger.log_and_print(message="Exception occurred: Error in Dartboard (single cell)",
                                  level=logging.ERROR, logger=self.logger)
                    continue

                bar()

        try:
            db_start = timeit.default_timer()
            average_dartboard_data_multiple_cells = self.generate_average_and_save_dartboard_multiple_cells(
                len(normalized_dartboard_data_multiple_cells),
                normalized_dartboard_data_multiple_cells, self.file_name)
            db_took = (timeit.default_timer() - db_start) * 1000.0
            db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
            print("\n")
            self.logger.log_and_print(message=f"Dartboard plot: Done!"
                                              f" It took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms",
                                      level=logging.INFO, logger=self.logger)
            return average_dartboard_data_multiple_cells
        except Exception as E:
            print(E)
            self.logger.log_and_print(message="Error in Dartboard (average dartboard for multiple cells)",
                                      level=logging.ERROR, logger=self.logger)

    def save_dartboard_data_single_cell(self, dartboard_data, cell_index):
        dartboard_data_filename = self.file_name + '_dartboard_data_cell_' + str(cell_index)
        self.dartboard_generator.save_dartboard_data_for_single_cell(dartboard_data_filename, dartboard_data)

    def generate_average_dartboard_data_single_cell(self, centroid_coords_list, cell, radii_after_normalization, cell_index, time_of_bead_contact, end_frame):
        if not cell.signal_data.empty:
            signal_data_for_cell = cell.signal_data.loc[cell.signal_data['frame'] >= 0]  # only data after bead contact
        else:
            signal_data_for_cell = cell.signal_data

        # generate cumualted dartboard data for one cell
        cumulated_dartboard_data_all_frames = self.dartboard_generator.cumulate_dartboard_data_multiple_frames(
            signal_data_for_cell,
            self.dartboard_number_of_sections,
            self.dartboard_number_of_areas_per_section,
            centroid_coords_list,
            radii_after_normalization,
            cell_index,
            time_of_bead_contact,
            end_frame)

        duration_of_measurement_after_bead_contact_in_seconds = (
                                                                            end_frame - time_of_bead_contact) / self.frames_per_second  # e.g. 600 Frames + 40 Frames, 40fps => 16s
        average_dartboard_data_per_second = np.divide(cumulated_dartboard_data_all_frames,
                                                      duration_of_measurement_after_bead_contact_in_seconds)

        return average_dartboard_data_per_second

    def normalize_average_dartboard_data_one_cell(self, average_dartboard_data, real_bead_contact_site,
                                                  normalized_bead_contact_site):
        return self.dartboard_generator.normalize_average_dartboard_data_one_cell(average_dartboard_data,
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


# ------------------------------------------ Shape Normalization ------------------------------------

    def apply_shape_normalization(self):
        savepath = self.save_path + '/normalization/'
        os.makedirs(savepath, exist_ok=True)

        normalized_cells_dict = {}

        print("\n")
        self.logger.log_and_print(message="Processing now continues with: ", level=logging.INFO, logger=self.logger)
        with alive_bar(len(self.cells_with_bead_contact), force_tty=True) as bar:
            for i, cell in enumerate(self.cells_with_bead_contact):
                time.sleep(.005)
                ratio = cell.give_ratio_image()
                try:
                    sh_start = timeit.default_timer()
                    normalized_ratio, centroid_coords_list = self.normalize_cell_shape(cell)
                    mean_ratio_value_list, radii_after_normalization = self.extract_information_for_hotspot_detection(
                        normalized_ratio)
                    normalized_cells_dict[cell] = (normalized_ratio, mean_ratio_value_list, radii_after_normalization, centroid_coords_list)

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

                io.imsave(savepath + self.measurement_name + cell.to_string(i) + 'ratio' + ".tif", ratio)
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

    def extract_information_for_hotspot_detection(self, normalized_image_series):
        mean_ratio_value_list = []
        radii_list = []
        frame_number = len(normalized_image_series)

        for frame in range(frame_number):
            current_frame = normalized_image_series[frame]
            thresholded_image = current_frame > 0.01  # exclude background from measurement
            # io.imshow(thresholded_image)
            # plt.show()
            label = skimage.measure.label(thresholded_image)
            regions = skimage.measure.regionprops(label_image=label, intensity_image=current_frame)
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
        for cell in self.cell_list:
            cell_mean_signal_amplitude = cell.calculate_mean_amplitude_of_signals_after_bead_contact()
            if cell_mean_signal_amplitude is not None:
                mean_amplitude_list_of_cells.append(cell_mean_signal_amplitude)
        return mean_amplitude_list_of_cells



# --------------------------- saving results -----------------------------------------

    def save_image_files(self):
        """
        Saves the image files within the cells of the cell list
        """
        for i, cell in enumerate(self.cells_with_bead_contact):
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
        for i, cell in enumerate(self.cells_with_bead_contact):
            io.imsave(save_path + '/'+ self.measurement_name + cell.to_string(i) + '_ratio_image' + '.tif', cell.give_ratio_image(), check_contrast=False)


        
    