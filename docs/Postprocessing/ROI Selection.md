---
layout: default
title: Segmentation/ Cell tracking
parent: Postprocessing
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
Because of the fact, that in our case, the beads are mostly prominent in the first channel, we apply the cell selection algorithm only onto the second channel. After that, the bounding boxes can be used in the first channel for cropping out the cells, too.   

## Example

In each frame, the StarDist-algorithm tries to detect cells and creates a labelled image: 

<img width="635" alt="Bildschirmfoto 2023-09-23 um 12 48 59" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/336b00f0-f3e2-442d-9c71-1f839b578284">

The trackpy algorithm associates labels, enabling the generation of cell traces that can then be used to crop individual cell images from each frame, resulting in a series of smaller images for each cell.

<img width="635" alt="Bildschirmfoto 2023-09-23 um 12 48 09" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/c16b584d-945c-4c70-8c97-fde1d6c52dcc">


## References

For segmentation, we use **[StarDist](https://github.com/stardist/stardist)**

For cell tracking, we use **[Trackpy](http://soft-matter.github.io/trackpy/v0.6.1/)**
