---
layout: default
title: Hotspot Detection
parent: Analysis
nav_order: 1
---

# Hotspot Detection

{: .note-title }
> Explanation:
Calcium microdomains are defined as "small, compact connected sets of pixels with high [Ca2+] values." (Diercks et al., 2019).

{: .note-title }
> How it works:
The average value is calculated for each image of the ratio image series. Based on this value, a  threshold value for 
distinguishing noise from signal can be calculated(Diercks et al., 2019). 
Groups of connected pixels with a pixel value higher than the threshold are considered calcium microdomains. The area
must lie within a certain range.

{: .note-title }
> Example:



