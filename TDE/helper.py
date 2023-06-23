import numpy as np
import skimage
from scipy import ndimage
from matplotlib import pyplot as plt


def convert_to_uint(imf):
    if np.any(imf<0):
        imf -= imf.min()
    imu = np.zeros(imf.shape, dtype=np.uint16)
    if imf.ndim == 2:
        if imf.max() > 1.0 or imf.min() < -1.0:
            imu = skimage.img_as_uint(imf / np.linalg.norm(imf))
        else:
            imu = skimage.img_as_uint(imf)
    else:
        if imf.max() > 1.0 or imf.min() < -1.0:
            for t in range(imf.shape[0]):
                imu[t] = skimage.img_as_uint(imf[t] / np.linalg.norm(imf[t]))
        else:
            for t in range(imf.shape[0]):
                imu[t] = skimage.img_as_uint(imf[t])
    return imu


def convert_to_float_ski(imu):
    imf = np.zeros(imu.shape, dtype=np.uint16)
    if imu.ndim == 2:
        imf = skimage.img_as_float(imu)
    else:
        for t in range(imu.shape[0]):
            imf[t] = skimage.img_as_float(imu[t])
    return imf


def convert_to_float(img):
    if np.any(img<0):
        img -= img.min()
    im_f = np.zeros(img.shape)
    for t in range(img.shape[0]):
        im_f[t] = (img[t] / img[t].max()).astype(np.float64)
    return im_f


def get_blocks(A, sz):
    block_m = sz  # rows in block
    block_n = sz  # cols in block
    B = A.reshape((-1, block_m, A.shape[1] // block_n, block_n))
    return B.transpose((0, 2, 1, 3))

def homogeneity_measure(im_blocks):
    m1 = np.array([[0, 0, 0], [-1, 2, -1], [0, 0, 0]])
    m2 = np.array([[0, -1, 0], [0, 2, 0], [0, -1, 0]])
    m3 = np.array([[-1, 0, 0], [0, 2, 0], [0, 0, -1]])
    m4 = np.array([[0, 0, -1], [0, 2, 0], [-1, 0, 0]])
    m5 = np.array([[0, 0, 0], [0, 2, -1], [0, -1, 0]])
    m6 = np.array([[0, 0, 0], [-1, 2, 0], [0, -1, 0]])
    m7 = np.array([[0, -1, 0], [-1, 2, 0], [0, 0, 0]])
    m8 = np.array([[0, -1, 0], [0, 2, -1], [0, 0, 0]])
    masks = np.array([m1, m2, m3, m4, m5, m6, m7, m8])

    x = im_blocks.shape[0]
    y = im_blocks.shape[1]
    nblocks = x*y
    h = np.zeros((x, y))

    for i in range(x):
        for j in range(y):
            ib = im_blocks[i, j]
            im = np.zeros(len(masks))
            for k, m in enumerate(masks):
                im[k] = np.linalg.norm(ndimage.convolve(ib, m))
            h[i,j] = np.sum(im)

    return h

def estimate_gaussian_noise_variance(img, blocksize=20, k=20):
    if img.shape[0] % blocksize != 0:
        img = img[:-(img.shape[0] % blocksize), :-(img.shape[1] % blocksize)]
    im_b = get_blocks(img, blocksize)
    h = homogeneity_measure(im_b)
    variances = np.var(im_b, axis=(2, 3))
    means = np.mean(im_b, axis=(2, 3))
    h_flat = h.flatten()
    v_flat = variances.flatten()
    m_flat = means.flatten()

    v3 = v_flat[np.argpartition(h_flat, 3)]

    index_array = np.argpartition(h_flat, kth=k)
    vsk = v_flat[index_array]
    msk = m_flat[index_array]

    v = 0
    for i in range(k):
        if vsk[k] < 3* v3[:3].mean():
            v += vsk[k]


    vmean_bg = np.mean(vsk[:k])
    mmean_bg = np.mean(msk[:k])
    return v, mmean_bg


def plot_data(img, t=0):
    fig, ax = plt.subplots(figsize=[10, 10])
    if img.ndim == 2:
        ax.imshow(img)
    elif img.ndim == 3:
        ax.imshow(img[t])
    ax.axis('off')
    plt.show()
