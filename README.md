# IGM Paleo Glacier Model

## Overview
This project contains the resources necessary for running the world wide IGM Paleo Glacier  model. The [Instructed Glacier Model (IGM)](https://github.com/jouvetg/igm) is a machine learning glacier model that can run very fast on GPU's. Here we use custom modules to download and use paleo-climate data with the IGM model. Required dependencies and installation steps are described in detail below.
## Background
IGM is well suited to grab glacier data from the Randolph Glacier Inventory and adding available climate/mass balance and topography data. This is mostly focused towards recent and  future projections. Here we load paleo data and use them in a custom module:

   - [**Chelsa**](https://chelsa-climate.org) with [**PBCOR**](https://www.gloh2o.org/pbcor/): Paleo climate data
   - [**GEBCO**](https://www.gebco.net/): Topography data
   - [**EPICA**](https://doi.pangaea.de/10.1594/PANGAEA.683655): Ice core data and delta T as a proxy for temperature

## Prerequisites
- Python 3.10 (>3.11)
- pip
- Anaconda (recommended for environments)

## Installation
The model consists of two parts, *pre-processing* (downloading and processing climate data) and *simulation* (running IGM with the processed climate data).

>This installation process has been tested in WSL (Windows Subsystem for Linux).

### First time setup 
The first step is to install the required dependencies. It is recommended to first install Anaconda or an equivalent for environment set up. 

```shell
wget https://repo.anaconda.com/archive/Anaconda3-2023.09-0-Linux-x86_64.sh
bash Anaconda3-2023.09-0-Linux-x86_64.sh
```

Create and activate a new environment with Python version 3.10:
``` 
conda create --name pre_process python=3.10
conda activate pre_process
```

The required packages and versions can be installed by pip with `requirements.txt` in the main directory:
```shell
pip install -r requirements.txt
```

#### Downloading climate data
Navigate to the `glacer_data/` folder and run the `pre_process.py` script:
```shell
python3 pre_process.py
```

The first time you run the script, it will download the data from various sources and store it under the `glacier_data` directory. The total amount of data is ~18 GB, it may take some time to download. 

##### CHELSA data file errors
The `download_chelsa.py` script uses an outdated link. If you get "unsupported file format" errors, or the CHELSA tif-files download in less than 1 second, download the files manually with the `chelsa_paths.txt` file:
```
wget --no-host-directories --force-directories --input-file=chelsa_paths.txt
```

If the files are located in sub folders, extract them all to  the same `glacer_data/chelsa/` folder.

Alternatively, select and download manually from https://chelsa-climate.org/downloads/:

Under `GLOBAL/input/`, select:
- `dem_latlong.nc` for the DEM
Under `GLOBAL/climatologies/1981-2010/` select the folders:
- `pr/` for precipitation
- `tas/` for temperature

Download the wget `.txt` generated file. Run the command:
```
wget --no-host-directories --force-directories --input-file=envidatS3paths.txt
```

If the files are located in sub folders, extract them all to  the same `glacer_data/chelsa/` folder.

### Clipping data for a new region
You can now download and automatically pre-process climate and topography data for selected regions. Suggested workflow:
- Create a bounding box in ArcGIS
- Export its extent in EPSG format
- Process the data with the extent information as described in example below.
- 
#### Example: The Caucasus mountain range
```shell
python3 pre_process.py --crs "EPSG:32638" --bounds -52549.60008263553 4495896.221676036 856472.3595563626 4927057.129636544 --output_dir caucasus
```

This will place three files (`atm.nc`, `boot.nc` and `dT_epica.nc`) in a folder named `caucasus/` in the current directory. These Files needs to be moved/copied to the folder with the IGM run file (`params.json`) under a new folder named `data/`. See the `igm_run/example/` folder to get an idea. 

Example folder structure:
```directory 
igm_run/
	├── example/
	└── caucasus/ 
		├── data/  
		│	├── atm.nc
		│	├── boot.nc
		│	└── dT_epica.nc
		├── modules_custom/
		│   └── ...
		├──	params.json
		└── paleo_igm.sh
```

A good approach for multiple runs is to copy and rename the `example/` folder for each newly clipped region. Multiple runs on the same region (with new `params.json`) can be automatically handled by running the `paleo_igm.sh` script in place of `igm_run`.

## Running IGM with paleo data
Before running IGM, it must also be installed ([see IGM wiki](https://github.com/jouvetg/igm/wiki/1.-Installation)). Installing IGM on a separate conda environment is recommended. 

Define your `params.json` and run the script `paleo_igm.sh` with data and file structure in the example above.

## Custom Modules
The `modules_custom` directory contains custom modules that are used by IGM to load the paleo climate data inputs. These modules include:
- `clim_pism.py`: A module for handling climate data from PISM.
- `plot_smb.py`: A module for plotting surface mass balance data.
- `plot-climate-forcing.py`: A module for plotting climate forcing data.
- `smb_pism.py`: A module for calculating surface mass balance using data in the PISM format.