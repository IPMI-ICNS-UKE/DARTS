from TDE.deconvolution import Deconvolution
from postprocessing.cell import CellImage, ChannelImage
from psf.psf import PSF
from skimage import restoration
import numpy as np


class BaseDecon:
    def execute(self, input_roi_channel1, input_roi_channel2, parameters):
        print(self.give_name())
        processed_roi_channel1, processed_roi_channel2 = self.deconvolve(input_roi_channel1, input_roi_channel2,
                                                                         parameters)
        return processed_roi_channel1, processed_roi_channel2

    def give_name(self):
        return "...deconvolution.."

    def deconvolve(self, input_roi_channel1, input_roi_channel2, parameters):
        return input_roi_channel1, input_roi_channel2

    def get_psf(self, input_roi_channel1, parameters):
        if input_roi_channel1.ndim == 2:
            xdims = input_roi_channel1.shape
        elif input_roi_channel1.ndim == 3:
            xdims = (input_roi_channel1.shape[1], input_roi_channel1.shape[2])
        else:
            xdims = None

        psf_data = parameters['psf']
        psf_data['xysize'] = input_roi_channel1.shape[1]

        psf_data_ch1 = psf_data
        psf_data_ch1['lambdaEx'] = psf_data['lambdaEx_ch1']
        psf_data_ch1['lambdaEm'] = psf_data['lambdaEm_ch1']
        psf_data_ch2 = psf_data
        psf_data_ch2['lambdaEx'] = psf_data['lambdaEx_ch2']
        psf_data_ch2['lambdaEm'] = psf_data['lambdaEm_ch2']

        psf_ch1 = PSF(xdims, **psf_data_ch1)
        psf_ch2 = PSF(xdims, **psf_data_ch2)
        return psf_ch1, psf_ch2


class TDEDeconvolution(BaseDecon):
    def __int__(self):
        super().__init__()

    def deconvolve(self, input_roi_channel1, input_roi_channel2, parameters):
        self.eps = 0.001
        self.N = 1
        self.l = parameters['deconvolution']['lambda']
        self.lt = parameters['deconvolution']['lambda_t']
        psf_ch1, psf_ch2 = self.get_psf(input_roi_channel1, parameters)

        Decon1 = Deconvolution(psf_ch1.data, input_roi_channel1, self.l, self.lt, self.eps, self.N)
        channel1_deconvolved = Decon1.deconvolve()
        Decon2 = Deconvolution(psf_ch2.data, input_roi_channel2, self.l, self.lt, self.eps, self.N)
        channel2_deconvolved = Decon2.deconvolve()

        return channel1_deconvolved, channel2_deconvolved

    def give_name(self):
        return "TDE Deconvolution"


class LRDeconvolution(BaseDecon):
    def __int__(self):
        super().__init__()

    def deconvolve(self, input_roi_channel1, input_roi_channel2, parameters):
        psf_ch1, psf_ch2 = self.get_psf(input_roi_channel1, parameters)
        channel1_deconvolved = np.empty_like(input_roi_channel1).astype(float)
        channel2_deconvolved = np.empty_like(input_roi_channel2).astype(float)
        for frame in range(input_roi_channel1.shape[0]):
            channel1_deconvolved[frame, :, :] = restoration.richardson_lucy(input_roi_channel1[frame, :, :], psf_ch1.data, num_iter=30)
            channel2_deconvolved[frame, :, :] = restoration.richardson_lucy(input_roi_channel2[frame, :, :], psf_ch2.data, num_iter=30)
        return channel1_deconvolved, channel2_deconvolved

    def give_name(self):
        return "Lucy-Richardson Deconvolution"
