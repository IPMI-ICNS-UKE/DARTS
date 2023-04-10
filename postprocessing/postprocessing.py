import skimage.io as io
import tifffile
from skimage import color
from csbdeep.utils import normalize
from matplotlib import pyplot as plt
import numpy as np
from postprocessing import membrane_detection
from skimage.util import img_as_ubyte
from tifffile import imread

class BaseSegmentation:
    def __init__(self):
        self.membraneDetector = membrane_detection.MembraneDetector()

    # returns a list of corresponding cell membranes in both channels [(cell1_channel1, cell1_channel2), (cell2_channel1, cell2_channel2), ...]
    def find_cell_pairs (self, image):
        # returns the rectangular ROIs containing the cell membranes
        # returns the original image but without the areas surrounding the membranes (mask has already been applied)
        membrane_ROIs_bounding_boxes, original_image_only_membranes = self.membraneDetector.return_membrane_ROIs(image)

        #now the bounding boxes can be applied to both channels in the same order
        cropped_cell_images_channel1 = self.membraneDetector.get_cropped_ROIs_from_image(original_image_only_membranes,
                                                                                         membrane_ROIs_bounding_boxes) #image needs to be specified as channel 1 image
        cropped_cell_images_channel2 = self.membraneDetector.get_cropped_ROIs_from_image(original_image_only_membranes,
                                                                                         membrane_ROIs_bounding_boxes) #image needs to be specified as channel 2 image
        zipped_cell_list = list(zip(cropped_cell_images_channel1, cropped_cell_images_channel2))
        return zipped_cell_list



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
        self.channel1 = step.execute(self.channel1, parameters)
        self.channel2 = step.execute(self.channel2, parameters)

        self.steps_executed.append(step.give_name())

    def calculate_ratio(self):
        ratio = self.channel1.return_image()/self.channel2.return_image()
        return ratio

    def get_imageROI_channel1 (self):
        return self.channel1

    def get_imageROI_channel2(self):
        return self.channel2


class ImageROI:
    def __init__(self, image, roi_coord, wl):
        self.image = image
        self.wavelength = wl

    def return_image(self):
        return self.image


    def get_wavelength (self):
        return self.wavelength





class ATPImageProcessor:
    def __init__(self, path, parameter_dict):
        
        self.image = tifffile.imread(path)
        self.parameters = parameter_dict
        self.cell_list = []
        self.segmentation = BaseSegmentation()
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
        # print (len(segmented_cell_in_both_channels))
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

    def save_image_files (self, save_path):
        i = 1
        for cell in self.cell_list:
            io.imsave(save_path + '/test_image_channel1_' + str(i) + '.tif', cell.get_imageROI_channel1().return_image())
            io.imsave(save_path + '/test_image_channel2_' + str(i) + '.tif', cell.get_imageROI_channel2().return_image())
            i += 1


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
    def execute (self, channel, parameters): # needs to be changed
        print(self.give_name())
        return self.calculate_ratio_dartboard(channel, parameters)

    def calculate_ratio_dartboard (self, channel, parameters):
        ratios = []
        #for area1, area2 in zip(dartboard_channel1, dartboard_channel2):
        #    r = area1.measure() / area2.measure()
        #    ratios.append(r)
        #return ratios
        return channel

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

#commit message added
