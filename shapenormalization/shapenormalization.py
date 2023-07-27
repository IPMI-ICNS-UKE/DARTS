import numpy as np
from scipy import interpolate
from scipy.ndimage import shift
from csbdeep.utils import normalize
from skimage import measure


class ShapeNormalization:
    def __init__(self, ratio, channel1, channel2, model, edge_list=None, centroid_list=None):
        self.ratio_image = ratio
        self.channel1 = channel1
        self.channel2 = channel2
        self.model = model
        self.edge_list = edge_list
        self.centroid_list = centroid_list

        self.centroid_coords_list = []


    def shift_image_to_centroid(self, image, centroid):

        image_height, image_width = image.shape

        centroid_x, centroid_y = centroid
        shift_x = int(image_width / 2 - centroid_x)
        shift_y = int(image_height / 2 - centroid_y)

        # Pad the image with zeros
        padding = max(abs(shift_x), abs(shift_y))
        padded_image = np.pad(image, padding, mode='constant', constant_values=0)

        # Shift the padded image
        shifted_image = shift(padded_image, (shift_y, shift_x), mode='constant', cval=0)
        return shifted_image

    def shift_edge_coord(self, shifted_image, edgecoord, centroid):
        middle = np.array(shifted_image.shape) / 2

        image_height, image_width = shifted_image.shape


        centroid_x, centroid_y = centroid

        # Calculate the shift needed
        shift_x = int(image_width / 2 - centroid_x)
        shift_y = int(image_height / 2 - centroid_y)

        shifted_edge_x = edgecoord[1] + shift_x
        shifted_edge_y = edgecoord[0] + shift_y
        return shifted_edge_x, shifted_edge_y

    def shapeNormalization(self, centeredData, x, y):
        edgeCoords = np.array([y, x]).T
        centroid = np.array(centeredData.shape) / 2

        # move to center -> so origin for polar coordinates is at centroid
        centeredEdgeCoords = edgeCoords - centroid
        centeredEdgeCoords_c = np.vstack([centeredEdgeCoords, centeredEdgeCoords[0, :]])

        # convert to polar coodinates. gives transformation parameters
        polCoords = np.zeros_like(centeredEdgeCoords_c)
        polCoords[:, 0], polCoords[:, 1] = np.arctan2(centeredEdgeCoords_c[:, 0], centeredEdgeCoords_c[:, 1]), np.hypot(
            centeredEdgeCoords_c[:, 0], centeredEdgeCoords_c[:, 1])

        # has to start from 0 to 2pi for the interpolation
        polCoords_sorted = np.vstack(
            [polCoords[-1, :] - [2 * np.pi, 0], polCoords, polCoords[0, :] + [2 * np.pi, 0]])

        # scale parameter --> transforms edge coordinates onto circle
        scale_parameter = (0.962 * np.mean(polCoords_sorted[:, 1])) / polCoords_sorted[:, 1]


        # ---- now: transformation of entire image

        sz = centeredData.shape


        # generate image coordinates of output image with origin in centroid
        y, x = np.meshgrid(range(1, sz[1] + 1), range(1, sz[0] + 1))
        x_shifted = x - centroid[1]
        y_shifted = y - centroid[0]

        # calculate positions in input image
        theta, rho = np.arctan2(y_shifted, x_shifted), np.hypot(x_shifted, y_shifted)

        # add small linearly increasing scalar to ensure uniqueness
        a = np.linspace(1, 2, len(scale_parameter))
        scale_parameter_a = scale_parameter + (a / 1e10)

        # transform: interpolate INVERSE transformation to get new coordinates
        f = interpolate.interp1d(polCoords_sorted[:, 0], 1 / scale_parameter_a, fill_value="extrapolate")
        rho = rho * f(theta)

        x_new, y_new = rho * np.cos(theta) + centroid[1], rho * np.sin(theta) + centroid[0]

        # interpolate Data to output template
        y_coords = np.arange(centeredData.shape[0])
        x_coords = np.arange(centeredData.shape[1])
        interpolating_function = interpolate.RegularGridInterpolator((y_coords, x_coords), centeredData,
                                                                     bounds_error=False)

        # Create a grid for the interpolator using the previously computed x and y
        points = np.vstack((y_new.ravel(), x_new.ravel())).T

        # Interpolate
        normalized_data = interpolating_function(points)

        # Reshape the data back to the original shape and set nan to 0
        normalized_data_reshaped = np.nan_to_num(normalized_data.reshape(sz, order='F'))

        return normalized_data_reshaped

    def find_edge_and_centroid(self, img_frame):

        img_labels, img_details = self.model.predict_instances(normalize(img_frame), predict_kwargs=dict(verbose=False))

        regions = measure.regionprops(img_labels)[0]

        edgecoord = img_details['coord'][0]

        centroid = regions.centroid
        return edgecoord, centroid

    def get_centroid_coords_list(self):
        return self.centroid_coords_list



    def pad_array(self, arr, shape):
        pad_shape = [(0, max_shape - cur_shape) for max_shape, cur_shape in zip(shape, arr.shape)]
        return np.pad(arr, pad_shape)

    def apply_shape_normalization(self):
        if self.ratio_image.ndim == 3:
            normalized_data_list = []
            nframes = self.ratio_image.shape[0]
            for i in range(nframes):
                if self.edge_list is not None:
                    edge = self.edge_list[i]
                    centroid = self.centroid_list[i]
                else:
                    edge, centroid = self.find_edge_and_centroid(self.channel1[i])

                self.centroid_coords_list.append(centroid)

                img_shifted = self.shift_image_to_centroid(self.ratio_image[i], centroid)
                x_s, y_s = self.shift_edge_coord(img_shifted, edge, centroid)
                ndata = self.shapeNormalization(img_shifted, x_s, y_s)
                normalized_data_list.append(ndata)
            max_shape = np.max([arr.shape for arr in normalized_data_list], axis=0)
            padded_arrays = [self.pad_array(arr, max_shape) for arr in normalized_data_list]
            normalized_data = np.stack(padded_arrays)

        elif self.ratio_image.ndim == 2:
            if self.edge_list is not None:
                edge = self.edge_list
                centroid = self.centroid_list
            else:
                edge, centroid = self.find_edge_and_centroid(self.channel1)

            self.centroid_coords_list.append(centroid)

            img_shifted = self.shift_image_to_centroid(self.ratio_image, centroid)
            x_s, y_s = self.shift_edge_coord(img_shifted, edge, centroid)
            normalized_data = self.shapeNormalization(img_shifted, x_s, y_s)
        else:
            normalized_data = None

        return normalized_data

