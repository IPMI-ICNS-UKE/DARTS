---
layout: default
title: Background Subtraction
parent: Postprocessing Components
nav_order: 3
---

# Background Subtraction

## Explanation
Background signal can obscure or interefere with the relevant biological structures. That is why it is important to remove the background. Background correction methods aim to enhance the quality of the image. One possible method to correct the background is to apply a background subtraction algorithm, that we also used in our script. 


## How it works
The mean intensity of the background is measured in the first and in the last frame. Next, a linear interpolation is used
to estimate the mean background intensity in the frames in between. The frame-specific mean value is then subtracted from the whole image. To avoid integer-overflow, the maximum subtraction only sets pixels to zero instead of assigning very large values to the pixels. 

The background was separated from the cells using a threshold function from skimage. 
