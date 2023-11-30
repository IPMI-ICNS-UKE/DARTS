---
layout: default
title: Usage
parent: Getting Started
nav_order: 2
---

# Usage

## Starting the script
After installing the necessary packages, activate the environment

``
conda activate DARTS
``

and then run

```
python main.py
```

Depending on the python versions you have installed, it might be `python3 main.py`.

## First GUI: Initial information
This initiates the first GUI, prompting for general information. In the top left corner, you must specify whether the raw data is in dual-channel format (two channels in one file) or single-channel format (both channels separated in individual files), along with setting the source and results directories. An example of a source directory can be found below the GUI.

In the bottom left, provide measurement properties like scale (pixels per micron) and frame rate. This data is critical for accurate Calcium Microdomains measurements. Additionally, specifying the correct cell type is crucial as the internal calibration depends on it.

In the top right corner, input information regarding the post-processing pipeline, shape normalization, and analysis. It's essential to specify:

1. Whether registration should be calculated frame-by-frame (not recommended) or only in the first frame (recommended, refer to the 'Registration' section).
2. The choice of deconvolution algorithm (LR or TDE, consult the 'Deconvolution' section).
3. Selection of the appropriate bleaching correction algorithm (additive no fit, multiplicative simple ratio, biexponential fit additive).

In the bottom right corner, you can initiate or cancel the analysis.
![Bildschirmfoto 2023-10-21 um 16 20 19](https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/49a83945-a0ea-4254-981b-fc4b600569e4)

An example for a source directory: 

<img width="781" alt="Bildschirmfoto 2023-09-23 um 13 02 31" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/a3d4c9c8-2e88-4dd3-bdc1-d2867f152e5b">


Example image: 

<img width="622" alt="Bildschirmfoto 2023-09-23 um 13 03 31" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/bb34d520-e8b3-4ed9-8e63-849f2fcfa894">

## Test file 
You can try out the script by yourself using the test file that was uploaded to the DARTS-Repo. You can find the file in the following folder: https://github.com/IPMI-ICNS-UKE/DARTS/tree/main/DARTS_test_file. 

The bottom cell has a bead contact at approximately frame 45: 

<img width="622" alt="Bildschirmfoto 2023-09-27 um 11 33 07" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/a6a07fa9-2d75-406f-8b29-f45fc27fe4e4">


## Definition of bead contacts 
After clicking on "Start", there will appear a GUI for each image file, so that the bead contacts can be defined. A bead contact is defined as the contact of a (stimulatory) with the cells of interest. Internally, it consists of (1) the bead contact time, e.g. frame 300 and (2) the bead contact position relative to the center of the cell, e.g. 1 o'clock or 12 o'clock. In order to define bead contacts, the user needs to enter information regarding each bead contact manually. Use the following procedure to define bead contacts: 

1. Have a look at the whole image sequence to identify bead contacts. Beads usually appear in the first couple seconds of the addition, depending on the time of addition. 
2. Click on "Bead contact position/time of bead contact" in the option menu below the "Add bead contact"-button. 
3. In the left channel, click on the bead contact site between the cell of interest and the bead. Alternatively, use the text field. In the example below, the bead contacts are marked with a yellow cross. The correct definition of the bead contact time and position is crucial for useful results.
4. Click on "Position inside cell" in the option menu.  
5. In the left channel, click on the cell, that interacts with the bead. Alternatively, you can type the coordinates in the text field. Ideally, you aim for the center. This will facilitate the assignment of the bead contact to the cell. In the example below, the cells of interest are marked with a red cross.
6. Repeat the steps 2. to 5. for each bead contact in the image sequence. 
7. Once you have described every bead contact for this measurement, click on the button in the bottom right ("continue with next image or processing, respectively"). Repeat the steps 1. to 7. for every following image file or file pair in case of single file setup.

![Bildschirmfoto 2023-10-21 um 16 30 45](https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/1ae79491-7ae9-49c6-a37c-3679a0590a82)


## Output of running the script 
After the definition of bead contacts, the script processes the image files by itself (postprocessing, shape normalization, analysis). Depending on the input data, this can take up to 
hours to complete. 

The output of the script consists of various files: 
1. for each image file, each detected cell image is saved as a ratio image and a corresponding normalized ratio image. If there have been detected Calcium microdomains in the cells, then the corresponding excel files will be saved to the same directories.
2. On the top layer of the results directory, you will find a text-file with all the defined bead contacts (Bead_contact_information.txt).
3. Based on the microdomain-measurement, you will find information regarding the number of responding cells (percentage of cells, that have at least one Calcium microdomain after the bead contact) and the mean amplitude of the responding cells (mean amplitude of the calcium signals in the responding cells)
4. In the Excel-file "microdomain_data", you can find the number of signals in each detected cell in each frame from 1 second before until 15s seconds after bead contact.
5. Finally, in the directory "Dartboards/Dartboard_data", you can find excel sheets for each detected cells, displaying the number of microdomains in each dartboard area and each frame (see below). These excel files can be used to generate dartboards (see section Analysis > Dartboards). 

Example for output:

<img width="788" alt="Bildschirmfoto 2023-09-23 um 13 51 10" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/1e14a989-5e52-48ce-bae4-9ec0a4cf9921">

Example for dartboard data table for one cell:

<img width="1119" alt="Bildschirmfoto 2023-09-23 um 13 52 43" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/92ca8474-bb14-4c83-8e60-49cecbc46b31">
