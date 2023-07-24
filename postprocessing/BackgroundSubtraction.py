import skimage.measure
import numpy as np
import matplotlib.pyplot as plt
import skimage.io as io
import os
from skimage.filters import threshold_triangle, threshold_mean, threshold_otsu


class BackgroundSubtractor():
    def __init__(self, segmentation):
        self.segmentation = segmentation

    def clear_outside_of_cells(self, roi_before_backgroundcor_dict, cell_list):

        roi_cell_list = []
        for i in range(len(roi_before_backgroundcor_dict)):
            particle = list(roi_before_backgroundcor_dict.keys())[i]
            [roi1_old, roi2_old, particle_dataframe_subset, shifted_frame_masks] = roi_before_backgroundcor_dict[particle]

            roi1 = cell_list[i].give_image_channel1()
            roi2 = cell_list[i].give_image_channel2()
            roi1_background_subtracted = self.set_background_to_zero(shifted_frame_masks, roi1)
            roi2_background_subtracted = self.set_background_to_zero(shifted_frame_masks, roi2)
            ratio = cell_list[i].ratio
            ratio_background_subtracted = self.set_background_to_zero(shifted_frame_masks, ratio)
            roi_cell_list.append((roi1_background_subtracted, roi2_background_subtracted, particle_dataframe_subset,
                                  shifted_frame_masks, ratio_background_subtracted))
        return roi_cell_list

    def set_background_to_zero(self, frame_masks, cell_image_series):
        """
        Set background in a given cell image series to zero using a series of boolean masks
        :param frame_masks:
        :param cell_image_series:
        :return: the background subtracted image series
        """
        frame_number = len(cell_image_series)
        copy = cell_image_series.copy()
        for frame in range(frame_number):
            copy[frame] = self.apply_masks_on_image_series(cell_image_series[frame], frame_masks[frame])
        return copy

    def apply_masks_on_image_series(self, image_series, masks):
        """
        Applies a mask onto an image and sets a copy of the image series to 0 if the mask is True at that position
        :param image_series:
        :param masks:
        :return:
        """
        copy = image_series.copy()
        for frame in range(len(image_series)):
            copy[frame][masks[frame]] = 0
        return copy

    def measure_mean_background_intensity(self, image_frame):
        threshold = round(threshold_mean(image_frame))
        not_background_label = skimage.measure.label(image_frame > threshold)
        not_background_label[not_background_label > 1] = 1
        background_label = 1 - not_background_label
        region = skimage.measure.regionprops(label_image=background_label,
                                                         intensity_image=image_frame)
        background_mean_intensity = round(region[0].intensity_mean)
        return background_mean_intensity

    def subtract_background(self, channel_image_series):

        # mean intensity of background in first frame
        mean_background_first_frame = self.measure_mean_background_intensity(channel_image_series[0])

        # mean intensity of background in last frame
        mean_background_last_frame = self.measure_mean_background_intensity(channel_image_series[len(channel_image_series)-1])

        # linear interpolation data
        frames = [0, len(channel_image_series)-1]
        subtrahends = [mean_background_first_frame, mean_background_last_frame]
        # plt.plot(frames, thresholds)

        background_subtracted_channel = channel_image_series.copy()
        for frame in range(len(channel_image_series)):
            subtrahend = round(np.interp(frame, frames, subtrahends))
            max_value = np.max(background_subtracted_channel[frame])
            background_subtracted_channel[frame] -= subtrahend
            background_subtracted_channel[frame][background_subtracted_channel[frame] > max_value] = 0

        return background_subtracted_channel
