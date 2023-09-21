---
layout: default
title: ROI Selection
parent: Postprocessing Components
nav_order: 5
---

# **ROI Selection**

{: .note-title }
> General information:

Defining regions of interest in microscopy images can be a time-consuming process. In order to automate this 
step, we decided to combine the advantages of (1) automated cell segmentation and (2) cell tracking over time. 

{: .note-title }
> How it works:

The cells are segmented in each frame of the microscopy images using the StarDist-algorithm for star-convex objects. We apply 
a pretrained model for the detection of nuclei in fluorescence images that can be transferred to the cell detection. 
For each cell label in each frame, relevant data is measured (coordinates, edge, bounding box, ...) by the skimage.regionprops 
function. 
The trackpy-package is used to connect the cell labels in each frame so that each cell will later consist of a time series 
of cell images in both channels. 


{: .note-title }
> Example:


<br>
<br>

{: .note-title }
> References:

For segmentation, we use **[StarDist](https://github.com/stardist/stardist)**

For cell tracking, we use **[Trackpy](http://soft-matter.github.io/trackpy/v0.6.1/)**