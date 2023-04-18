import skimage.io as io
import tifffile
from matplotlib import pyplot as plt
from postprocessing import membrane_detection, Cell_Image_Registration
from stardist.models import StarDist2D






class BaseSegmentation:
    def __init__(self, segmentation_model):
        self.membraneDetector = membrane_detection.MembraneDetector(segmentation_model)
        self.cellRegistrator = Cell_Image_Registration.CellImageRegistrator ()

    def find_cell_membrane_pairs(self, image_wavelength_1, image_wavelength_2):
        """
        Finds the pairs of cells in two corresponding fluorescence microscopy image time series and returns a zipped
        list of the ROIs containing the cells. The membranes of the main cells in the ROIs are separated from cell images
        overlapping with the ROI.

        :param image_wavelength_1: image stack in the first wavelength, for example 488nm
        :param image_wavelength_2: image stack in the second wavelength, for example 561nm
        :return:  a list in the following style:
                    [[cell_1_channel_1, cell_1_channel_2], [cell_2_channel_1, cell_2_channel_2], ...]
        """

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



        # find the cells in the first frame of the reference channel
        membrane_ROIs_bounding_boxes_channel_1, cell_masks = self.membraneDetector.find_cell_ROIs(image_wavelength_1[0])

        # now the bounding boxes can be applied to both channels in the same order
        cropped_cell_images_channel1 = self.membraneDetector.get_cropped_ROIs_from_image(image_wavelength_1,
                                                                                         membrane_ROIs_bounding_boxes_channel_1)

        cropped_cell_images_channel2 = self.membraneDetector.get_cropped_ROIs_from_image(image_wavelength_2,
                                                                                         membrane_ROIs_bounding_boxes_channel_1)


        # register cropped cells in first frame and override the ROIs of the cell images in channel 2
        for i in range(len(cropped_cell_images_channel1)):
            current_channel1_image = cropped_cell_images_channel1[i][0]  # takes the first frame of the current cell image in channel
            current_channel2_image = cropped_cell_images_channel2[i][0]

            x_offset, y_offset = self.cellRegistrator.measure_offset(current_channel1_image, current_channel2_image)

            corrected_bounding_box = self.cellRegistrator.return_corrected_ROI(-x_offset,
                                                                               -y_offset,
                                                                               membrane_ROIs_bounding_boxes_channel_1[i])
            cropped_cell_images_channel2[i] = self.membraneDetector.get_cropped_ROIs_from_image(image_wavelength_2,
                                                                                                corrected_bounding_box)[0]

        # saves the registered and cropped raw images of the cells on the computer
        save_path = "/Users/dejan/Documents/Doktorarbeit/Python_save_path/raw_cell_images"
        self.save_cropped_cell_images(cropped_cell_images_channel1, cropped_cell_images_channel2, save_path)

        # creates a list of cropped cell images in tuples:    [(cell_1_channel_1, cell_1_channel_2),
        #                                                      (cell_2_channel_1, cell_2_channel_2), ..]
        zip_cell_list = list(zip(cropped_cell_images_channel1, cropped_cell_images_channel2))

        # modifies the channel images by segmenting the membrane (congruent in both channels)
        zip_cell_list[:] = [self.membraneDetector.segment_membrane_in_roi_cell_pair(tuple) for tuple in zip_cell_list]

        zip_cell_list = self.membraneDetector.cut_out_cells_from_ROIs(zip_cell_list, cell_masks) # needs to be updated after implementation of registration

        return zip_cell_list

    def save_cropped_cell_images(self, channel_1_cell_images, channel_2_cell_images, save_path):
        """
        Saves the unprocessed but cropped raw cell images on the computer
        """
        i = 1
        for i in range(len(channel_1_cell_images)):
            io.imsave(save_path + '/raw_cropped_cell_image_channel_1_nr_' + str(i) + '.tif',
                      channel_1_cell_images[i])
            io.imsave(save_path + '/raw_cropped_cell_image_channel_2_nr_' + str(i) + '.tif',
                      channel_2_cell_images[i])
            i += 1


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
    def __init__(self, image, wl):
        self.image = image
        self.wavelength = wl

    def return_image(self):
        return self.image


    def get_wavelength (self):
        return self.wavelength


