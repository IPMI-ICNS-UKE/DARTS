import skimage.measure
import numpy as np
from skimage.filters import threshold_mean
import pywt
from abc import ABC, abstractmethod


class BaseBackgroundSubtractor(ABC):
    def execute(self, imgs, parameters=None):
        return self.subtract_background(imgs, parameters)

    @abstractmethod
    def subtract_background(self, imgs, parameters=None):
        """
        Algorithm‑specific background removal.
        Subclasses *must* override.
        """
        return imgs

    def give_name(self):
        return "...background subtraction..."


class BackgroundSubtractorMasked(BaseBackgroundSubtractor):
    def __init__(self, segmentation):
        self.segmentation = segmentation

    def clear_outside_of_cells(self, cells_with_bead_contact):
        for cell in cells_with_bead_contact:
            cell.set_image_channel1(self.set_background_to_zero(cell.frame_masks, cell.give_image_channel1()))
            cell.set_image_channel2(self.set_background_to_zero(cell.frame_masks, cell.give_image_channel2()))
            cell.ratio = self.set_background_to_zero(cell.frame_masks, cell.ratio)

    def set_background_to_zero(self, frame_masks, cell_image_series):
        """
        Set background in a given cell image series to zero using a series of boolean masks
        :param frame_masks:
        :param cell_image_series:
        :return: the background subtracted image series
        """
        frame_number = len(cell_image_series)
        copy = cell_image_series.copy()
        for frame in range(frame_number):
            copy[frame] = self.apply_masks_on_image_series(cell_image_series[frame], frame_masks[frame])
        return copy

    def apply_masks_on_image_series(self, image_series, masks):
        """
        Applies a mask onto an image and sets a copy of the image series to 0 if the mask is True at that position
        :param image_series:
        :param masks:
        :return:
        """
        copy = image_series.copy()
        for frame in range(len(image_series)):
            copy[frame][masks[frame]] = 0
        return copy

    def measure_mean_background_intensity(self, image_frame):
        threshold = round(threshold_mean(image_frame))
        not_background_label = skimage.measure.label(image_frame > threshold)
        not_background_label[not_background_label > 1] = 1
        background_label = 1 - not_background_label
        region = skimage.measure.regionprops(label_image=background_label,
                                                         intensity_image=image_frame)
        background_mean_intensity = round(region[0].intensity_mean)
        return background_mean_intensity

    def subtract_background(self, channel_image_series, parameters=None):

        # mean intensity of background in first frame
        mean_background_first_frame = self.measure_mean_background_intensity(channel_image_series[0])

        # mean intensity of background in last frame
        mean_background_last_frame = self.measure_mean_background_intensity(channel_image_series[len(channel_image_series)-1])

        # linear interpolation data
        frames = [0, len(channel_image_series)-1]
        subtrahends = [mean_background_first_frame, mean_background_last_frame]
        # plt.plot(frames, thresholds)

        background_subtracted_channel = channel_image_series.copy()
        for frame in range(len(channel_image_series)):
            subtrahend = round(np.interp(frame, frames, subtrahends))
            # for values <= subtrahend: set to 0
            copy = background_subtracted_channel[frame].copy()
            copy[copy <= subtrahend] = 0

            # for values > subtrahend
            copy[copy > subtrahend] -= subtrahend

            background_subtracted_channel[frame] = copy

        return background_subtracted_channel

    def give_name(self):
        return "Background Subtraction Masked"


