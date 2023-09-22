---
layout: default
title: Dartboards
parent: Analysis
nav_order: 2
---

# Dartboards

## Explanation
This method was described earlier in Diercks et al. (2019). It aims to assign detected Calcium Microdomains to areas on 
a dartboard. It provides an easy-to-understand overview of the distribution of signals and allows to compare whole sets of
cells with each other. 

## How it works
In order to assign the detected signals to certain dartboard areas, the (1) relative distance of the signal from the centroid coordinates (of the frame) and (2) the angle relative to the centroid coordinates are measured. This enables to project each signal onto a normalized dartboard. Signals close to the edge are projected to an outer area on the dartbaord, for example. Preservation of the signal distribution requires the normalization of the signal information to the bead contact position. 
We chose the position "2 o'clock" as the normalized bead contact position. If a cell has the bead contact at 10 o'clock, for example, then all the signal information will be normalized to the contact site, so that superposition of multiple information from different cells and frames leads to a correct dartboard representation. 


## Illustration
24 cells have been processed with our pipeline. For each cell and frame, there is a dartboard representation that is normalized to the specific bead contact site of the cell. All the dartboard information for the frames within the first 5 seconds after bead contact were cumulated and divided by 5 to obtain the mean number and distribution of signals within the first 5 seconds. 
<br>
![example_dartboard](https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/b1753f83-e811-49e9-834b-4d7aa9f6940d)
<br>
## Representation and usage 
After running the script, you can find Excel-files for each cell saved on your computer. 
<br>
<img width="788" alt="Bildschirmfoto 2023-09-22 um 14 36 26" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/57df4af1-342f-4710-bfac-4a08ea962391">
<br>
The Excel files contain information for each frame and each dartboard area, leading to a 2D-Matrix/table. 
<br>
<br>
Example: 
<br>
<br>
<img width="1040" alt="Bildschirmfoto 2023-09-22 um 14 35 53" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/e806567c-7c10-4114-a0eb-6a2341d62b30">
<br>

Based on this, you can create various dartboards depending on (1) the chosen time interval (e.g. bead contact (0 seconds) to 5 seconds after bead contact) and (2) the selected subset of cells.  
After running the main-script, you need to run the script "DartboardPlotGUI.py" in order to create your dartboards. You can either choose the "per-frame"- or the "per-second"-representation. 
<br>
<img width="812" alt="Bildschirmfoto 2023-09-22 um 14 40 34" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/815f002d-aac1-439a-8c1c-b14442b06a26">




