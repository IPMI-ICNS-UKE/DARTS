---
layout: default
title: Dartboards
parent: Analysis
nav_order: 2
---

# Dartboards
{: .note-title }
> Explanation:
This method was described earlier in Diercks et al. (2019). It aims to assign detected calcium microdomains to areas on 
a dartboard. it provides an easy-to-understand overview of the distribution of signals and allows to compare whole sets of
cells with each other. 

{: .note-title }
> How it works:
The position of each calcium microdomain is characterized by "centroid coordinates". Based on these coordinates and the position relative 
to the center (distance, angle) of the shape normalized image, the signals can be assigned to certain fields on the dartboard. To be able to
compare multiple cells with each other, we implemented (1) the shape normalization and (2) normalized the cell radii, so that 
signals close to the edge are always close to the dartboard's edge and not outside.
For further information, see Diercks et al. (2019).

{: .note-title }
> Example:
