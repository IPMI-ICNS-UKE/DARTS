# DARTS
<p align="center">
  <img width="700" align="center" alt="image" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/f10a8e5d-6e71-49ef-82ab-0b9b4595fd74">
</p>

## About
**DARTS** is an integrated tool for the analysis of Ca<sup>2+</sup> microdomains in immune cells (Jurkat T cells, primary murine cells, NK).
For detailed information, see [Docs](https://ipmi-icns-uke.github.io/DARTS/).

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
For detailed information regarding the installation, see [Docs](https://ipmi-icns-uke.github.io/DARTS/)


## Usage
1. Store raw image files in a source directory. All common microscopy image formats can be opened, e.g. ics- or tif-files. 
2. Run python main.py
3. Enter relevant information in the GUI. 
4. If necessary, define the bead contacts for each cell of interest in each image file.

<img width="1512" alt="Bildschirmfoto 2023-09-14 um 12 13 52" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/c0630881-da3b-4d02-bfdf-600cfe94b608">
<img width="1312" alt="Bildschirmfoto 2023-09-14 um 12 17 14" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/4b3b2770-117b-4df9-a6b9-b1459899c80a">


## License 


## References and Citing
If DARTS is useful for a project that leads to publication, please acknowledge DARTS by citing it.

[1]  DARTS: an open-source Python pipeline for Ca2+ microdomain analysis in live cell imaging data 

[2] Diercks BP, Werner R, Schetelig D, Wolf IMA, Guse AH. High-Resolution Calcium Imaging Method for Local Calcium Signaling. Methods Mol Biol. 2019;1929:27-39. doi: [https://doi.org/10.1007/978-1-4939-9030-6_3](https://doi.org/10.1007/978-1-4939-9030-6_3)

