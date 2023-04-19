from skimage.transform import SimilarityTransform
from skimage.transform import warp

class CellImage:
    def __init__(self, roi1, roi2):
        self.channel1 = roi1
        self.channel2 = roi2
        self.steps_executed = []
        self.ratio = None
        self.cell_image_registrator = CellImageRegistrator()

    def channel_registration(self):
        print("Here comes the channel registration")
        x_offset, y_offset = self.cell_image_registrator.measure_mean_offset_optical_flow(self.channel1.return_image(),
                                                                                          self.channel2.return_image())
        tform = SimilarityTransform(translation=(-x_offset, -y_offset))
        self.channel2.image = warp(self.channel2.return_image, tform)

    def calculate_ratio(self):
        ratio = self.channel1.return_image()/self.channel2.return_image()
        return ratio

    def give_image_channel1(self):
        return self.channel1.return_image()

    def give_image_channel2(self):
        return self.channel2.return_image()

    def execute_processing_step(self, step, parameters):
        self.channel1 = step.execute(self.channel1, parameters)
        self.channel2 = step.execute(self.channel2, parameters)
        self.steps_executed.append(step.give_name())



class ChannelImage:
    def __init__(self, roi, wl):

        # ((y1, y2), (x1, x2)) = roi_coord
        # self.image = image[:, y1:y2, x1:x2]
        self.image = roi
        self.wavelength = wl

    def return_image(self):
        return self.image

    def return_membrane (self):
        return self.membrane

    def getWavelength (self):
        return self.wavelength


from skimage import io
from skimage import registration
import numpy as np
from scipy.ndimage import shift
from matplotlib import pyplot as plt


class CellImageRegistrator:
    def __init__(self):
        pass

    def measure_mean_offset_optical_flow (self, channel_1_image, channel_2_image):
        """
        Performs optical flow measurement with a reference image and a corresponding offset image.

        :param reference_channel_first_frame: the reference image
        :param offset_channel_first_frame:  the cell image that has an offset compared to the reference
        :return xoff:
        """

        flow = registration.optical_flow_tvl1(channel_1_image, channel_2_image)

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

        """
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
        """

        return xoff, yoff


