from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, color, filters as filters
from scipy import ndimage
import matplotlib.patches as mpatches
from skimage.segmentation import watershed
import skimage.measure as measure
from skimage.morphology import area_closing
from skimage.feature import peak_local_max
from skimage.measure import regionprops, label
from skimage.util import invert
import numpy as np
import math



class MembraneDetector:

    # returns a list containing the images of membranes in a fluorescence microscopy image
    def return_membrane_ROIs (self, image):
        original_image = image.copy()
        # manipulate image with gaussian filtering and Otsu's thresholding
        image = filters.gaussian(image, 2)
        image = image < filters.threshold_triangle(image)

        #invert image so that holes can be properly filled
        image_inverted = invert(image)


        # Fill holes within the cells in the binary image
        image_closed = area_closing(image_inverted, area_threshold=100000, connectivity=2)

        # label the cell membranes
        labels = label(image_closed, connectivity = 2)

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
        regions = [r for r in regions if r.area > 8000 and r.area < 12000]

        # remove the non-segmented areas from the original image
        mask = image == True  # just the 2D boolean-array in image
        original_image[mask] = 0

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
        return membrane_ROIs_bounding_boxes, original_image


    # receives a list of bounding boxes defining the ROIs
    # applies the ROIs on an image and returns a list of cropped images
    def get_cropped_ROIs_from_image (self, img, membrane_ROIs_bounding_boxes):
        cropped_ROIs_with_cells = []
        for bbox in membrane_ROIs_bounding_boxes:
            cropped_image = img[(bbox[0]):(bbox[2]), (bbox[1]):(bbox[3])]  #minr, minc, maxr, maxc = region.bbox
            cropped_ROIs_with_cells.append(cropped_image)
        return cropped_ROIs_with_cells





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

#commit message added
