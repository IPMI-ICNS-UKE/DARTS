import skimage.io as io
from matplotlib import pyplot as plt
from stardist.models import Config2D, StarDist2D
from csbdeep.utils import normalize
import tomli

# example file: frame 1 of "170424 2.tif" data
file = "Data/170424 2_1.tif"

img = io.imread(file)

plt.imshow(img)
plt.show()

parameters = dict(path="", nb_rois=3)

# print(parameters)
print(parameters["nb_rois"])

# apply StarDist for segmentation
model = StarDist2D.from_pretrained('2D_versatile_fluo')
seg_img, output_specs = model.predict_instances(normalize(img), prob_thresh=0.6, nms_thresh=0.2)
print("Total number of rois found: ", len(output_specs['coord']))

coords_lst = []
implot = plt.imshow(img)
if len(output_specs['coord']) >= 0:
    for coords in output_specs['coord']:
        # output_specs['coord']: [[y coords], [x coords]]
        x_coords = coords[1]
        y_coords = coords[0]

        # plot coordinates on tif image
        for x_, y_ in zip(x_coords, y_coords):
            x_cord = x_
            y_cord = y_
            plt.scatter([x_cord], [y_cord])
        plt.show()

        coords_lst.append(list(zip(x_coords, y_coords)))
