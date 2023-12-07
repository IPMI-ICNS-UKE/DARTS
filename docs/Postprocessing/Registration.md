---
layout: default
title: Registration
parent: Postprocessing
nav_order: 2
---

# **Registration**

## What is registration?

Image registration involves estimating a transformation that aligns points from one image to their corresponding points
in another image. This transformation establishes a mapping between the coordinate systems of the fixed and moving 
images. In the context of fluorescence microscopy, image registration is relevant because in dual-channel imaging, the channels often are not aligned perfectly. This could cause unwanted alterations of the signal. 
<br>
<br>


## What kind of approaches exist?

Various approaches exist for image registration, including:
- feature-based methods
- intensity-based methods 
- phase correlation
- elastic registration 
- affine registration 
- non-affine registration
<br>


## Which approach did we use?

Since we are working with low signal-to-noise ratio images, feature based methods may be less effective 
because the presence of noise can affect the detection and matching of distinct features and can therefore 
lead to suboptimal registration results.

We utilized the **[SimpleITK](https://simpleitk.readthedocs.io/en/master/about.html)** Python package that was installed 
with **`pip install SimpleITK`**.
SimpleITK, built on top of ITK (Insight Segmentation and Registration Toolkit), is an open-source library. 
SimpleITK offers a user-friendly interface for common operations such as filtering, registration, segmentation, 
and feature extraction.
In the context of registration, it offers different types type of transformations, global and local ones.
The available transformations are listed [here](https://simpleitk.readthedocs.io/en/master/registrationOverview.html).
We applied the `affine` transformation to define the mapping between images.

Below, you can find an example image. As shown, SITK with affine transformation works really well on our low signal-to-noise
ratio images:

![sitk_registration_example](https://github.com/IPMI-ICNS-UKE/DARTS/assets/127941319/058d7b73-0ea2-44f7-8ed7-571b6872576e)


We offer the user the option to choose whether to employ the registration method frame by frame or not. As the latter option 
is much more time-efficient and provides good results, we recommend not to use the registration frame-by-frame. Instead, 
letting the script calculate the transformation in the first frame and using it for the following frames is recommended.

For more code details, please visit our [Github page](https://github.com/IPMI-ICNS-UKE/T-DARTS/blob/main/postprocessing/registration.py)
