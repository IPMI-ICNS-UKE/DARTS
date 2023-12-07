---
layout: default
title: Installation
parent: Getting Started
nav_order: 1
warning: true
---

# Installation

We recommend using [anaconda](https://www.anaconda.com/download) to install python and the necessary packages.
Make sure to install correctly and to include the correct python executable in your path. 
For more information, see for example [here](https://docs.anaconda.com/free/anaconda/install/index.html).


Make sure git is installed on your system, then clone the repository by running 

``
git clone https://github.com/IPMI-ICNS-UKE/DARTS.git
``

in your command line.

## Installation with bioformats

Verify you are in the folder containing the `DARTS.yml` file and run 

```
conda env create -f DARTS.yml
conda activate DARTS
```

This includes the [bioformats library](http://www.openmicroscopy.org/bio-formats/), which allows processing of common microscopy imaging formats.

For this, the following prerequisites also need to be fulfilled:
1. Java Development Kit (JDK) needs to be installed. 
You can download the JDK from the official Oracle website or use OpenJDK. 
   
2. The `JAVA_HOME` environment variable needs to be set correctly to point to the directory of your JDK installation.
On Linux or MacOS you can set it temporarily with
```
   export JAVA_HOME=/path/to/your/jdk
```
On Windows, you'd set it via the System Properties > Environment Variables dialog. To point to a specific version:
Make sure to point to the correct version of jdk, since newer ones are not compatible. We tested successfully using v8. 

### Complete example installation on MacOS using homebrew

As an example, we provide here a step-by-step guide to install the java dependencies for bioformats using [homebrew](https://brew.sh/).

We were successfull using v8 of JDK. Install it by running

```
   brew install adoptopenjdk/openjdk/adoptopenjdk8
```

You can check which versions of Java you have installed by running 
```
/usr/libexec/java_home -V
```
To set JAVA_HOME for a particular version, you can use the following 
```
export JAVA_HOME=$(/usr/libexec/java_home -v 8)
```
Or add the above line to your shell configuration file (e.g., ~/.bashrc, ~/.bash_profile, ~/.zshrc) to make the change persistent across sessions.

Alternatively, you can install `jenv` to switch between java versions.

Install by 
```
brew install jenv
```
Then integrate into shell (Use ~/.zshrc if you're using the Zsh shell.)
```
echo 'export PATH="$HOME/.jenv/bin:$PATH"' >> ~/.bash_profile
echo 'eval "$(jenv init -)"' >> ~/.bash_profile
source ~/.bash_profile
```

Add java versions to `jenv`
```
jenv add $(/usr/libexec/java_home -v 8)
```
Now you can switch with 
```
jenv global 8
```

## Installation without bioformats

If the image data you are working with is in `.tif` format, or you convert it beforehand, for example using ImageJ,
you don't need to install bioformats and java. In this case, install the packages by 

``
conda env create -f DARTS_without_bioformats.yml
conda activate DARTS
``