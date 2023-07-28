import os
from pathlib import Path

import numpy as np
import pandas as pd
import tomli
from general.processing import ImageProcessor
from stardist.models import StarDist2D
import skimage.io as io
import matplotlib.pyplot as plt
from skimage.measure import regionprops
import math
from csbdeep.utils import normalize
from shapenormalization.shapenormalization import ShapeNormalization

#%%

results_dir = "results/shapenormalization_figures/"
os.makedirs(results_dir, exist_ok=True)


folder = "/Users/lwoelk/Library/Mobile Documents/com~apple~CloudDocs/Daten/CDarts/Paper Figures/HN1L/K2"
filename = "160718 3_cell3.tif"

#%%

image = io.imread(folder + "/" + filename)

#%%
t1=0
t2=10

fig, ax = plt.subplots(nrows=2, ncols=2)
ax[0,0].imshow(image[t1])
ax[1,0].imshow(image[t2])
plt.show()


#%%
def cartesian_to_polar(xs, ys, origin):
    x0, y0 = origin
    try:
        iter(xs)
    except TypeError:
        xs = [xs]
    try:
        iter(ys)
    except TypeError:
        ys = [ys]
    polar_coords = []
    for x, y in zip(xs, ys):
        r = math.sqrt((x - x0)**2 + (y - y0)**2)
        theta = math.atan2(y - y0, x - x0)
        polar_coords.append((r, theta))
    return np.array(polar_coords)

def find_maxmin_r(rs, thetas, origin):
    x0, y0 = origin

    min_r_index = np.argmin(rs)
    max_r_index = np.argmax(rs)

    min_point = (rs[min_r_index] * math.cos(thetas[min_r_index]) + x0, rs[min_r_index] * math.sin(thetas[min_r_index]) + y0)
    max_point = (rs[max_r_index] * math.cos(thetas[max_r_index]) + x0, rs[max_r_index] * math.sin(thetas[max_r_index]) + y0)

    return min_point, max_point

def find_edge_and_centroid(frame):
    model = StarDist2D.from_pretrained('2D_versatile_fluo')
    img, output_specs = model.predict_instances(normalize(frame), prob_thresh=0.6, nms_thresh=0.2,
                                                predict_kwargs=dict(verbose=False))
    edge = output_specs["coord"][0]
    regions = regionprops(img)
    props = regions[0]
    y0, x0 = props.centroid
    closed_edge = np.hstack((edge, edge[:, 0].reshape(2, 1)))

    pc = cartesian_to_polar(edge[1, :], edge[0, :], [x0, y0])
    r = pc[:, 0]
    theta = pc[:, 1]

    rmin_cart, rmax_cart = find_maxmin_r(r, theta, [x0, y0])

    return edge, closed_edge, [x0, y0], rmin_cart, rmax_cart


#%%

def plot_accesoires(frame):

    edge, closed_edge, [x0, y0], rmin_cart, rmax_cart\
        = find_edge_and_centroid(frame)

    ratio = frame
    channel1 = None
    channel2 = None
    model = None
    edge_list = edge
    centroid_list = [x0, y0]

    SN = ShapeNormalization(ratio, channel1, channel2, model,
                            edge_list, centroid_list)

    normalized_ratio_image = SN.apply_shape_normalization()


    edge_n, closed_edge_n, [x0_n, y0_n], rmin_cart_n, rmax_cart_n = \
        find_edge_and_centroid(normalized_ratio_image)

    result_img = {}
    result_img["closed_edge"] = closed_edge
    result_img["centroid"] = centroid_list
    result_img["rmin_cart"] = rmin_cart
    result_img["rmax_cart"] = rmax_cart

    result_norm = {}
    result_norm["closed_edge"] = closed_edge_n
    result_norm["centroid"] = [x0_n, y0_n]
    result_norm["rmin_cart"] = rmin_cart_n
    result_norm["rmax_cart"] = rmax_cart_n
    return result_img, result_norm, normalized_ratio_image


#%%

frame1 = image[t1]
frame2 = image[t2]

result_img, result_norm, normalized_ratio_image = plot_accesoires(frame1)

closed_edge = result_img["closed_edge"]
[x0, y0] = result_img["centroid"]
[x1, y1] = result_img["rmin_cart"]
[x2, y2] = result_img["rmax_cart"]

closed_edge_n = result_norm["closed_edge"]
[x0_n, y0_n] = result_norm["centroid"]
[x1_n, y1_n] = result_norm["rmin_cart"]
[x2_n, y2_n] = result_norm["rmax_cart"]

