---
layout: default
title: Bleaching Correction
parent: Postprocessing Components
nav_order: 2
---

# **Bleaching Correction**

<br>
<br>

{: .note-title }
> General information

Photobleaching is a common problem in fluorescence microscopy. It leads to a gradual decrease in 
fluorescence signal intensity over time and results in intensity decay, loss of information and - if not corrected - to 
false interpretations. Therefore it is crucial to compensate for signal intensity loss.
<br>
<br>

{: .note-title }
> Background information

There are several Bleaching correction approaches.
In the framework of this project, we work on **calcium microdomains** (see reference paper: [Diercks et al. - 2019 - 
High-resolution calcium imaging method for local calcium signaling](https://pubmed.ncbi.nlm.nih.gov/30710265/)). 

This program was developed to automatically process calcium imaging data. Similar to the aforementioned reference paper,
we carry out an **additive frame-by-frame bleaching correction** algorithm. Local calcium imaging employs the two dyes 
Fura-Red and Fluo-4. Given the negligible bleaching of Fluo-4 in comparison to Fura-Red, only the bleaching 
characteristics of Fura-Red are considered.
<br>
<br>

{: .note-title }
> Bleaching Algorithm: Pseudocode

Here is an exemplified code of the bleaching correction:

```markdown
# ref_i: reference image series (Fura_Red)
reference_mean_intensity = measure_mean_intensity(ref_i[frame_0])
for frame_n in ref_i:
    mean_intensity = measure_mean_intensity(ref_i[frame])
    difference = reference_mean_intensity - mean_intensity
    for pixel in ref_i[frame_n]:
        if pixel_value > 0:
            pixel_intensity += difference
```
<br>
<br>

{: .note-title }
> Example of a bleaching corrected intensity timeline:

Blue = correction <br>
Red = without correction

![Bleaching correction image](/assets/img/Bleaching_correction.PNG)