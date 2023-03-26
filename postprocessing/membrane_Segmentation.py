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