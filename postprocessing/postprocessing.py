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
        ((y1, y2), (x1, x2)) = roi_coord
        self.image = image[:, y1:y2, x1:x2]
        self.wavelength = wl

    def return_image(self):
        return self.image



class BaseCaImageProcessor:
    def __init__(self, path, parameter_dict):
        self.image = io.imread(path)
        self.parameters = parameter_dict
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