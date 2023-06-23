import numpy as np
from scipy import signal
from scipy import ndimage



class Operator:

    FT = None

    def __init__(self, dims, data=None, dtype=np.float64):
        self.dims = dims
        if data is not None:
            self.data = data
        else:
            self.data = np.zeros(dims, dtype=dtype)

    def __add__(self, other):
        newdata = self.data
        if isinstance(other, np.ndarray) or isinstance(other, float) or isinstance(other, int) or isinstance(other, complex):
            newdata += other
        if isinstance(other, Operator):
            newdata += other.data
        return self.__class__(self.dims, newdata)

    def __sub__(self, other):
        newdata = self.data
        if isinstance(other, np.ndarray) or isinstance(other, float) or isinstance(other, int) or isinstance(other, complex):
            newdata -= other
        if isinstance(other, Operator):
            newdata -= other.data
        return self.__class__(self.dims, newdata)

    def __mul__(self, other):
        newdata = self.data
        if isinstance(other, np.ndarray) or isinstance(other, float) or isinstance(other, int) or isinstance(other, complex):
            newdata *= other
        if isinstance(other, Operator):
            newdata *= other.data
        return self.__class__(self.dims, newdata)

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__sub__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __iadd__(self, other):
        newdata = self.data
        if isinstance(other, np.ndarray) or isinstance(other, float) or isinstance(other, int) or isinstance(other, complex):
            newdata += other
        if isinstance(other, Operator):
            newdata += other.data
        self.data = newdata
        return self

    def __isub__(self, other):
        newdata = self.data
        if isinstance(other, np.ndarray) or isinstance(other, float) or isinstance(other, int) or isinstance(other, complex):
            newdata -= other
        if isinstance(other, Operator):
            newdata -= other.data
        self.data = newdata
        return self

    def __imul__(self, other):
        newdata = self.data
        if isinstance(other, np.ndarray) or isinstance(other, float) or isinstance(other, int) or isinstance(other, complex):
            newdata *= other
        if isinstance(other, Operator):
            newdata *= other.data
        self.data = newdata
        return self

    def conjugate(self):
        new = self.copy()
        new.data = np.conj(new.data())
        return new

    def conjugate_inplace(self):
        newdata = np.conj(self.data)
        self.data = newdata
        return self

    def reciprocal(self):
        return self.__class__(self.dims, np.reciprocal(self.data))


    def time_dependent(self):
        if len(self.dims) == 2:
            return False
        elif len(self.dims) == 3:
            return True
        else:
            return None

    def convolve(self, other):
        return self.__class__(self.dims, ndimage.convolve(self.data, other))

    def correlate(self, other):
        return self.__class__(self.dims, ndimage.correlate(self.data, other))

    def fourier_transform_inplace(self):
        newdata = np.fft.fftn(self.data)
        self.data = newdata
        return self

    def fourier_transform(self):
        return self.__class__(dims=self.dims, data=np.fft.fftn(self.data))

    def fourier_back_transform(self):
        return self.__class__(self.dims, np.fft.ifftn(self.data))

    def fourier_transform_slicewise(self):
        newdata = np.zeros(self.dims, np.complex128)
        if self.time_dependent():
            for t in range(self.dims[0]):
                newdata[t] = np.fft.fftn(self.data[t])
        else:
            newdata = np.fft.fftn(self.data)
        return self.__class__(self.dims, newdata)

    def fourier_back_transform_slicewise(self):
        newdata = np.zeros(self.dims, np.complex128)
        if self.time_dependent():
            for t in range(self.dims[0]):
                newdata[t] = np.fft.ifftn(self.data[t])
        else:
            newdata = np.fft.ifftn(self.data)
        return self.__class__(self.dims, newdata)

            #def convolve_with(self, b):
    #    return signal.fftconvolve(self.data, b, 'same')
    def convolve_with(self, b):
        return ndimage.convolve(self.data, b)

    def correlate_with(self, b):
        return signal.fftconvolve(self.data[::-1, ::-1], b, 'same')

    def calculate_fourier_transform(self):
        self.FT = np.fft.fftn(self.data)
        return self.FT

    def multiply_with(self, b):
        return np.multiply(self.data, b)

    def calculate_back_transform(self):
        self.data = np.real(np.fft.ifftshift(np.fft.ifftn(self.FT)))
        return self.data


class FourierDerivative(Operator):

    def __init__(self, axes, dims, dtype=np.complex128, delta=1.0):
        super().__init__(dims, dtype)
        self.axes = axes
        self.delta = delta
        self.data = np.zeros(self.dims, dtype=np.complex128)

        # axes : 0=t, 1=y, 2=x  / 0:y, 1:x
        if axes == "xx":
            if self.time_dependent():
                Nx = self.dims[2]
                for i in range(Nx):
                    self.data[:, :, i] = self.Lw_oneaxis(Nx, i)
            else:
                Nx = self.dims[1]
                for i in range(Nx):
                    self.data[:, i] = self.Lw_oneaxis(Nx, i)
        if axes == "yy":
            if self.time_dependent():
                Ny = self.dims[1]
                for i in range(Ny):
                    self.data[:, i, :] = self.Lw_oneaxis(Ny, i)
            else:
                Ny = self.dims[0]
                for i in range(Ny):
                    self.data[i, :] = self.Lw_oneaxis(Ny, i)
        if axes == "xy":
            if self.time_dependent():
                Ny = self.dims[1]
                Nx = self.dims[2]
                for i in range(Ny):
                    for j in range(Nx):
                        self.data[:, i, j] = self.Lw_twoaxis(Ny, Nx, i, j)
            else:
                Ny = self.dims[0]
                Nx = self.dims[1]
                for i in range(Ny):
                    for j in range(Nx):
                        self.data[i, j] = self.Lw_twoaxis(Ny, Nx, i, j)
        if axes == "tt":
            Nt = self.dims[0]
            for t in range(Nt):
                self.data[t, :, :] = self.Lw_oneaxis(Nt, t)
        if axes == "xt":
            Nt = self.dims[0]
            Nx = self.dims[2]
            for t in range(Nt):
                for i in range(Nx):
                    self.data[t, :, i] = self.Lw_twoaxis(Nt, Nx, t, i)
        if axes == "yt":
            Nt = self.dims[0]
            Ny = self.dims[1]
            for t in range(Nt):
                for i in range(Ny):
                    self.data[t, i, :] = self.Lw_twoaxis(Nt, Ny, t, i)

    def Lw_oneaxis(self, N, i):
        w = 2 * np.pi * i / N
        LW = np.exp(-1.j * w) - 2 + np.exp(1.j * w)
        return LW

    def Lw_twoaxis(self, N1, N2, i, j):
        w1 = 2 * np.pi * i / N1
        w2 = 2 * np.pi * j / N2
        LW = np.sqrt(2) * (1 - np.exp(-1.j * w1) - np.exp(-1.j * w2) + np.exp(-1.j * (w1 + w2)))
        return LW


