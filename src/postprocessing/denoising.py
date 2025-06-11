import gc
from .operation import *
from .sparse_iteration import *
import numpy as np
try:
    import cupy as cp
except ImportError:
    cupy = None
xp = np if cp is None else cp
if xp is not cp:
    warnings.warn("could not import cupy... falling back to numpy & cpu.")


class BaseDenoise:
    def execute(self, input_roi_channel1, input_roi_channel2, parameters):
        processed_roi_channel1, processed_roi_channel2 = self.denoise(input_roi_channel1, input_roi_channel2, parameters)
        return processed_roi_channel1, processed_roi_channel2

    def give_name(self):
        return "Base Denoising" 
    
    def denoise(self, input_roi_channel1, input_roi_channel2, parameters):
        return input_roi_channel1, input_roi_channel2


class SparseHessian(BaseDenoise):
    def __int__(self):
        super().__init__()
    
    def denoise(self, input_roi_channel1, input_roi_channel2, parameters):
        
        
        
        
        
        
        return 0
    
    def give_name(self):
        return "Sparse-Hessian Denoising"