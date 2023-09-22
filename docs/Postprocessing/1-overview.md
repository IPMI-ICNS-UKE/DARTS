---
layout: default
title: Overview
parent: Postprocessing Components
nav_order: 1
---

# Overview

After the acquisition of microscopy data, the raw image files need to be processed to enable further analysis. We 
implemented a postprocessing pipeline based on [1], but with a modified order. The pipeline consists of: 
- Registration / Channel alignment
- Background subtraction
- Segmentation / Cell tracking 
- Deconvolution
- Bleaching correction 
- First median filter
- generation of ratio images
- Second median filter
- clear images outside the cells (set to 0)


<br>
<br>

[1] High-Resolution Calcium Imaging Method for Local Calcium Signaling
