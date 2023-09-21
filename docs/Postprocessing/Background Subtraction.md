---
layout: default
title: Background Subtraction
parent: Postprocessing Components
nav_order: 4
---

# Background Subtraction

{: .note-title }
> Explanation:
/ChatGPT: Background correction, in the context of microscopy image processing, refers to a series of techniques used to 
remove or reduce the unwanted, non-biological signals from an image. Microscopy images often suffer from variations in 
llumination, sensor noise, or other artifacts, which can obscure or interfere with the relevant biological structures or 
features of interest. Background correction methods aim to enhance the quality and clarity of the image, allowing for 
more accurate and reliable analysis and interpretation.
ChatGPT/

We decided to use the background subtraction. 

{: .note-title }
> How it works:
The mean intensity of the background is measured in the first and in the last frame. Next, a linear interpolation is used
to estimate the mean intensity in the frames in between. The frame-specific mean value is then subtracted from the whole image.
The background was separated from the cells using a threshold function from skimage. 

{: .note-title }
> Example:
hier Bild einfügen vor und nach Background subtraction? 
