from stardist.models import StarDist2D
from csbdeep.utils import normalize



class SegmentationSD:
    def __init__(self, model='2D_versatile_fluo'):
        self.model = StarDist2D.from_pretrained(model)
        pass

    def give_coord(self, input_image):
        # gives list of all coordinates of ROIS in channel1
        seg_img, output_specs = self.model.predict_instances(normalize(input_image), prob_thresh=0.6, nms_thresh=0.2)
       # if len(output_specs['coord']) >= 0:
       #     for coords in output_specs['coord']:
       #         x_coords = coords[1]
       #         y_coords = coords[0]
       #         coord_list.append(list(zip(x_coords, y_coords)))
       # coord_list.sort(key=lambda coord_list1: coord_list1[2])
        return output_specs['coord']


