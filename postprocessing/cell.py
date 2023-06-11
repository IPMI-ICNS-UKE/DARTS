import numpy as np
import pandas as pd
import trackpy as tp
import skimage
from scipy.ndimage import shift
import skimage.io as io
import matplotlib.pyplot as plt
from skimage import measure
from tqdm import tqdm
from statistics import mean



class CellImage:
    def __init__(self, roi1, roi2, atp_image_converter, atp_flag, estimated_cell_area, cell_image_data=None, frame_masks=None):
        self.channel1 = roi1
        self.channel2 = roi2
        self.steps_executed = []
        self.ratio = None
        self.cell_image_registrator = None
        self.atp_image_converter = atp_image_converter
        self.atp_flag = atp_flag
        self.estimated_cell_area = estimated_cell_area
        self.more_than_one_trajectory = False
        self.processing_flag = None
        self.cell_image_data = cell_image_data
        self.frame_masks = frame_masks
        self.frame_number = len(self.channel1.return_image())

        self.normalized_ratio_image = None

        self.cell_is_preactivated = False
        self.number_of_frames_before_cell_activation = 0
        self.signal_data = None




    def is_preactivated(self, ratio_preactivation_threshold):
        """
        Checks if a cell image shows a preactivated cell. (A cell activated before addition of beads or compound.)
        :param ratio_activation_threshold:
        :return:
        """
        cell_preactivated = self.measure_mean_ratio_single_frame(0) > ratio_preactivation_threshold
        self.cell_is_preactivated = cell_preactivated
        return cell_preactivated

    def measure_mean_ratio_in_all_frames(self):
        """
        Measures the mean ratio of this cell image series in every frame.
        :return:
        """
        for frame in range(self.frame_number):
            self.measure_mean_ratio_single_frame(frame)

    def measure_mean_values_in_first_n_frames(self, number_of_frames):
        mean_values = []
        for n in range(number_of_frames):
            current_mean = self.measure_mean_ratio_single_frame(n)
            mean_values.append(current_mean)
        return mean_values

    def standard_deviation_of_mean_values(self,mean_values):
        return np.std(mean_values)

    def calculate_signal_threshold(self, first_n_frames):
        mean_values_in_first_n_frames = self.measure_mean_values_in_first_n_frames(first_n_frames)
        mean_value_of_mean_values = mean(mean_values_in_first_n_frames)
        standard_deviation = self.standard_deviation_of_mean_values(mean_values_in_first_n_frames)
        signal_threshold = mean_value_of_mean_values + 1.96*standard_deviation  # just an example
        return signal_threshold

    def measure_mean_ratio_single_frame(self, frame):
        """
        Measures the mean ratio in the ratio image series of this cell image in one given frame. Uses
        the cell mask from the earlier segmentation.

        :param frame:
        :return: Mean ratio of cell image in specific frame
        """
        boolean_mask = np.invert(self.frame_masks[frame])
        label = skimage.measure.label(boolean_mask)

        # channel_1_frame_image = self.channel1.return_image()[frame]
        # channel_2_frame_image = self.channel2.return_image()[frame]

        regionprops_ratio = measure.regionprops(label, intensity_image=self.ratio[frame])
        mean_ratio_frame = regionprops_ratio[0].intensity_mean

        # print("mean values")
        # print(str(mean_channel1_frame))
        # print(str(mean_channel2_frame))
        return mean_ratio_frame


    def generate_ratio_image_series(self):
        ratio_image = self.channel1.return_image().astype(float)
        frame_number = len(self.channel1.return_image())

        print("Calculate ratio")
        for frame in tqdm(range(frame_number)):
            ratio_image[frame] = self.calculate_ratio(frame)
        self.ratio = ratio_image

    def calculate_ratio(self, frame_number):
        """
        Calculates the ratio of two corresponding cell images (same frame) and returns the ratio image
        :param frame_number:
        :return:
        """
        frame_channel_1 = (self.channel1.return_image())[frame_number] * 1.0
        frame_channel_2 = (self.channel2.return_image())[frame_number] * 1.0

        # ratio = np.divide(frame_channel_1, frame_channel_2)

        # division of the two image arrays, but sets pixels to zero if divisor is zero
        ratio = np.divide(frame_channel_1, frame_channel_2, out=np.zeros_like(frame_channel_1), where=frame_channel_2!=0)
        # TO DO user needs to specify which channel is the dividend and which is the divisor
        return ratio

    def give_ratio_image(self):
        """
        Returns the ratio_image
        """
        return self.ratio

    def give_image_channel1(self):
        return self.channel1.return_image()

    def give_image_channel2(self):
        return self.channel2.return_image()

    def set_image_channel2(self,processed_image_series):
        self.channel2.set_image(processed_image_series)

    def execute_processing_step(self, step, parameters):
        self.channel1 = step.execute(self.channel1, parameters)
        self.channel2 = step.execute(self.channel2, parameters)
        self.steps_executed.append(step.give_name())


    def channel_registration(self):
        if not self.atp_flag:
            print("Here comes the channel registration")
            channel_1_image = self.channel1.return_image().copy()
            channel_2_image = self.channel2.return_image().copy()

            """
            # if the cell image represents a cell loaded with the ATP-sensor, then each frame of each cell image needs to be
            # modified so that frame-by-frame-segmentation works
            if self.atp_flag:
                for frame in range(len(channel_1_image)):
                    channel_1_image[frame] = self.atp_image_converter.prepare_ATP_image_for_segmentation_registration(channel_1_image[frame],
                                                                                                     self.estimated_cell_area)
                    channel_2_image[frame] = self.atp_image_converter.prepare_ATP_image_for_segmentation_registration(channel_2_image[frame],
                                                                                                     self.estimated_cell_area)
            """

            trajectory_channel_1 = self.cell_image_registrator.generate_trajectory(channel_1_image)
            trajectory_channel_2 = self.cell_image_registrator.generate_trajectory(channel_2_image)
            x_offset, y_offset = self.cell_image_registrator.calculate_channel_offset(trajectory_channel_1,
                                                                                      trajectory_channel_2)
            x_offset, y_offset = round(x_offset), round(y_offset)

            self.channel2.set_image(self.cell_image_registrator.shift_channel(self.channel2.return_image(), x_offset, y_offset))

    def give_thresholded_image(self, frame, threshold):
        thresholded_frame = frame > threshold
        return thresholded_frame



    def calculate_ratio_image(self):
        """
        Calculates the ratio image for each cell image pair (each frame) and returns the ratio image
        :return:
        """
        ratio_image = self.channel1.return_image().astype(float)
        frame_number = len(self.channel1.return_image())

        for frame in range(frame_number):
            ratio_image[frame] = self.calculate_ratio(frame)
        self.ratio = np.nan_to_num(ratio_image)
        return self.ratio








