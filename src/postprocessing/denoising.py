import gc
from .denoising_utils.sparse_hessian import sparse_hessian
import numpy as np
import warnings

try:
    import cupy as cp
except ImportError:
    cp = None
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

        iters = 100
        fidelity = 150
        sparsity = 10
        contiz = 0.5
        mu = 1
        
        out1 = np.empty_like(input_roi_channel1, dtype=float)
        out2 = np.empty_like(input_roi_channel2, dtype=float)

        is_stack = input_roi_channel1.ndim == 3

        if is_stack:
            # process every frame (time index) independently
            for f in range(input_roi_channel1.shape[0]):
                out1[f] = sparse_hessian(
                    input_roi_channel1[f].astype(float),
                    iteration_num=iters,
                    fidelity=fidelity,
                    sparsity=sparsity,
                    contiz=contiz,
                    mu=mu,
                )
                out2[f] = sparse_hessian(
                    input_roi_channel2[f].astype(float),
                    iteration_num=iters,
                    fidelity=fidelity,
                    sparsity=sparsity,
                    contiz=contiz,
                    mu=mu,
                )
        else:
            # single frame: call once
            out1 = sparse_hessian(
                input_roi_channel1.astype(float),
                iteration_num=iters,
                fidelity=fidelity,
                sparsity=sparsity,
                contiz=contiz,
                mu=mu,
            )
            out2 = sparse_hessian(
                input_roi_channel2.astype(float),
                iteration_num=iters,
                fidelity=fidelity,
                sparsity=sparsity,
                contiz=contiz,
                mu=mu,
            )
        
        if xp is not np:
            out1 = cp.asnumpy(out1)
            out2 = cp.asnumpy(out2)

        return out1, out2    

    
    def give_name(self):
        return "Sparse-Hessian Denoising"
    
