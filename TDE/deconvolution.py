import numpy as np

import TDE.derivatives as dv
from TDE.timedependence import time_dependent, convolve_fft


class Deconvolution:

    def __init__(self, psf, inputimage, l, lt, eps, N, delta=1.0, verbose=False):
        self.verbose = verbose
        self.l = l
        self.lt = lt
        self.eps = eps
        self.N = N
        self.delta = delta
        if time_dependent(inputimage.shape):
            self.dims = (inputimage.shape[0] + 6, inputimage.shape[1], inputimage.shape[2])
            self.xdims = (self.dims[1], self.dims[2])
            self.h = np.zeros(self.dims)
            self.h[self.dims[0] // 2, :, :] = psf
            self.f = np.zeros(self.dims)
            self.f[3:-3] = inputimage
            self.f[0] = inputimage[0]
            self.f[1] = inputimage[0]
            self.f[2] = inputimage[0]
            self.f[-1] = inputimage[-1]
            self.f[-2] = inputimage[-1]
            self.f[-3] = inputimage[-1]
        else:
            self.dims = inputimage.shape
            self.xdims = self.dims
            self.h = psf
            self.f = inputimage
            self.lt = 0.0
        self.H0 = np.sum(np.square(self.h))
        self.P = np.zeros(self.dims)
        self.b = convolve_fft(self.f, self.h)
        self.Lwxx = dv.fourierderivative(self.dims, "xx")
        self.Lwxy = dv.fourierderivative(self.dims, "xy")
        self.Lwyy = dv.fourierderivative(self.dims, "yy")
        self.Lw = [self.Lwxx, self.Lwxy, self.Lwyy]
        if time_dependent(self.dims):
            self.Lwtt = dv.fourierderivative(self.dims, "tt", delta)
            self.Lwxt = dv.fourierderivative(self.dims, "xt", delta)
            self.Lwyt = dv.fourierderivative(self.dims, "yt", delta)
            self.Lwt = [self.Lwtt, self.Lwxt, self.Lwyt]
        else:
            self.lt = 0.0
            self.Lwt = 0.0
        self.zeta = 0.8
        self.tol = 1e-6
        self.gw = np.zeros(self.dims, np.complex128)
        self.Pw = np.zeros(self.dims, np.complex128)

    def construct_initial_guess(self):
        hw = np.fft.fftn(self.h)
        h_2 = np.conj(hw) * hw

        Pw = np.zeros(self.dims, np.complex128) + h_2
        Pw += self.l * (1 + np.sum(np.conj(self.Lw) * self.Lw, axis=0))
        if time_dependent(self.f.shape):
            Pw += self.lt * (1 + np.sum(np.conj(self.Lwt) * self.Lwt, axis=0))
        # Pw += self.lt * (1 + np.conj(self.Lwtt)*self.Lwtt)

        gw = np.reciprocal(Pw) * np.fft.fftn(self.b)

        # gw = np.reciprocal(Pw) * np.conj(hw) * fw
        self.gw = gw
        self.Pw = Pw

        self.P = np.real(np.fft.ifftshift(np.fft.ifftn(1 / np.sqrt(Pw))))
        g = np.real(np.fft.ifftn(gw))
        # g = np.real(np.fft.ifftshift(np.fft.ifftn(gw)))

        return g

    def compute_N(self, g):
        N = np.zeros(g.shape)
        N[np.where(g < 0)] = 1.0
        return N

    def compute_W(self, g):
        gxx = dv.apply_dxx(g)
        gxy = dv.apply_dxy(g)
        gyy = dv.apply_dyy(g)
        E2 = np.square(g) + np.square(gxx) + np.square(gxy) + np.square(gyy)
        return 1 / (self.eps + E2), gxx, gxy, gyy

    def compute_Wt(self, g):
        gtt = dv.apply_dtt(g, self.delta)
        gxt = dv.apply_dxt(g, self.delta)
        gyt = dv.apply_dyt(g, self.delta)
        E2t = np.square(g) + np.square(gtt) + np.square(gxt) + np.square(gyt)
        return 1 / (self.eps + E2t), gtt, gxt, gyt

    def compute_R(self, g):

        N = self.compute_N(g)

        W, gxx, gxy, gyy = self.compute_W(g)
        tmp = dv.apply_dxx_minus(W * gxx)
        tmp += dv.apply_dxy_minus(W * gxy)
        tmp += dv.apply_dyy_minus(W * gyy)
        tmp += 100 * N * g + W * g
        tmp *= self.l

        if time_dependent(self.f.shape):
            Wt, gtt, gxt, gyt = self.compute_Wt(g)
            tmpt = dv.apply_dtt_minus(Wt * gtt, self.delta)
            tmpt += dv.apply_dxt_minus(Wt * gxt, self.delta)
            tmpt += dv.apply_dyt_minus(Wt * gyt, self.delta)
            tmpt += Wt * g
            tmpt *= self.lt
            hhg = convolve_fft(convolve_fft(g, self.h[:, ::-1, ::-1]), self.h[:, ::-1, ::-1])
            R = self.b - hhg - tmp - tmpt
        else:
            hhg = convolve_fft(convolve_fft(g, self.h[::-1, ::-1]), self.h[::-1, ::-1])
            R = self.b - hhg - tmp
        # hhg = convolve_fft(convolve_fft(g, self.h[::-1, ::-1, ::-1]), self.h[::-1, ::-1, ::-1])

        return R

    def compute_D(self, g):

        N = self.compute_N(g)
        W, gxx, gxy, gyy = self.compute_W(g)

        # tmp =  dv.apply_dxx_minus(dv.apply_dxx_minus(W))
        # tmp += dv.apply_dxy_minus(dv.apply_dxy_minus(W))
        # tmp += dv.apply_dyy_minus(dv.apply_dyy_minus(W))
        tmp = dv.apply_dxx_minus(dv.apply_dxx(W))
        tmp += dv.apply_dxy_minus(dv.apply_dxy(W))
        tmp += dv.apply_dyy_minus(dv.apply_dyy(W))

        D = 100 * self.l * N * g + self.l * (W + tmp) + self.H0

        if time_dependent(self.f.shape):
            Wt, gtt, gxt, gyt = self.compute_Wt(g)
            # tmp =  dv.apply_dtt_minus(dv.apply_dtt_minus(Wt, self.delta))
            # tmp += dv.apply_dxt_minus(dv.apply_dxt_minus(Wt, self.delta))
            # tmp += dv.apply_dyt_minus(dv.apply_dyt_minus(Wt, self.delta))
            tmp = dv.apply_dtt_minus(dv.apply_dtt(Wt, self.delta))
            tmp += dv.apply_dxt_minus(dv.apply_dxt(Wt, self.delta))
            tmp += dv.apply_dyt_minus(dv.apply_dyt(Wt, self.delta))

            D += self.lt * (Wt + tmp)

        return D

    def compute_U(self, R, D):
        pr = convolve_fft(self.P, R)
        dpr = np.reciprocal(D) * pr
        U = convolve_fft(self.P, dpr)
        return U

    def deconvolve(self):

        g0 = self.construct_initial_guess()

        R = self.compute_R(g0)
        D = self.compute_D(g0)
        U = self.compute_U(R, D)

        g = g0
        e = np.sum(np.square(R))
        ebar = e
        gbar = g
        Rbar = R
        k = 0
        while ((k < self.N) and (e > self.tol)):
            if self.verbose:
                print("k = " + str(k))
            zeta = self.zeta
            while zeta > 10 - 12:
                if self.verbose:
                    print("zeta = ", zeta, "  e = ", ebar)
                gbar = g + zeta * U
                Rbar = self.compute_R(gbar)
                ebar = np.sum(np.square(Rbar))
                zeta *= 0.7
                if ebar < e or np.abs(ebar - e) < self.tol:
                    break
            g = gbar
            R = Rbar
            e = ebar
            k += 1
            D = self.compute_D(g)
            U = self.compute_U(R, D)
        if time_dependent(self.f.shape):
            return g[3:-3]
        else:
            return g

    def deconvolve_shortcut(self):

        g0 = self.construct_initial_guess()

        R = self.compute_R(g0)
        D = self.compute_D(g0)
        U = self.compute_U(R, D)

        g = g0
        e = np.sum(np.square(R))
        ebar = e
        gbar = g
        Rbar = R
        zeta = self.zeta
        max_it = 10
        for _ in range(max_it):
            if self.verbose:
                print("zeta = ", zeta, "  e = ", ebar)
            gbar = g + zeta * U
            Rbar = self.compute_R(gbar)
            ebar = np.sum(np.square(Rbar))
            zeta *= 0.7
            if (ebar < e) or (np.abs(ebar - e) < self.tol) or (zeta < 10e-12):
                break
        g = gbar
        R = Rbar
        e = ebar
        D = self.compute_D(g)
        U = self.compute_U(R, D)
        if time_dependent(self.f.shape):
            return g[3:-3]
        else:
            return g
