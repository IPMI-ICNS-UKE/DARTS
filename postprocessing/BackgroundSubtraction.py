


class BackgroundSubtractor():
    def __init__(self):
        pass

    def apply_backgroundcorrection(self, roi_before_backgroundcor_dict):

        roi_cell_list = []
        for particle in roi_before_backgroundcor_dict:
            [roi1, roi2, particle_dataframe_subset, shifted_frame_masks] = roi_before_backgroundcor_dict[particle]

            roi1_background_subtracted = self.delete_background(shifted_frame_masks, roi1)
            roi2_background_subtracted = self.delete_background(shifted_frame_masks, roi2)

            roi_cell_list.append((roi1_background_subtracted, roi2_background_subtracted, particle_dataframe_subset,
                                  shifted_frame_masks))
        return roi_cell_list

    def delete_background(self, frame_masks, cell_image_series):
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

    def subtract_background(self, frame_masks, cell_image_series):
        pass

