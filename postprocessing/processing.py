import skimage.io as io
import numpy as np
from postprocessing.cell import CellImage, ChannelImage
from postprocessing.segmentation import SegmentationSD
from matplotlib import pyplot as plt


class ImageProcessor:
    def __init__(self, path, parameter_dict):
        self.image = io.imread(path)
        # separate image into 2 channels: left half and right half
        if self.image.ndim == 3:      # for time series
            self.channel1, self.channel2 = np.split(self.image, 2, axis=2)
            self.t_max, self.y_max, self.x_max = self.image.shape
        elif self.image.ndim == 2:    # for static images
            self.channel1, self.channel2 = np.split(self.image, 2, axis=1)
            self.y_max, self.x_max = self.image.shape
        self.parameters = parameter_dict
        self.cell_list = []
        self.ratio_list = []
        self.nb_rois = None
        self.roi_coord = None

        self.segmentation = SegmentationSD()
        self.decon = None
        self.bleaching = None

        #self.seg_model = segmentation_model
        #self.membraneSegmentation = None
        #self.bg_correction = None
        #self.dartboard = None
        #self.ratioCalculation = None

        self.wl1 = self.parameters["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["wavelength_2"]  # wavelength channel2
        self.processing_steps = [self.decon, self. bleaching]
        #self.processing_steps = [self.decon, self.membraneSegmentation, self.bleaching, self.dartboard,
        #                         self.ratioCalculation]
        # Reihenfolge??? -> Reihenfolge mit DropDown Menu bestimmen?
        # lieber als set implementieren?

    def select_rois(self):

        # TODO: Segmentierung über die Zeit?
        # TODO: specify which channel to segment first
        seg_image = self.channel1[0]
        roi_coord_1 = self.segmentation.give_coord(seg_image)
        roi_coord_2 = roi_coord_1[0, 1, :] + (self.x_max // 2)

        self.nb_rois = len(roi_coord_1)
        self.roi_coord = np.zeros((self.nb_rois, 2))

        # TODO: how to specify offset
        yoffset = .03 * self.y_max
        xoffset = .03 * self.x_max
        for i in range(self.nb_rois):
            ymin = np.min(roi_coord_1[i, 0, :]) - yoffset
            ymax = np.max(roi_coord_1[i, 0, :]) + yoffset
            xmin = np.min(roi_coord_1[i, 1, :]) - xoffset
            xmax = np.max(roi_coord_1[i, 1, :]) + xoffset

            roi1 = self.channel1[int(ymin):int(ymax), int(xmin):int(xmax)]
            roi2 = self.channel2[int(ymin):int(ymax), int(xmin):int(xmax)]
            self.cell_list.append(CellImage(ChannelImage(roi1, self.wl1),
                                            ChannelImage(roi2, self.wl2)))


    def plot_rois(self):

        fig, ax = plt.subplots()
        ax.imshow(self.image)
        for i in range(self.nb_rois):
            ymin = np.min(roi_coord_1[i, 0, :]) - yoffset
            ymax = np.max(roi_coord_1[i, 0, :]) + yoffset
            xmin = np.min(roi_coord_1[i, 1, :]) - xoffset
            xmax = np.max(roi_coord_1[i, 1, :]) + xoffset




    def start_postprocessing(self):
        self.select_rois()
        for cell in self.cell_list:
            cell.channel_registration()
            for step in self.processing_steps:
                if step is not None:
                    step.run(cell, self.parameters)

    def return_ratios(self):
        for cell in self.cell_list:
            self.ratio_list.append(cell.calculate_ratio())
        return self.ratio_list


    def plot_cells(cell_list):
        nb_cells = len(cell_list)

        fig, ax = plt.subplots()


