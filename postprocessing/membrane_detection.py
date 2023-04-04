#!/usr/bin/env python
__author__ = "Sreenivas Bhattiprolu"
# modified by Dejan Kovacevic


"""
This code performs detection of cells marked with a fluorophore on the membrane.

Step 1: Read image and define pixel size (if needed to convert results into microns, not pixels)
Step 2: Denoising, if required and threshold image to separate grains from boundaries.
Step 3: Clean up image, if needed (erode, etc.) and create a mask for grains
Step 4: Label grains in the masked image
Step 5: Measure the properties of each grain (object)
Step 6: Output results into a csv file
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import ndimage
from skimage import measure, color, io
from skimage.segmentation import clear_border

# STEP1 - Read image and define pixel size
img = cv2.imread("/Users/dejan/Downloads/MemBrite-Fix-488-568-640-yeast-mix.jpg", 0)
# img = cv2.imread ("/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_488-4.tif", 0)

pixels_to_um = 0.5  # (1 px = 500 nm)

# cropped_img = img[0:450, :]   #Crop the scalebar region

# Step 2: Denoising, if required and threshold image
gaussian_blurred = cv2.GaussianBlur (img, (1,1),0)

# Otherwise, try Median or NLM
# plt.hist(img.flat, bins=100, range=(0,255))

# Change the grey image to binary by thresholding.
ret, thresh = cv2.threshold(gaussian_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)


# Step 3: Clean up image, if needed (erode, etc.) and create a mask for grains

# kernel = np.ones((3, 3), np.uint8)
# eroded = cv2.erode(thresh, kernel, iterations=1)
# dilated = cv2.dilate(eroded, kernel, iterations=1)

# Now, we need to apply threshold, meaning convert uint8 image to boolean.
mask = thresh == 255  # Sets TRUE for all 255 valued pixels and FALSE for 0
mask = clear_border(mask)   #Removes edge touching particles.

io.imshow(mask)  # cv2.imshow() not working on boolean arrays so using io
# io.imshow(mask[250:280, 250:280])   #Zoom in to see pixelated binary image

# Step 4: Label particles in the masked image

# Now we have well separated particles and background. Each particle is like an object.
# The scipy ndimage package has a function 'label' that will number each object with a unique ID.

# The 'structure' parameter defines the connectivity for the labeling.
# This specifies when to consider a pixel to be connected to another nearby pixel,
# i.e. to be part of the same object.

# use 8-connectivity, diagonal pixels will be included as part of a structure
# this is ImageJ default but we have to specify this for Python, or 4-connectivity will be used
# 4 connectivity would be [[0,1,0],[1,1,1],[0,1,0]]
s = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
# label_im, nb_labels = ndimage.label(mask)
labeled_mask, num_labels = ndimage.label(mask, structure=s)

# The function outputs a new image that contains a different integer label
# for each object, and also the number of objects found.

# color the labels to see the effect
img2 = color.label2rgb(labeled_mask, bg_label=0)

# cv2.imshow('Colored Grains', img2)
# cv2.waitKey(0)

# View just by making mask=threshold and also mask = dilation (after morph operations)
# Some grains are well separated after morph operations

# Now each object had a unique number in the image.
# Total number of labels found are...
# print(num_labels)

# Step 5: Measure the properties of each grain (object)

# regionprops function in skimage measure module calculates useful parameters for each object.

clusters = measure.regionprops(labeled_mask, img)  # send in original image for Intensity measurements

# The output of the function is a list of object properties.

# Test a few measurements
# print(clusters[0].perimeter)

# Can print various parameters for all objects
# for prop in clusters:
#    print('Label: {} Area: {}'.format(prop.label, prop.area))

# Step 6: Output results into a csv file
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



fig, ax = plt.subplots(figsize=(10, 6))
ax.imshow(img)

cell_list = []

cell_number = 0
for region in clusters:
    # take regions with large enough areas
    if region.area > 50 and region.area < 1000:
        # draw rectangle around segmented area
        minr, minc, maxr, maxc = region.bbox
        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                  fill=False, edgecolor='white', linewidth=1.5)
        ax.add_patch(rect)
        cropped_image = img[(minr):(maxr), (minc):(maxc)]
        # cv2.imwrite("test_segmentaiton_" + str (cell_number) + ".jpg", cropped_image)
        cell_number += 1

ax.set_axis_off()
plt.tight_layout()
plt.show()



"""
OLD CODE: 

import matplotlib.pyplot as plt
from skimage import data
from skimage.filters import threshold_otsu, gaussian, threshold_triangle
from skimage import io
from skimage.color import rgb2gray

#read image and create grayscale image
original_image = io.imread("MemBrite-Fix-488-568-640-yeast-mix.jpg")
grayscale_image = rgb2gray(original_image)

#smoothen image with gaussian filter
gaussian_blurred = gaussian(grayscale_image, 0.2)

#thresholding
thresh = threshold_otsu(gaussian_blurred)
binary = gaussian_blurred > thresh

#plotting
fig, axes = plt.subplots(ncols=2, figsize=(10, 5))
ax = axes.ravel()
ax[0] = plt.subplot(1, 2, 1)
ax[1] = plt.subplot(1, 2, 2, sharex=ax[0], sharey=ax[0])

ax[0].imshow(original_image, cmap=plt.cm.gray)
ax[0].set_title('Original image')
ax[0].axis('off')

ax[1].imshow(binary, cmap=plt.cm.gray)
ax[1].set_title('Smoothened and thresholded')
ax[1].axis('off')

plt.show()
"""