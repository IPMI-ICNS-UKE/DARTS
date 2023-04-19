from stardist.models import StarDist2D
from csbdeep.utils import normalize
import numpy as np
from skimage import filters as filters
from skimage.morphology import area_closing
from skimage.morphology import binary_erosion, binary_dilation, remove_small_holes
from skimage.segmentation import clear_border
from skimage.util import invert

class SegmentationSD:
    def __init__(self, model='2D_versatile_fluo'):
        self.model = StarDist2D.from_pretrained(model)
        pass

    def give_coord(self, input_image):
        # gives list of all coordinates of ROIS in channel1
        seg_img, output_specs = self.model.predict_instances(normalize(input_image), prob_thresh=0.6, nms_thresh=0.2)
       # if len(output_specs['coord']) >= 0:
       #     for coords in output_specs['coord']:
       #         x_coords = coords[1]
       #         y_coords = coords[0]
       #         coord_list.append(list(zip(x_coords, y_coords)))
       # coord_list.sort(key=lambda coord_list1: coord_list1[2])
        return output_specs['coord']

class BaseSegmentation:
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

class ATPImageConverter:
    """
    Converts ATP-sensor images so that they can be processed in the segmentation pipeline.
    """

    def prepare_ATP_image_for_segmentation(self, img):
        """
        Prepares fluorescence microscopy images of the membrane (loaded with an ATP-sensor) so that they can get
        segmented by the Stardist algorithm.
        :param img: the fluorescence microscopy image
        :return: converted copy of the image (holes filled etc.)
        """
        original_image = img.copy()
        # smoothing and thresholding
        img = filters.gaussian(img, 2)
        # triangle for 100x images, li for 63x images
        img = img < filters.threshold_triangle(img)
        # img = img < filters.threshold_li(img)

        # remove small holes; practically removing small objects from the inside of the cell membrane
        # param area_threshold = 1000 for 100x images, 500 for 63x images
        img = remove_small_holes(img, area_threshold=1000, connectivity=2)

        # invert image so that holes can be properly filled
        img = invert(img)

        # dilate image to close holes in the membrane
        number_of_iterations = 4
        img = self.binary_dilate_n_times(img, number_of_iterations)

        # Fill holes within the cell membranes in the binary image
        # param area_threshold = 200000 for 100x images, 100000 for 63x images
        img = area_closing(img, area_threshold=200000, connectivity=2)

        # erode again after dilation (same number of iterations)
        img = self.binary_erode_n_times(img, number_of_iterations)

        # remove objects on the edge
        img = clear_border(img)

        # assign the value 255 to all black spots in the image and the value 0 to all white areas
        mask_positive = img == True
        mask_negative = img == False

        original_img_masked = original_image.copy()
        original_img_masked[mask_positive] = 255
        original_img_masked[mask_negative] = 0

        return original_img_masked

    def binary_erode_n_times(self, img, n):
        """
        Returns the binary-eroded input image "img" after n iterations.
        :param img: the input image
        :param n: the number of iterations
        :return: the n-times binary-eroded image
        """
        img_eroded = img
        for x in range(n):
            img_eroded = binary_erosion(img_eroded)
        return img_eroded

    def binary_dilate_n_times(self, img, n):
        """
        Returns the binary-dilated input image "img" after n iterations.
        :param img: the input image
        :param n: the number of iterations
        :return: the n-times binary-dilated image
        """
        img_dilated = img
        for x in range(n):
            img_dilated = binary_dilation(img_dilated)
        return img_dilated

    def segment_membrane_in_ATP_image_pair(self, channel_1_image, channel_2_image):
        channel1 = channel_1_image.copy()
        channel2 = channel_2_image.copy()

        gaussian = filters.gaussian(channel_1_image, 1.5)
        binary_image = gaussian < filters.threshold_li(gaussian)

        # remove small holes; practically removing small objects from the inside of the cell membrane
        # inverted logic
        # param area_threshold = 1000 for 100x images, 500 for 63x images
        small_objects_removed = remove_small_holes(binary_image, area_threshold=1000, connectivity=2)
        membrane_mask = small_objects_removed == True

        channel1 = self.apply_mask_on_image(channel1, membrane_mask, 0)
        channel2 = self.apply_mask_on_image(channel2, membrane_mask, 0)

        return channel1, channel2