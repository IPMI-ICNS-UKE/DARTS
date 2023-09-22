---
layout: default
title: Dartboards
parent: Analysis
nav_order: 2
---

# Dartboards

## Explanation
This method was described earlier in Diercks et al. (2019). It aims to assign detected Calcium Microdomains to areas on 
a dartboard. It provides an easy-to-understand overview of the distribution of signals and allows to compare whole sets of
cells with each other. 

## How it works
In order to assign the detected signals to certain dartboard areas, the (1) relative distance of the signal from the centroid coordinates (of the frame) and (2) the angle relative to the centroid coordinates are measured. This enables to project each signal onto a normalized dartboard. Signals close to the edge are projected to an outer area on the dartbaord, for example. Preservation of the signal distribution requires the normalization of the signal information to the bead contact position. 
We chose the position "2 o'clock" as the normalized position. If a cell has the bead contact at 10 o'clock, for example, then all the signal information will be normalized to the contact site. 


## Illustration