pc = cartesian_to_polar(closed_edge[1, :-1], closed_edge[0, :-1], [x0, y0])
pc_1 = cartesian_to_polar(x1, y1, [x0, y0])
pc_1[0][0] = pc_1[0][0] * (0.962 * np.mean(pc[:,0])/ pc_1[0][0])
pc_1_cart = (pc_1[0][0] * math.cos(pc_1[0][1]) + x0_n, pc_1[0][0] * math.sin(pc_1[0][1]) + y0_n)
pc_2 = cartesian_to_polar(x2, y2, [x0, y0])
pc_2[0][0] = pc_2[0][0] * (0.962 * np.mean(pc[:,0])/ pc_2[0][0])
pc_2_cart = (pc_2[0][0] * math.cos(pc_2[0][1]) + x0_n, pc_2[0][0] * math.sin(pc_2[0][1]) + y0_n)

fig, ax = plt.subplots(nrows=2, ncols=2)
ax[0,0].imshow(frame1)
ax[0,0].plot(closed_edge[1,:], closed_edge[0,:], color='red')
ax[0,0].plot(x0, y0, 'o', color='red')
ax[0,0].plot((x0, x1), (y0, y1), '-r', linewidth=2.5)
ax[0,0].plot((x0, x2), (y0, y2), '-r', linewidth=2.5)
#ax[0,0].plot((x0, x1), (y0, y1), '-r', linewidth=2.5)
#ax[0,0].plot((x0, x2), (y0, y2), '-r', linewidth=2.5)
ax[0,1].imshow(normalized_ratio_image)
ax[0,1].plot(closed_edge_n[1,:], closed_edge_n[0,:], color='red')
ax[0,1].plot(x0_n, y0_n, 'o', color='red')
ax[0,1].plot((x0_n, pc_1_cart[0]), (y0_n, pc_1_cart[1]), '-r', linewidth=2.5)
ax[0,1].plot((x0_n, pc_2_cart[0]), (y0_n, pc_1_cart[1]), '-r', linewidth=2.5)
plt.show()

#%%


print(closed_edge[0,:-1].shape)

#%%
fig, ax = plt.subplots()
ax.imshow(normalized_ratio_image)
plt.show()


#%%

print(edge[:, 0].reshape(2,1).shape)

#%%




parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
model = StarDist2D.from_pretrained('2D_versatile_fluo')

for file in os.listdir(folder):
     filename = os.fsdecode(file)
     if filename.endswith(".tif") or filename.endswith(".tiff"):
        parameters["inputoutput"]["path_to_input_combined"] = folder + "/" + filename
        print("processing image ", parameters["inputoutput"]["path_to_input_combined"])

        parameters["inputoutput"]["start_frame"] = None
        parameters["inputoutput"]["end_frame"] = None

        fname_short = Path(parameters["inputoutput"]["path_to_input_combined"]).stem

        Processor = ImageProcessor(parameters, model)

        Processor.start_postprocessing()

        for i, cell in enumerate(Processor.cell_list):
            normalized_ratio, centroid_coords = Processor.normalize_cell_shape(cell)

            t=0
            fig, ax = plt.subplots(ncols=2)
            ax[0].imshow(cell.ratio[t])
            ax[1].imshow(normalized_ratio[t])
            for ax_i in ax.reshape(-1):
                ax_i.axis('off')
            fig.savefig(results_dir + fname_short + '_shapecomp_cell'+str(i)+ '_t'+str(t)+'.jpg')


            mean_r = pd.Series(cell.ratio.mean(axis=(1,2))/ cell.ratio.mean(axis=(1,2)).max())
            mean_n = pd.Series(normalized_ratio.mean(axis=(1,2))/normalized_ratio.mean(axis=(1,2)).max())

            area_n = pd.Series(np.count_nonzero(normalized_ratio, axis=(1,2)) / np.count_nonzero(normalized_ratio, axis=(1,2)).max())
            area_r = pd.Series(np.count_nonzero(cell.ratio, axis=(1,2)) / np.count_nonzero(cell.ratio, axis=(1,2)).max())

            window_size = 100

            fig, ax = plt.subplots()
            ax.plot(area_r.rolling(window=window_size).mean(), color='r')
            ax.plot(area_n.rolling(window=window_size).mean(), ':', color='r')
            ax.plot(mean_r.rolling(window=window_size).mean(), color='b')
            ax.plot(mean_n.rolling(window=window_size).mean(), ':', color='b')
            ax.set_ylabel('normalized to maximum value')
            ax.set_xlabel('t')
            fig.savefig(results_dir + fname_short + '_areamean_cell'+str(i)+ '_t'+str(t)+'.jpg')



