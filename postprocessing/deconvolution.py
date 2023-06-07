from TDE.deconvolution import Deconvolution
from postprocessing.cell import CellImage, ChannelImage
from psf.psf import PSF

class TDEDecon:

    def __init__(self, parameters):
        self.eps = 0.001
        self.N = 1
        self.l = parameters['deconvolution']['lambda']
        self.lt = parameters['deconvolution']['lambda_t']

    def run(self, cell, parameters):
        channel1 = cell.channel1.image
        channel2 = cell.channel2.image

        if channel1.ndim == 2: xdims = channel1.shape
        elif channel1.ndim == 3: xdims = (channel1.shape[1], channel1.shape[2])
        else: xdims = None

        psf_data = parameters['psf']
        psf_data['xysize'] = channel1.shape[1]

        psf_data_ch1 = psf_data
        psf_data_ch1['lambdaEx'] = psf_data['lambdaEx_ch1']
        psf_data_ch1['lambdaEm'] = psf_data['lambdaEm_ch1']
        psf_data_ch2 = psf_data
        psf_data_ch2['lambdaEx'] = psf_data['lambdaEx_ch2']
        psf_data_ch2['lambdaEm'] = psf_data['lambdaEm_ch2']


        pf_ch1 = PSF(xdims, **psf_data_ch1)
        pf_ch2 = PSF(xdims, **psf_data_ch2)

        Decon1 = Deconvolution(pf_ch1.data, channel1, self.l, self.lt, self.eps, self.N)
        channel1_deconvolved = Decon1.deconvolve()
        Decon2 = Deconvolution(pf_ch2.data, channel1, self.l, self.lt, self.eps, self.N)
        channel2_deconvolved = Decon2.deconvolve()

        return channel1_deconvolved, channel2_deconvolved

    def give_name(self):
        return "...deconvolution.."

    def deconvolve(self, input_roi, parameters):
        return input_roi

