---
layout: default
title: Segmentation/ Cell tracking
parent: Postprocessing Components
nav_order: 4
---

# Segmentation/ Cell tracking (ROI Selection)

## Motivation 
Defining regions of interest in microscopy images can be a time-consuming process. In order to automate this 
step, we decided to combine the advantages of (1) automated cell segmentation and (2) cell tracking over time. 

## How it works

The cells are segmented in each frame of the microscopy images using the StarDist-algorithm for star-convex objects. The segmentation creates labels for each detected cell. 
For each cell label in each frame, relevant data is measured (coordinates, edge, bounding box, ...) by the skimage.regionprops 
function. 
The trackpy-package is used to connect the cell labels in each frame so that each cell will later consist of a time series 
of cell images in both channels. Variables such as the memory, the maximum positional alteration between two frames and others can be modified by the user.  
After identifying the cells, the cell-specific information regarding the position and the bounding boxes are used to crop an image series out of the channel images (same size as raw data). 
Because of the fact, that in our case, the beads are mostly prominent in the first channel, we apply the cell selection algorithm only on the seconds channel. After that, the bounding boxes for cell cropping can be used in the first channel as well.   

## Example

<img width="284" alt="Stardist_illustration" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/5238fb3d-73c6-496a-9cc4-a67719487b90">

<br>
<br>

## References

For segmentation, we use **[StarDist](https://github.com/stardist/stardist)**

For cell tracking, we use **[Trackpy](http://soft-matter.github.io/trackpy/v0.6.1/)**
