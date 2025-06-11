from src.TDEntropyDeconvolution.util.deconvolution import Deconvolution
from src.TDEntropyDeconvolution.psf.psf import PSF
from skimage import restoration
import numpy as np


class BaseDecon:
    def execute(self, input_roi_channel1, input_roi_channel2, parameters):
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

        psf_data = parameters["processing_pipeline"]["postprocessing"]["psf"]
        psf_data['xysize'] = input_roi_channel1.shape[1]

        psf_data_ch1 = psf_data.copy()
        psf_data_ch1['lambdaEx'] = psf_data['lambdaEx_ch1']
        psf_data_ch1['lambdaEm'] = psf_data['lambdaEm_ch1']
        psf_data_ch2 = psf_data.copy()
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
        self.l = parameters['processing_pipeline']['postprocessing']['TDE_lambda']
        self.lt = parameters['processing_pipeline']['postprocessing']['TDE_lambda_t']
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
            channel1_deconvolved[frame, :, :] = restoration.richardson_lucy(input_roi_channel1[frame, :, :], psf_ch1.data, num_iter=4, clip=False)
            channel2_deconvolved[frame, :, :] = restoration.richardson_lucy(input_roi_channel2[frame, :, :], psf_ch2.data, num_iter=4, clip=False)
        return channel1_deconvolved, channel2_deconvolved

    def give_name(self):
        return "Lucy-Richardson Deconvolution"
    

class LWDeconvolution(BaseDecon):
    def __init__(self):
        super().__init__()
    
    def deconvolve(self, input_roi_channel1, input_roi_channel2, parameters):
        xp = np #change if work with cupy
 
        psf_ch1, psf_ch2 = self.get_psf(input_roi_channel1, parameters)

        n_iter = parameters["processing_pipeline"]["postprocessing"]["decon_iter"]

        # pre-compute the OTF (= FFT of the PSF) once per channel
        otf_ch1 = xp.fft.fftn(psf_ch1.data,s=input_roi_channel1.shape[-2:])
        otf_ch2 = xp.fft.fftn(psf_ch2.data,s=input_roi_channel2.shape[-2:])

        # allocate output arrays, float32/float64 depending on input
        ch1_deconv = xp.empty_like(input_roi_channel1).astype(float)
        ch2_deconv = xp.empty_like(input_roi_channel2).astype(float)

        #PROCESS EACH FRAME (first axis) INDEPENDENTLY
        for f in range(input_roi_channel1.shape[0]):   #iterate over z-slices / time frames
            data1 = input_roi_channel1[f].astype(float)  
            data2 = input_roi_channel2[f].astype(float)  

            # parameters & initial guesses
            t      = 1.0                               
            gamma1 = 1.0                              
            xk1    = data1.copy()                      
            xk2    = data2.copy()                     
            xk1_old = xk1                              
            xk2_old = xk2                              
            
            #main itereration loop
            for i in range(n_iter):
                if i == 0:
                    # residual r = y – H x
                    r1 = xp.fft.fftn(data1) - otf_ch1 * xp.fft.fftn(xk1)
                    r2 = xp.fft.fftn(data2) - otf_ch2 * xp.fft.fftn(xk2)
                    # x ← x + t Hᵀ r
                    xk1 = xk1 + t * xp.fft.ifftn(xp.conj(otf_ch1) * r1).real
                    xk2 = xk2 + t * xp.fft.ifftn(xp.conj(otf_ch2) * r2).real
                else:                                  # accelerated Land-Weber (Nesterov/FISTA flavour)
                    gamma2 = 0.5 * (xp.sqrt(4*gamma1**2 + gamma1**4)) - gamma1**2
                    beta   = -gamma2 * (1 - 1/gamma1)  # momentum weight

                    # yₖ = xₖ + β (xₖ – xₖ₋₁) — extrapolation
                    y1 = xk1 + beta * (xk1 - xk1_old)
                    y2 = xk2 + beta * (xk2 - xk2_old)

                    # residual r = y – H y
                    r1 = xp.fft.fftn(data1) - otf_ch1 * xp.fft.fftn(y1)
                    r2 = xp.fft.fftn(data2) - otf_ch2 * xp.fft.fftn(y2)

                    # y ← y + t Hᵀ r  — gradient step at extrapolated point
                    y1 = y1 + t * xp.fft.ifftn(xp.conj(otf_ch1) * r1).real
                    y2 = y2 + t * xp.fft.ifftn(xp.conj(otf_ch2) * r2).real

                    # enforce non-negativity 
                    y1 = xp.maximum(y1, 1e-6, dtype='float32')
                    y2 = xp.maximum(y2, 1e-6, dtype='float32')

                    #roll iterates forward
                    gamma1  = gamma2                   
                    xk1_old = xk1                      
                    xk2_old = xk2
                    xk1     = y1                       
                    xk2     = y2

            ch1_deconv[f] = xk1                       
            ch2_deconv[f] = xk2                       

        return ch1_deconv, ch2_deconv                 


    def give_name(self):
        return "Land-Weber Deconvolution"
