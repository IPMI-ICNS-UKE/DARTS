from __future__ import print_function
import matplotlib.pyplot as plt
from skimage import filters as filters
import matplotlib.patches as mpatches
import skimage.measure as measure
from skimage.morphology import area_closing
from skimage.morphology import binary_erosion, binary_dilation, remove_small_holes
from skimage.segmentation import clear_border
from skimage.measure import label
from skimage.util import invert
from skimage import io
from csbdeep.utils import normalize


class MembraneDetector:
    """
    A class that is able to detect the plasma membranes of cells in fluorescence microscopy images.
    """
    def __init__(self, segmentation_model):
        # creates a pretrained model
        self.segm_model = segmentation_model

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

    def find_cell_ROIs(self, img):
        """
        Finds the cell images in an image stack and returns the rectangular
        bounding boxes ("ROIs") and also a masks for the cell areas in these ROIs

        :param img: the input image stack, usually a fluorescence microscopy image stack in tiff format
        :return: returns an ordered list of ROIs and a boolean mask to segment
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


        # labelling of the cell images with Stardist2D
        labels, _ = self.segm_model.predict_instances(normalize(original_img_masked))
        regions = measure.regionprops(labels)
        # exclude labels that are too small
        # r.area > 6000 for 100x images, >500 for 63x images
        regions = [r for r in regions if r.area > 500]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(original_image)

        membrane_ROIs_bounding_boxes = []
        cropped_masks = []

        for region in regions:
            # create bounding box and append it to the "ROI-list"
            minr, minc, maxr, maxc = region.bbox
            membrane_ROIs_bounding_boxes.append((minr, minc, maxr, maxc))

            # create rectangle for visualisation
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor='red', linewidth=1.5)
            ax.add_patch(rect)
            cropped_mask = mask_negative[minr:maxr, minc:maxc]

            cropped_masks.append(cropped_mask)
        plt.show()

        return membrane_ROIs_bounding_boxes, cropped_masks

    def segment_membrane_in_roi_cell_pair(self, roi_tuple):
        """
        Segments the membrane in a cell image stack consisting of two ROIs (one for each channel), Sets the
        values outside the membrane to 0. The same membrane-area will be applied to both channels.

        :param roi_tuple: a tuple containing the ROIs of two corresponding cell image stacks (channel_1_roi, channel_2_roi)
        :return: a tuple containing the two membrane ROIs (one for each channel), congruent to each other
        """
        roi_tuple_channel_1 = roi_tuple[0].copy()
        roi_tuple_channel_2 = roi_tuple[1].copy()

        for frame_i in range(len(roi_tuple[0])):
            gaussian = filters.gaussian(roi_tuple[0][frame_i], 1.5)
            binary_image = gaussian < filters.threshold_li(gaussian)

            # remove small holes; practically removing small objects from the inside of the cell membrane
            # inverted logic
            # param area_threshold = 1000 for 100x images, 500 for 63x images
            small_objects_removed = remove_small_holes(binary_image, area_threshold=500, connectivity=2)
            membrane_mask = small_objects_removed == True

            roi_tuple_channel_1[frame_i] = self.apply_mask_on_image(roi_tuple[0][frame_i], membrane_mask, 0)
            roi_tuple_channel_2[frame_i] = self.apply_mask_on_image(roi_tuple[1][frame_i], membrane_mask, 0)

        return (roi_tuple_channel_1, roi_tuple_channel_2)

    def cut_out_cells_from_ROIs (self, cropped_cell_images_tuple, cell_masks):
        """
        Applies the previously generated mask containing the cell area on the cropped cell image stack. Sometimes other cells
        overlap into the ROI of a cell.

        :param cropped_cell_images_tuple: tuple containing two corresponding cell image stacks
        :param cell_masks: boolean masks to be applied on the ROIs
        :return: return the "cleaned" ROIs of the cells
        """
        images_tuple_copy = cropped_cell_images_tuple.copy()
        cleaned_rois = []
        for tuple_i in range(len(cropped_cell_images_tuple)):  # for each tuple
            current_mask = cell_masks[tuple_i]

            for frame in range(len(cropped_cell_images_tuple[0][0])):  # for each frame
                cropped_cell_images_tuple[tuple_i][0][frame] = self.apply_mask_on_image(cropped_cell_images_tuple[tuple_i][0][frame],
                                                                                 current_mask,
                                                                                 0)
                cropped_cell_images_tuple[tuple_i][1][frame] = self.apply_mask_on_image(cropped_cell_images_tuple[tuple_i][0][frame],
                                                                                 current_mask,
                                                                                 0)
            cleaned_rois.append((cropped_cell_images_tuple[tuple_i][0],
                                 cropped_cell_images_tuple[tuple_i][1]))
        return cleaned_rois


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

    def get_cropped_ROIs_from_image(self, img, membrane_ROIs_bounding_boxes):
        """
        Returns a list containing the cropped rectangular image stacks from the source image stack, based on the regions of interest
        in the list membrane_ROIs_bounding_boxes.

        :param img: the source image stack
        :param membrane_ROIs_bounding_boxes: the ordered list containing the regions of interest ("bounding boxes")
        :return: an ordered list containing the images representing the regions of interest in an image
        """
        cropped_ROIs_with_cells = []
        for bbox in membrane_ROIs_bounding_boxes:
            number_of_frames = len(img)
            min_y, max_y, min_x, max_x = (bbox[0]), (bbox[2]), (bbox[1]), (bbox[3])
            cropped_image = img[0:number_of_frames, min_y:max_y, min_x:max_x]
            cropped_ROIs_with_cells.append(cropped_image)
        return cropped_ROIs_with_cells

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





# Output of measurements to csv-file
"""
# The output of the function is a list of object properties.

# Test a few measurements
# print(clusters[0].perimeter)

# Can print various parameters for all objects
# for prop in clusters:
#    print('Label: {} Area: {}'.format(prop.label, prop.area))

# STEP 6

# Best way is to output all properties to a csv file

propList = ['Area',
            'Perimeter',
            'MinIntensity',
            'MeanIntensity',
            'MaxIntensity']

output_file = open('image_measurement.csv', 'w')
output_file.write(',' + ",".join(propList) + '\n')  # join strings in array by commas, leave first cell blank
# First cell blank to leave room for header (column names)

for cluster_props in clusters:
    # output cluster properties to the excel file
    output_file.write(str(cluster_props['Label']))
    for i, prop in enumerate(propList):
        if (prop == 'Area'):
            to_print = cluster_props[prop] * pixels_to_um ** 2  # Convert pixel square to um square
        elif (prop.find('Intensity') < 0):  # Any prop without Intensity in its name
            to_print = cluster_props[prop] * pixels_to_um
        else:
            to_print = cluster_props[prop]  # Remaining props, basically the ones with Intensity in its name
        output_file.write(',' + str(to_print))
    output_file.write('\n')
output_file.close()  # Closes the file, otherwise it would be read only.
"""
