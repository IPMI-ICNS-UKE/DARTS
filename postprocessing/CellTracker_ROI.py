import pandas as pd
import trackpy as tp
import skimage
from csbdeep.utils import normalize
import numpy as np
from scipy.ndimage import shift
import matplotlib.pyplot as plt
from alive_progress import alive_bar
import time

pd.options.mode.chained_assignment = None  # default='warn'
tp.quiet(suppress=True)

class CellTracker:
    def __init__(self):
        pass
        # self.model = StarDist2D.from_pretrained('2D_versatile_fluo')

    def stardist_segmentation_in_frame(self, image_frame, model):
        """
        Performs Stardist-segmentation in an image frame, not a time-series.
        :param image_frame:
        :return: The labels in the frame detected by the Stardist algorithm
        """
        img_labels, img_details = model.predict_instances(normalize(image_frame),
                                                               predict_kwargs=dict(verbose=False))
        return img_labels, img_details

    def generate_trajectory(self, image_series, model):
        """
        Generates a chronologically ordered list of coordinates of a specified point that is detected by StarDist. Looks
        like this: [[87, 402], [87, 402], [86, 402], [86, 402], [86, 402], [87, 402], ...]

        :param image_series: image series of one channel
        :return: dataframe and set of particles for later
        """
        number_of_frames = len(image_series)
        labels_for_each_frame = []  # segmented image respectively
        details_for_each_frame = []  # segmented image respectively

        print("\nSegmentation of cells: ")
        counter = 1

        with alive_bar(len(image_series), force_tty=True) as bar:
            # for frame in tqdm(range(len(image_series)), position=0, leave=True):
            for frame in range(len(image_series)):
                time.sleep(.005)
                # print("Segmentation of frame: ", counter)
                label_in_frame, details_in_frame = self.stardist_segmentation_in_frame(image_series[frame], model)
                labels_for_each_frame.append(label_in_frame)
                details_for_each_frame.append(details_in_frame)
                counter = counter + 1
                bar()

        print("\nCelltracking: ")
        features = pd.DataFrame()
        with alive_bar(len(image_series), force_tty=True) as bar:
            for num, img in enumerate(image_series):
                time.sleep(.005)
                for r, region in enumerate(skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img)):
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
                                                        'image filled': region.image_filled,
                                                        'edge': details_for_each_frame[num]['coord'][r],
                                                        'edge_x': details_for_each_frame[num]['coord'][r][0, :] - region.bbox[0],
                                                        'edge_y': details_for_each_frame[num]['coord'][r][1, :] - region.bbox[1]
                        }, ])

                bar()

        if not features.empty:
            tp.annotate(features[features.frame == (0)], image_series[0])
            # tracking, linking of coordinates
            search_range = 50  # TO DO: needs to be optimised, adaptation to estimated cell diameter/area
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

        # max_delta_x += max_delta_x * 1.2
        # max_delta_y += max_delta_x * 1.2

        return max_delta_x, max_delta_y

    def generate_shifted_frame_masks(self, empty_rois, dataframe, particle, x_shift_all, y_shift_all):
        """
        Creates a series of boolean masks for a cell image series so that background subtraction can be performed later.
        """
        frame_number = len(empty_rois)
        label_container = empty_rois.copy()
        images_inside_bboxes = self.get_images_inside_bboxes(dataframe, particle)
        boolean_mask = np.empty_like(empty_rois, dtype=bool)

        for frame in range(frame_number):
            current_label = images_inside_bboxes[frame]
            # io.imshow(current_label)
            # plt.show()

            label_container[frame, 0:len(current_label), 0:len(current_label[0])] = current_label
            label_container[frame] = shift(label_container[frame], shift=(x_shift_all[frame], y_shift_all[frame]))
            boolean_mask[frame] = label_container[frame] == 0


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

            # print("frame:", frame)
            # print(int(roi_list[frame][2]), int(roi_list[frame][3]), int(roi_list[frame][0]), int(roi_list[frame][1]))
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
            if(roi[0] < 0 or roi[1] > (xmax*0.5) or roi[2] < 0 or roi[3] > ymax):
                return False
        return True

    def equal_width_and_height(self,max_delta_x,max_delta_y):
        if(max_delta_x>max_delta_y):
            return max_delta_x,max_delta_x
        elif(max_delta_y>max_delta_x):
            return max_delta_y,max_delta_y
        else:
            return max_delta_x,max_delta_y

    def create_roi_template(self,image_series,max_delta_x,max_delta_y):
        cropped_template = np.zeros_like(image_series[:,0:max_delta_y,0:max_delta_x])
        return cropped_template

    def create_cell_image_series(self,empty_rois,intensity_image_series,bbox_list):
        roi_with_intensity_image = empty_rois.copy()
        for i in range(len(intensity_image_series)):
            delta_y = bbox_list[i][2] - bbox_list[i][0]
            delta_x = bbox_list[i][3] - bbox_list[i][1]

            roi_with_intensity_image[i][0:delta_y,0:delta_x] = intensity_image_series[i]
        return roi_with_intensity_image

    def crop_image_series_with_rois(self,image_series,bbox_list):
        cropped_images_list = []
        for i in range(len(image_series)):
            min_row, min_col, max_row, max_col = bbox_list[i]
            cropped_image = image_series[i][min_row:max_row, min_col:max_col]
            cropped_images_list.append(cropped_image)
        return cropped_images_list

    def create_roi_image_series(self, empty_rois, intensity_images_in_bbox, shift_x_list, shift_y_list):
        roi_image_series = empty_rois.copy()
        for i in range(len(empty_rois)):
            delta_x_image = len(intensity_images_in_bbox[i][0])
            delta_y_image = len(intensity_images_in_bbox[i])
            roi_image_series[i][0:delta_y_image, 0:delta_x_image] = intensity_images_in_bbox[i]

            x_shift = shift_x_list[i]
            y_shift = shift_y_list[i]
            roi_image_series[i] = shift(roi_image_series[i], shift=(x_shift, y_shift))
        return roi_image_series

    def calculate_shift_in_each_frame(self, centroid_bbox_offset_list, max_delta_x, max_delta_y):
        x_shift_all = []
        y_shift_all = []
        for i in range(len(centroid_bbox_offset_list)):
            centroid_bbox_offset_x = centroid_bbox_offset_list[i][0]
            centroid_bbox_offset_y = centroid_bbox_offset_list[i][1]
            x_shift = round(0.5 * max_delta_x - centroid_bbox_offset_x)
            y_shift = round(0.5 * max_delta_y - centroid_bbox_offset_y)
            x_shift_all.append(x_shift)
            y_shift_all.append(y_shift)
        return x_shift_all, y_shift_all


    def give_rois(self, channel1, channel2, ymax, xmax, model):
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

        # print("Get rois")

        dataframe, particle_set = self.generate_trajectory(channel2, model)




        roi_cell_list = []
        for particle in particle_set:
            particle_dataframe_subset = self.get_dataframe_subset(dataframe, particle)
            coords_list = self.get_coords_list_for_particle(particle, dataframe)
            bbox_list = self.get_bboxes_list(particle, dataframe)
            centroid_minus_bbox_offset = self.get_offset_between_centroid_and_bbox(particle,dataframe)
            max_delta_x, max_delta_y = self.get_max_bbox_shape(bbox_list)
            max_delta_x, max_delta_y = self.equal_width_and_height(max_delta_x, max_delta_y)
            max_delta_x, max_delta_y = int(max_delta_x*1.4), int(max_delta_y*1.4)

            try:
                # roi_list_particle = self.generate_ROIs_based_on_trajectories(max_delta_x, max_delta_y, coords_list)
                empty_rois = self.create_roi_template(channel1, max_delta_x, max_delta_y)  # empty rois with maximum bbox size
                image_series_channel_1_bboxes = self.crop_image_series_with_rois(channel1, bbox_list)
                image_series_channel_2_bboxes = self.crop_image_series_with_rois(channel2, bbox_list)
                x_shift_all, y_shift_all = self.calculate_shift_in_each_frame(centroid_minus_bbox_offset,max_delta_x,max_delta_y)

                particle_dataframe_subset.loc[:, 'xshift'] = x_shift_all
                particle_dataframe_subset.loc[:, 'yshift'] = y_shift_all

                roi1 = self.create_roi_image_series(empty_rois, image_series_channel_1_bboxes,x_shift_all,y_shift_all)
                roi2 = self.create_roi_image_series(empty_rois, image_series_channel_2_bboxes,x_shift_all,y_shift_all)
                shifted_frame_masks = self.generate_shifted_frame_masks(empty_rois,dataframe,particle,x_shift_all,y_shift_all)
                roi1_background_subtracted = self.background_subtraction(shifted_frame_masks,roi1)
                roi2_background_subtracted = self.background_subtraction(shifted_frame_masks,roi2)
                roi_cell_list.append(
                    (roi1_background_subtracted, roi2_background_subtracted, particle_dataframe_subset, shifted_frame_masks))
            except Exception as E:
                print(E)
                print("Error Roi selection/ tracking")
                continue

        return roi_cell_list


