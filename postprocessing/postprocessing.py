import skimage.io as io
from csbdeep.utils import normalize
from matplotlib import pyplot as plt
import numpy as np


class BaseSegmentation:
    def __init__(self):
        pass

    def give_coord_channel1(self, input_image, seg_model):
        # gives list of all coordinates of ROIS in channel1
        coord_list1 = []
        seg_img_channel1, output_specs_channel1 = seg_model.predict_instances(normalize(np.hsplit(input_image, 2)[0]),
                                                                              prob_thresh=0.6, nms_thresh=0.2)
        if len(output_specs_channel1['coord']) >= 0:
            for coords in output_specs_channel1['coord']:
                x_coords = coords[1]
                y_coords = coords[0]
                coord_list1.append(list(zip(x_coords, y_coords)))
        coord_list1.sort(key=lambda coord_list1: coord_list1[2])
        return coord_list1

    def give_coord_channel2(self, input_image, seg_model):
        # gives list of all coordinates of ROIS in channel2
        coord_list2 = []
        seg_img_channel2, output_specs_channel2 = seg_model.predict_instances(normalize(np.hsplit(input_image, 2)[1]),
                                                                              prob_thresh=0.6, nms_thresh=0.2)
        if len(output_specs_channel2['coord']) >= 0:
            for coords in output_specs_channel2['coord']:
                x_coords = coords[1]
                x_coords = [x + float(input_image.shape[1] / 2) for x in x_coords]
                y_coords = coords[0]
                coord_list2.append(list(zip(x_coords, y_coords)))
        coord_list2.sort(key=lambda coord_list1: coord_list1[2])
        return coord_list2



class BaseDecon:

    def execute(self, input_roi, parameters):
        processed_roi = self.deconvolve(input_roi, parameters)
        return processed_roi

    def give_name(self):
        return "...deconvolution.."

    def deconvolve(self, input_roi, parameters):
        return input_roi



class BaseCell:
    def __init__(self, roi1, roi2):
        self.channel1 = roi1
        self.channel2 = roi2
        self.steps_executed = []
        self.ratio = None

    def channel_registration(self):
        # registration of channel 1 and 2
        pass

    def execute_processing_step(self, step, parameters):
        self.channel1 = step.execute(self.channel1, parameters)
        self.channel2 = step.execute(self.channel2, parameters)
        self.steps_executed.append(step.give_name())

    def calculate_ratio(self):
        ratio = self.channel1.return_image()/self.channel2.return_image()
        return ratio


class ImageROI:
    def __init__(self, image, roi_coord, wl):

        x1 = int(min(point[0] for point in roi_coord))
        x2 = int(max(point[0] for point in roi_coord))
        y1 = int(min(point[1] for point in roi_coord))
        y2 = int(max(point[1] for point in roi_coord))

        # ((y1, y2), (x1, x2)) = roi_coord
        # self.image = image[:, y1:y2, x1:x2]
        self.image = image[y1:y2, x1:x2]
        self.wavelength = wl

    def return_image(self):
        return self.image



class BaseCaImageProcessor:
    def __init__(self, path, parameter_dict, segmentation_model):
        self.image = io.imread(path)
        self.parameters = parameter_dict
        self.seg_model = segmentation_model
        self.cell_list = []
        self.ratio_list = []
        self.segmentation = BaseSegmentation()
        self.decon = BaseDecon()
        self.bleaching = None
        self.bg_correction = None
        self.wl1 = self.parameters["wavelength_1"] # wavelength channel1
        self.wl2 = self.parameters["wavelength_2"] # wavelength channel2
        self.processing_steps = [self.decon, self.bleaching, self.bg_correction]


    def segment_cells(self):
        roi_coord_list_1 = self.segmentation.give_coord_channel1(self.image, self.seg_model)
        roi_coord_list_2 = self.segmentation.give_coord_channel2(self.image, self.seg_model)
        for coord1, coord2 in zip(roi_coord_list_1, roi_coord_list_2):
            self.cell_list.append(BaseCell(ImageROI(self.image, coord1, self.wl1),
                                           ImageROI(self.image, coord2, self.wl2)))

    def start_postprocessing(self):
        self.segment_cells()
        for cell in self.cell_list:
           cell.channel_registration()
           for step in self.processing_steps:
                   cell.execute_processing_step(step, self.parameters)

    def return_ratios(self):
        for cell in self.cell_list:
            self.ratio_list.append(cell.calculate_ratio())
        return self.ratio_list


def plot_cells(processor, path):
    fig, axs = plt.subplots(len(processor.cell_list), 2)
    axs[0, 0].set_title("channel1 wavelength: " + str(processor.cell_list[0].channel1.wavelength))
    axs[0, 1].set_title("channel2 wavelength: " + str(processor.cell_list[0].channel2.wavelength))

    for row in range(len(processor.cell_list)):
        axs[row, 0].imshow(processor.cell_list[row].channel1.image)
        axs[row, 1].imshow(processor.cell_list[row].channel2.image)
    plt.savefig(path + "cropped_cells")