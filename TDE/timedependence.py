import numpy as np
from scipy import ndimage
from scipy import signal


def time_dependent(dims):
    if len(dims) == 2:
        return False
    else:
        return True


def apply_slicewise(func, data, dtype=np.float64):
    result = np.zeros(data.shape, dtype=dtype)
    if time_dependent(data.shape):
        for t in range(data.shape[0]):
            result[t] = func(data[t])
    else:
        result = func(data)
    return result


def convolve_slicewise(data, weights, dtype=np.float64):
    result = np.zeros(data.shape, dtype=dtype)
    if time_dependent(data.shape):
        for t in range(data.shape[0]):
            result[t] = ndimage.convolve(data[t], weights)
    else:
        result = ndimage.convolve(data, weights)
    return result


def correlate_slicewise(data, weights, dtype=np.float64):
    result = np.zeros(data.shape, dtype=dtype)
    if time_dependent(data.shape):
        for t in range(data.shape[0]):
            result[t] = ndimage.correlate(data[t], weights)
    else:
        result = ndimage.correlate(data, weights)
    return result


def convolve_slicewise_fft(data, weights, dtype=np.float64):
    result = np.zeros(data.shape, dtype=dtype)
    if time_dependent(data.shape):
        for t in range(data.shape[0]):
            result[t] = signal.fftconvolve(data[t], weights, 'same')
    else:
        result = signal.fftconvolve(data, weights, 'same')
    return result


def correlate_slicewise_fft(data, weights, dtype=np.float64):
    result = np.zeros(data.shape, dtype=dtype)
    if time_dependent(data.shape):
        for t in range(data.shape[0]):
            result[t] = signal.fftconvolve(data[t], weights[::-1, ::-1], 'same')
    else:
        result = signal.fftconvolve(data, weights[::-1, ::-1], 'same')
    return result


def convolve_fft(data, weights):
    return np.real(np.fft.ifftshift(np.fft.ifftn(np.fft.fftn(data) * np.fft.fftn(weights))))
