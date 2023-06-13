import pandas as pd
import trackpy as tp
import skimage
from stardist.models import StarDist2D
from csbdeep.utils import normalize
import numpy as np
from scipy.ndimage import shift
import matplotlib.pyplot as plt
from tqdm import tqdm



class CellTracker:
    def __init__(self):
        self.model = StarDist2D.from_pretrained('2D_versatile_fluo')

    def stardist_segmentation_in_frame(self, image_frame):
        """
        Performs Stardist-segmentation in an image frame, not a time-series.
        :param image_frame:
        :return: The labels in the frame detected by the Stardist algorithm
        """
        img_labels, img_details = self.model.predict_instances(normalize(image_frame))
        return img_labels

    def generate_trajectory(self, image_series):
        """
        Generates a chronologically ordered list of coordinates of a specified point that is detected by StarDist. Looks
        like this: [[87, 402], [87, 402], [86, 402], [86, 402], [86, 402], [87, 402], ...]

        :param image_series: image series of one channel
        :return: dataframe and set of particles for later
        """
        number_of_frames = len(image_series)
        labels_for_each_frame = []  # segmented image respectively

        counter = 1
        for frame in range(len(image_series)):
            print("Segmentation of frame: ", counter)
            label_in_frame = self.stardist_segmentation_in_frame(image_series[frame])
            labels_for_each_frame.append(label_in_frame)
            counter = counter + 1

        features = pd.DataFrame()
        for num, img in enumerate(image_series):
            for region in skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img):
                if True:
                    features = features._append([{  'y': region.centroid[0],
                                                    'x': region.centroid[1],
                                                    'y_centroid_minus_bbox': region.centroid[0]-region.bbox[0],
                                                    'x_centroid_minus_bbox': region.centroid[1]-region.bbox[1],
                                                    'frame': num,
                                                    'bbox': region.bbox,
                                                    'area': region.area,
                                                    # Q: diameter could be relevant to check cell size
                                                    'equivalent_diameter_area': region.equivalent_diameter_area,
                                                    'mean_intensity': region.intensity_mean,
                                                    'image_intensity': region.image_intensity,
                                                    'image filled': region.image_filled
                    }, ])

        if not features.empty:
            tp.annotate(features[features.frame == (0)], image_series[0])
            # tracking, linking of coordinates
            search_range = 10  # TO DO: needs to be optimised, adaptation to estimated cell diameter/area
            t = tp.link_df(features, search_range, memory=0)
            t = tp.filtering.filter_stubs(t, threshold=number_of_frames-1)
            # print (t)
            # tp.plot_traj(t, superimpose=fluo_image[0])
            # print (t)
            particle_set = set(t['particle'].tolist())
            # print(particle_set)
            return t, particle_set

    def get_max_bbox_shape(self, bboxlist):
        """
        Searches the maximum width and height in a list of bounding boxes
        and then expand the maximum width and height by 10 percent to prevent the cell touching the border of
        the cropped image
        :param bboxlist:
        :return: max_delta_x: max width; max_delta_y: max height
        """
        max_delta_x = 0
        max_delta_y = 0
        for bbox in bboxlist:
            y_min = bbox[0]
            x_min = bbox[1]
            y_max = bbox[2]
            x_max = bbox[3]
            delta_x = x_max - x_min
            delta_y = y_max - y_min
            if (delta_x > max_delta_x):
                max_delta_x = delta_x
            if (delta_y > max_delta_y):
                max_delta_y = delta_y

        # if resize_box_factor is not None:
        #     max_delta_x += max_delta_x * resize_box_factor
        #     max_delta_y += max_delta_x * resize_box_factor
        # print(max_delta_x, max_delta_y)

        return max_delta_x, max_delta_y

    def generate_frame_masks(self, dataframe, particle, image_series, half_max_delta_x, half_max_delta_y):
        """
        Creates a series of boolean masks for a cell image series so that background subtraction can be performed later.
        Uses the offset between the current bounding box and the biggest bounding box of an image series to shift the
        created mask into the right position.

        :param dataframe:
        :param particle:
        :param image_series:
        :param half_max_delta_x:
        :param half_max_delta_y:
        :return: series of boolean masks
        """
        bbox_list = self.get_bboxes_list(particle, dataframe)

        coords_bbox_offset = self.get_offset_between_centroid_and_bbox(particle, dataframe)
        frame_number = len(bbox_list)
        new_array = np.zeros_like(image_series)
        images_inside_bboxes = self.get_images_inside_bboxes(dataframe, particle)
        boolean_mask = np.empty_like(new_array, dtype=bool)

        for frame in range(frame_number):
            centroid_y_minus_bbox_offset = coords_bbox_offset[frame][1]
            centroid_x_minus_bbox_offset = coords_bbox_offset[frame][0]
            # bbox_ymin, bbox_xmin, bbox_ymax, bbox_xmax = bbox_list[frame]
            current_label = images_inside_bboxes[frame]
            # io.imshow(current_label)
            # plt.show()
            x_shift = round(half_max_delta_x - centroid_x_minus_bbox_offset)
            y_shift = round(half_max_delta_y - centroid_y_minus_bbox_offset)
            new_array[frame, 0:len(current_label), 0:len(current_label[0])] = current_label
            new_array[frame] = shift(new_array[frame], shift=(x_shift, y_shift))
            boolean_mask[frame] = new_array[frame] == 0

        return boolean_mask

    def background_subtraction(self, frame_masks, cell_image_series):
        """
        Subtract background in a given cell image series by using a series of boolean masks
        :param frame_masks:
        :param cell_image_series:
        :return: the background subtracted image series
        """
        frame_number = len(cell_image_series)
        copy = cell_image_series.copy()
        for frame in range(frame_number):
            copy[frame] = self.apply_masks_on_image_series(cell_image_series[frame], frame_masks[frame])
        return copy

    def get_images_inside_bboxes (self, dataframe, particle):
        """
        Returns the labeled images for a given particle/cell image series from earlier segmentation, which are saved
        in a dataframe.
        :param dataframe:
        :param particle:
        :return: The list of labeled images, in this case: cell image series saved in list
        """
        subset = dataframe.loc[dataframe['particle'] == particle]
        label_images = subset["image_intensity"].values.tolist()
        return label_images

    def get_dataframe_subset(self, dataframe, particle):
        subset = dataframe.loc[dataframe['particle'] == particle]
        return subset

    def round_coord_list(self, coords_list):
        """
        rounds the coordinates in a given coords list, typically from float to integer.
        :param coords_list:
        :return: list with rounded coordinates
        """
        rounded_coords_list = []
        for coord in coords_list:
            rounded_coord = round(coord)
            rounded_coords_list.append(rounded_coord)
        return rounded_coords_list

    def get_coords_list_for_particle(self, particle, dataframe):
        """
        Returns the list of x- and y-coordinates for a particle/cell in a dataframe
        :param particle:
        :param dataframe:
        :return:
        """
        subset = dataframe.loc[dataframe['particle'] == particle]
        x_coords = self.round_coord_list(subset["x"].values.tolist())
        y_coords = self.round_coord_list(subset["y"].values.tolist())
        coords_list = list(zip(x_coords, y_coords))
        return coords_list

    def get_bboxes_list(self,particle,dataframe):
        """
        Returns a list of bounding boxes of a cell image series.
        :param particle:
        :param dataframe:
        :return:
        """
        subset = dataframe.loc[dataframe['particle'] == particle]
        bbox_list = subset["bbox"].values.tolist()
        return bbox_list

    def get_offset_between_centroid_and_bbox(self, particle, dataframe):
        """
        Returns the offset between the centroid position which is used for the cell tracking (extracted from regionprops)
        and the bounding box position (upper left corner) in each frame. The cell images are going to be shifted by a
        vector consisting of a delta_x and a delta_y.

        :param particle:
        :param dataframe:
        :return:
        """
        subset = dataframe.loc[dataframe['particle'] == particle]
        y_centroid_minus_bbox_list = self.round_coord_list(subset["y_centroid_minus_bbox"].values.tolist())
        x_centroid_minus_bbox_list = self.round_coord_list(subset["x_centroid_minus_bbox"].values.tolist())
        offset_list = list(zip(x_centroid_minus_bbox_list, y_centroid_minus_bbox_list))
        return offset_list

    def generate_ROIs_based_on_trajectories(self, max_delta_x, max_delta_y, coords_list):
        """
        Generates a list of rectangular ROIs based on a list of coordinates and the maximum size of all the bounding
        boxes so that all the cell images in one series fit into the later ROI.

        :param max_delta_x:
        :param max_delta_y:
        :param coords_list:
        :return:
        """
        roi_list = []
        for elem in coords_list:
            x_min = round(elem[0] - 0.5*max_delta_x)
            x_max = round(elem[0] + 0.5*max_delta_x)
            y_min = round(elem[1] - 0.5*max_delta_y)
            y_max = round(elem[1] + 0.5*max_delta_y)

            if(x_max-x_min != max_delta_x):
                difference = max_delta_x-(x_max-x_min)
                x_max = x_max + difference

            if (y_max - y_min != max_delta_y):
                difference = max_delta_y - (y_max - y_min)
                y_max = y_max + difference

            # print(x_min, x_max, y_min, y_max)
            # x_min -= 0.15 * (x_max - x_min)
            # x_max += 0.15 * (x_max - x_min)
            # y_min -= 0.15 * (y_max - y_min)
            # y_max += 0.15 * (y_max - y_min)
            #
            # max_delta_x = x_max - x_min
            # max_delta_y = y_max - y_min

            roi_list.append((x_min, x_max, y_min, y_max))

        return roi_list

    def correct_coordinates(self,ymin,ymax,xmin,xmax):
        ymin_corrected = ymin
        ymax_corrected = ymax
        xmin_corrected = xmin
        xmax_corrected = xmax

        if(ymin<0):
            ymin_corrected = 0
        if(ymax < 0):
            ymax_corrected = 0
        if(xmin < 0):
            xmin_corrected = 0
        if(xmax < 0):
            xmax_corrected = 0
        return xmin_corrected, xmax_corrected, ymin_corrected, ymax_corrected

    def generate_sequence_moving_ROI(self, image, roi_list, max_delta_x, max_delta_y):
        """
        Applies a list of rectangular ROI definitions onto an image and cuts out the correct ROI in each frame. Returns
        the cropped image series.

        :param image:
        :param roi_list:
        :param max_delta_x:
        :param max_delta_y:
        :return:
        """
        frame_number = len(image)
        slice_roi = np.s_[:, int(0):int(max_delta_y), int(0):int(max_delta_x)]
        cropped_image = image[slice_roi].copy()

        for frame in range(frame_number):
            # print("ymin " + str(int(roi_list[frame][2])))
            # print("ymax " + str(int(roi_list[frame][3])))
            # print("xmin " + str(int(roi_list[frame][1])))
            # print("xmax " + str(int(roi_list[frame][0])))

            print(int(roi_list[frame][2]), int(roi_list[frame][3]), int(roi_list[frame][0]), int(roi_list[frame][1]))
            # ggf. statt int() die Methode round() verwenden?
            # print("coordinates")
            # print(str(int(roi_list[frame][0])))
            # print(str(int(roi_list[frame][1])))
            # print(str(int(roi_list[frame][2])))
            # print(str(int(roi_list[frame][3])))

            cropped_image[frame] = image[frame][int(roi_list[frame][2]):int(roi_list[frame][3]),
                                                int(roi_list[frame][0]):int(roi_list[frame][1])]
        return cropped_image

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

    def cell_completely_in_image(self, roi_list_particle, ymax, xmax):
        """
        Checks, if the cell is completely in the image in each frame
        :return:
        """
        for roi in roi_list_particle:
            if(roi[0] < 0 or roi[1] > xmax or roi[2] < 0 or roi[3] > ymax):
                return False
        return True


    def give_rois(self, channel1, channel2, ymax, xmax):
        """
        Finds cells in two given channel image series and returns a list of the corresponding cropped cell image series.
        Background subtraction included.
        In addition, the tuple contains the cell image data from the pandas dataframe
        [(cell_1_roi1_background_subtracted, cell_1_roi1_background_subtracted, cell_1_cellimage_data),
         (cell_2_roi1_background_subtracted, cell_2_roi1_background_subtracted, cell_2_cellimage_data)
         ...]

        :param channel1:
        :param channel2:
        :return:
        """
        print("Get rois")
        dataframe, particle_set = self.generate_trajectory(channel1)
        # hier ggf. auch generate trajectory für channel2

        roi_cell_list = []
        for particle in tqdm(particle_set):
            particle_dataframe_subset = self.get_dataframe_subset(dataframe, particle)
            coords_list = self.get_coords_list_for_particle(particle, dataframe)
            bbox_list = self.get_bboxes_list(particle, dataframe)
            max_delta_x, max_delta_y = self.get_max_bbox_shape(bbox_list)

            roi_list_particle = self.generate_ROIs_based_on_trajectories(max_delta_x, max_delta_y, coords_list)


            # print("condition")
            # print(self.cell_completely_in_image(roi_list_particle, ymax, xmax))
            if (self.cell_completely_in_image(roi_list_particle, ymax, xmax)):
                roi1 = self.generate_sequence_moving_ROI(channel1, roi_list_particle, max_delta_x, max_delta_y)
                frame_masks = self.generate_frame_masks(dataframe, particle, roi1, 0.5*max_delta_x, 0.5*max_delta_y)
                roi1_background_subtracted = self.background_subtraction(frame_masks, roi1)

                roi2 = self.generate_sequence_moving_ROI(channel2, roi_list_particle, max_delta_x, max_delta_y)
                roi2_background_subtracted = self.background_subtraction(frame_masks, roi2)
                roi_cell_list.append((roi1_background_subtracted, roi2_background_subtracted, particle_dataframe_subset, frame_masks))
        return roi_cell_list

