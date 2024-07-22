---
layout: default
title: Installation
parent: Getting Started
nav_order: 1
warning: true
---

# Installation
## without bioformats
- Install Python 3.10.0, following the instructions on the official website (https://www.python.org/downloads/release/python-3100/)
- Install Anaconda (https://docs.anaconda.com/free/anaconda/install/index.html)
- Install the latest git version via your terminal (see https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- In the terminal window, navigate to the folder where you want to save the required code. 
- Type ```git clone https://github.com/IPMI-ICNS-UKE/DARTS.git``` into the terminal window and press enter. The github repository should now be cloned to your local machine. Alternatively, download the .zip file on the github-page.
- In the terminal window, navigate to the subfolder "src/TDEntropyDeconvolution" inside the DARTS folder
- Type ```git clone https://github.com/IPMI-ICNS-UKE/TDEntropyDeconvolution``` to clone this module to your computer
- In the terminal window, create a conda environment DARTS: ```conda create --name DARTS```
- Activate the conda environment: ```conda activate DARTS```
- Install the necessary packages and their dependencies by executing this command in the terminal:

```
pip install matplotlib stardist trackpy tomli tensorflow alive-progress openpyxl pystackreg tkcalendar tomlkit simpleitk-simpleelastix
```
- Alternatively, install the packages separately (pip install <package>)

## with bioformats
This includes the [bioformats library](http://www.openmicroscopy.org/bio-formats/), which allows the import and processing of common microscopy imaging formats.

After running the steps in the section "without bioformats", follow these steps to install python-bioformats: 

1. Java Development Kit (JDK) needs to be installed. 
You can download the JDK from the official Oracle website or use OpenJDK. 
   
2. The `JAVA_HOME` environment variable needs to be set correctly to point to the directory of your JDK installation.
On Linux or MacOS you can set it temporarily with
```
   export JAVA_HOME=/path/to/your/jdk
```
On Windows, you'd set it via the System Properties > Environment Variables dialog. To point to a specific version:
Make sure to point to the correct version of jdk, since newer ones are not compatible. We tested successfully using v8. 

After installing the JDK and setting the environment variable correctly, execute the following code in the terminal while 
the conda environment "DARTS" is still activated:

```pip install python-bioformats```

### JDK installation on MacOS using homebrew

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

