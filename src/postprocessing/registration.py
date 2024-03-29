from alive_progress import alive_bar
import time
import numpy as np
from pystackreg import StackReg

try:
    import SimpleITK as sitk
except ImportError:
    print("SimpleITK cannot be loaded")
    sitk = None


class RegistrationBase:
    def __init__(self):
        pass


class Registration_SITK(RegistrationBase):
    def __init__(self):
        super().__init__()

    def channel_registration(self, channel1, channel2, framebyframe=True):

        print("\nRegistration of channel 1 and channel 2: ")
        channel2_registered = np.zeros_like(channel2)

        elastixImageFilter = sitk.ElastixImageFilter()
        elastixImageFilter.LogToConsoleOff()

        if framebyframe:
            with alive_bar(len(channel1), force_tty=True) as bar:
                for f in range(len(channel1)):
                    time.sleep(.005)
                    image_sitk = sitk.GetImageFromArray(channel1[f])
                    offset_image_sitk = sitk.GetImageFromArray(channel2[f])

                    elastixImageFilter.SetFixedImage(image_sitk)
                    elastixImageFilter.SetMovingImage(offset_image_sitk)
                    elastixImageFilter.SetParameterMap(sitk.GetDefaultParameterMap("affine"))

                    elastixImageFilter.Execute()
                    result_affine = elastixImageFilter.GetResultImage()
                    channel2_registered[f] = sitk.GetArrayFromImage(result_affine)
                    bar()
        else:
            image_sitk = sitk.GetImageFromArray(channel1[0])
            offset_image_sitk = sitk.GetImageFromArray(channel2[0])

            elastixImageFilter.SetFixedImage(image_sitk)
            elastixImageFilter.SetMovingImage(offset_image_sitk)
            elastixImageFilter.SetParameterMap(sitk.GetDefaultParameterMap("affine"))

            elastixImageFilter.Execute()
            result_affine = elastixImageFilter.GetResultImage()
            channel2_registered[0] = sitk.GetArrayFromImage(result_affine)

            transformParameterMap = elastixImageFilter.GetTransformParameterMap()

            with alive_bar(len(channel1), force_tty=True) as bar:
                for f in range(len(channel1)):
                    if f == 0:
                        pass
                    else:
                        time.sleep(.005)
                        offset_image_sitk = sitk.GetImageFromArray(channel2[f])
                        transformixImageFilter = sitk.TransformixImageFilter()
                        transformixImageFilter.SetLogToConsole(False)
                        transformixImageFilter.SetTransformParameterMap(transformParameterMap)
                        transformixImageFilter.SetMovingImage(offset_image_sitk)
                        transformixImageFilter.Execute()
                        result_affine = transformixImageFilter.GetResultImage()
                        channel2_registered[f] = sitk.GetArrayFromImage(result_affine)
                    bar()

        return channel2_registered


class Registration_SR(RegistrationBase):
    def __init__(self):
        super().__init__()

    def channel_registration(self, channel1, channel2, framebyframe=False):
        """
        Registration of the two channels based on affine transformation. The first channel is defined as the reference
        channel, the second one as the offset channel. A transformation matrix is calculated by comparing the first frame
        of each channel. The matrix is applied to each frame of the offset channel.
        Assumption: The offset remains constant from the first to the last frame.
        """
        print("Registration of channel 1 and channel 2: ")
        image = channel1[0]
        offset_image = channel2[0]
        sr = StackReg(StackReg.AFFINE)
        transformation_matrix = sr.register(image, offset_image)

        channel2_registered = np.zeros_like(channel2)

        for frame in range(len(channel2)):
            channel2_registered[frame] = sr.transform(channel2[frame], transformation_matrix)
        # self.channel2 = sr.transform(self.channel2, transformation_matrix)

        return channel2_registered
