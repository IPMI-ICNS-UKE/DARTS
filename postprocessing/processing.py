import math
import skimage.io as io
import numpy as np
from postprocessing.cell import CellImage, ChannelImage
from postprocessing.segmentation import SegmentationSD, ATPImageConverter
from postprocessing.CellTracker_ROI import CellTracker
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle
from pystackreg import StackReg

class ImageProcessor:
    def __init__(self, parameter_dict):
        self.parameters = parameter_dict

        # handle different input formats: either two channels in one image or one image per channel
        if self.parameters["properties"]["channel_format"] == "two-in-one":
            self.image = io.imread(self.parameters["inputoutput"]["path_to_input_combined"])
            # separate image into 2 channels: left half and right half
            if self.image.ndim == 3:  # for time series
                self.channel1, self.channel2 = np.split(self.image, 2, axis=2)
                self.t_max, self.y_max, self.x_max = self.image.shape
            elif self.image.ndim == 2:  # for static images
                self.channel1, self.channel2 = np.split(self.image, 2, axis=1)
                self.y_max, self.x_max = self.image.shape
        elif self.parameters["properties"]["channel_format"] == "single":
            self.channel1 = io.imread(self.parameters["inputoutput"]["path_to_input_channel1"])
            self.channel2 = io.imread(self.parameters["inputoutput"]["path_to_input_channel2"])
            if self.channel1.ndim == 3:  # for time series
                self.image = np.concatenate((self.channel1, self.channel2), axis=2)
                self.t_max, self.y_max, self.x_max = self.image.shape
            elif self.channel1.ndim == 2:
                self.image = np.concatenate((self.channel1, self.channel2), axis=1)
                self.y_max, self.x_max = self.image.shape
        self.scale_microns_per_pixel = self.parameters["properties"]["scale_microns_per_pixel"]
        self.estimated_cell_diameter_in_pixels = self.parameters["properties"]["estimated_cell_diameter_in_pixels"]
        self.estimated_cell_area = round((0.5*self.estimated_cell_diameter_in_pixels)**2 * math.pi)

        self.ATP_flag = self.parameters["properties"]["ATP"]
        self.cell_list = []
        self.ratio_list = []
        self.nb_rois = None
        self.roi_minmax_list = []
        # self.roi_coord_list = []
        self.roi_bounding_boxes = []
        self.cell_tracker = CellTracker()
        self.segmentation = SegmentationSD()
        self.ATP_image_converter = ATPImageConverter()
        self.decon = None
        self.bleaching = None

        self.wl1 = self.parameters["properties"]["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["properties"]["wavelength_2"]  # wavelength channel2
        self.processing_steps = [self.decon, self.bleaching]

    def select_rois(self):
        if not self.ATP_flag:
            # offset = self.estimated_cell_diameter_in_pixels * 0.6
            roi_list_cell_pairs = self.cell_tracker.give_rois(self.channel1, self.channel2)
            self.nb_rois = len(roi_list_cell_pairs)
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
                                                self.segmentation,
                                                self.ATP_image_converter,
                                                self.ATP_flag,
                                                self.estimated_cell_area))
        elif self.ATP_flag:
            seg_image = self.channel1[0].copy()
            if self.ATP_flag:
                seg_image = self.ATP_image_converter.prepare_ATP_image_for_segmentation(seg_image, self.estimated_cell_area)
            self.roi_bounding_boxes = self.segmentation.give_coord(seg_image, self.estimated_cell_area, self.ATP_flag)
            self.nb_rois = len(self.roi_bounding_boxes)
            yoffset = round(0.2 * self.estimated_cell_diameter_in_pixels)
            xoffset = round(0.2 * self.estimated_cell_diameter_in_pixels)

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

    def channel_registration(self):
        """
        Registration of the two channels based on affine transformation. The first channel is defined as the reference
        channel, the second one as the offset channel. A transformation matrix is calculated by comparing the first frame
        of each channel. The matrix is applied to each frame of the offset channel.
        Assumption: The offset remains constant from the first to the last frame.
        """
        print("registration of channel 1 and channel 2")
        image = self.channel1[0]
        offset_image = self.channel2[0]
        sr = StackReg(StackReg.AFFINE)
        transformation_matrix = sr.register(image, offset_image)

        for frame in range(len(self.channel2)):
            self.channel2[frame] = sr.transform(self.channel2[frame], transformation_matrix)
        # self.channel2 = sr.transform(self.channel2, transformation_matrix)

        fig = plt.figure(figsize=(10, 10))
        ax1 = fig.add_subplot(2, 2, 1)
        ax1.imshow(offset_image, cmap='gray')
        ax1.title.set_text('Input Image')
        ax2 = fig.add_subplot(2, 2, 4)
        ax2.imshow(self.channel2[0], cmap='gray')
        # ax2.imshow(self.channel2, cmap='gray')
        ax2.title.set_text('Affine')
        plt.show()

    def save_registered_first_frames(self):
        save_path = "/Users/dejan/Documents/Doktorarbeit/Python_save_path/"
        io.imsave(save_path + '/channel_1_frame_1' + '.tif', self.channel1)
        io.imsave(save_path + '/channel_2_frame_1_registered' + '.tif', self.channel2)

    def start_postprocessing(self):
        # TO DO ggf. hier channel_registration mit dem ganzen Bild?
        # self.channel_registration()
        # self.save_registered_first_frames()
        self.select_rois()
        for cell in self.cell_list:
            for step in self.processing_steps:
                if step is not None:
                    step.run(cell, self.parameters)

    def return_ratios(self):
        for cell in self.cell_list:
            self.ratio_list.append(cell.calculate_ratio())
        return self.ratio_list

    def add_scale_bars(self):
        """
        Adds scale bars to the cell image time series before saving them.
        """

    def save_image_files(self, save_path):
        """
        Saves the image files within the cells of the celllist in the given path.
        :param save_path: The target path.
        """
        i = 1
        for cell in self.cell_list:
            io.imsave(save_path + '/test_image_channel1_' + str(i) + '.tif', cell.give_image_channel1())
            io.imsave(save_path + '/test_image_channel2_' + str(i) + '.tif', cell.give_image_channel2())
            i += 1

    def save_ratio_image_files(self, save_path):
        i = 1
        for cell in self.cell_list:
            io.imsave(save_path + '/ratio_image' + str(i) + '.tif', cell.return_ratio_image())
            i += 1
