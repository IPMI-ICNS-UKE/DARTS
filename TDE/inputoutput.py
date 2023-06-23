import os
import numpy as np
from PIL import Image


def inputoutput(save_path, read_path, image_name, create_image_folder):
    """
    This function creates folders where to save results and also the path where to find the input image.
    **** Here: input is a single image! ****
    :param create_image_folder: whether to create a new folder for each processed image
    :param save_path: where to save results
    :param read_path: where the input image is located
    :param image_name: name of the input image (including file extension, i.e. "abc.tif"
    :return:
    path where to find input image including image name with file extension,
    path where to save result including image name without file extension,
    image name without file extension
    """
    im_name = os.path.splitext(image_name)[0]
    if create_image_folder:
        save_path += im_name + '/'
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    read_image_path = read_path + image_name
    save_image_path = save_path + im_name
    return read_image_path, save_image_path


def inputoutput_folder(save_path, read_path, create_image_folder):
    """
    This function creates folders where to save results and also creates a list of input paths
    according to the given folder.
    **** Here: all images in given folder will be processed! ****
    :param save_path: where to save results
    :param read_path: where to read input images - all images in this folder will be read!
    :param create_image_folder: whether to create a new folder for each processed image
    :return:
    list of paths where to read input images
    list of paths where to save respective results -> each image in own folder
    """
    _, _, filenames = next(os.walk(read_path))
    savepaths = []
    readpaths = []
    for f in filenames:
        fname = os.path.splitext(f)[0]
        if create_image_folder:
            spath = save_path + fname + '/'
        else:
            spath = save_path
        if not os.path.exists(spath):
            os.makedirs(spath)
        savepaths.append(spath + fname)
        readpaths.append(read_path + f)
    return readpaths, savepaths


def convert_to_16bit(inputarray):
    frames = inputarray.shape[0]
    zgray = np.zeros(inputarray.shape)
    for t in range(frames):
        # Convert to 16 bit unsigned integers.
        zgray[t] = (65535 * ((inputarray[t] - inputarray.min()) / inputarray.ptp())).astype(np.uint16)
    return zgray


def save_as_16bit(data, savename, savedir):
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    data16 = convert_to_16bit(data)
    imlist = []
    for m in data16:
        imlist.append(Image.fromarray(m))
    imlist[0].save(savedir + savename, save_all=True, append_images=imlist[1:])
    return


def create_noisename(p, g):
    return "p{1:.2f}g{:06.2e}".format(p, g)


def create_spotname(size, spotsize, brightness, motionscale):
    return "sz" + str(size) + "spsz" + str(spotsize) + "bts" + str(brightness) + "mtn" + str(motionscale)


def create_deconname(lamb, lamb_t, maxit, eps):
    return "lamb{0:.2f}lambt{1:.2f}eps{2:.2e}maxit{3}".format(lamb, lamb_t, eps, maxit)


def create_filename_decon(path, lamb, lamb_t, maxit, eps):
    return path + '_' + create_deconname(lamb, lamb_t, maxit, eps) + '_deconvolved.tif'


def cut_roi(img,  upper_left, size="all", time="all"):
    if size != "all":
        if len(img.shape) == 2:
            img = img[upper_left[0]:upper_left[0] + size, upper_left[1]:upper_left[1] + size]
        elif len(img.shape) == 3:
            img = img[:, upper_left[0]:upper_left[0] + size, upper_left[1]:upper_left[1] + size]
    if time != 'all' and len(img.shape) == 3:
        r1, r2 = time
        img = img[r1:r2, :, :]
    return img


def cut_roi_psf(psf, size):
    if size != "all":
        psf_im = Image.fromarray(psf)
        psf_small = psf_im.resize((size, size), resample=Image.NEAREST)
        psf_small_ar = np.asarray(psf_small)
        return psf_small_ar
    else:
        return psf


def set_baseline(original, img):
    for t in range(original.shape[0]):
        baseline = original[t].mean()
        img[t] = img[t] - (img[t].mean() - baseline)
    return img
