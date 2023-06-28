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

from general.cell import CellImage, ChannelImage
from postprocessing.segmentation import SegmentationSD, ATPImageConverter
from postprocessing.CellTracker_ROI import CellTracker
from postprocessing.deconvolution import TDEDeconvolution, LRDeconvolution, BaseDecon
from postprocessing.registration import Registration_SITK, Registration_SR
from analysis import HotSpotDetection
from shapenormalization.shapenormalization import ShapeNormalization
from analysis.Dartboard import DartboardGenerator
from postprocessing.Bleaching import BleachingAdditiveNoFit
from analysis.Bead_Contact_GUI import BeadContactGUI
from general.RatioToConcentrationConverter import RatioConverter
from postprocessing.BackgroundSubtraction import BackgroundSubtractor

logger = logging.getLogger(__name__)


try:
    import SimpleITK as sitk
except ImportError:
    print("SimpleITK cannot be loaded")
    sitk = None


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
    def __init__(self, parameter_dict, stardist_model):
        self.parameters = parameter_dict
        self.model = stardist_model
        start = parameter_dict["inputoutput"]["start_frame"]
        end = parameter_dict["inputoutput"]["end_frame"]

        # handle different input formats: either two channels in one image or one image per channel
        if self.parameters["properties"]["channel_format"] == "two-in-one":
            self.image = io.imread(self.parameters["inputoutput"]["path_to_input_combined"])
            self.image = cut_image_frames(self.image, start, end)
            # separate image into 2 channels: left half and right half
            if self.image.ndim == 3:  # for time series
                self.channel1, self.channel2 = np.split(self.image, 2, axis=2)
                self.t_max, self.y_max, self.x_max = self.image.shape
            elif self.image.ndim == 2:  # for static images
                self.channel1, self.channel2 = np.split(self.image, 2, axis=1)
                self.y_max, self.x_max = self.image.shape
        elif self.parameters["properties"]["channel_format"] == "single":
            self.channel1 = io.imread(self.parameters["inputoutput"]["path_to_input_channel1"])
            self.channel1 = cut_image_frames(self.channel1, start, end)
            self.channel2 = io.imread(self.parameters["inputoutput"]["path_to_input_channel2"])
            self.channel2 = cut_image_frames(self.channel2, start, end)
            if self.channel1.ndim == 3:  # for time series
                self.image = np.concatenate((self.channel1, self.channel2), axis=2)
                self.t_max, self.y_max, self.x_max = self.image.shape
            elif self.channel1.ndim == 2:
                self.image = np.concatenate((self.channel1, self.channel2), axis=1)
                self.y_max, self.x_max = self.image.shape
        self.scale_microns_per_pixel = self.parameters["properties"]["scale_microns_per_pixel"]
        self.estimated_cell_diameter_in_pixels = self.parameters["properties"]["estimated_cell_diameter_in_pixels"]

        self.estimated_cell_area = round((0.5 * self.estimated_cell_diameter_in_pixels) ** 2 * math.pi)
        self.cell_type = self.parameters["properties"]["cell_type"]
        self.spotHeight = None
        if self.cell_type == 'primary':
            self.spotHeight = 112.5
        elif self.cell_type == 'jurkat':
            self.spotHeight = 72

        self.frame_number = len(self.channel1)
        self.save_path = self.parameters["inputoutput"]["path_to_output"]
        self.ATP_flag = self.parameters["properties"]["ATP"]
        self.cell_list = []
        self.excluded_cells_list = []
        self.ratio_list = []
        self.nb_rois = None
        self.roi_minmax_list = []
        # self.roi_coord_list = []
        self.roi_bounding_boxes = []
        self.cell_tracker = CellTracker()
        self.segmentation = SegmentationSD(self.model)
        self.ATP_image_converter = ATPImageConverter()
        self.background_subtractor = BackgroundSubtractor(self.segmentation)
        # ff
        self.deconvolution_parameters = self.parameters["deconvolution"]
        if self.deconvolution_parameters["decon"] == "TDE":
            self.deconvolution = TDEDeconvolution()
        elif self.deconvolution_parameters["decon"] == "LR":
            self.deconvolution = LRDeconvolution()
        else:
            self.deconvolution = BaseDecon()

        if self.parameters["properties"]["bleaching_correction_in_pipeline"]:
            if self.parameters["properties"]["bleaching_correction_algorithm"] == "additiv no fit":
                self.bleaching = BleachingAdditiveNoFit()
            else:
                self.bleaching = None
        else:
            self.bleaching = None

        self.dataframes_microdomains_list = []
        self.dartboard_number_of_sections = self.parameters["properties"]["dartboard_number_of_sections"]
        self.dartboard_number_of_areas_per_section = self.parameters["properties"][
            "dartboard_number_of_areas_per_section"]

        self.ratio_preactivation_threshold = self.parameters["properties"]["ratio_preactivation_threshold"]
        self.frames_per_second = self.parameters["properties"]["frames_per_second"]
        # self.number_of_frames_to_analyse = self.parameters["properties"]["number_of_frames_to_analyse"]
        self.ratio_converter = RatioConverter()
        self.minimum_spotsize = 4
        self.duration_of_measurement = 600  # from bead contact + maximum 600 frames (40fps and 600 frames => 15sec)
        self.min_ratio = 0.1
        self.max_ratio = 2.0
        # self.microdomain_signal_threshold = self.parameters["properties"]["microdomain_signal_threshold"]


        self.hotspotdetector = HotSpotDetection.HotSpotDetector(self.save_path,
                                                                self.parameters["inputoutput"]["excel_filename"],
                                                                self.frames_per_second,
                                                                self.ratio_converter)
        self.dartboard_generator = DartboardGenerator(self.save_path, self.frames_per_second)
        if self.parameters["properties"]["registration_method"] == "SITK" and sitk is not None:
            self.registration = Registration_SITK()
        else:
            self.registration = Registration_SR()

        self.wl1 = self.parameters["properties"]["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["properties"]["wavelength_2"]  # wavelength channel2
        self.processing_steps = [self.bleaching]

    def select_rois(self):
        roi_before_backgroundcor_dict = self.cell_tracker.give_rois(self.channel1, self.channel2, self.model)
        return roi_before_backgroundcor_dict

    def deconvolve_cell_images(self, roi_before_backgroundcor_dict):
            roi_after_decon_dict = {}
            print("\n"+ self.deconvolution.give_name() + ": ")
            with alive_bar(len(roi_before_backgroundcor_dict), force_tty=True) as bar:
                time.sleep(.005)
                for cells_for_decon in roi_before_backgroundcor_dict:
                    [roi_channel1, roi_channel2, particle_dataframe_subset,
                     shifted_frame_masks] = roi_before_backgroundcor_dict[cells_for_decon]
                    roi_channel1_decon, roi_channel2_decon = self.deconvolution.execute(roi_channel1, roi_channel2,
                                                                              self.parameters)
                    roi_after_decon_dict[cells_for_decon] = [roi_channel1_decon, roi_channel2_decon,
                                                             particle_dataframe_subset, shifted_frame_masks]
                    bar()

            return roi_after_decon_dict

    def clear_outside_of_cells(self, roi_after_decon_dict):
        roi_list_cell_pairs = self.background_subtractor.clear_outside_of_cells(roi_after_decon_dict)
        return roi_list_cell_pairs

    def background_subtraction(self, channel_1, channel_2):
        print("\nBackground subtraction: ")
        with alive_bar(1, force_tty=True) as bar:
            time.sleep(.005)
            channel_1_background_subtracted = self.background_subtractor.subtract_background(channel_1)
            channel_2_background_subtracted = self.background_subtractor.subtract_background(channel_2)
            bar()

        return channel_1_background_subtracted, channel_2_background_subtracted


    def create_cell_images(self, roi_list_cell_pairs):
        self.nb_rois = len(roi_list_cell_pairs)
        print("\nCreating cell images: ")
        with alive_bar(self.nb_rois, force_tty=True) as bar:
            time.sleep(.005)
            for i in range(self.nb_rois):

                self.cell_list.append(CellImage(ChannelImage(roi_list_cell_pairs[i][0], self.wl1),
                                                ChannelImage(roi_list_cell_pairs[i][1], self.wl2),
                                                self.x_max,
                                                roi_list_cell_pairs[i][2],
                                                roi_list_cell_pairs[i][3])
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

    def plot_rois(self, plotall=False):

        def format_axes(fig):
            for i, ax in enumerate(fig.axes):
                ax.set_axis_off()

        if plotall:
            cmap_min = self.image[0].min()
            cmap_max = self.image[0].max()
            wratios = np.ones(self.nb_rois + 1)
            wratios[1:] *= 0.5

            fig = plt.figure(layout="constrained", figsize=((self.nb_rois + 1) * 2, 3))
            gs = GridSpec(2, self.nb_rois + 1, figure=fig, width_ratios=wratios)
            ax1 = fig.add_subplot(gs[:, 0])
            ax1.imshow(self.image[0], vmin=cmap_min, vmax=cmap_max)

            for i in range(self.nb_rois):
                ax2 = fig.add_subplot(gs[0, i + 1])
                ax3 = fig.add_subplot(gs[1, i + 1])
                ax2.imshow(self.cell_list[i].give_image_channel1()[0], vmin=cmap_min, vmax=cmap_max)
                ax3.imshow(self.cell_list[i].give_image_channel2()[0], vmin=cmap_min, vmax=cmap_max)
                [[xmin, ymin], [xmax, ymax]] = self.roi_minmax_list[i]

                w = xmax - xmin
                h = ymax - ymin
                os = self.x_max // 2
                ax1.add_patch(Rectangle((xmin, ymin), w, h,
                                        edgecolor='blue',
                                        facecolor='none',
                                        lw=1))
                ax1.add_patch(Rectangle((xmin + os, ymin), w, h,
                                        edgecolor='red',
                                        facecolor='none',
                                        lw=1))
                ax2.add_patch(Rectangle((0, 0), w - 1, h - 1,
                                        edgecolor='blue',
                                        facecolor='none',
                                        lw=1))
                ax3.add_patch(Rectangle((0, 0), w - 1, h - 1,
                                        edgecolor='red',
                                        facecolor='none',
                                        lw=1))
                ax1.text(xmin + 0.5 * w, ymin + 0.5 * h, str(i + 1), va="center", ha="center", c="blue")
                ax1.text((xmin + 0.5 * w) + os, ymin + 0.5 * h, str(i + 1), va="center", ha="center", c="red")

                ax2.text(0.5, 0.5, str(i + 1), transform=ax2.transAxes, va="center", ha="center", c="blue")
                ax3.text(0.5, 0.5, str(i + 1), transform=ax3.transAxes, va="center", ha="center", c="red")

            format_axes(fig)

            plt.show(block=False)
        else:
            fig, ax = plt.subplots()
            ax.imshow(self.image[0])
            for i in range(self.nb_rois):
                [[xmin, ymin], [xmax, ymax]] = self.roi_minmax_list[i]
                w = xmax - xmin
                h = ymax - ymin
                os = self.x_max // 2
                ax.add_patch(Rectangle((xmin, ymin), w, h,
                                       edgecolor='blue',
                                       facecolor='none',
                                       lw=1))
                ax.add_patch(Rectangle((xmin + os, ymin), w, h,
                                       edgecolor='red',
                                       facecolor='none',
                                       lw=1))
            format_axes(fig)
            plt.show(block=False)

        return fig

    def save_registered_first_frames(self):
        io.imsave(self.save_path + '/channel_1_frame_1' + '.tif', self.channel1)
        io.imsave(self.save_path + '/channel_2_frame_1_registered' + '.tif', self.channel2)

    def start_postprocessing(self):
        # channel registration
        self.channel2 = self.registration.channel_registration(self.channel1, self.channel2,
                                                               self.parameters["properties"][
                                                                   "registration_framebyframe"])
        # background subtraction
        self.channel1, self.channel2 = self.background_subtraction(self.channel1, self.channel2)

        # segmentation of cells, tracking
        cell_rois = self.select_rois()

        # deconvolution
        roi_after_deconvolution_dict = self.deconvolve_cell_images(cell_rois)

        # clear area outside the cells
        roi_list_cell_pairs = self.clear_outside_of_cells(roi_after_deconvolution_dict)

        # cell images
        self.create_cell_images(roi_list_cell_pairs)

        # bead contact, user input
        if len(self.cell_list) > 0:
            self.define_bead_contacts()

        # bleaching correction
        self.bleaching_correction()

        # generation of ratio images
        self.generate_ratio_images()

    def bleaching_correction(self):
        print("\n" + self.bleaching.give_name() + ": ")
        with alive_bar(len(self.cell_list), force_tty=True) as bar:
            for cell in self.cell_list:
                time.sleep(.005)
                for step in self.processing_steps:
                    if step is not None:
                        time.sleep(.005)
                        step.run(cell, self.parameters, self.model)
                bar()

    def generate_ratio_images(self):
        for cell in self.cell_list:
            cell.generate_ratio_image_series()
            cell.set_ratio_range(self.min_ratio, self.max_ratio)

    def detect_hotspots(self, ratio_image, mean_ratio_value_list, cell, i):
        if cell.bead_contact_site != 0:  # if user defined a bead contact site (in the range from 1 to 12)
            start_frame = cell.time_of_bead_contact
            frame_number_cell = cell.frame_number
            end_frame = 0
            if start_frame + self.duration_of_measurement > frame_number_cell+1:
                end_frame = frame_number_cell-1
            else:
                end_frame = start_frame + self.duration_of_measurement

            measurement_microdomains = self.hotspotdetector.measure_microdomains(ratio_image,
                                                                                 start_frame,
                                                                                 end_frame,
                                                                                 mean_ratio_value_list,
                                                                                 self.spotHeight,
                                                                                 self.minimum_spotsize,   # lower area limit
                                                                                 20,  # upper area limit
                                                                                 self.cell_type)
            cell.signal_data = measurement_microdomains
            self.dataframes_microdomains_list.append(measurement_microdomains)




    def define_bead_contacts(self):
        """
        Let user define the bead contacts (time, location) for each cell
        :return:
        """
        bead_contact_gui = BeadContactGUI(self.image, self.cell_list, self.dartboard_number_of_sections)
        bead_contact_gui.run_main_loop()



    def save_measurements(self, i):
        self.hotspotdetector.save_dataframes(self.dataframes_microdomains_list, i)


    def generate_average_dartboard_data_per_second_single_cell(self, centroid_coords_list, cell, radii_after_normalization, cell_index):
        # generate cumualted dartboard data for one cell
        cumulated_dartboard_data_all_frames = self.dartboard_generator.cumulate_dartboard_data_multiple_frames(cell.frame_number,
                                                                                       cell.signal_data,
                                                                                       self.dartboard_number_of_sections,
                                                                                       self.dartboard_number_of_areas_per_section,
                                                                                       centroid_coords_list,
                                                                                       radii_after_normalization,
                                                                                       cell_index)
        # calculate number of seconds of measurement and divide cumulated dartboard data by time in seconds
        start_frame = cell.time_of_bead_contact
        frame_number_cell = cell.frame_number
        if start_frame + self.duration_of_measurement > frame_number_cell + 1:
            end_frame = frame_number_cell - 1
        else:
            end_frame = start_frame + self.duration_of_measurement
        duration_of_measurement_in_seconds = (end_frame-start_frame)/self.frames_per_second  # e.g. 600 Frames, 40fps => 15s
        average_dartboard_data_per_second = np.divide(cumulated_dartboard_data_all_frames, duration_of_measurement_in_seconds)

        return average_dartboard_data_per_second

    def normalize_average_dartboard_data_one_cell(self, average_dartboard_data, real_bead_contact_site,
                                                  normalized_bead_contact_site):
        return self.dartboard_generator.normalize_average_dartboard_data_one_cell(average_dartboard_data,
                                                                                  real_bead_contact_site,
                                                                                  normalized_bead_contact_site)

    def generate_average_and_save_dartboard_multiple_cells(self, dartboard_data_multiple_cells):
        average_dartboard_data_per_second_multiple_cells = self.dartboard_generator.calculate_mean_dartboard_multiple_cells(dartboard_data_multiple_cells,
                                                                                   self.dartboard_number_of_sections,
                                                                                   self.dartboard_number_of_areas_per_section)

        self.dartboard_generator.save_dartboard_plot(average_dartboard_data_per_second_multiple_cells,
                                                     len(dartboard_data_multiple_cells),
                                                     self.dartboard_number_of_sections,
                                                     self.dartboard_number_of_areas_per_section)

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
            mean_ratio_value = regions[0].intensity_mean
            mean_ratio_value_list.append(mean_ratio_value)
            current_radius = regions[0].equivalent_diameter_area / 2
            radii_list.append(current_radius)

        return mean_ratio_value_list, radii_list

    def return_ratios(self):
        for cell in self.cell_list:
            self.ratio_list.append(cell.calculate_ratio())
        return self.ratio_list

    def add_scale_bars(self):
        """
        Adds scale bars to the cell image time series before saving them.
        """

    def save_image_files(self):
        """
        Saves the image files within the cells of the celllist in the given path.
        :param save_path: The target path.
        """
        i = 1
        for cell in self.cell_list:
            io.imsave(self.save_path + '/cell_image_channel1_' + str(i) + '.tif', cell.give_image_channel1(),
                      check_contrast=False)

            io.imsave(self.save_path + '/cell_image_channel2_' + str(i) + '.tif', cell.give_image_channel2(),
                      check_contrast=False)
            # format = 'tiff'
            # import imageio
            # imageio.imwrite(f'image.{format}', cell.give_image_channel2())
            # import tifffile
            # tifffile.imsave(self.save_path + '/cell_image_channel2_' + str(i) + '.tif',cell.give_image_channel2())
            i += 1

    def save_ratio_image_files(self):
        i = 1
        for cell in self.cell_list:
            io.imsave(self.save_path + '/ratio_image' + str(i) + '.tif', cell.give_ratio_image(), check_contrast=False)
            i += 1
