# DARTS

![overview](/docs/assets/img/Figure_1_dart.png)

## About
**DARTS** is an integrated tool for the analysis of Ca<sup>2+</sup> microdomains in immune cells (Jurkat T cells, primary murine cells, NK).
For detailed information, see the [Documentation](https://ipmi-icns-uke.github.io/DARTS/).

It combines the following modules:

- Postprocessing
   - channel registration
   - background subtraction
   - cell detection and tracking
   - deconvolution
   - bleaching correction
   - ratio computation 
- Shape Normalization
- Hotspot Detection and Dartboard visualization (based on [2])



## Installation 
We recommend using [anaconda](https://www.anaconda.com/download) to install the necessary packages.

Download and install anaconda and python and either clone the DARTS code with 
``
git clone https://github.com/IPMI-ICNS-UKE/DARTS.git
``

or download the .zip file via the download button. Navigate to the folder containing the `DARTS.yml` file and run 

```
conda env create -f DARTS.yml
conda activate DARTS
```

in the command line. 

For more information regarding the installation, see the [Documentation](https://ipmi-icns-uke.github.io/DARTS/)


## Usage
1. Store raw image files in a source directory. All common microscopy image formats can be opened, e.g. ics- or tif-files. 
2. Run `python main.py` in the terminal/ shell/ powershell or IDE of your choice.
3. Enter relevant information in the GUI. 
4. If necessary, define the bead contacts for each cell of interest in each image file.

![Main](https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/3549d0d5-5f8d-4d47-bf8c-096202c99bb0)
![Bead contacts](https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/d145d44f-f154-4125-b15d-3b82a40c788a)



## License
This code runs under the Apache 2.0 license.

## References and Citing
If DARTS is useful for a project that leads to publication, please acknowledge DARTS by citing it.

[1]  DARTS: an open-source Python pipeline for Ca2+ microdomain analysis in live cell imaging data 

[2] Diercks BP, Werner R, Schetelig D, Wolf IMA, Guse AH. High-Resolution Calcium Imaging Method for Local Calcium Signaling. Methods Mol Biol. 2019;1929:27-39. doi: [https://doi.org/10.1007/978-1-4939-9030-6_3](https://doi.org/10.1007/978-1-4939-9030-6_3)

