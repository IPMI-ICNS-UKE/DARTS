import skimage.io as io


class BaseSegmentation:
    def __init__(self):
        pass

    def give_coord_channel1(self, input_image):
        # gives list of all coordinates of ROIS in channel1
        coord_list1 = []
        return coord_list1
    def give_coord_channel2(self, input_image):
        # gives list of all coordinates of ROIS in channel2
        coord_list2 = []
        return coord_list2

class MembraneSegmentation (BaseSegmentation):

    def execute(self, channel1_roi, channel2_roi, parameters):
        processed_roi = self.createMembraneMask (channel1_roi, channel2_roi, parameters)
        return processed_roi

    # same ROI for both channels needed
    def createMembraneMask (self, channel1_roi, channel2_roi, parameters):
        segmented_Membrane = None
        gaussian_blur_sigma = 2.0
        threshold = 0
        return segmented_Membrane

    # reduces channel_roi-image with the help of a "binary" membrane mask
    def applyMembraneMask (self, channel_roi, membrane_mask):
        intersection = []
        return intersection

    # Are the membranes in the two channels congruent?
    def calculate_Congruence (self, channel_roi1, channel_roi2):
        pass

    def give_name (self):
        return "Membransegmentierung"




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
        if (isinstance(step, MembraneSegmentation)):
            segmentedMembraneMask = step.execute(self.channel1, self.channel2, parameters) # not very handsome code
            self.channel1 = step.applyMembraneMask(self.channel1, segmentedMembraneMask)
            self.channel2 = step.applyMembraneMask(self.channel2, segmentedMembraneMask)
        else:
            self.channel1 = step.execute(self.channel1, parameters)
            self.channel2 = step.execute(self.channel2, parameters)

        self.steps_executed.append(step.give_name())

    def calculate_ratio(self):
        ratio = self.channel1.return_image()/self.channel2.return_image()
        return ratio




class ImageROI:
    def __init__(self, image, roi_coord, wl):
        ((y1, y2), (x1, x2)) = roi_coord
        self.image = image[:, y1:y2, x1:x2]
        self.wavelength = wl
        # a "Sub-ROI" of the original ROI containing the membrane of the cell
        self.membrane = None

    def return_image(self):
        return self.image

    def return_membrane (self):
        return self.membrane

    def getWavelength (self):
        return self.wavelength





class BaseATPImageProcessor:
    def __init__(self, path, parameter_dict):
        self.image = io.imread(path)
        self.parameters = parameter_dict
        self.cell_list = []
        self.ratio_list = []
        self.segmentation = BaseSegmentation()
        self.membraneSegmentation = MembraneSegmentation()
        self.decon = BaseDecon()
        self.bleaching = BaseBleaching()
        self.bg_correction = BackgroundSubtraction()
        self.dartboard = Dartboard()
        self.ratioCalculation = RatioCalculation()

        self.wl1 = self.parameters["wavelength_1"] # wavelength channel1
        self.wl2 = self.parameters["wavelength_2"] # wavelength channel2
        self.processing_steps = [self.decon, self.bleaching, self.bg_correction,\
                                 self.membraneSegmentation, self.dartboard, self.ratioCalculation]


    def segment_cells(self):
        roi_coord_list_1 = self.segmentation.give_coord_channel1(self.image)
        roi_coord_list_2 = self.segmentation.give_coord_channel2(self.image)
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


class BaseBleaching:
    def give_name (self):
        return "Bleaching correction..."

    def execute (self, input_roi, parameters):
        bleaching_corrected = self.bleachingCorrection(input_roi, parameters)
        return bleaching_corrected

    def bleachingCorrection (self, input_roi, parameters):
        wavelength = input_roi.getWavelength()
        if (wavelength == parameters ["wavelength_1"]):
            pass
        elif (wavelength == parameters ["wavelength_2"]):
            pass
        return input_roi


class BleachingExponentialFit (BaseBleaching):
    def __init__(self):
        pass



class BackgroundSubtraction:
    def execute (self, channel, parameters):
        return self.subtract_background(channel)

    def subtract_background(self, channel):
        pass

    def give_name(self):
        return "Background subtracted"

class Dartboard:
    def __init__(self, n):
        self.numberOfFields = n

    def execute (self, channel, parameters):
        return self.applyDartboardOnMembrane(channel, parameters)

    # returns areas that divide a circular ROI into n sub-ROIs
    def applyDartboardOnMembrane(self, channel_membrane, parameters):
        pass

class RatioCalculation:
    def execute (self, dartboard_channel1, dartboard_channel2, parameters):
        return self.calculateRatioDartboard(dartboard_channel1, dartboard_channel2, parameters)

    def calculateRatioDartboard (self, dartboard_channel1, dartboard_channel2, parameters):
        ratio = []
        for area1, area2 in zip(dartboard_channel1, dartboard_channel2):
            r = area1.measure() / area2.measure()
            ratio.append(r)
        return ratio

    def give_name(self):
        return "Ratio für Dartboard-Bereiche berechnet"







