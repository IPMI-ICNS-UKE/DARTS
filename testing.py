import skimage.io as io
from matplotlib import pyplot as plt
from stardist.models import Config2D, StarDist2D
from csbdeep.utils import normalize
import numpy as np
import tomli


def plot_coord_on_img(x_coord, y_coord):
    for x_, y_ in zip(x_coord, y_coord):
        x_cord = x_
        y_cord = y_
        plt.scatter([x_cord], [y_cord])
    plt.show()


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

seg_img_channel1, output_specs_channel1 = model.predict_instances(normalize(np.hsplit(img, 2)[0]),
                                                                  prob_thresh=0.6,
                                                                  nms_thresh=0.2)
seg_img_channel2, output_specs_channel2 = model.predict_instances(normalize(np.hsplit(img, 2)[1]),
                                                                  prob_thresh=0.6,
                                                                  nms_thresh=0.2)

print("Total number of rois found in channel1: ", len(output_specs_channel1['coord']),
      "\nTotal number of rois found in channel2: ", len(output_specs_channel2['coord']))

plt.imshow(img)
coord_list1 = []
if len(output_specs_channel1['coord']) >= 0:
    for coords in output_specs_channel1['coord']:
        x_coords = coords[1]
        y_coords = coords[0]

        plot_coord_on_img(x_coords, y_coords)

        coord_list1.append(list(zip(x_coords, y_coords)))

plt.imshow(img)
coord_list2 = []
if len(output_specs_channel2['coord']) >= 0:
    for coords in output_specs_channel2['coord']:
        x_coords = coords[1]
        # since the segmentation was applied to each half of the image separately it is necessary to convert the
        # x coordinates back
        x_coords = [x + float(img.shape[1]/2) for x in x_coords]
        y_coords = coords[0]

        plot_coord_on_img(x_coords, y_coords)

        coord_list2.append(list(zip(x_coords, y_coords)))



