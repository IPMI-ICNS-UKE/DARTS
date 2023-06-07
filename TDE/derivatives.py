import numpy as np
from scipy import ndimage
from TDE.timedependence import time_dependent



def Lw_oneaxis(N, i):
    w = 2 * np.pi * i / N
    LW = np.exp(-1.j * w) - 2 + np.exp(1.j * w)
    return LW


def Lw_twoaxis(N1, N2, i, j):
    w1 = 2 * np.pi * i / N1
    w2 = 2 * np.pi * j / N2
    LW = np.sqrt(2) * (1 - np.exp(-1.j * w1) - np.exp(-1.j * w2) + np.exp(-1.j * (w1 + w2)))
    return LW


def fourierderivative(dims, axes, delta=1.0):
    data = np.zeros(dims, np.complex128)
    # axes : 0=t, 1=y, 2=x  / 0:y, 1:x
    if axes == "xx":
        if time_dependent(dims):
            Nx = dims[2]
            for i in range(Nx):
                data[:, :, i] = Lw_oneaxis(Nx, i)
        else:
            Nx = dims[1]
            for i in range(Nx):
                data[:, i] = Lw_oneaxis(Nx, i)
    if axes == "yy":
        if time_dependent(dims):
            Ny = dims[1]
            for i in range(Ny):
                data[:, i, :] = Lw_oneaxis(Ny, i)
        else:
            Ny = dims[0]
            for i in range(Ny):
                data[i, :] = Lw_oneaxis(Ny, i)
    if axes == "xy":
        if time_dependent(dims):
            Ny = dims[1]
            Nx = dims[2]
            for i in range(Ny):
                for j in range(Nx):
                    data[:, i, j] = Lw_twoaxis(Ny, Nx, i, j)
        else:
            Ny = dims[0]
            Nx = dims[1]
            for i in range(Ny):
                for j in range(Nx):
                    data[i, j] = Lw_twoaxis(Ny, Nx, i, j)
    if axes == "tt":
        Nt = dims[0]
        for t in range(Nt):
            data[t, :, :] = delta**2 * Lw_oneaxis(Nt, t)
    if axes == "xt":
        Nt = dims[0]
        Nx = dims[2]
        for t in range(Nt):
            for i in range(Nx):
                data[t, :, i] = delta * Lw_twoaxis(Nt, Nx, t, i)
    if axes == "yt":
        Nt = dims[0]
        Ny = dims[1]
        for t in range(Nt):
            for i in range(Ny):
                data[t, i, :] = delta * Lw_twoaxis(Nt, Ny, t, i)
    return data




def apply_dxx(data):
    # time series: (t, y, x)    2d image: (y, x)
    if time_dependent(data.shape):
        axis = 2
    else:
        axis = 1
    return ndimage.convolve1d(data, np.array([1, -2, 1]), axis, mode='wrap')

def apply_dyy(data):
    # time series: (t, y, x)    2d image: (y, x)
    if time_dependent(data.shape):
        axis = 1
    else:
        axis = 0
    return ndimage.convolve1d(data, np.array([1, -2, 1]), axis, mode='wrap')

def apply_dxy(data):
    dxy = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
    # time series: (t, y, x)    2d image: (y, x)
    dims = data.shape
    if time_dependent(dims):
        d = np.zeros(dims)
        for t in range(dims[0]):
            d[t] = ndimage.convolve(data[t], dxy, mode='wrap', origin=[-1, -1])
        return d
    else:
        return ndimage.convolve(data, dxy, mode='wrap', origin=[-1, -1])

def apply_dtt(data, delta=1.0):
    # time series: (t, y, x)    2d image: (y, x)
    axis = 0
    return ndimage.convolve1d(data, delta**2*np.array([1, -2, 1]), axis, mode='wrap')

def apply_dxt(data, delta=1.0):
    dims = data.shape
    dxt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
    # time series: (t, y, x)    2d image: (y, x)
    d = np.zeros(dims)
    for y in range(dims[1]):
        d[:, y, :] = ndimage.convolve(data[:, y, :], delta*dxt, mode='wrap', origin=[-1, -1])
    return d

def apply_dyt(data, delta=1.0):
    dims = data.shape
    dyt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
    # time series: (t, y, x)    2d image: (y, x)
    d = np.zeros(dims)
    for x in range(dims[2]):
        d[:, :, x] = ndimage.convolve(data[:, :, x], delta*dyt, mode='wrap', origin=[-1, -1])
    return d


def apply_dxx_minus(data):
    dims = data.shape
    # time series: (t, y, x)    2d image: (y, x)
    if time_dependent(dims):
        axis = 2
    else:
        axis = 1
    return ndimage.correlate1d(data, np.array([1, -2, 1]), axis, mode='wrap')

def apply_dyy_minus(data):
    dims = data.shape
    # time series: (t, y, x)    2d image: (y, x)
    if time_dependent(dims):
        axis = 1
    else:
        axis = 0
    return ndimage.correlate1d(data, np.array([1, -2, 1]), axis, mode='wrap')

def apply_dxy_minus(data):
    dims = data.shape
    dxy = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
    # time series: (t, y, x)    2d image: (y, x)
    if time_dependent(dims):
        d = np.zeros(dims)
        for t in range(dims[0]):
            d[t] = ndimage.correlate(data[t], dxy, mode='wrap', origin=[-1, -1])
        return d
    else:
        return ndimage.correlate(data, dxy, mode='wrap', origin=[-1, -1])

def apply_dtt_minus(data, delta=1.0):
    # time series: (t, y, x)    2d image: (y, x)
    axis = 0
    return ndimage.correlate1d(data, delta**2*np.array([1, -2, 1]), axis, mode='wrap')

def apply_dxt_minus(data, delta=1.0):
    dims = data.shape
    dxt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
    # time series: (t, y, x)    2d image: (y, x)
    d = np.zeros(dims)
    for y in range(dims[1]):
        d[:, y, :] = ndimage.correlate(data[:, y, :], delta*dxt, mode='wrap', origin=[-1, -1])
    return d

def apply_dyt_minus(data, delta=1.0):
    dims = data.shape
    dyt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
    # time series: (t, y, x)    2d image: (y, x)
    d = np.zeros(dims)
    for x in range(dims[2]):
        d[:, :, x] = ndimage.correlate(data[:, :, x], delta*dyt, mode='wrap', origin=[-1, -1])
    return d
