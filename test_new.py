import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tomli
from csbdeep.utils import normalize
from scipy import interpolate
from scipy.ndimage import shift
from skimage import measure
from stardist.models import StarDist2D

from postprocessing.processing import ImageProcessor


#%%

def shapeNormalization(centeredData, x, y, radius=None):
    #coordinates of cell shape
    edgeCoords = np.array([y, x]).T
    centroid = np.array(centeredData.shape) / 2
    area = np.count_nonzero(centeredData)

    if radius is not None:
        cellRadius = radius
    else:
        cellRadius = math.sqrt(area/math.pi)

    #move to center
    centeredEdgeCoords = edgeCoords - centroid
    centeredEdgeCoords = np.vstack([centeredEdgeCoords, centeredEdgeCoords[0, :]])

    # convert to polar coodinates. gives transformation parameters
    polCoords = np.zeros_like(centeredEdgeCoords)
    polCoords[:, 0], polCoords[:, 1] = np.arctan2(centeredEdgeCoords[:, 0], centeredEdgeCoords[:, 1]), np.hypot(centeredEdgeCoords[:, 0], centeredEdgeCoords[:, 1])
    transformParameter = polCoords

    #has to start from 0 to 2pi
    transformParameter = np.vstack([transformParameter[-1, :] - [2*np.pi, 0], transformParameter, transformParameter[0, :] + [2*np.pi, 0]])

    #scale parameter
    transformParameter[:, 1] = (0.962 * np.mean(transformParameter[:, 1])) /transformParameter[:, 1]

    # do transformation with image
    sz = centeredData.shape

    #set to image center
    aMid = (np.array(sz)+1)/2

    # generate image coordinates of output image with origin in aMid
    y, x = np.meshgrid(range(1, sz[1] + 1), range(1, sz[0] + 1))
    x = x - aMid[1]
    y = y - aMid[0]

    # calculate positions in input image
    theta, rho = np.arctan2(y, x), np.hypot(x, y)

    #add small linearly increasing scalar to ensure uniqueness
    a = np.linspace(1, 2, transformParameter.shape[0])
    transformParameter = transformParameter + (a[:, np.newaxis] / 1e10)

    # transform
    f = interpolate.interp1d(transformParameter[:, 0], (1) / transformParameter[:, 1], fill_value="extrapolate")
    rho = rho * f(theta)

    x, y = rho * np.cos(theta) + aMid[1], rho * np.sin(theta) + aMid[0]

    # interpolate Data to output template
    y_coords = np.arange(centeredData.shape[0])
    x_coords = np.arange(centeredData.shape[1])
    interpolating_function = interpolate.RegularGridInterpolator((y_coords, x_coords), centeredData, bounds_error=False)

    # Create a grid for the interpolator using the previously computed x and y
    points = np.vstack((y.ravel(), x.ravel())).T

    # Interpolate
    normalized_data = interpolating_function(points)

    # Reshape the data back to the original shape
    normalized_data = normalized_data.reshape(sz)

    return normalized_data, cellRadius

def shift_image_to_centroid(image, centroid):
    # Get the shape of the image
    image_height, image_width = image.shape

    # Unpack the centroid coordinates
    centroid_x, centroid_y = centroid

    # Calculate the shift needed
    shift_x = int(image_width / 2 - centroid_x)
    shift_y = int(image_height / 2 - centroid_y)

    # Pad the image with zeros
    padding = max(abs(shift_x), abs(shift_y))
    padded_image = np.pad(image, padding, mode='constant', constant_values=0)

    # Shift the padded image
    shifted_image = shift(padded_image, (shift_y, shift_x), mode='constant', cval=0)
    return shifted_image


#%%

parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

Processor = ImageProcessor(parameters)

image = Processor.image

Processor.channel2 = Processor.registration.channel_registration(Processor.channel1, Processor.channel2,
                                                                 Processor.parameters["properties"]["registration_framebyframe"])
Processor.select_rois()

cell_list = Processor.cell_list

cell1 = cell_list[1]

#%%
segmodel = StarDist2D.from_pretrained('2D_versatile_fluo')

cell1_ch1 = cell1.channel1.original_image
cell1_ch2 = cell1.channel2.original_image

i=0
img_frame = cell1_ch1[i]
img_labels, img_details = segmodel.predict_instances(normalize(img_frame))
regions = measure.regionprops(img_labels)[0]

coord = img_details['coord'][0]
centroid = regions.centroid
#%%

fig, ax = plt.subplots()
ax.imshow(img_labels)
plt.show()

#%%

ratio = cell1.channel1.image/cell1.channel2.image

fig, ax = plt.subplots()
ax.imshow(ratio[0])
plt.show()



#%%
img_bin = img_frame
img_bin[np.where(img_labels==0)] =0

fig, ax = plt.subplots()
ax.imshow(img_bin)
plt.show()
#%%

img_shifted = shift_image_to_centroid(img_bin, centroid)
middle = np.array(img_shifted.shape)/2

image_height, image_width = img_shifted.shape

# Unpack the centroid coordinates
centroid_x, centroid_y = centroid

# Calculate the shift needed
shift_x = int(image_width / 2 - centroid_x)
shift_y = int(image_height / 2 - centroid_y)

#x = coord[1]+shift_coord[1]
#y = coord[0]+shift_coord[0]
x = coord[1]+ shift_x
y = coord[0] +shift_y

fig, ax = plt.subplots()
ax.imshow(img_shifted)
ax.plot(x, y)
plt.show()
#%%
res, r = shapeNormalization(img_shifted, x,y)

#%%
fig, ax = plt.subplots(ncols=2)
ax[0].imshow(img_shifted)
ax[1].imshow(res2)
plt.show()

#%%

res[np.where(res is np.nan)] = 0

#%%

res2 = np.nan_to_num(res)

#%%

res2[0,-1]

#%%

res2.ndim

#%%