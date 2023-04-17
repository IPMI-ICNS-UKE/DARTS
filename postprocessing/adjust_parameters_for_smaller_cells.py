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
from stardist.models import StarDist2D
from stardist.data import test_image_nuclei_2d
from stardist.plot import render_label
from csbdeep.utils import normalize
import matplotlib.pyplot as plt


def binary_erode_n_times(img, n):
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


def binary_dilate_n_times(img, n):
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


img = io.imread("/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230221_ATPOS_Optimierung_1_w1Dual-CF-488-561-camera2-1-duplicate-10frames.tif")
img = img[0]
original_image = img.copy()

# smoothing and thresholding
img = filters.gaussian(img, 2)
img = img < filters.threshold_li(img)



# remove small holes; practically removing small objects from the inside of the cell membrane
img = remove_small_holes(img, area_threshold=500, connectivity=2)
# 1000, 500,


# invert image so that holes can be properly filled
img = invert(img)

# dilate image to close holes in the membrane
number_of_iterations = 4
img = binary_dilate_n_times(img, number_of_iterations)


# Fill holes within the cell membranes in the binary image
img = area_closing(img, area_threshold=10000, connectivity=2)
# 200000, 100000, 50000, 10000


# erode again after dilation (same number of iterations)
img = binary_erode_n_times(img, number_of_iterations)


# remove objects on the edge
img = clear_border(img)


# assign the value 255 to all black spots in the image and the value 0 to all white areas
# kopie_mit_einsen = np.ones_like(img)
mask_positive = img == True
mask_negative = img == False

original_img_masked = original_image.copy()
original_img_masked[mask_positive] = 255
original_img_masked[mask_negative] = 0

segmentation_model = StarDist2D.from_pretrained('2D_versatile_fluo')
# labelling of the cell images with Stardist2D
labels, _ = segmentation_model.predict_instances(normalize(original_img_masked))
io.imshow(labels)
regions = measure.regionprops(labels)
regions = [r for r in regions if r.area > 500]
# 6000, 1000, 500

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

plt.subplot(1,2,1)
plt.imshow(original_image, cmap="gray")
plt.axis("off")
plt.title("input image")

plt.subplot(1,2,2)
plt.imshow(render_label(labels, img=original_image))
plt.axis("off")
plt.title("prediction + input overlay")
plt.show()