class ImageOperator(Operator):

    def __init__(self, dims, data=None, dtype=np.float64):
        super().__init__(dims, data, dtype)
        self.nframes = 1
        if self.time_dependent():
            self.nframes = dims[0]

    def give_timeframe(self, t):
        if self.time_dependent():
            return self.data[t]
        else:
            return self.data

    def set_timeframe(self, x, t):
        if self.time_dependent():
            self.data[t] = x
        else:
            self.data = x
        return

    def set_timeframe_FT(self, x, t):
        if self.time_dependent():
            self.FT[t] = x
        else:
            self.FT = x
        return

    def apply_dxx(self):
        # time series: (t, y, x)    2d image: (y, x)
        if self.time_dependent():
            axis = 2
        else:
            axis = 1
        return ndimage.convolve1d(self.data, np.array([1, -2, 1]), axis, mode='wrap')

    def apply_dyy(self):
        # time series: (t, y, x)    2d image: (y, x)
        if self.time_dependent():
            axis = 1
        else:
            axis = 0
        return ndimage.convolve1d(self.data, np.array([1, -2, 1]), axis, mode='wrap')

    def apply_dxy(self):
        dxy = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
        # time series: (t, y, x)    2d image: (y, x)
        if self.time_dependent():
            d = np.zeros(self.dims)
            for t in range(self.dims[0]):
                d[t] = ndimage.convolve(self.data[t], dxy, mode='wrap', origin=[-1, -1])
            return d
        else:
            return ndimage.convolve(self.data, dxy, mode='wrap', origin=[-1, -1])

    def apply_dtt(self):
        # time series: (t, y, x)    2d image: (y, x)
        axis = 0
        return ndimage.convolve1d(self.data, np.array([1, -2, 1]), axis, mode='wrap')

    def apply_dxt(self):
        dxt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
        # time series: (t, y, x)    2d image: (y, x)
        d = np.zeros(self.dims)
        for y in range(self.dims[1]):
            d[:, y, :] = ndimage.convolve(self.data[:, y, :], dxt, mode='wrap', origin=[-1, -1])
        return d

    def apply_dyt(self):
        dyt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
        # time series: (t, y, x)    2d image: (y, x)
        d = np.zeros(self.dims)
        for x in range(self.dims[2]):
            d[:, :, x] = ndimage.convolve(self.data[:, :, x], dyt, mode='wrap', origin=[-1, -1])
        return d


    def apply_dxx_minus(self):
        # time series: (t, y, x)    2d image: (y, x)
        if self.time_dependent():
            axis = 2
        else:
            axis = 1
        return ndimage.correlate1d(self.data, np.array([1, -2, 1]), axis, mode='wrap')

    def apply_dyy_minus(self):
        # time series: (t, y, x)    2d image: (y, x)
        if self.time_dependent():
            axis = 1
        else:
            axis = 0
        return ndimage.correlate1d(self.data, np.array([1, -2, 1]), axis, mode='wrap')

    def apply_dxy_minus(self):
        dxy = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
        # time series: (t, y, x)    2d image: (y, x)
        if self.time_dependent():
            d = np.zeros(self.dims)
            for t in range(self.dims[0]):
                d[t] = ndimage.correlate(self.data[t], dxy, mode='wrap', origin=[-1, -1])
            return d
        else:
            return ndimage.correlate(self.data, dxy, mode='wrap', origin=[-1, -1])

    def apply_dtt_minus(self):
        # time series: (t, y, x)    2d image: (y, x)
        axis = 0
        return ndimage.correlate1d(self.data, np.array([1, -2, 1]), axis, mode='wrap')

    def apply_dxt_minus(self):
        dxt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
        # time series: (t, y, x)    2d image: (y, x)
        d = np.zeros(self.dims)
        for y in range(self.dims[1]):
            d[:, y, :] = ndimage.correlate(self.data[:, y, :], dxt, mode='wrap', origin=[-1, -1])
        return d

    def apply_dyt_minus(self):
        dyt = np.array([[1., -1.], [-1., 1.]])*np.sqrt(2)
        # time series: (t, y, x)    2d image: (y, x)
        d = np.zeros(self.dims)
        for x in range(self.dims[2]):
            d[:, :, x] = ndimage.correlate(self.data[:, :, x], dyt, mode='wrap', origin=[-1, -1])
        return d
