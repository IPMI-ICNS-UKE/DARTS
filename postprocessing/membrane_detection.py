from __future__ import print_function



class MembraneDetector:


    def give_masked_image(self, img):
        """
        Returns a masked image
        :param img: the input image stack, usually a fluorescence microscopy image stack in tiff format
        """
        original_image = img.copy()

        # smoothing and thresholding
        img = filters.gaussian(img, 2)
        # triangle for 100x images, li for 63x images
        img = img < filters.threshold_li(img)
        # img = img < filters.threshold_triangle(img)

        # remove small holes; practically removing small objects from the inside of the cell membrane
        # param area_threshold = 1000 for 100x images, 500 for 63x images
        img = remove_small_holes(img, area_threshold=500, connectivity=2)

        # invert image so that holes can be properly filled
        img = invert(img)

        # dilate image to close holes in the membrane
        number_of_iterations = 4
        img = self.binary_dilate_n_times(img, number_of_iterations)

        # Fill holes within the cell membranes in the binary image
        # param area_threshold = 200000 for 100x images, 100000 for 63x images
        img = area_closing(img, area_threshold=100000, connectivity=2)

        # erode again after dilation (same number of iterations)
        img = self.binary_erode_n_times(img, number_of_iterations)

        # remove objects on the edge
        img = clear_border(img)

        # assign the value 255 to all black spots in the image and the value 0 to all white areas
        # kopie_mit_einsen = np.ones_like(img)
        mask_positive = img == True
        mask_negative = img == False

        original_img_masked = original_image.copy()
        original_img_masked[mask_positive] = 255
        original_img_masked[mask_negative] = 0

        return original_img_masked

    def find_cell_ROIs(self, img):
        """
        Finds the cell images in an image stack and returns the rectangular
        bounding boxes ("ROIs") and also a masks for the cell areas in these ROIs

        :param img: the input image stack, usually a fluorescence microscopy image stack in tiff format
        :return: returns an ordered list of ROIs and a boolean mask to segment
        """
        """
        original_image = img.copy()
        # smoothing and thresholding
        img = filters.gaussian(img, 2)
        # triangle for 100x images, li for 63x images
        img = img < filters.threshold_triangle(img)
        # img = img < filters.threshold_li(img)

        # remove small holes; practically removing small objects from the inside of the cell membrane
        # param area_threshold = 1000 for 100x images, 500 for 63x images
        img = remove_small_holes(img, area_threshold=1000, connectivity=2)

        # invert image so that holes can be properly filled
        img = invert(img)

        # dilate image to close holes in the membrane
        number_of_iterations = 4
        img = self.binary_dilate_n_times(img, number_of_iterations)

        # Fill holes within the cell membranes in the binary image
        # param area_threshold = 200000 for 100x images, 100000 for 63x images
        img = area_closing(img, area_threshold=200000, connectivity=2)

        # erode again after dilation (same number of iterations)
        img = self.binary_erode_n_times(img, number_of_iterations)

        # remove objects on the edge
        img = clear_border(img)

        # assign the value 255 to all black spots in the image and the value 0 to all white areas
        mask_positive = img == True
        mask_negative = img == False

        original_img_masked = original_image.copy()
        original_img_masked[mask_positive] = 255
        original_img_masked[mask_negative] = 0


        # labelling of the cell images with Stardist2D
        labels, _ = self.segm_model.predict_instances(normalize(original_img_masked))
        regions = measure.regionprops(labels)
        # exclude labels that are too small
        # r.area > 6000 for 100x images, >500 for 63x images
        regions = [r for r in regions if r.area > 6000]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(original_image)

        membrane_ROIs_bounding_boxes = []
        cropped_masks = []

        for region in regions:
            # create bounding box and append it to the "ROI-list"
            minr, minc, maxr, maxc = region.bbox
            membrane_ROIs_bounding_boxes.append((minr, minc, maxr, maxc))

            # create rectangle for visualisation
            rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                      fill=False, edgecolor='red', linewidth=1.5)
            ax.add_patch(rect)
            cropped_mask = mask_negative[minr:maxr, minc:maxc]

            cropped_masks.append(cropped_mask)
        plt.show()

        return membrane_ROIs_bounding_boxes, cropped_masks
        """

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


    def apply_mask_on_image(self, img, mask, n):
        """
        Applies a boolean mask on an image-array. Every value in the image that the mask is "True" for will be changed
        to the parameter n.

        :param img: the image-array to be modified
        :param n: target value of the elements in the img that are "True" in the mask
        :param mask: boolean mask which will be applied. Needs to have the same size as img
        :return: returns the modified image
        """
        original_image = img

        original_image[mask] = n
        return original_image

