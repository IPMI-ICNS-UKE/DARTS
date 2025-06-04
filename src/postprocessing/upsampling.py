import warnings
import numpy as np
try:
    import cupy as cp
except ImportError:
    cp = None

xp = np if cp is None else cp
if xp is not cp:
    warnings.warn("CuPy not found – running on CPU / NumPy.", RuntimeWarning)


# ---------------------------------------------------------------------
# 2.  Helper functions
# ---------------------------------------------------------------------
def spatial_upsample(stack: xp.ndarray, n: int = 2) -> xp.ndarray:
    """
    Insert (n−1) zero rows/cols between existing pixels.
    Equivalent to `scipy.signal.upfirdn` with a Dirac kernel.
    """
    stack = xp.asarray(stack, dtype=stack.dtype, order="C")

    if stack.ndim == 2:
        sx, sy = stack.shape
        out = xp.zeros((sx * n, sy * n), dtype=stack.dtype)
        out[0:sx * n:n, 0:sy * n:n] = stack
        return out

    elif stack.ndim == 3:
        t, sx, sy = stack.shape
        out = xp.zeros((t, sx * n, sy * n), dtype=stack.dtype)
        out[:, 0:sx * n:n, 0:sy * n:n] = stack
        return out

    else:                
        raise ValueError("Input must be 2-D or 3-D (frames × X × Y).")


def fourier_upsample(stack: xp.ndarray, n: int = 2) -> xp.ndarray:
    """
    FFT zero-padding interpolation.
    Produces a smooth image that preserves original frequency content.
    """
    stack = xp.asarray(stack, dtype=stack.dtype, order="C")

    add_axis = False
    if stack.ndim == 2:
        stack = stack[None, ...]
        add_axis = True

    t, sx, sy = stack.shape
    out = xp.empty((t, sx * n, sy * n), dtype=stack.dtype)

    pad_x = (sx * n - sx) // 2
    pad_y = (sy * n - sy) // 2

    for i in range(t):
        f = xp.fft.fftshift(xp.fft.fftn(stack[i]))
        fpad = xp.pad(f, ((pad_x, pad_x), (pad_y, pad_y)), mode="constant")
        out[i] = xp.real(xp.fft.ifftn(xp.fft.ifftshift(fpad)))

    return out[0] if add_axis else out

class BaseUpsample:
    """Boiler-plate wrapper so the pipeline can treat upsampling like deconvolution."""

    def execute(self, input_roi_channel1, input_roi_channel2, parameters):
        out1, out2 = self.upsample(input_roi_channel1,
                                   input_roi_channel2,
                                   parameters)
        return out1, out2

    def upsample(self, input_roi_channel1, input_roi_channel2, parameters):
        return input_roi_channel1, input_roi_channel2

    def give_name(self):
        return "...upsampling..."


class SpatialUpsampling(BaseUpsample):
    """Zero-insertion upsampling (fast, keeps exact pixel values)."""

    def upsample(self, input_roi_channel1, input_roi_channel2, parameters):
        n = parameters['processing_pipeline']['postprocessing'].get(
            'upsample_factor', 2)
        return (spatial_upsample(input_roi_channel1, n),
                spatial_upsample(input_roi_channel2, n))

    def give_name(self):
        return "Spatial Upsampling"


class FourierUpsampling(BaseUpsample):
    """FFT zero-padding upsampling (smooth, preserves frequency content)."""

    def upsample(self, input_roi_channel1, input_roi_channel2, parameters):
        n = parameters['processing_pipeline']['postprocessing'].get(
            'upsample_factor', 2)
        return (fourier_upsample(input_roi_channel1, n),
                fourier_upsample(input_roi_channel2, n))

    def give_name(self):
        return "Fourier Upsampling"
