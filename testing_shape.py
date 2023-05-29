import time
import matplotlib.pyplot as plt
from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor
from stardist.models import StarDist2D
from csbdeep.utils import normalize

from skimage import filters as filters, measure
import numpy as np

from scipy.ndimage import shift
from scipy import interpolate
#%%

def cartesian_to_polar(points):
    # Convert to polar coordinates
    r = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2)
    theta = np.arctan2(points[:, 1], points[:, 0])
    # Convert angles to range 0 to 2π
    theta = np.where(theta < 0, theta + 2 * np.pi, theta)

    polar_points = np.column_stack((r, theta))
    # Sort points by theta
    #sorted_points = polar_points[polar_points[:, 1].argsort()]
    return polar_points


def sort_polar_coord(polar_points):
    return polar_points[polar_points[:, 1].argsort()]


def polar_to_cartesian(polar_points):
    # polar_points should be a 2D numpy array where each row is a point in polar coordinates
    # with the first column as r and the second column as theta.

    x = polar_points[:, 0] * np.cos(polar_points[:, 1])
    y = polar_points[:, 0] * np.sin(polar_points[:, 1])
    cartesian_points = np.column_stack((x, y))

    return cartesian_points

def make_image_square(image):
    # To make it square, get the dimension of the image
    height, width = image.shape

    # Find the difference in dimensions
    diff = abs(height - width)

    # If height is greater than width
    if height > width:
        # Add padding to width
        square_image = np.pad(image, ((0, 0), (diff//2, diff - diff//2)), mode='constant', constant_values=0)

    # If width is greater than height
    elif width > height:
        # Add padding to height
        square_image = np.pad(image, ((diff//2, diff - diff//2), (0, 0)), mode='constant', constant_values=0)
    else:
        square_image = None
    return square_image

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
#%%
centroid = regions.centroid
#centroid = np.column_stack((cell1.cell_image_data['x_centroid_minus_bbox'][i], cell1.cell_image_data['y_centroid_minus_bbox'][i]))

#%%
fig, ax = plt.subplots()
ax.imshow(img_frame)
ax.plot(coord[1], coord[0], 'o', color='red')
ax.plot(coord[1][0], coord[0][0], 'o', color='yellow')
ax.plot(centroid[1], centroid[0], color='red', marker='o')

plt.show()

#%%

cart_coord = coord.T - centroid
polar_coord = cartesian_to_polar(cart_coord)

r = polar_coord[:, 0]
theta = polar_coord[:,1]
transformParameter = 0.962 * np.mean(r) / r

rnew = r*transformParameter

c = np.expand_dims(np.array(centroid), axis=1)
new_coord = np.column_stack((rnew, theta))
new_coord_cart = polar_to_cartesian(new_coord).T + c
#%%

fig, ax = plt.subplots()
ax.imshow(img_frame)
ax.plot(coord[1], coord[0], 'o', color='red')
ax.plot(new_coord_cart[1], new_coord_cart[0], 'o', color='yellow')
ax.plot(centroid[1], centroid[0], color='red', marker='o')

plt.show()

#%%

x = np.arange(img_frame.shape[0])
y = np.arange(img_frame.shape[1])

xx, yy = np.meshgrid(x,y)
xx = xx - c[0]
yy = yy - c[1]

polar_grid = cartesian_to_polar(np.column_stack((xx, yy)))
r_grid = polar_grid[:,0]
theta_grid = polar_grid[:,1]

#%%
f = interpolate.interp1d(r, 1/transformParameter,fill_value="extrapolate")
#%%
r_grid_new = r_grid * f(r_grid)

polar_grid_new = np.column_stack((r_grid_new, theta_grid))
cart_grid_new = polar_to_cartesian(polar_grid_new) + c.T
#%%
sorted_coord = cart_grid_new[cart_grid_new[:, 0].argsort()]

#%%

f2 = interpolate.RegularGridInterpolator((sorted_coord[:,0], sorted_coord[:,1]), img_frame)
#%%
print(sorted_coord)

#%%
polar_grid.shape
#%%










#%%
#%%
shifted_image = shift_image_to_centroid(img_frame, centroid)

sz = shifted_image.shape
middle = (sz[0]/2, sz[1]/2)

#shifted_coord = coord + middle
shift_x = int(img_frame.shape[0] / 2 - centroid[0])
shift_y = int(img_frame.shape[1] / 2 - centroid[1])

fig, ax = plt.subplots()
ax.imshow(shifted_image)
ax.plot(middle[0], middle[1], 'o', color='red')
ax.plot(coord[1]+shift_y, coord[0]+shift_x, 'o', color='red')
#ax.plot(coord[1]+middle[1], coord[0]+middle[0], 'o', color='red')

plt.show()
#%%
print(img_frame.shape[1] /2 )
print(centroid[1])

#%%
cart_coord = coord.T - middle
polar_coord = cartesian_to_polar(cart_coord)

r = polar_coord[:, 0]
transformParameter = 0.962 * np.mean(r) / r

#%%
print(np.arange(5))
#%%

coord2 = polar_to_cartesian(polar_coord)
print(coord2-cart_coord)
#%%
sz = np.array(shifted_image.shape)
mid = (sz+1)  /2
print(mid)
#%%


xx, yy = np.meshgrid(np.arange(sz[0]), np.arange(sz[1]))
xx = xx-mid[0]
yy = yy-mid[1]

grid_coord = cartesian_to_polar(np.column_stack((xx,yy)))
#%%
print(grid_coord[:,0].shape)

#%%
f = interpolate.interp1d(polar_coord[:,0], 1/transformParameter)

#%%
rho = grid_coord[:,0]
theta = grid_coord[:,1]
rho = rho * f(theta)
#%%
print(rho.shape)
print(theta.shape)
#%%
new_coord  = polar_to_cartesian(np.column_stack((rho, theta))) +mid
#%%
f2 = interpolate.RegularGridInterpolator((new_coord[:,0], new_coord[:,1]), shifted_image)

#%%
normalized_data = interp2(double(centeredData), x(:), y(:));
normalized_data = reshape(normalized_data, sz);


#%%
print(x.shape)
print(y.shape)

#%%

cell1.cell_image_data['x_centroid_minus_bbox']

#%%

plt.imshow(cell1.channel1.original_image[0])
plt.show()

#%%

img_details.keys()

#%%

from matplotlib import pyplot as plt

#%%

plt.imshow(ratio_raw[0])
plt.show()
#%%

img_frame = channel1[0]

segmodel = StarDist2D.from_pretrained('2D_versatile_fluo')

img_labels, img_details = segmodel.predict_instances(normalize(img_frame))
regions = measure.regionprops(img_labels)

#%%

plt.imshow(img_labels)
plt.show()

#%%

coord = img_details['coord']

coord1 = coord[1]

fig, ax = plt.subplots()
ax.imshow(img_frame)
ax.plot(coord1[1], coord1[0], 'o')
ax.plot(regions[1].centroid[1], regions[1].centroid[0], color='red', marker='o')
plt.show()

#%%
import numpy as np

def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return(rho, phi)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)


#%%

print(regions[0].centroid)