---
layout: home
title: Welcome
nav_order: 1
---

# **DARTS**: <br> **An open-source Python pipeline for Ca2+ microdomain analysis in live cell imaging data**

<br>
<br>

## General Information

DARTS is a pipeline for Ca2+ microdomain analysis in live cell imaging data written in Python 3 by Lena-Marie Woelk, Dejan Kovacevic, Hümeyra Husseini and Fritz Förster.
For support, please open an [issue](https://github.com/IPMI-ICNS-UKE/DARTS/issues) or contact us directly.

This pipeline is part of the sfb1328 [A02 project](https://www.sfb1328.de/index.php?id=29). 


[View it on GitHub](https://github.com/IPMI-ICNS-UKE/DARTS){: .btn .btn-outline }
<br>
<br>


## Program Structure

![overview](/assets/img/Figure_1_dart.png)

The pipeline can be roughly divided into three parts:

1. [Postprocessing Components]({% link Postprocessing/Postprocessing Components.md %}#Postprocessing Components)
2. [Shape normalization]({% link Postprocessing/Shape Normalization.md %}#Shape Normalization)
3. [Analysis]({% link Analysis/Analysis.md %}#Analysis)

### General postprocessing

These components include segmentation and cell tracking to identify regions of interest (ROI), image improvement by bleaching 
correction, deconvolution and denoising, background subtraction and ratiometric image handling, i.e. registration of two input channels
and ratio computation.

### Shape Normalization

This part normalizes arbitrary cell shapes (within certain convexity constraints) onto a circle with a well-defined radius
to facilitate comparison of Ca2+ microdomains across multiple cells with differing morphologies.

### Analysis

The normalized cells are then analyzed to detect Ca2+ hotspots and the results given as data tables and visualized either on an
individual basis or across multiple cells on a dartboard shape, where hotspot frequency and location can be analyzed for different time
frames.