class WaveletBackgroundSubtractor(BaseBackgroundSubtractor):
    """
    Wavelet-based per-pixel background estimator (refactored from the original
    procedural code).  Usage:

        wbs = WaveletBackgroundSubtractor(background_flag=3)
        clean = wbs.subtract_background(img_stack)          # (T, H, W) or (H, W)

    Parameters
    ----------
    background_flag : int {1, …, 5}
        Controls the pre-clipping strategy (see _precondition()).
    th : float
        Threshold term used in iterative clipping (default 1 → √|res| / 2).
    dlevel : int
        Wavelet decomposition level.
    wavename : str
        PyWavelets wavelet family name.
    max_iter : int
        Iterations of “estimate → clip bright outliers → re-estimate”.
    dtype : numpy dtype
        Working dtype for internal arrays (default float32).
    """

    def __init__(
        self,
        th: float = 1.0,
        dlevel: int = 7,
        wavename: str = "db6",
        max_iter: int = 3,
        dtype=np.float32,
    ):
        self.th = th
        self.dlevel = dlevel
        self.wavename = wavename
        self.max_iter = max_iter
        self.dtype = dtype


    def subtract_background(self, imgs, parameters):
        """
        Apply wavelet background removal.

        Parameters
        ----------
        imgs : ndarray
            Shape (H, W) or (T, H, W); any integer or float type.

        Returns
        -------
        ndarray
            Background-subtracted array with the same shape as `imgs`
            and dtype as given in constructor.
        """
        imgs = np.asarray(imgs, dtype=self.dtype)
        original_shape = imgs.shape
        is_stack = imgs.ndim == 3

        # Normalise 0-1 to get scale invariance (original code behaviour)
        scaler = np.max(imgs)
        if scaler == 0:
            return imgs.copy()  # blank input, nothing to do
        imgs = imgs / scaler

        # Pre-condition according to the chosen flag
        background_method = parameters["processing_pipeline"]["postprocessing"]["wavelet_algorithm"]
        imgs_pc = self._precondition(imgs, background_method)

        # Estimate background
        bg = self._background_estimation(imgs_pc)

        # Subtract and rescale back
        cleaned = imgs - bg
        cleaned = np.clip(cleaned, 0, None)  # keep non-negative
        cleaned *= scaler

        return cleaned.reshape(original_shape)

    
    #INTERNAL HELPERS
    def _precondition(self, img, background_method):
        """
        Implements the five branches of the original method1.
        Operates on a float32 array already normalised to [0, 1].
        """
        if background_method in (None, "", "None"):
            return img
        if background_method == "Weak-HI":
            return img / 2.5
        if background_method == "Strong-HI":
            return img / 2.0
        # flags 3-5: clip bright pixels before background estimation
        mean_val = np.mean(img)
        if background_method == "Weak-LI":
            clip_val = mean_val / 2.5
        elif background_method == "Strong-LI":
            clip_val = mean_val
        elif background_method == "Medium-HI":
            clip_val = img
        else:
            clip_val = mean_val / 2.0

        img_clipped = img.copy()
        img_clipped[img > clip_val] = clip_val
        return img_clipped

    #wavelet helpers
    @staticmethod
    def _low_freq_only(coeffs):
        """
        Return a coefficient tree in which all detail bands are zeroed
        **using each level's own shape**, so `pywt.waverec2` never sees
        mismatched array sizes.
        """

        vec = [coeffs[0]]  # keep cA_n

        for ch, cv, cd in coeffs[1:]:
            z = np.zeros_like(ch)       # template from *this* level
            vec.append((z, z, z))
        return vec

    @staticmethod
    def _trim_to_original(arr, target_shape):
        """
        PyWavelets may pad images when sizes are odd.  Trim to original shape.
        """
        return arr[: target_shape[0], : target_shape[1]]

    # main background estimator
    def _background_estimation(self, imgs):
        """
        Core of the algorithm; works for 2-D or 3-D stacks.
        """
        if imgs.ndim == 2:
            return self._background_single(imgs)
        # 3-D time stack
        t, h, w = imgs.shape
        bg = np.zeros_like(imgs)
        for idx in range(t):
            bg[idx] = self._background_single(imgs[idx])
        return bg

    def _background_single(self, img):
        """
        Estimate background for a single 2-D frame.
        """
        h, w = img.shape

        # Clamp the wavelet depth so the smallest sub‑band is at least 1×1
        max_lvl = pywt.dwt_max_level(min(h, w), pywt.Wavelet(self.wavename).dec_len)
        level = min(self.dlevel, max_lvl)

        res = img.copy()

        for _ in range(self.max_iter):
            coeffs = pywt.wavedec2(res, wavelet=self.wavename, level=level)
            vec = self._low_freq_only(coeffs)

            b_iter = pywt.waverec2(vec, wavelet=self.wavename)
            b_iter = self._trim_to_original(b_iter, (h, w))

            # Optional iterative clipping step
            if self.th > 0:
                eps = np.sqrt(np.abs(res)) / 2.0
                mask = img > (b_iter + eps)
                res[mask] = b_iter[mask] + eps[mask]
            else:
                break  # no clipping requested

        return b_iter.astype(self.dtype)

    def give_name(self):
        return "Background Subtraction Wavelet"