class ATPImageProcessor:
    """
    A Processor of fluorescence microscope images, which show the signal of an ATP-sensor on the membrane of cells.
    The sensor is a ratiometric sensor. That's why there are two channels. One of the channels serves as the reference
    channel. The other channel represents the ATP-dependent channel.
    """
    def __init__(self, path_wavelength_1, path_wavelength_2, segmentation_model, parameter_dict):

        self.image_wavelength_1 = tifffile.imread(path_wavelength_1)
        self.image_wavelength_2 = tifffile.imread(path_wavelength_2)

        self.parameters = parameter_dict
        self.seg_model = segmentation_model
        self.cell_list = []
        self.segmentation = BaseSegmentation(segmentation_model)
        self.decon = BaseDecon()
        self.bleaching = BaseBleaching()
        self.bg_correction = BackgroundSubtraction()
        self.dartboard = Dartboard(10)
        self.ratio_calculation = RatioCalculation()


        self.wl1 = self.parameters["wavelength_1"]  # wavelength channel1
        self.wl2 = self.parameters["wavelength_2"]  # wavelength channel2

        self.wl1 = self.parameters["wavelength_1"] # wavelength channel1
        self.wl2 = self.parameters["wavelength_2"] # wavelength channel2


        self.processing_steps = [self.decon, self.bleaching, self.dartboard, self.ratio_calculation]

    def segment_cells(self):
        """
        Segments the cell membranes in the images of both wavelengths and creates a cell list with new cells, which
        contain the representations of the membrane in both channels
        """
        segmented_cells_in_both_channels = self.segmentation.find_cell_membrane_pairs(self.image_wavelength_1,
                                                                                      self.image_wavelength_2)
        for cellpair in segmented_cells_in_both_channels:
            self.cell_list.append(BaseCell(ImageROI(cellpair[0], self.wl1),
                                           ImageROI(cellpair[1], self.wl2)))

    def start_postprocessing(self):

        """
        Starts the postprocessing-pipeline after segmentaiton of the cells. Each cell has to execute a list of defined
        steps
        """
        if (len(self.cell_list) > 0):
            for cell in self.cell_list:
                cell.channel_registration()
                for step in self.processing_steps:
                    cell.execute_processing_step(step, self.parameters)
        else:
            print ("No cells have been detected!")


        for cell in self.cell_list:

            cell.channel_registration()
            for step in self.processing_steps:
                cell.execute_processing_step(step, self.parameters)


    def return_ratios(self):
        ratio_list = []
        for cell in self.cell_list:
            ratio_list.append(cell.calculate_ratio())
        return ratio_list

    def save_image_files(self, save_path):
        """
        Saves the image files within the cells of the celllist in the given path.
        :param save_path: The target path.
        """
        i = 1
        for cell in self.cell_list:
            io.imsave(save_path + '/test_image_channel1_' + str(i) + '.tif', cell.get_imageROI_channel1().return_image())
            io.imsave(save_path + '/test_image_channel2_' + str(i) + '.tif', cell.get_imageROI_channel2().return_image())
            i += 1


class BaseBleaching:
    def execute(self, input_roi, parameters):
        bleaching_corrected = self.bleaching_correction(input_roi, parameters)
        print(self.give_name())
        return bleaching_corrected

    def bleaching_correction(self, input_roi, parameters):
        wavelength = input_roi.get_wavelength()

        # bleaching corrections in reference channel and sensor channel are different
        if wavelength == parameters["wavelength_1"]:
            pass
        elif wavelength == parameters["wavelength_2"]:
            pass
        return input_roi

    def give_name(self):
        return "bleaching corrected"


class BleachingExponentialFit (BaseBleaching):
    def __init__(self):
        pass


class BackgroundSubtraction:
    def execute(self, channel, parameters):
        print(self.give_name())
        return self.subtract_background(channel)

    def subtract_background(self, channel):
        pass

    def give_name(self):
        return "Background subtracted"


class Dartboard:
    def __init__(self, n):
        self.numberOfFields = n

    def execute(self, channel, parameters):
        print(self.give_name())
        return self.apply_dartboard_on_membrane(channel, parameters)

    # returns areas that divide a circular ROI into n sub-ROIs
    def apply_dartboard_on_membrane(self, channel_membrane, parameters):
        dartboard_areas = []
        dartboard_areas.append(DartboardArea())
        return channel_membrane

    def give_name(self):
        return "dartboard erstellt"


class DartboardArea:
    def measure(self):
        return 0


class RatioCalculation:
    def execute(self, channel, parameters):  # needs to be changed
        print(self.give_name())
        return self.calculate_ratio_dartboard(channel, parameters)


    def calculate_ratio_dartboard (self, channel, parameters):


    def calculate_ratio_dartboard (self, dartboard_channel1, dartboard_channel2, parameters):

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

