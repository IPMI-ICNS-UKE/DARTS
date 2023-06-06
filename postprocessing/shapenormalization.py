import math

import numpy as np
from scipy import interpolate
from scipy.ndimage import shift
from postprocessing.cell import CellImage
from stardist.models import StarDist2D
from csbdeep.utils import normalize
from skimage import measure


class ShapeNormalization:
    def __init__(self, cell: CellImage):
        if not isinstance(cell, CellImage):
            raise TypeError(f"Expected argument of type CellImage, got {type(cell).__name__}")
        self.ratio_image = cell.calculate_ratio_image
        self.channel1 = cell.channel1.original_image
        self.channel2 = cell.channel2.original_image

    def shift_image_to_centroid(self, image):

        image_height, image_width = image.shape

        centroid_x, centroid_y = self.centroid
        shift_x = int(image_width / 2 - centroid_x)
        shift_y = int(image_height / 2 - centroid_y)

        # Pad the image with zeros
        padding = max(abs(shift_x), abs(shift_y))
        padded_image = np.pad(image, padding, mode='constant', constant_values=0)

        # Shift the padded image
        shifted_image = shift(padded_image, (shift_y, shift_x), mode='constant', cval=0)
        return shifted_image

    def shift_edge_coord(self):
        middle = np.array(self.ratio_image.shape) / 2

        image_height, image_width = self.ratio_image.shape


        centroid_x, centroid_y = self.centroid

        # Calculate the shift needed
        shift_x = int(image_width / 2 - centroid_x)
        shift_y = int(image_height / 2 - centroid_y)

        shifted_edge_x = self.edgecoord[1] + shift_x
        shifted_edge_y = self.edgecoord[0] + shift_y
        return shifted_edge_x, shifted_edge_y

    def shapeNormalization(self, centeredData, x, y, radius=None):
        # coordinates of cell shape
        edgeCoords = np.array([y, x]).T
        centroid = np.array(centeredData.shape) / 2
        area = np.count_nonzero(centeredData)

        if radius is not None:
            cellRadius = radius
        else:
            cellRadius = math.sqrt(area / math.pi)

        # move to center
        centeredEdgeCoords = edgeCoords - centroid
        centeredEdgeCoords = np.vstack([centeredEdgeCoords, centeredEdgeCoords[0, :]])

        # convert to polar coodinates. gives transformation parameters
        polCoords = np.zeros_like(centeredEdgeCoords)
        polCoords[:, 0], polCoords[:, 1] = np.arctan2(centeredEdgeCoords[:, 0], centeredEdgeCoords[:, 1]), np.hypot(
            centeredEdgeCoords[:, 0], centeredEdgeCoords[:, 1])
        transformParameter = polCoords

        # has to start from 0 to 2pi
        transformParameter = np.vstack(
            [transformParameter[-1, :] - [2 * np.pi, 0], transformParameter, transformParameter[0, :] + [2 * np.pi, 0]])

        # scale parameter
        transformParameter[:, 1] = (0.962 * np.mean(transformParameter[:, 1])) / transformParameter[:, 1]

        # do transformation with image
        sz = centeredData.shape

        # set to image center
        aMid = (np.array(sz) + 1) / 2

        # generate image coordinates of output image with origin in aMid
        y, x = np.meshgrid(range(1, sz[1] + 1), range(1, sz[0] + 1))
        x = x - aMid[1]
        y = y - aMid[0]

        # calculate positions in input image
        theta, rho = np.arctan2(y, x), np.hypot(x, y)

        # add small linearly increasing scalar to ensure uniqueness
        a = np.linspace(1, 2, transformParameter.shape[0])
        transformParameter = transformParameter + (a[:, np.newaxis] / 1e10)

        # transform
        f = interpolate.interp1d(transformParameter[:, 0], (1) / transformParameter[:, 1], fill_value="extrapolate")
        rho = rho * f(theta)

        x, y = rho * np.cos(theta) + aMid[1], rho * np.sin(theta) + aMid[0]

        # interpolate Data to output template
        y_coords = np.arange(centeredData.shape[0])
        x_coords = np.arange(centeredData.shape[1])
        interpolating_function = interpolate.RegularGridInterpolator((y_coords, x_coords), centeredData,
                                                                     bounds_error=False)

        # Create a grid for the interpolator using the previously computed x and y
        points = np.vstack((y.ravel(), x.ravel())).T

        # Interpolate
        normalized_data = interpolating_function(points)

        # Reshape the data back to the original shape and set nan to 0
        normalized_data = np.nan_to_num(normalized_data.reshape(sz))

        return normalized_data, cellRadius


    def find_edge_and_centroid(self, img_frame):
        segmodel = StarDist2D.from_pretrained('2D_versatile_fluo')

        img_labels, img_details = segmodel.predict_instances(normalize(img_frame))
        regions = measure.regionprops(img_labels)[0]

        edgecoord = img_details['coord'][0]
        centroid = regions.centroid
        return edgecoord, centroid


    def apply_shape_normalization(self):
        normalized_data = np.zeros_like(self.ratio_image)
        if self.ratio_image.ndim == 3:
            nframes = self.ratio_image.shape[2]
            for i in range(nframes):
                edge, centroid = self.find_edge_and_centroid(self.channel1[i])
                img_shifted = self.shift_image_to_centroid(self.ratio_image[i])
                x_s, y_s = self.shift_edge_coord()
                normalized_data[i], cellRadius = self.shapeNormalization(img_shifted, x_s, y_s)
        elif self.ratio_image.ndim == 2:
            edge, centroid = self.find_edge_and_centroid(self.channel1)
            img_shifted = self.shift_image_to_centroid(self.ratio_image)
            x_s, y_s = self.shift_edge_coord()
            normalized_data, cellRadius = self.shapeNormalization(img_shifted, x_s, y_s)
        else:
            normalized_data = None

        return normalized_data


