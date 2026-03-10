import os
import time
import pandas as pd
import trackpy as tp
from trackpy.linking.utils import SubnetOversizeException
import skimage
from skimage.color import label2rgb
import imageio.v2 as iio
from csbdeep.utils import normalize
import numpy as np
from scipy.ndimage import shift
from alive_progress import alive_bar


pd.options.mode.chained_assignment = None  # default='warn'
tp.quiet(suppress=True)

class CellTracker:
    def __init__(self, scale_pixels_per_micron):
        pass
        # self.model = StarDist2D.from_pretrained('2D_versatile_fluo')
        self.scale_pixels_per_micron = scale_pixels_per_micron
        self._overlay_written = False

    def stardist_segmentation_in_frame(self, image_frame, model):
        """
        Performs Stardist-segmentation in an image frame, not a time-series.
        :param image_frame:
        :return: The labels in the frame detected by the Stardist algorithm
        """
        # StarDist scale is derived from the measurement scale (pixels per micron). 9.765 = pixels_per_micron for 63x Enhancement
        stardist_scale = 9.765 / self.scale_pixels_per_micron if self.scale_pixels_per_micron else 0.25
        img_labels, img_details = model.predict_instances(
            normalize(image_frame),
            predict_kwargs=dict(verbose=False),
            scale=stardist_scale,
        )
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

                # Save an overlay for the first frame to visualize StarDist detections
                if frame == 0 and not self._overlay_written:
                    base_dir = getattr(self, "save_path", ".")
                    os.makedirs(base_dir, exist_ok=True)
                    overlay = label2rgb(label_in_frame, image=image_series[frame], bg_label=0, alpha=0.3)
                    overlay_path = os.path.join(base_dir, "stardist_overlay_frame0.png")
                    iio.imwrite(overlay_path, (overlay * 255).astype(np.uint8))
                    print(f"Saved StarDist overlay for frame 0 to: {overlay_path}")
                    self._overlay_written = True
                counter = counter + 1
                bar()

        print("\nCelltracking: ")
        features = pd.DataFrame()
        bbox_sizes = []
        with alive_bar(len(image_series), force_tty=True) as bar:
            for num, img in enumerate(image_series):
                time.sleep(.005)
                for r, region in enumerate(skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img)):
                    width = region.bbox[3] - region.bbox[1]
                    height = region.bbox[2] - region.bbox[0]
                    bbox_sizes.append(max(width, height))
                    features = features._append([{  'y': region.centroid[0],
                                                    'x': region.centroid[1],
                                                    'y_centroid_minus_bbox': region.centroid[0]-region.bbox[0],
                                                    'x_centroid_minus_bbox': region.centroid[1]-region.bbox[1],
                                                    'frame': num,
                                                    'bbox': region.bbox,
                                                    'area in (µm)^2': region.area / (self.scale_pixels_per_micron ** 2),
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
            # Debug: how many detections per frame before linking
            per_frame_counts = features.groupby('frame').size()
            print(
                "Detections per frame before tracking: "
                f"min={per_frame_counts.min()}, "
                f"median={per_frame_counts.median()}, "
                f"max={per_frame_counts.max()}, "
                f"total={len(features)}"
            )
            # tp.annotate(features[features.frame == (0)], image_series[0])  # generates a plot
            # tracking, linking of coordinates
            adaptive_search_range = False
            search_ranges = (
                self._build_search_ranges(bbox_sizes) if adaptive_search_range else [60]
            )
            t = None
            for search_range in search_ranges:
                try:
                    t = tp.link_df(features, search_range, memory=3)
                    # Debug: inspect raw track lengths before filtering
                    track_lengths = t.groupby('particle')['frame'].nunique()
                    long_tracks = track_lengths[track_lengths > 50]
                    print(f"Track lengths (frames) before stub filtering, search_range={search_range}: "
                          f"{len(long_tracks)} tracks >50 frames, "
                          f"max={long_tracks.max() if not long_tracks.empty else 0}")
                    if not long_tracks.empty:
                        print(long_tracks.sort_values(ascending=False).head())
                    break
                except SubnetOversizeException as exc:
                    print(f"search_range {search_range} too large ({exc}); trying a smaller value.")
                    continue

            if t is None:
                raise RuntimeError("Unable to link trajectories: all search_range candidates were too large. "
                                   "Try reducing expected cell movement or lower search_range manually.")
            #t = tp.filtering.filter_stubs(t, threshold=number_of_frames-250) #Threshold cell
            t = tp.filtering.filter_stubs(t, threshold = max(10, int(0.4 * number_of_frames)))

            # print (t)
            # tp.plot_traj(t, superimpose=image_series[0])
            # print (t)
            particle_set = set(t['particle'].tolist())
            # print(particle_set)

            # Debug overlay: show centroids of tracks that survived filtering on frame 0
            base_dir = getattr(self, "save_path", ".")
            os.makedirs(base_dir, exist_ok=True)
            keep_df = t[t['particle'].isin(particle_set)]
            if not keep_df.empty:
                first_frame = int(keep_df['frame'].min())
                frame_tracks = keep_df[keep_df['frame'] == first_frame]
                if not frame_tracks.empty and first_frame < len(image_series):
                    frame_img = image_series[first_frame].astype(float)
                    max_val = frame_img.max()
                    if max_val > 0:
                        frame_img = frame_img / max_val
                    overlay = np.dstack([frame_img, frame_img, frame_img])

                    for _, row in frame_tracks.iterrows():
                        y = int(round(row['y']))
                        x = int(round(row['x']))
                        y0, y1 = max(0, y - 2), min(overlay.shape[0], y + 3)
                        x0, x1 = max(0, x - 2), min(overlay.shape[1], x + 3)
                        overlay[y0:y1, x0:x1, :] = [1.0, 0.0, 0.0]  # red mark

                    overlay_path = os.path.join(base_dir, f"tracks_overlay_frame{first_frame}.png")
                    iio.imwrite(overlay_path, (overlay * 255).astype(np.uint8))
                    print(f"Saved tracked-cells overlay for frame {first_frame} to: {overlay_path}")

            return t, particle_set

    def _build_search_ranges(self, bbox_sizes):
        """
        Build a list of search_range candidates based on observed cell size to avoid oversize subnets.
        """
        if bbox_sizes:
            median_size = float(np.median(bbox_sizes))
            base = int(np.clip(median_size * 0.75, 5, 60))
        else:
            base = 60

        candidates = [base, int(base * 0.75), 60, 40, 30, 20, 10, 5]
        search_ranges = []
        for candidate in candidates:
            candidate_int = max(1, int(round(candidate)))
            if candidate_int not in search_ranges:
                search_ranges.append(candidate_int)

        return search_ranges

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
            # corresponding_frame = bbox[0]
            y_min = bbox[1][0]
            x_min = bbox[1][1]
            y_max = bbox[1][2]
            x_max = bbox[1][3]
            delta_x = x_max - x_min
            delta_y = y_max - y_min
            if (delta_x > max_delta_x):
                max_delta_x = delta_x
            if (delta_y > max_delta_y):
                max_delta_y = delta_y

        return max_delta_x, max_delta_y

    def build_stable_track_bbox(self, bbox_list, image_series, margin=15, size_percentile=95):
        """
        Build one fixed ROI for the whole track from:
        - mean bbox center across time
        - robust bbox size (percentile) across time
        """
        if not bbox_list:
            raise ValueError("Cannot build stable track bbox without bbox data.")

        centers_x = []
        centers_y = []
        widths = []
        heights = []
        for _, bbox in bbox_list:
            min_row, min_col, max_row, max_col = bbox
            widths.append(max_col - min_col)
            heights.append(max_row - min_row)
            centers_x.append(0.5 * (min_col + max_col))
            centers_y.append(0.5 * (min_row + max_row))

        center_x = float(np.mean(centers_x))
        center_y = float(np.mean(centers_y))
        width = int(np.ceil(np.percentile(widths, size_percentile))) + 2 * margin
        height = int(np.ceil(np.percentile(heights, size_percentile))) + 2 * margin
        width, height = self.equal_width_and_height(width, height)

        _, y_max, x_max = image_series.shape
        min_col = int(round(center_x - 0.5 * width))
        min_row = int(round(center_y - 0.5 * height))
        max_col = min_col + width
        max_row = min_row + height

        if min_col < 0:
            max_col -= min_col
            min_col = 0
        if min_row < 0:
            max_row -= min_row
            min_row = 0
        if max_col > x_max:
            shift_left = max_col - x_max
            min_col -= shift_left
            max_col = x_max
        if max_row > y_max:
            shift_up = max_row - y_max
            min_row -= shift_up
            max_row = y_max

        min_col = max(0, min_col)
        min_row = max(0, min_row)
        return min_row, min_col, max_row, max_col

    def generate_shifted_frame_masks(self, empty_rois, dataframe, particle, x_shift_all, y_shift_all):
        """
        Creates a series of boolean masks for a cell image series so that background subtraction can be performed later.
        """
        # frame_number = len(empty_rois)
        label_container = empty_rois.copy()
        images_inside_bboxes = self.get_images_inside_bboxes(dataframe, particle)
        boolean_mask = np.empty_like(empty_rois, dtype=bool)

        for frame in range(len(x_shift_all)):
            current_label = images_inside_bboxes[frame]

            x_shift = x_shift_all[frame]
            y_shift = y_shift_all[frame]

            label_container[frame, 0:len(current_label), 0:len(current_label[0])] = current_label
            label_container[frame] = shift(label_container[frame], shift=(x_shift, y_shift))
            boolean_mask[frame] = label_container[frame] == 0


        return boolean_mask

    def generate_frame_masks_for_fixed_bbox(self, empty_rois, particle_dataframe_subset, fixed_bbox, x_shift_all=None, y_shift_all=None):
        """
        Map original per-frame masks into the fixed-bbox ROI coordinate system.
        """
        boolean_mask = np.empty_like(empty_rois, dtype=bool)
        fixed_min_row, fixed_min_col, _, _ = fixed_bbox
        filled_images = particle_dataframe_subset["image filled"].values.tolist()
        bbox_values = particle_dataframe_subset["bbox"].values.tolist()

        if x_shift_all is None:
            x_shift_all = [0] * len(filled_images)
        if y_shift_all is None:
            y_shift_all = [0] * len(filled_images)

        for frame in range(len(filled_images)):
            mask_canvas = np.zeros_like(empty_rois[frame], dtype=np.uint8)
            current_mask = filled_images[frame].astype(np.uint8)
            min_row, min_col, _, _ = bbox_values[frame]

            row_start = int(min_row - fixed_min_row)
            col_start = int(min_col - fixed_min_col)
            row_end = row_start + current_mask.shape[0]
            col_end = col_start + current_mask.shape[1]

            target_height, target_width = mask_canvas.shape
            target_row_start = max(0, row_start)
            target_col_start = max(0, col_start)
            target_row_end = min(target_height, row_end)
            target_col_end = min(target_width, col_end)

            source_row_start = max(0, -row_start)
            source_col_start = max(0, -col_start)
            source_row_end = source_row_start + (target_row_end - target_row_start)
            source_col_end = source_col_start + (target_col_end - target_col_start)

            if target_row_end <= target_row_start or target_col_end <= target_col_start:
                boolean_mask[frame] = True
                continue

            mask_canvas[target_row_start:target_row_end, target_col_start:target_col_end] = current_mask[
                source_row_start:source_row_end,
                source_col_start:source_col_end,
            ]

            if x_shift_all[frame] != 0 or y_shift_all[frame] != 0:
                mask_canvas = shift(mask_canvas, shift=(x_shift_all[frame], y_shift_all[frame]), order=0)

            boolean_mask[frame] = mask_canvas == 0

        return boolean_mask



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

    def get_bboxes_list(self,particle_dataframe_subset):
        """
        Returns a list of bounding boxes of a cell image series.
        :param particle:
        :param dataframe:
        :return:
        """

        return particle_dataframe_subset["bbox"].values.tolist()

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

    def create_roi_template(self,image_series,max_delta_x,max_delta_y, number_bboxes):
        cropped_template = np.zeros_like(image_series[0:number_bboxes,0:max_delta_y,0:max_delta_x])
        return cropped_template

    def create_cell_image_series(self,empty_rois,intensity_image_series,bbox_list):
        roi_with_intensity_image = empty_rois.copy()
        for i in range(len(intensity_image_series)):
            delta_y = bbox_list[i][2] - bbox_list[i][0]
            delta_x = bbox_list[i][3] - bbox_list[i][1]

            roi_with_intensity_image[i][0:delta_y,0:delta_x] = intensity_image_series[i]
        return roi_with_intensity_image

    def crop_image_series_with_rois(self,image_series,bbox_list, delta):
        cropped_images_list = []
        shift_correction_list = []
        for bbox in bbox_list:
            i = bbox[0]  # bbox is a tuple now. (corresponding frame, bbox)
            min_row, min_col, max_row, max_col = bbox[1]
            min_row, min_col, max_row, max_col = min_row-delta, min_col-delta, max_row+delta-1, max_col+delta-1  # -1 als workaround gegen broadcast error
            t_max, y_max, x_max = image_series.shape

            if min_row < 0:
                min_row = 0
            if min_col < 0:
                min_col = 0
            if max_row > y_max:
                max_row = y_max-1
            if max_col > x_max:
                max_col = x_max - 1

            min_row_difference = bbox[1][0] - min_row
            min_col_difference = bbox[1][1] - min_col
            shift_correction_list.append((min_col_difference, min_row_difference))  # col = x, row = y

            cropped_image = image_series[i][min_row:max_row, min_col:max_col]
            cropped_images_list.append(cropped_image)
        return cropped_images_list, shift_correction_list

    def crop_image_series_with_fixed_bbox(self, image_series, frame_indices, bbox):
        min_row, min_col, max_row, max_col = bbox
        cropped_images_list = []
        shift_correction_list = []
        for frame_idx in frame_indices:
            cropped_images_list.append(image_series[frame_idx][min_row:max_row, min_col:max_col])
            shift_correction_list.append((0, 0))
        return cropped_images_list, shift_correction_list

    def create_roi_image_series(self, empty_rois, intensity_images_in_bbox, shift_x_list, shift_y_list):
        roi_image_series = empty_rois.copy()

        for i in range(len(intensity_images_in_bbox)):
            delta_x_image = len(intensity_images_in_bbox[i][0])
            delta_y_image = len(intensity_images_in_bbox[i])

            target_height, target_width = roi_image_series[i].shape
            copy_height = min(delta_y_image, target_height)
            copy_width = min(delta_x_image, target_width)
            if copy_height <= 0 or copy_width <= 0:
                continue

            roi_image_series[i][0:copy_height, 0:copy_width] = intensity_images_in_bbox[i][0:copy_height, 0:copy_width]

            """
            if intensity_images_in_bbox[i].shape == roi_image_series[i].shape:
                roi_image_series[i][0:delta_y_image, 0:delta_x_image] = intensity_images_in_bbox[i]
            elif :
                x_difference =
            """

            x_shift = shift_x_list[i]
            y_shift = shift_y_list[i]
            roi_image_series[i] = shift(roi_image_series[i], shift=(x_shift, y_shift))
        return roi_image_series

    def calculate_shift_in_each_frame(self, centroid_bbox_offset_list, max_delta_x, max_delta_y, shift_correction_list):
        x_shift_all = []
        y_shift_all = []
        for i in range(len(centroid_bbox_offset_list)):
            centroid_bbox_offset_x = centroid_bbox_offset_list[i][0]
            centroid_bbox_offset_y = centroid_bbox_offset_list[i][1]
            x_shift = round(0.5 * max_delta_x - centroid_bbox_offset_x) - shift_correction_list[i][0]
            y_shift = round(0.5 * max_delta_y - centroid_bbox_offset_y) - shift_correction_list[i][1]
            x_shift_all.append(x_shift)
            y_shift_all.append(y_shift)
        return x_shift_all, y_shift_all


    def give_rois(self, channel1, channel2, model):
        """
        Finds cells in two given channel image series and returns a list of the corresponding cropped cell image series.
        In addition, the tuple contains the cell image data from the pandas dataframe
        [(cell_1_roi1, cell_1_roi1, cell_1_cellimage_data),
         (cell_2_roi1, cell_2_roi1, cell_2_cellimage_data)
         ...]

        :param channel1:
        :param channel2:
        :return:
        """
        dataframe, particle_set = self.generate_trajectory(channel2, model)

        roi_before_backgroundcor_dict = {}
        for particle in particle_set:
            particle_dataframe_subset = self.get_dataframe_subset(dataframe, particle)

            # clean up of dataframe in case that there are missing rows
            particle_dataframe_subset.reset_index(drop=True, inplace=True)
            frame_list_before_correction = particle_dataframe_subset['frame'].copy().values.tolist()
            bbox_list = list(zip(frame_list_before_correction, self.get_bboxes_list(particle_dataframe_subset)))

            corrected_frame_list = list(range(len(particle_dataframe_subset.index)))
            particle_dataframe_subset['frame'] = corrected_frame_list


            centroid_minus_bbox_offset = self.get_offset_between_centroid_and_bbox(particle, dataframe)
            max_delta_x, max_delta_y = self.get_max_bbox_shape(bbox_list)
            max_delta_x, max_delta_y = self.equal_width_and_height(max_delta_x, max_delta_y)
            max_delta_x, max_delta_y = int(max_delta_x*1.4) + 15, int(max_delta_y*1.4) + 15

            try:
                empty_rois = self.create_roi_template(channel1, max_delta_x, max_delta_y, len(bbox_list))  # empty rois with maximum bbox size
                image_series_channel_1_bboxes, shift_correction_list = self.crop_image_series_with_rois(channel1, bbox_list, 10)
                image_series_channel_2_bboxes, shift_correction_list = self.crop_image_series_with_rois(channel2, bbox_list, 10)
                x_shift_image, y_shift_image = self.calculate_shift_in_each_frame(centroid_minus_bbox_offset,max_delta_x,max_delta_y, shift_correction_list)
                roi1_uncentered = self.create_roi_image_series(
                    empty_rois,
                    image_series_channel_1_bboxes,
                    [0] * len(image_series_channel_1_bboxes),
                    [0] * len(image_series_channel_1_bboxes),
                )
                roi2_uncentered = self.create_roi_image_series(
                    empty_rois,
                    image_series_channel_2_bboxes,
                    [0] * len(image_series_channel_2_bboxes),
                    [0] * len(image_series_channel_2_bboxes),
                )
                roi1 = self.create_roi_image_series(empty_rois, image_series_channel_1_bboxes, x_shift_image, y_shift_image)
                roi2 = self.create_roi_image_series(empty_rois, image_series_channel_2_bboxes, x_shift_image, y_shift_image)

                x_shift_bbox, y_shift_bbox = self.correct_shift_list_for_bbox(x_shift_image,y_shift_image,shift_correction_list)

                particle_dataframe_subset.loc[:, 'xshift'] = x_shift_bbox
                particle_dataframe_subset.loc[:, 'yshift'] = y_shift_bbox

                shifted_frame_masks = self.generate_shifted_frame_masks(empty_rois, dataframe, particle, x_shift_bbox,
                                                                        y_shift_bbox)
                uncentered_frame_masks = self.generate_shifted_frame_masks(
                    empty_rois,
                    dataframe,
                    particle,
                    [shift_x for shift_x, _ in shift_correction_list],
                    [shift_y for _, shift_y in shift_correction_list],
                )

                stable_bbox = self.build_stable_track_bbox(bbox_list, channel1)
                stable_height = stable_bbox[2] - stable_bbox[0]
                stable_width = stable_bbox[3] - stable_bbox[1]
                empty_stable_rois = self.create_roi_template(channel1, stable_width, stable_height, len(bbox_list))
                stable_roi1_bboxes, _ = self.crop_image_series_with_fixed_bbox(channel1, frame_list_before_correction, stable_bbox)
                stable_roi2_bboxes, _ = self.crop_image_series_with_fixed_bbox(channel2, frame_list_before_correction, stable_bbox)
                stable_roi1 = self.create_roi_image_series(
                    empty_stable_rois,
                    stable_roi1_bboxes,
                    [0] * len(stable_roi1_bboxes),
                    [0] * len(stable_roi1_bboxes),
                )
                stable_roi2 = self.create_roi_image_series(
                    empty_stable_rois,
                    stable_roi2_bboxes,
                    [0] * len(stable_roi2_bboxes),
                    [0] * len(stable_roi2_bboxes),
                )
                stable_frame_masks = self.generate_frame_masks_for_fixed_bbox(
                    empty_stable_rois,
                    particle_dataframe_subset,
                    stable_bbox,
                )
                stable_centroid_minus_bbox_offset = list(
                    zip(
                        self.round_coord_list((particle_dataframe_subset["x"] - stable_bbox[1]).values.tolist()),
                        self.round_coord_list((particle_dataframe_subset["y"] - stable_bbox[0]).values.tolist()),
                    )
                )
                stable_shift_correction_list = [(0, 0)] * len(stable_roi1_bboxes)
                stable_x_shift_image, stable_y_shift_image = self.calculate_shift_in_each_frame(
                    stable_centroid_minus_bbox_offset,
                    stable_width,
                    stable_height,
                    stable_shift_correction_list,
                )
                stable_roi1_centered = self.create_roi_image_series(
                    empty_stable_rois,
                    stable_roi1_bboxes,
                    stable_x_shift_image,
                    stable_y_shift_image,
                )
                stable_roi2_centered = self.create_roi_image_series(
                    empty_stable_rois,
                    stable_roi2_bboxes,
                    stable_x_shift_image,
                    stable_y_shift_image,
                )
                stable_centered_frame_masks = self.generate_frame_masks_for_fixed_bbox(
                    empty_stable_rois,
                    particle_dataframe_subset,
                    stable_bbox,
                    stable_x_shift_image,
                    stable_y_shift_image,
                )

                roi_before_backgroundcor_dict[particle] = [
                    roi1,
                    roi2,
                    particle_dataframe_subset,
                    shifted_frame_masks,
                    roi1_uncentered,
                    roi2_uncentered,
                    uncentered_frame_masks,
                    stable_roi1,
                    stable_roi2,
                    stable_frame_masks,
                    stable_roi1_centered,
                    stable_roi2_centered,
                    stable_centered_frame_masks,
                ]
            except Exception as E:
                print(E)
                print("Error Roi selection/ tracking")
                continue


        return roi_before_backgroundcor_dict


    def correct_shift_list_for_bbox(self,x_shift_list,y_shift_list,shift_correction_list):
        x_shift_bbox_list = []
        y_shift_bbox_list = []
        for i in range(len(x_shift_list)):
            x_shift = x_shift_list[i]
            y_shift = y_shift_list[i]
            x_shift_bbox = x_shift + shift_correction_list[i][0]
            y_shift_bbox = y_shift + shift_correction_list[i][1]
            x_shift_bbox_list.append(x_shift_bbox)
            y_shift_bbox_list.append(y_shift_bbox)

        return x_shift_bbox_list, y_shift_bbox_list
