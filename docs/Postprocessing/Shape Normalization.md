---
layout: default
title: Shape normalization
nav_order: 4
has_children: false
---


# Shape Normalization

This part of the program takes a cell of arbitrary (reasonably convex) shape and returns the same cell normalized onto a circle.

Crucial for this step is the correct segmentation of the cell outline, since this determines the transformation.

Our implementation was inspired by the approach used by [Möhl et. al 2012](https://doi.org/10.1242/jcs.090746).

