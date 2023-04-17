from stardist.models import StarDist2D
from csbdeep.utils import normalize
from skimage import filters as filters
from skimage.morphology import area_closing
from skimage.morphology import binary_erosion, binary_dilation, remove_small_holes
from skimage.segmentation import clear_border
from skimage.util import invert


class SegmentationSD:
    def __init__(self, model='2D_versatile_fluo'):
        self.model = StarDist2D.from_pretrained(model)

    def give_coord(self, input_image):
        # gives list of all coordinates of ROIS in channel1
        seg_img, output_specs = self.model.predict_instances(normalize(input_image), prob_thresh=0.6, nms_thresh=0.2)
        return output_specs['coord']


class SegmentationATP:
    def __init__(self, model='2D_versatile_fluo'):
        self.model = StarDist2D.from_pretrained(model)

    def give_coord(self, input_image):
        masked_image = self.give_masked_image(input_image)
        seg_img, output_specs = self.model.predict_instances(normalize(masked_image))
        return output_specs['coord']

    def give_masked_image(self, img):
        """
        Returns a masked image
        :param img: the input image stack, usually a fluorescence microscopy image stack in tiff format
        """
        original_image = img.copy()

        # smoothing and thresholding
        img = filters.gaussian(img, 2)
        # triangle for 100x images, li for 63x images
        img = img < filters.threshold_li(img)
        # img = img < filters.threshold_triangle(img)

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
        # kopie_mit_einsen = np.ones_like(img)
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
