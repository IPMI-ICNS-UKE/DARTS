import pandas as pd
import trackpy as tp
import skimage
from stardist.models import StarDist2D
from csbdeep.utils import normalize
import skimage.io as io
import numpy as np


class CellTracker:
    def __init__(self):
        self.model = StarDist2D.from_pretrained('2D_versatile_fluo')

    def stardist_segmentation_in_frame(self, image_frame):
        img_labels, img_details = self.model.predict_instances(normalize(image_frame))
        return img_labels

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
            label_in_frame = self.stardist_segmentation_in_frame(image_series[frame])
            labels_for_each_frame.append(label_in_frame)

        features = pd.DataFrame()
        for num, img in enumerate(image_series):
            for region in skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img):
                if True:  # or region.area > 3000:  # TO DO needs to be optimised
                    features = features._append([{  'y': region.centroid[0],
                                                    'x': region.centroid[1],
                                                    # 'y': region.bbox[0],  # y coordinate of upper left corner of bbox (ymin)
                                                    # 'x': region.bbox[1],  # x coordinate of upper left corner of bbox (xmin)
                                                    'frame': num,
                                                    'bbox': region.bbox,
                                                    'area': region.area,
                    }, ])

        trajectory_coordinates_rounded = []
        if (not features.empty):
            tp.annotate(features[features.frame == (0)], image_series[0])
            # tracking, linking of coordinates
            search_range = 30  # TO DO: needs to be optimised, adaptation to estimated cell diameter/area
            t = tp.link_df(features, search_range, memory=0)
            t = tp.filtering.filter_stubs(t, threshold=number_of_frames)
            # tp.plot_traj(t, superimpose=fluo_image[0])
            # print (t)
            particle_set = set(t['particle'].tolist())
            print(particle_set)
            return t, particle_set

    def round_coord_list (self, coords_list):
        rounded_coords_list = []
        for coord in coords_list:
            rounded_coord = round(coord)
            rounded_coords_list.append(rounded_coord)
        return rounded_coords_list

    def get_coords_list_for_particle(self, particle, dataframe):
        subset = dataframe.loc[dataframe['particle'] == particle]
        x_coords = self.round_coord_list(subset["x"].values.tolist())
        y_coords = self.round_coord_list(subset["y"].values.tolist())
        coords_list = list(zip(x_coords,y_coords))
        print("coords list")
        print(coords_list)
        return coords_list

    def generate_ROIs_based_on_trajectories(self, offset, coords_list):
        roi_list = []
        for elem in coords_list:
            x_min = elem[0] - offset
            x_max = elem[0] + offset
            y_min = elem[1] - offset
            y_max = elem[1] + offset
            roi_list.append((x_min, x_max, y_min, y_max))
        return roi_list

    def generate_sequence_moving_ROI(self, image, roi_list, offset):
        frame_number = len(image)
        slice_roi = np.s_[:, int(0):int(2*offset), int(0):int(2*offset)]
        cropped_image = image[slice_roi]

        for frame in range(frame_number):
            cropped_original_frame = image[frame][int(roi_list[frame][2]):int(roi_list[frame][3]),
                                                  int(roi_list[frame][0]):int(roi_list[frame][1])]
            cropped_image[frame] = cropped_original_frame
        return cropped_image

    def give_rois(self, channel1, channel2, offset):
        dataframe, particle_set = self.generate_trajectory(channel1)
        roi_cell_list = []
        for particle in particle_set:
            coords_list = self.get_coords_list_for_particle(particle, dataframe)
            roi_list_particle = self.generate_ROIs_based_on_trajectories(offset, coords_list)
            roi1 = self.generate_sequence_moving_ROI(channel1, roi_list_particle, offset)
            roi2 = self.generate_sequence_moving_ROI(channel2, roi_list_particle, offset)
            roi_cell_list.append((roi1, roi2))
        return roi_cell_list

