from __future__ import print_function
import matplotlib.pyplot as plt
from skimage import filters as filters
import matplotlib.patches as mpatches
import skimage.measure as measure
from skimage.morphology import area_closing
from skimage.morphology import binary_erosion, binary_dilation, remove_small_holes
from skimage.measure import label
from skimage.util import invert


class MembraneDetector:
    """
    A class that is able to detect the plasma membranes of cells in fluorescence microscopy images.
    """

    def return_membrane_ROIs(self, image):
        """
        Returns a list containing the rectangular ROIs surrounding cell membranes in a fluorescence microscopy image and
        a mask for the original image to separate the membranes from the rest.

        :param image: the fluorescence microscopy image
        :return:
        membrane_ROIs_bounding_boxes -  is the ordered list containing the rectangular ROIs;
        mask -  is the binary mask for manipulation of the original image (see apply_mask_on_image(img, mask))
        """
        # manipulate image with gaussian filtering and thresholding
        image = filters.gaussian(image, 2)
        image = image < filters.threshold_li(image)

        # remove small holes; practically removing small objects from the inside of the cell membrane
        image = remove_small_holes(image, area_threshold=1000, connectivity=2)

        # invert image so that holes can be properly filled
        image_inverted = invert(image)

        # dilate image to close holes in the membrane
        number_of_iterations = 4
        image_inverted_dilated = self.binary_dilate_n_times(image_inverted, number_of_iterations)

        # Fill holes within the cell membranes in the binary image
        image_inverted_dilated_closed = area_closing(image_inverted_dilated, area_threshold=200000, connectivity=2)

        # erode again after dilation (same number of iterations)
        image_inverted_eroded_closed = self.binary_erode_n_times(image_inverted_dilated_closed, number_of_iterations)

        # label the cells
        labels = label(image_inverted_eroded_closed, connectivity=2)

        # Watershed causes trouble...
        """
        # separation of the objects in the image by watershed
        # does not really work(?)
        # alternatively use find contours and draw contours
        distance = ndimage.distance_transform_edt(image_closed)
        coords = peak_local_max(distance, footprint=np.ones((3, 3)), labels=image_closed)
        mask = np.zeros(distance.shape, dtype=bool)
        mask[tuple(coords.T)] = True
        markers, _ = ndimage.label(mask)
        labels = watershed(-distance, markers, mask=image_closed)
        """

        # measure the properties of the regions and exclude the regions with small areas
        regions = measure.regionprops(labels)

        # only include regions with an area within a certain range, experimentally determined range...
        regions = [r for r in regions if 6000 < r.area < 13000]

        # create mask for the original image; mask will be returned by this function
        mask = image == True  # just the 2D boolean-array in image

        # process the segmented regions
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(image)

        membrane_ROIs_bounding_boxes = []
        for region in regions:
            # create bounding box and append it to the "ROI-list"
            minr, minc, maxr, maxc = region.bbox
            membrane_ROIs_bounding_boxes.append((minr, minc, maxr, maxc))

            # create rectangle
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor='red', linewidth=1.5)

            ax.add_patch(rect)
        plt.show()
        return membrane_ROIs_bounding_boxes, mask

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
        Returns a list containing the cropped rectangular images from the source image, based on the regions of interest
        in the list membrane_ROIs_bounding_boxes.

        :param img: the source image
        :param membrane_ROIs_bounding_boxes: the ordered list containing the regions of interest ("bounding boxes")
        :return: an ordered list containing the images representing the regions of interest in an image
        """
        cropped_ROIs_with_cells = []
        for bbox in membrane_ROIs_bounding_boxes:
            cropped_image = img[(bbox[0]):(bbox[2]), (bbox[1]):(bbox[3])]  # minr, minc, maxr, maxc = region.bbox
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