class ChannelImage:
    def __init__(self, roi, wl, original_image=None):
        self.image = roi
        self.wavelength = wl
        self.original_image = original_image

    def return_image(self):
        return self.image

    def getWavelength (self):
        return self.wavelength

    def set_image(self, img):
        self.image = img


class CellImageRegistrator:
    def __init__(self, segmentation):
        self.segmentation = segmentation

    def generate_trajectory(self, image_series):
        """
        Generates a chronologically ordered list of coordinates of a specified point that is detected by StarDist. Looks
        like this: [[87, 402], [87, 402], [86, 402], [86, 402], [86, 402], [87, 402], ...]

        :param image_series: image series of one channel
        :return: list of coordinates of cell image (actually centroid) in each frame [[x1,y1],[x2,y2],[x3,y3],...]
        """
        number_of_frames = len(image_series)
        labels_for_each_frame = []

        for frame in range(len(image_series)):
            label_in_frame = self.segmentation.stardist_segmentation_in_frame(image_series[frame])
            labels_for_each_frame.append(label_in_frame)

        features = pd.DataFrame()
        for num, img in enumerate(image_series):
            for region in skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img):
                if True: #  or region.area > 3000:  # TO DO needs to be optimised
                    features = features._append([{# 'y': region.centroid[0],
                                                  # 'x': region.centroid[1],
                                                  'y': region.bbox[0],  # y coordinate of upper left corner of bbox (ymin)
                                                  'x': region.bbox[1],  # x coordinate of upper left corner of bbox (xmin)
                                                  'frame': num,
                                                  'bbox': region.bbox,
                                                  'area': region.area,
                                                  }, ])
        # more than one trajectory, when image preparation by atp image converter was not enough to fill the inside of
        # the cell image
        trajectory_coordinates_rounded = []
        if (not features.empty):
            tp.annotate(features[features.frame == (0)], image_series[0])
            # tracking, linking of coordinates
            search_range = 30  # TO DO: needs to be optimised, adaptation to estimated cell diameter/area
            t = tp.link_df(features, search_range, memory=0)
            t = tp.filtering.filter_stubs(t, threshold=number_of_frames)
            # tp.plot_traj(t, superimpose=fluo_image[0])

            cell_image_information = t.loc[t['particle'] == 0]
            trajectory_coordinates = cell_image_information[['x', 'y']]
            trajectory_coordinates_float = trajectory_coordinates.values.tolist()
            for elem in trajectory_coordinates_float:
                current_y = elem[0]
                current_x = elem[1]
                rounded_y = round(current_y)
                rounded_x = round(current_x)
                trajectory_coordinates_rounded.append([rounded_y, rounded_x])
        elif(features.empty):
            pass
        return trajectory_coordinates_rounded

    def calculate_channel_offset(self, coords_channel_1, coords_channel_2):
        x_deviation = 0
        y_deviation = 0
        frame_number = len(coords_channel_1)
        for frame in range(frame_number):
            current_x_coord_channel_1 = coords_channel_1[frame][0]
            current_x_coord_channel_2 = coords_channel_2[frame][0]
            current_y_coords_channel_1 = coords_channel_1[frame][1]
            current_y_coords_channel_2 = coords_channel_2[frame][1]
            x_deviation += (current_x_coord_channel_1 - current_x_coord_channel_2)
            y_deviation += (current_y_coords_channel_1 - current_y_coords_channel_2)
        if frame_number != 0:
            x_deviation = x_deviation/frame_number
            y_deviation = y_deviation/frame_number
        return x_deviation, y_deviation

    def shift_channel(self, channel, x_offset, y_offset):
        shifted_channel = channel.copy()
        for frame in range(len(channel)):
            shifted_channel[frame] = shift(channel[frame], shift=(-x_offset, -y_offset), mode='constant')
        return shifted_channel

