import skimage.io as io
import numpy as np
from postprocessing.cell import CellImage, ChannelImage
from postprocessing.segmentation import SegmentationSD
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

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
        self.roi_coord = []

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

        # TODO: how to specify offset
        yoffset = .03 * self.y_max
        xoffset = .03 * self.x_max
        for i in range(self.nb_rois):
            ymin = np.min(roi_coord_1[i, 0, :]) - yoffset
            ymax = np.max(roi_coord_1[i, 0, :]) + yoffset
            xmin = np.min(roi_coord_1[i, 1, :]) - xoffset
            xmax = np.max(roi_coord_1[i, 1, :]) + xoffset

            slice_roi = np.s_[:,int(ymin):int(ymax), int(xmin):int(xmax)]
            roi_c = [[xmin, ymin],[xmax,ymax]]
            self.roi_coord.append(roi_c)

            roi1 = self.channel1[slice_roi]
            roi2 = self.channel2[slice_roi]
            self.cell_list.append(CellImage(ChannelImage(roi1, self.wl1),
                                            ChannelImage(roi2, self.wl2)))


    def plot_rois(self):

        def format_axes(fig):
            for i, ax in enumerate(fig.axes):
                ax.set_axis_off()

        cmap_min = self.image[0].min()
        cmap_max = self.image[0].max()
        wratios = np.ones(self.nb_rois+1)
        wratios[1:] *= 0.5


        fig = plt.figure(layout="constrained",figsize=((self.nb_rois+1)*2 , 3))
        gs = GridSpec(2, self.nb_rois+1, figure=fig, width_ratios=wratios)
        ax1 = fig.add_subplot(gs[:, 0])
        ax1.imshow(self.image[0], vmin=cmap_min, vmax=cmap_max)

        for i in range(self.nb_rois):
            ax2 = fig.add_subplot(gs[0, i+1])
            ax3 = fig.add_subplot(gs[1, i+1])
            ax2.imshow(self.cell_list[i].give_image_channel1()[0], vmin=cmap_min, vmax=cmap_max)
            ax3.imshow(self.cell_list[i].give_image_channel2()[0], vmin=cmap_min, vmax=cmap_max)
            [[xmin, ymin], [xmax, ymax]] = self.roi_coord[i]

            w = xmax-xmin
            h = ymax-ymin
            os = self.image.shape[1]//2
            ax1.add_patch(Rectangle((xmin, ymin), w, h,
                                 edgecolor='blue',
                                 facecolor='none',
                                 lw=1))
            ax1.add_patch(Rectangle((xmin+os, ymin), w, h,
                                    edgecolor='red',
                                    facecolor='none',
                                    lw=1))
            ax2.add_patch(Rectangle((0,0), w-1, h-1,
                                    edgecolor='blue',
                                    facecolor='none',
                                    lw=1))
            ax3.add_patch(Rectangle((0,0), w-1, h-1,
                                    edgecolor='red',
                                    facecolor='none',
                                    lw=1))
            ax1.text(xmin+0.5*w, ymin+0.5*h, str(i+1), va="center", ha="center", c="blue")
            ax1.text((xmin+0.5*w)+os, ymin+0.5*h, str(i+1), va="center", ha="center", c="red")

            ax2.text(0.5, 0.5, str(i+1), transform=ax2.transAxes, va="center", ha="center", c="blue")
            ax3.text(0.5, 0.5, str(i+1), transform=ax3.transAxes, va="center", ha="center", c="red")

        format_axes(fig)

        plt.show(block=False)
        return fig




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



