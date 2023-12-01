from csbdeep.utils import normalize
from skimage import measure

import statistics




class SegmentationSD:
    def __init__(self, model):
        self.model = model

    def give_coord(self, input_image, estimated_cell_area, atp_flag):
        # gives list of all coordinates of ROIS in channel1
        seg_img, output_specs = self.model.predict_instances(normalize(input_image), prob_thresh=0.6, nms_thresh=0.2,
                                                        predict_kwargs=dict(verbose=False))
        regions = measure.regionprops(seg_img)
        cell_images_bounding_boxes = []
        # TO DO threshold needs to be optimised/generalised for resolution/cell type/ATP vs. Calcium images
        # TO DO for example 63x images of ATP-sensor loaded cells vs. 100x
        # TO DO cells diameter should be specified in pixels (=> user input: expected diameter in microns and scale)
        for region in regions:
            if (not atp_flag or (
                    region.area > 1.2 * estimated_cell_area)):  # < 1.5 * estimated_cell_area): # TO DO needs to be optimised
                miny_bbox, minx_bbox, maxy_bbox, maxx_bbox = region.bbox
                cell_images_bounding_boxes.append((miny_bbox, maxy_bbox, minx_bbox, maxx_bbox))
        return cell_images_bounding_boxes

    def find_median_image_size(self, regions):
        regions_areas = [r.area for r in regions]
        return statistics.median(regions_areas)

    def stardist_segmentation_in_frame(self, image_frame):
        img_labels, img_details = self.model.predict_instances(normalize(image_frame), predict_kwargs=dict(verbose=False))
        return img_labels

