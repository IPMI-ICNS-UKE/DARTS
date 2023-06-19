import math
import skimage.io as io
import numpy as np
from alive_progress import alive_bar
import time
from postprocessing.cell import CellImage, ChannelImage
from postprocessing.segmentation import SegmentationSD, ATPImageConverter
from postprocessing.CellTracker_ROI import CellTracker
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

from postprocessing.registration import Registration_SITK, Registration_SR

from postprocessing import HotSpotDetection
from postprocessing.shapenormalization import ShapeNormalization

from postprocessing.Dartboard import DartboardGenerator
from postprocessing.Bleaching import BleachingAdditiveFit
from postprocessing.Bead_Contact_GUI import BeadContactGUI


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
        self.segmentation = SegmentationSD()
        self.ATP_image_converter = ATPImageConverter()
        self.decon = None
        self.bleaching = BleachingAdditiveFit()
        self.dataframes_microdomains_list = []
        self.dartboard_number_of_sections = self.parameters["properties"]["dartboard_number_of_sections"]
        self.dartboard_number_of_areas_per_section = self.parameters["properties"][
            "dartboard_number_of_areas_per_section"]

        self.ratio_preactivation_threshold = self.parameters["properties"]["ratio_preactivation_threshold"]
        self.frames_per_second = self.parameters["properties"]["frames_per_second"]
        self.number_of_frames_to_analyse = self.parameters["properties"]["number_of_frames_to_analyse"]
        self.microdomain_signal_threshold = self.parameters["properties"]["microdomain_signal_threshold"]
        self.hotspotdetector = HotSpotDetection.HotSpotDetector(self.save_path,
                                                                self.parameters["inputoutput"]["excel_filename"],
                                                                self.frames_per_second)
        self.dartboard_generator = DartboardGenerator(self.save_path)
        if self.parameters["properties"]["registration_method"] == "SITK" and sitk is not None:
            self.registration = Registration_SITK()
        else:
            self.registration = Registration_SR()

        self.wl1 = self.parameters["properties"]["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["properties"]["wavelength_2"]  # wavelength channel2
        self.processing_steps = [self.decon, self.bleaching]

    def select_rois(self):
        if not self.ATP_flag:
            # offset = self.estimated_cell_diameter_in_pixels * 0.6
            roi_list_cell_pairs = self.cell_tracker.give_rois(self.channel1, self.channel2, self.y_max, self.x_max,
                                                              self.model)
            self.nb_rois = len(roi_list_cell_pairs)
            print("\nCalculating ratio: ")
            with alive_bar(self.nb_rois, force_tty=True) as bar:
                time.sleep(.005)
                for i in range(self.nb_rois):
                    """
                    roi_m = [[xmin, ymin], [xmax, ymax]]
    
                    self.roi_minmax_list.append(roi_m)
                    # self.roi_coord_list.append(roi_coord[i])
    
                    roi1 = self.channel1[slice_roi]
                    roi2 = self.channel2[slice_roi]
                    """

                    """ # commented out for trouble shooting
                    if self.ATP_flag:
                        roi1, roi2 = self.ATP_image_converter.segment_membrane_in_ATP_image_pair(roi1, roi2,
                                                                                                 self.estimated_cell_area)
                    """

                    self.cell_list.append(CellImage(ChannelImage(roi_list_cell_pairs[i][0], self.wl1),
                                                    ChannelImage(roi_list_cell_pairs[i][1], self.wl2),

                                                    self.ATP_image_converter,
                                                    self.ATP_flag,
                                                    self.estimated_cell_area,
                                                    self.x_max,
                                                    roi_list_cell_pairs[i][2],
                                                    roi_list_cell_pairs[i][3])
                                                    )
                    bar()
        elif self.ATP_flag:
            seg_image = self.channel1[0].copy()

            if self.ATP_flag:
                seg_image = self.ATP_image_converter.prepare_ATP_image_for_segmentation(seg_image,
                                                                                        self.estimated_cell_area)

            self.roi_bounding_boxes = self.segmentation.give_coord(seg_image, self.estimated_cell_area, self.ATP_flag,
                                                                   self.model)
            print(self.roi_bounding_boxes)
            self.nb_rois = len(self.roi_bounding_boxes)
            yoffset = round(0.6 * self.estimated_cell_diameter_in_pixels)
            xoffset = round(0.6 * self.estimated_cell_diameter_in_pixels)

            for i in range(self.nb_rois):
                ymin = self.roi_bounding_boxes[i][0] - yoffset
                ymax = self.roi_bounding_boxes[i][1] + yoffset
                xmin = self.roi_bounding_boxes[i][2] - xoffset
                xmax = self.roi_bounding_boxes[i][3] + xoffset
                ymin, ymax, xmin, xmax = self.correct_coordinates(ymin, ymax, xmin, xmax)
                slice_roi = np.s_[:, int(ymin):int(ymax), int(xmin):int(xmax)]
                roi_m = [[xmin, ymin], [xmax, ymax]]
                self.roi_minmax_list.append(roi_m)
                # self.roi_coord_list.append(roi_coord[i])

                roi1 = self.channel1[slice_roi]
                roi2 = self.channel2[slice_roi]
                self.cell_list.append(CellImage(ChannelImage(roi1, self.wl1),
                                                ChannelImage(roi2, self.wl2),
                                                self.segmentation,
                                                self.ATP_image_converter,
                                                self.ATP_flag,
                                                self.estimated_cell_area))

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
        # find the cells
        self.select_rois()

        # bead contact, user input
        if len(self.cell_list) > 0:
            bead_contact_information = self.define_bead_contacts()
            self.assign_bead_contacts_to_cells(bead_contact_information)


        print("\nBleaching correction: ")
        with alive_bar(len(self.cell_list), force_tty=True) as bar:
            for cell in self.cell_list:
                time.sleep(.005)
                for step in self.processing_steps:
                    if step is not None:
                        time.sleep(.005)
                        step.run(cell, self.parameters, self.model)

                cell.generate_ratio_image_series()
                bar()

    def assign_bead_contacts_to_cells(self, bead_contact_information):
        for bead_contact in bead_contact_information:
            cell_index = bead_contact.return_cell_index()
            start_frame = bead_contact.return_frame_number()
            location = bead_contact.return_location()
            self.cell_list[cell_index].time_of_bead_contact = start_frame
            self.cell_list[cell_index].bead_contact_site = location

    def detect_hotspots(self, ratio_image, cell, i):
        if (not cell.is_preactivated(self.ratio_preactivation_threshold)):
            measurement_microdomains = self.hotspotdetector.measure_microdomains(ratio_image,
                                                                                 self.microdomain_signal_threshold,
                                                                                 6,   # lower area limit
                                                                                 20)  # upper area limit
            cell.signal_data = measurement_microdomains
            # self.hotspotdetector.save_dataframe(measurement_microdomains, i)
            self.dataframes_microdomains_list.append(measurement_microdomains)

        else:
            # print("this cell is preactivated")  # only temporarily
            self.excluded_cells_list.append(cell)
            cell.is_excluded = True

    def define_bead_contacts(self):
        """
        Let user define the bead contacts (time, location) for each cell
        :return:
        """
        bead_contact_gui = BeadContactGUI(self.image, self.cell_list, self.dartboard_number_of_sections)
        bead_contact_gui.run_main_loop()
        information = bead_contact_gui.return_bead_contact_information()
        return information



    def save_measurements(self):
        self.hotspotdetector.save_dataframes(self.dataframes_microdomains_list)


    def generate_average_dartboard_data_single_cell(self, centroid_coords_list, cell, cell_image_radius_after_normalization, cell_index):
        # dartboard_generator = DartboardGenerator(self.save_path)


        dartboard_data_all_frames = self.dartboard_generator.calculate_signals_in_dartboard_each_frame(cell.frame_number,
                                                                                       cell.signal_data,
                                                                                       self.dartboard_number_of_sections,
                                                                                       self.dartboard_number_of_areas_per_section,
                                                                                       centroid_coords_list,
                                                                                       cell_image_radius_after_normalization,
                                                                                       cell_index)
        start_frame = cell.time_of_bead_contact
        end_frame = cell.frame_number - 1
        mean_dartboard_data_single_cell = self.dartboard_generator.calculate_mean_dartboard(dartboard_data_all_frames,

                                                                                       start_frame,
                                                                                       end_frame,
                                                                                       self.dartboard_number_of_sections,
                                                                                       self.dartboard_number_of_areas_per_section)

        return mean_dartboard_data_single_cell

    def normalize_average_dartboard_data_one_cell(self, average_dartboard_data, real_bead_contact_site,
                                                  normalized_bead_contact_site):
        return self.dartboard_generator.normalize_average_dartboard_data_one_cell(average_dartboard_data,
                                                                                  real_bead_contact_site,
                                                                                  normalized_bead_contact_site)


    def generate_average_and_save_dartboard_multiple_cells(self, dartboard_data_multiple_cells):
        # dartboard_generator = DartboardGenerator(self.save_path)

        average_dartboard_data = self.dartboard_generator.calculate_mean_dartboard(dartboard_data_multiple_cells,

                                                                              0,
                                                                              10,
                                                                              self.dartboard_number_of_sections,
                                                                              self.dartboard_number_of_areas_per_section)


        self.dartboard_generator.save_dartboard_plot(average_dartboard_data,
                                                len(dartboard_data_multiple_cells),
                                                self.dartboard_number_of_sections,
                                                self.dartboard_number_of_areas_per_section)


    def normalize_cell_shape(self, cell):
        SN = ShapeNormalization(cell.ratio, cell.channel1.image, cell.channel2.image, self.model)
        cell.normalized_ratio_image = SN.apply_shape_normalization()
        centroid_coords_list = SN.get_centroid_coords_list()
        return cell.normalized_ratio_image, centroid_coords_list


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
            i += 1

    def save_ratio_image_files(self):
        i = 1
        for cell in self.cell_list:
            io.imsave(self.save_path + '/ratio_image' + str(i) + '.tif', cell.give_ratio_image(), check_contrast=False)
            i += 1
