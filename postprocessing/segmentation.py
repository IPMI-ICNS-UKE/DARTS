from stardist.models import StarDist2D
from csbdeep.utils import normalize
from skimage import filters as filters, measure
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
        regions = measure.regionprops(seg_img)
        cell_images_bounding_boxes = []

        for region in regions:
            miny_bbox, minx_bbox, maxy_bbox, maxx_bbox = region.bbox
            cell_images_bounding_boxes.append((miny_bbox, maxy_bbox, minx_bbox, maxx_bbox))

        return cell_images_bounding_boxes


class ATPImageConverter:
    """
    Converts ATP-sensor images so that they the cell images can be segmented by Stardist properly.
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
        # img = img < filters.threshold_triangle(img)
        img = img < filters.threshold_li(img)

        # remove small holes; practically removing small objects from the inside of the cell membrane
        # param area_threshold = 1000 for 100x images, 500 for 63x images
        img = remove_small_holes(img, area_threshold=500, connectivity=2)

        # invert image so that holes can be properly filled
        img = invert(img)

        # dilate image to close holes in the membrane
        number_of_iterations = 4
        img = self.binary_dilate_n_times(img, number_of_iterations)

        # Fill holes within the cell membranes in the binary image
        # param area_threshold = 200000 for 100x images, 100000 for 63x images
        img = area_closing(img, area_threshold=100000, connectivity=2)

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

        for frame in range(len(channel1)):
            gaussian = filters.gaussian(channel_1_image[frame], 1.5)
            binary_image = gaussian < filters.threshold_li(gaussian)

            # remove small holes; practically removing small objects from the inside of the cell membrane
            # inverted logic
            # param area_threshold = 1000 for 100x images, 500 for 63x images
            small_objects_removed = remove_small_holes(binary_image, area_threshold=500, connectivity=2)
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