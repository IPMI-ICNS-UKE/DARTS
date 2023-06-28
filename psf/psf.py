from TDE.operators import Operator
import numpy as np

class PSF(Operator):

    def __init__(self,  dims, **params):
        super().__init__(dims)
        if len(params) == 0:
            self.data = np.zeros(dims)
        else:
            self.data = self.point_spread_function(**params)

    def point_spread_function(self, type, lambdaEx, lambdaEm, numAper, magObj, rindexObj, \
                              ccdSize, dz, xysize, nslices, **kwargs):
        """
        Generate the point-spread function for a widefield microscope using a
        scalar diffraction-limited model (Stokseth refer to [1] and [3] below)
        References:
        ----------
        [1] P. A. Stokseth (1969). `Properties of a defocused optical system?.
        J. Opt. Soc. Am. A 59:1314?1321.
        [2] P. Pankajakshan, et al. (2010). `Point-spread function model for
        fluorescence macroscopy imaging?. In Proc. of Asilomar Conference on
        Signals, Systems and Computers.
        [3] P. Pankajakshan (2009). Blind Deconvolution for Confocal Laser
        Scanning Microscopy. Ph.D. thesis, Universit? de Nice Sophia-Antipolis.
        ----------
        Original matlab function:
        Author: Praveen Pankajakshan
        Email: praveen.pankaj@gmail.com
        Last modified: June 24, 2011 17:21
        Copyright (C) 2011 Praveen Pankajakshan

        :param type: microscopy type, either "confocal" or "widefield"
        :param lambdaEx: Excitation Wavelength (in nm)
        :param lambdaEm: Emission wavelength (in nm)
        :param numAper: Numerical aperture of the objective
        :param magObj: Objective total magnification
        :param rindexObj: Refractive index of the objective immersion medium
        :param ccdSize: Pixel dimension of the CCD (in the plane of the camera)
        :param dz: Optical axis Z sampling or defocusing (in nm)
        :param xysize: Size of the desired image (specimen view size/pixel dimension)
        :param nslices: Number of slices desired (Depth view/Z axis sampling)
        :param kwargs:
        depth: depth of the specimen under the cover-slip in nm
        rindex_sp: Refractive index of the specimen medium
        nor: Normalization on the PSF (default: no normalization)
             0: l-infinity normalization
             1: l-1 normalization
        :return:
        """

        # calculation of size size in the plane of the specimen
        dxy = ccdSize / magObj

        if "depth" not in kwargs or "rindexSp" not in kwargs:
            print("Refractive index of specimen or the imaging" \
                  " depth is missing. Assuming no spherical aberration.")
            rindexSp = rindexObj
            depth = 0
        else:
            rindexSp = kwargs["rindexSp"]
            depth = kwargs["depth"]

        if "nor" in kwargs:
            nor = kwargs["nor"]
        else:
            nor = 0  # default no normalization on the PSF

        psfEx = self.aberratedpsf(type, lambdaEx, numAper, rindexObj, dxy, dz, \
                             xysize, nslices, rindexSp, depth, mode='illumination')
        psfEm = self.aberratedpsf(type, lambdaEm, numAper, rindexObj, dxy, dz, \
                             xysize, nslices, rindexSp, depth, mode='emission')

        psf = psfEx * psfEm
        psf[np.argwhere(np.isnan(psf))] = np.finfo(float).eps

        if nor == 0:
            psf = psf / np.sum(psf)
        elif nor == 1:
            psf = psf / np.max(psf)

        if nslices == 1:
            psf = psf[:, :, 0]

        return psf

    def aberratedpsf(self, type, lamb, numAper, rindexObj, dxy, dz, \
                     xysize, nslices, rindexSp, depth, **kwargs):

        # initializing
        pupil = np.zeros((xysize, xysize))
        psf = np.zeros((xysize, xysize, nslices))

        N = xysize / 2
        n = nslices / 2

        # Pupil space size dimensions dkx, dky
        dkxy = (2 * np.pi) / (xysize * dxy)

        # Calculate the defocus
        defocus = np.linspace(-n, n - 1, num=nslices, endpoint=True) * dz
        # defocus = (-n:(n-1))*dz

        # Calculated the wavelength of light inside the objective lens and specimen
        lambdaObj = lamb / rindexObj
        lambdaSp = lamb / rindexSp

        # Calculate the wave vectors in vaccuum, objective and specimens
        k0 = 2 * np.pi / lamb
        kObj = 2 * np.pi / lambdaObj
        kSp = 2 * np.pi / lambdaSp

        # Radius of the pupil function disk
        # kMax = 4*xysize*((dxy*numAper)/lamb)^2;
        kMax = (2 * np.pi * numAper) / (lamb * dkxy)
        # Generate the pupil function amplitude
        kxcord = np.transpose(np.linspace(1, xysize, num=xysize)) - N - 1  # Setting N+1 as the center of the pupil
        kycord = kxcord
        [kx, ky] = np.meshgrid(kxcord, kycord)
        k = np.sqrt(kx ** 2 + ky ** 2)
        pupil = (k < kMax)

        # Calculate the sine of the semi-aperture angle in the objective lens
        sinthetaObj = (k * (dkxy)) / kObj
        sinthetaObj[sinthetaObj > 1] = 1
        # Calculate the cosine of the semi-aperture angle in the objective lens
        costhetaObj = np.finfo(float).eps + np.sqrt(1 - (sinthetaObj ** 2))

        # Calculate the sine of the semi-aperture angle in the specimen
        sinthetaSp = (k * (dkxy)) / kSp
        sinthetaSp[sinthetaSp > 1] = 1
        # Calculate the cosine of the semi-aperture angle in the specimen
        costhetaSp = np.finfo(float).eps + np.sqrt(1 - (sinthetaSp ** 2))

        # Defocus Phase calculation
        phid = (1.j * kObj) * costhetaObj
        # Spherical aberration phase calculation
        phisa = (1.j * k0 * depth) * ((rindexSp * costhetaSp) - (rindexObj * costhetaObj))
        # Calculate the optical path difference due to spherical aberrations
        OPDSA = np.exp(phisa)

        if "mode" in kwargs:
            mode = kwargs["mode"]
            # Apodizing the pupils for excitation and emission
            if mode == "illumination":
                pupil = (pupil * np.sqrt(costhetaObj))  # for illumination
            elif mode == "emission":
                pupil = (pupil / np.sqrt(costhetaObj))  # for emission
            else:
                print("invalid mode")
                return

        for zk in range(nslices):
            OPDDefocus = np.exp(defocus[zk] * phid)
            pupilDefocus = pupil * OPDDefocus
            pupilSA = pupilDefocus * OPDSA
            # Calculate the coherent PSF by using inverse Fourier Transform
            tmp = np.fft.ifft2(pupilSA)
            # Calculate the incoherent PSF from the coherent PSF
            psf[:, :, zk] = np.fft.fftshift(np.abs(tmp) ** 2)

        if type == "widefield":
            psf = np.sqrt(psf)
        return psf
