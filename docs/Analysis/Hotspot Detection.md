---
layout: default
title: Hotspot Detection
parent: Analysis
nav_order: 1
---

# Hotspot Detection

## Explanation
Calcium microdomains are defined as "small, compact connected sets of pixels with high [Ca2+] values." (Diercks et al., 2019). Each cell image series consists of multiples frames or ratio images. The threshold for the detection of Calcium Microdomains is based on the cell type and the frame-specific mean ratio value (Diercks et al., 2019). Every pixel surpassing the threshold value is considered as a potential member of a connected set of pixels (hotspot). If the area of connected pixels is within a certain range (e.g. 4 to 20 pixels), then a hotspot has been detected.  

## Illustration 
This ratio image shows hotspots in the center. 

<img width="576" alt="Bildschirmfoto 2023-09-22 um 14 14 10" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/1b7b1a2d-f11b-48e4-9f7d-14ca8683f05d">

For illustration purposes, the following image shows the potential Calcium microdomains after application of an arbitrary signal threshold. 
<img width="576" alt="Bildschirmfoto 2023-09-22 um 14 14 24" src="https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/bd61822a-f20f-44d7-b701-e51ac5fd5639">

Some of these hotspots might be considered as Calcium Microdomains based on their area, others might be excluded. 

