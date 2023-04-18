from skimage import io
from skimage import registration
import numpy as np
from scipy.ndimage import shift
from matplotlib import pyplot as plt


class CellImageRegistrator:
    def __init__(self):
        pass

    def measure_offset (self, reference_channel_first_frame, offset_channel_first_frame):
        """
        Performs optical flow measurement with a reference image and a corresponding offset image.

        :param reference_channel_first_frame: the reference image
        :param offset_channel_first_frame:  the cell image that has an offset compared to the reference
        :return xoff:
        """

        flow = registration.optical_flow_tvl1(reference_channel_first_frame, offset_channel_first_frame)

        # dense optical flow
        flow_x = flow[1, :, :]
        flow_y = flow[0, :, :]

        # find mean shift in x and y direction
        xoff = np.mean(flow_x)
        yoff = np.mean(flow_y)
        print("x offset" + str(xoff))
        print("y offset" + str(yoff))

        # round offsets
        xoff = round(xoff)
        yoff = round(yoff)

        return xoff, yoff

    def return_corrected_ROI (self, x_offset, y_offset, membrane_bounding_box):
        min_y = round(membrane_bounding_box[0] + y_offset)
        min_x = round(membrane_bounding_box[1] + x_offset)
        max_y = round(membrane_bounding_box[2] + y_offset)
        max_x = round(membrane_bounding_box[3] + x_offset)

        return [(min_y, min_x, max_y, max_x)]




# -- TEST AREA --
# path_reference = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_488-4-2-frame-duplicated-image-1-1_gray_8bit.tif"
# translated image in Fiji by 15pixels in x-direction and 15 pixels in y-direction
# path_offset = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_561-4-2-frame-duplicated-image-1-1-translated_15_15-2_gray_8_bit.tif"

path_offset = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/test_images_registration/abstract-paper-flower-pattern-656688606-5acfba2eae9ab80038461ca0-1-translated.tif"
path_reference = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/test_images_registration/abstract-paper-flower-pattern-656688606-5acfba2eae9ab80038461ca0.tif"

from skimage.color import rgb2gray
reference_channel = io.imread(path_reference)
offset_channel = io.imread(path_offset)

flow = registration.optical_flow_tvl1(reference_channel, offset_channel)

# dense optical flow
flow_x = flow[1, :, :]
flow_y = flow[0, :, :]

# find mean shift in x and y direction
xoff = np.mean(flow_x)
yoff = np.mean(flow_y)
print("x offset" + str(xoff))
print("y offset" + str(yoff))

# round offsets
xoff = round(xoff)
yoff = round(yoff)


corrected_image = shift(offset_channel, shift=(-xoff, -yoff), mode='constant')
fig = plt.figure(figsize=(10, 10))
ax1 = fig.add_subplot(2, 2, 1)
ax1.imshow(reference_channel, cmap='gray')
ax1.title.set_text('Reference Image')
ax2 = fig.add_subplot(2, 2, 2)
ax2.imshow(offset_channel, cmap='gray')
ax2.title.set_text('Offset image')
ax3 = fig.add_subplot(2, 2, 3)
ax3.imshow(corrected_image, cmap='gray')
ax3.title.set_text('Corrected')
plt.show()
# print("Pixels shifted by: ", xoff, yoff)
