import skimage.io as io
from csbdeep.utils import normalize
from matplotlib import pyplot as plt
import numpy as np
from postprocessing import membrane_detection






class BaseSegmentation:
    def __init__(self):
        self.membraneDetector = membrane_detection.MembraneDetector()

    # returns a list of corresponding cells in both channels [(cell1_channel1, cell1_channel2), (cell2_channel1, cell2_channel2), ...]
    def find_cell_pairs (self, input_image_path):
        test_input_path = "/Users/dejan/Downloads/MemBrite-Fix-488-568-640-yeast-mix.jpg"
        cell_list_wavelength1 = self.membraneDetector.detect_membranes_in_image(test_input_path)
        cell_list_wavelength2 = self.membraneDetector.detect_membranes_in_image(test_input_path)
        zip_list = list(zip(cell_list_wavelength1, cell_list_wavelength2))

        return zip_list

    def give_coord_channel1(self, input_image, seg_model):
        """

        :param input_image:
        :param seg_model:
        :return:
        """
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
        # mit offset bestimmen
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
        coord_list2.sort(key=lambda coord_list2: coord_list2[2])
        return coord_list2


class MembraneSegmentation (BaseSegmentation):

    def execute(self, channel1roi, channel2roi, parameters):
        processed_roi = self.create_membrane_mask (channel1roi, channel2roi, parameters)
        print (self.give_name())
        return processed_roi

    # same ROI for both channels needed
    def create_membrane_mask (self, channel1roi, channel2roi, parameters):
        segmented_membrane = None
        gaussian_blur_sigma = 2.0
        threshold = 0
        #return segmented_membrane
        return channel1roi

    # reduces channel_roi-image with the help of a "binary" membrane mask
    def apply_membrane_mask (self, channel_roi, membrane_mask):
        intersection = []
        #return intersection
        return channel_roi

    # Are the membranes in the two channels congruent?
    def calculate_congruence (self, channel_roi_1, channel_roi_2):
        pass

    def give_name (self):
        return "Membransegmentierung"




class BaseDecon:

    def execute(self, input_roi, parameters):
        processed_roi = self.deconvolve(input_roi, parameters)
        print(self.give_name())
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
        if (isinstance(step, MembraneSegmentation)):
            segmented_membrane_mask = step.execute(self.channel1, self.channel2, parameters) # not very handsome code
            self.channel1 = step.apply_membrane_mask(self.channel1, segmented_membrane_mask)
            self.channel2 = step.apply_membrane_mask(self.channel2, segmented_membrane_mask)
        elif (isinstance(step, RatioCalculation)):
            self.channel1 = step.execute(self.channel1, self.channel2, parameters)
            self.channel2 = step.execute(self.channel1, self.channel2, parameters)
        else:
            self.channel1 = step.execute(self.channel1, parameters)
            self.channel2 = step.execute(self.channel2, parameters)

        self.steps_executed.append(step.give_name())

    def calculate_ratio(self):
        ratio = self.channel1.return_image()/self.channel2.return_image()
        return ratio


class ImageROI:
    def __init__(self, image, roi_coord, wl):
        self.image = 0 #image[y1:y2, x1:x2]
        self.wavelength = wl

    def return_image(self):
        return self.image

    def return_membrane (self):
        return 0

    def get_wavelength (self):
        return self.wavelength





class ATPImageProcessor:
    def __init__(self, path, parameter_dict):
        self.image = io.imread(path)
        self.parameters = parameter_dict
        self.seg_model = segmentation_model
        self.cell_list = []
        self.segmentation = BaseSegmentation()
        self.membrane_segmentation = MembraneSegmentation()
        self.decon = BaseDecon()
        self.bleaching = BaseBleaching()
        self.bg_correction = BackgroundSubtraction()
        self.dartboard = Dartboard(10)
        self.ratio_calculation = RatioCalculation()

        self.wl1 = self.parameters["wavelength_1"] # wavelength channel1
        self.wl2 = self.parameters["wavelength_2"] # wavelength channel2

        self.processing_steps = [self.decon, self.bleaching, self.dartboard, self.ratio_calculation]


    def segment_cells(self):
        segmented_cell_in_both_channels= self.segmentation.find_cell_pairs(self.image)  # [[cell1roi488, cell1roi561], [], ...]
        for cellpair in segmented_cell_in_both_channels:
            self.cell_list.append(BaseCell(ImageROI(cellpair[0], 0, self.wl1),
                                           ImageROI(cellpair[1], 0, self.wl2)))

    def start_postprocessing(self):
        for cell in self.cell_list:

            cell.channel_registration()
            for step in self.processing_steps:
                cell.execute_processing_step(step, self.parameters)

    def return_ratios(self):
        ratio_list = []
        for cell in self.cell_list:
            ratio_list.append(cell.calculate_ratio())
        return ratio_list


class BaseBleaching:
    def give_name (self):
        return "Bleaching correction..."

    def execute (self, input_roi, parameters):
        bleaching_corrected = self.bleachingCorrection(input_roi, parameters)
        print(self.give_name())
        return bleaching_corrected

    def bleachingCorrection (self, input_roi, parameters):
        wavelength = input_roi.get_wavelength()

        # bleaching corrections in reference channel and sensor channel are different
        if (wavelength == parameters ["wavelength_1"]):
            pass
        elif (wavelength == parameters ["wavelength_2"]):
            pass
        return input_roi

    def give_name(self):
        return "bleaching corrected"


class BleachingExponentialFit (BaseBleaching):
    def __init__(self):
        pass



class BackgroundSubtraction:
    def execute (self, channel, parameters):
        print(self.give_name())
        return self.subtract_background(channel)

    def subtract_background(self, channel):
        pass

    def give_name(self):
        return "Background subtracted"

class Dartboard:
    def __init__(self, n):
        self.numberOfFields = n

    def execute (self, channel, parameters):
        print(self.give_name())
        return self.apply_dartboard_on_membrane(channel, parameters)

    # returns areas that divide a circular ROI into n sub-ROIs
    def apply_dartboard_on_membrane(self, channel_membrane, parameters):
        dartboard_areas = []
        dartboard_areas.append (DartboardArea())
        #return dartboard_areas
        return channel_membrane

    def give_name(self):
        return "dartboard erstellt"

class DartboardArea:
    def measure (self):
        return 0

class RatioCalculation:
    def execute (self, dartboard_channel1, dartboard_channel2, parameters):
        print(self.give_name())
        return self.calculate_ratio_dartboard(dartboard_channel1, dartboard_channel2, parameters)


    def calculate_ratio_dartboard (self, dartboard_channel1, dartboard_channel2, parameters):
        ratios = []
        #for area1, area2 in zip(dartboard_channel1, dartboard_channel2):
        #    r = area1.measure() / area2.measure()
        #    ratios.append(r)
        #return ratios
        return dartboard_channel1

    def give_name(self):
        return "Ratio für Dartboard-Bereiche berechnet"




def plot_cells(processor, path):
    fig, axs = plt.subplots(len(processor.cell_list), 2)
    axs[0, 0].set_title("channel1 wavelength: " + str(processor.cell_list[0].channel1.wavelength))
    axs[0, 1].set_title("channel2 wavelength: " + str(processor.cell_list[0].channel2.wavelength))

    for row in range(len(processor.cell_list)):
        axs[row, 0].imshow(processor.cell_list[row].channel1.image)
        axs[row, 1].imshow(processor.cell_list[row].channel2.image)
    plt.savefig(path + "cropped_cells")


