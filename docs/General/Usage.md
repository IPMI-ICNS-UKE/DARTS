---
layout: default
title: Usage
parent: Getting Started
nav_order: 2
---

# Usage

After installing the necessary packages, activate the environment

``
conda activate DARTS
``

and then run

```
python main.py
```

Depending on the python versions you have installed, it might be `python3 main.py`.

This initiates the first GUI, prompting for general information. In the top left corner, you must specify whether the raw data is in dual-channel format (two channels in one file) or single-channel format (both channels separated in individual files), along with setting the source and results directories. An example of a source directory can be found below the GUI.

In the bottom left, provide measurement properties like scale (pixels per micron) and frame rate. This data is critical for accurate Calcium Microdomains measurements. Additionally, specifying the correct cell type is crucial as the internal calibration depends on it.

In the top right corner, input information regarding the post-processing pipeline, shape normalization, and analysis. It's essential to specify:

1. Whether registration should be calculated frame-by-frame (not recommended) or only in the first frame (recommended, refer to the 'Registration' section).
2. The choice of deconvolution algorithm (LR or TDE, consult the 'Deconvolution' section).
3. Selection of the appropriate bleaching correction algorithm (additive no fit, multiplicative simple ratio, biexponential fit additive).

In the bottom right corner, you can initiate or cancel the analysis.

<img width="1512" alt="Bildschirmfoto 2023-09-23 um 12 57 24" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/d0539670-6432-43ec-acae-b01217ed2021">

An example for a source directory: 

<img width="781" alt="Bildschirmfoto 2023-09-23 um 13 02 31" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/a3d4c9c8-2e88-4dd3-bdc1-d2867f152e5b">


Example image: 

<img width="622" alt="Bildschirmfoto 2023-09-23 um 13 03 31" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/bb34d520-e8b3-4ed9-8e63-849f2fcfa894">


After clicking on "Start", there will appear a GUI for each image file, so that the bead contacts can be defined. A bead contact is defined as the contact of a (stimulatory) with the cells of interest. Internally, it consists of (1) the bead contact time, e.g. frame 300 and (2) the bead contact position relative to the center of the cell, e.g. 1 o'clock or 12 o'clock. In order to define bead contacts, the user needs to enter information regarding each bead contact manually. Use the following procedure to define bead contacts: 

1. Have a look at the whole image sequence to identify bead contacts. Beads usually appear in the first couple seconds of the addition, depending on the time of addition. 
2. Click on "Bead contact position/time of bead contact" in the option menu below the "Add bead contact"-button. 
3. In the left channel, click on the bead contact site between the cell of interest and the bead. Alternatively, use the text field. In the example below, the bead contacts are marked with a yellow cross. The correct definition of the bead contact time and position is crucial for useful results.
4. Click on "Position inside cell" in the option menu.  
5. In the left channel, click on the cell, that interacts with the bead. Alternatively, you can type the coordinates in the text field. Ideally, you aim for the center. This will facilitate the assignment of the bead contact to the cell. In the example below, the cells of interest are marked with a red cross.
6. Repeat the steps 2. to 5. for each bead contact in the image sequence. 
7. Once you have described every bead contact for this measurement, click on the button in the bottom right ("continue with next image or processing, respectively"). Repeat the steps 1. to 7. for every following image file or file pair in case of single file setup.

<img width="1312" alt="Bildschirmfoto 2023-09-23 um 13 22 28" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/70ae4e82-609b-410f-9ff7-f39824f192b3">




