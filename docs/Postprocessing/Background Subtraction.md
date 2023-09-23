---
layout: default
title: Background Subtraction
parent: Postprocessing
nav_order: 3
---

# Background Subtraction

## Explanation
Background signal can obscure or interefere with the relevant biological structures. That is why it is important to remove the background. Background correction methods aim to enhance the quality of the image. One possible method to correct the background is to apply a background subtraction algorithm, that we also used in our script. 


## How it works
The mean intensity of the background is measured in the first and in the last frame. Next, a linear interpolation is used
to estimate the mean background intensity in the frames in between. The frame-specific mean background value is then subtracted from the whole image. In order to avoid integer-overflow, the maximum subtraction only sets pixels to zero. Otherwise, the subtraction could result in very large intensity values, if the subtrahend > pixel value. 

The background was separated from the cells using a threshold function from skimage and creating a mask for the background. In the next step, the mean intensity was measured with the regionprops-function. 

## Example
A channel image before background subtraction: 

<img width="640" alt="Bildschirmfoto 2023-09-23 um 12 30 44" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/8aeab7f7-6dcc-4291-ac15-79053f0550b2">


The same image, but after background subtraction: 

<img width="638" alt="Bildschirmfoto 2023-09-23 um 12 30 04" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/12eb0c41-03cd-4e66-b6b3-711d0cb62f8d">

