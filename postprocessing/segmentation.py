import math

import matplotlib.pyplot as plt
# from stardist.models import StarDist2D
from csbdeep.utils import normalize
from skimage import filters as filters, measure
from skimage.morphology import area_closing
from skimage.morphology import binary_erosion, binary_dilation, remove_small_holes
from skimage.segmentation import clear_border
from skimage.util import invert
import skimage.io as io
import statistics
from scipy import ndimage as ndi
import pims

from postprocessing.membrane_detection import MembraneDetector
import os


class SegmentationSD:
    def __init__(self, model):
        self.model = model

    def give_coord(self, input_image, estimated_cell_area, atp_flag):
        # gives list of all coordinates of ROIS in channel1
        seg_img, output_specs = self.model.predict_instances(normalize(input_image), prob_thresh=0.6, nms_thresh=0.2,
                                                        predict_kwargs=dict(verbose=False))
        regions = measure.regionprops(seg_img)
        cell_images_bounding_boxes = []
        # TO DO threshold needs to be optimised/generalised for resolution/cell type/ATP vs. Calcium images
        # TO DO for example 63x images of ATP-sensor loaded cells vs. 100x
        # TO DO cells diameter should be specified in pixels (=> user input: expected diameter in microns and scale)
        for region in regions:
            if (not atp_flag or (
                    region.area > 1.2 * estimated_cell_area)):  # < 1.5 * estimated_cell_area): # TO DO needs to be optimised
                miny_bbox, minx_bbox, maxy_bbox, maxx_bbox = region.bbox
                cell_images_bounding_boxes.append((miny_bbox, maxy_bbox, minx_bbox, maxx_bbox))
        return cell_images_bounding_boxes

    def find_median_image_size(self, regions):
        regions_areas = [r.area for r in regions]
        return statistics.median(regions_areas)

    def stardist_segmentation_in_frame(self, image_frame):
        img_labels, img_details = self.model.predict_instances(normalize(image_frame), predict_kwargs=dict(verbose=False))
        return img_labels


class ATPImageConverter:
    def __init__(self):
        self.MembraneDetector = MembraneDetector()

    """
    Converts ATP-sensor images so that they the cell images can be segmented by Stardist properly.
    """

    def prepare_ATP_image_for_segmentation(self, img, estimated_cell_area):
        """
        Prepares fluorescence microscopy images of the membrane (loaded with an ATP-sensor) so that they can get
        segmented by the Stardist algorithm.
        :param img: the fluorescence microscopy image
        :param estimated_cell_area: the estimated average area of the cells represented by the image in square-pixels

        :return: converted copy of the image (holes filled etc.)
        """
        original_image = img.copy()
        # smoothing and thresholding
        img = filters.gaussian(img, 2)  # TO DO needs to be optimised
        # triangle for 100x images, li for 63x images; test with mean algorithm
        thresh = filters.threshold_triangle(img)
        img = img < thresh
        # img = img < filters.threshold_li(img) # TO DO needs to be optimised

        # remove small holes; removes small particles
        # param area_threshold = 1000 for 100x images, 500 for 63x images
        # img = remove_small_holes(img, area_threshold=estimated_cell_area*0.2, connectivity=2)
        # TO DO needs to be optimised

        # invert image so that holes can be properly filled
        img = invert(img)

        # remove objects on the edge
        img = clear_border(img)

        # dilate image to close holes in the membrane
        number_of_iterations = 4  # TO DO needs to be optimised
        img = self.binary_dilate_n_times(img, number_of_iterations)

        # Fill holes
        img = ndi.binary_fill_holes(img)

        # erode again after dilation (same number of iterations)
        img = self.binary_erode_n_times(img, number_of_iterations)
        # io.imshow(img)
        # plt.show()

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

    def segment_membrane_in_ATP_image_pair(self, channel_1_image, channel_2_image, estimated_cell_area):
        channel1 = channel_1_image.copy()
        channel2 = channel_2_image.copy()

        for frame in range(len(channel1)):
            gaussian = filters.gaussian(channel_1_image[frame], 2)
            binary_image = gaussian < filters.threshold_li(gaussian)  # TO DO needs to be optimised

            # remove small holes; practically removing small objects from the inside of the cell membrane
            # inverted logic
            # param area_threshold = 1000 for 100x images, 500 for 63x images
            small_objects_removed = remove_small_holes(binary_image, area_threshold=estimated_cell_area * 0.2,
                                                       connectivity=2)  # TO DO needs to be optimised
            membrane_mask = small_objects_removed == True
            channel1[frame] = self.apply_mask_on_image(channel1[frame], membrane_mask, 0)
            channel2[frame] = self.apply_mask_on_image(channel2[frame], membrane_mask, 0)

        return channel1, channel2

    def apply_mask_on_image(self, img, mask, n):
        """
        Applies a boolean mask on an image-array. Every value in the image that the mask is "True" for will be changed
        to the parameter n.

        :param img: the image-array to be modified
        :param n: target value of the elements in the img that are "True" in the mask
        :param mask: boolean mask which will be applied. Needs to have the same size as img
        :return: returns the modified image
        """
        original_image = img

        original_image[mask] = n
        return original_image


"""
# TEST AREA
image_converter = ATPImageConverter()
path = "/Users/dejan/Documents/GitHub/T-DARTS/Data/ATP/230221_ATPOS_Optimierung_1_w1Dual-CF-488-561-camera2-1-duplicate-10frames.tif"
atp_image = io.imread(path)
atp_image = atp_image[0]
image_converter.prepare_ATP_image_for_segmentation(atp_image)
"""
