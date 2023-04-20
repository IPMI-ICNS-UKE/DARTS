from __future__ import print_function



class MembraneDetector:


    def cut_out_cells_from_ROIs (self, cropped_cell_images_tuple, cell_masks):
        """
        Applies the previously generated mask containing the cell area on the cropped cell image stack. Sometimes other cells
        overlap into the ROI of a cell.

        :param cropped_cell_images_tuple: tuple containing two corresponding cell image stacks
        :param cell_masks: boolean masks to be applied on the ROIs
        :return: return the "cleaned" ROIs of the cells
        """
        images_tuple_copy = cropped_cell_images_tuple.copy()
        cleaned_rois = []
        for tuple_i in range(len(cropped_cell_images_tuple)):  # for each tuple
            current_mask = cell_masks[tuple_i]

            for frame in range(len(cropped_cell_images_tuple[0][0])):  # for each frame
                cropped_cell_images_tuple[tuple_i][0][frame] = self.apply_mask_on_image(cropped_cell_images_tuple[tuple_i][0][frame],
                                                                                 current_mask,
                                                                                 0)
                cropped_cell_images_tuple[tuple_i][1][frame] = self.apply_mask_on_image(cropped_cell_images_tuple[tuple_i][1][frame],
                                                                                 current_mask,
                                                                                 0)
            cleaned_rois.append((cropped_cell_images_tuple[tuple_i][0],
                                 cropped_cell_images_tuple[tuple_i][1]))
        return cleaned_rois

