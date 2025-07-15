# IGM Paleo Glacier Model

## Overview
This project contains the resources necessary for running the world wide IGM Paleo Glacier model. The [Instructed Glacier Model (IGM)](https://github.com/jouvetg/igm) is a machine learning glacier model that run very fast on GPU's. Here we use custom modules to download and use paleo-climate data with the IGM model. Required dependencies and installation steps are described in detail below.

### Directory structure
```
/
├── data/
│   ├── processed/                   # pre-processed and clipped data per location
│   └── raw/
│       ├── climate/                 # raw climate data downloads  
│       └── location_boundaries/     # shape file boundary for each location 
├── igm_run/                         # simulation run directory
├── scripts/
│   ├── download/                    # scripts for downloading and converting data
│   ├── make_simulation_directory/
│   │   ├── modules_custom/
│   │   └── make_new_simulation_directory.sh    # makes a simulation run directory for new location
│   ├── post_process/
│   └── pre_process/
│       ├── pre_processing_scripts
│       └── clip_glacial_index_method.py        # clips and pre-processes data to boundary
└── README.md
```

## Background
IGM is well suited to grab glacier data from the Randolph Glacier Inventory and adding available climate/mass balance and topography data. This is mostly focused towards recent and  future projections. Here we load paleo data and use them in a custom module:
- [**Chelsa**](https://chelsa-climate.org): Paleo climate data
- [**GEBCO**](https://www.gebco.net/): Topography data
- [**EPICA**](https://doi.pangaea.de/10.1594/PANGAEA.683655): Ice core data and delta T as a proxy for temperature
- [CMIP6 / MPI-ESM1-2](https://catalogue.ceda.ac.uk/uuid/65edc10dc0664aeda89dec81f2c6426e/): Modeled climate data for anomaly calculation.
- [Greenland Core Composite](https://doi.pangaea.de/10.1594/PANGAEA.957135): Ice core data and delta temperature
- [Antarctica Core Composite](https://doi.pangaea.de/10.1594/PANGAEA.810188): Ice core data and delta temperature

## Prerequisites
- Python 3.10 (>3.11)
- pip
- Anaconda (recommended for environments)

## First time setup 
The model consists of four parts,*download* (downloading relevant data sets), *pre-processing* (for processing climate data), *simulation* (running IGM with the processed climate data) and *post-processing* (converts results to shapefiles).

>This installation process has been tested in WSL (Windows Subsystem for Linux).

### Installing IGM and dependencies
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

The required packages and versions can be installed by pip with `requirements.txt` in the scripts/ directory:
```shell
cd scripts/
pip install -r requirements.txt
```

Install IGM ([see IGM wiki](https://github.com/jouvetg/igm/wiki/1.-Installation)). Installing IGM on a separate conda environment (separate from the pre_process) is recommended. 


### Downloading climate data
Navigate to the `scripts/download/` folder and run the `download_climate_data.py` script:
```shell
python download_climate_data.py
```
The script will download the data from various sources and store it under the `data/raw/climate/` directory. The total amount of data is ~18 GB, it may take some time to download. 

>TODO: This script does not yet download the core composites nor the modeled anomaly ESM data. Manual download and pre-processing required.


#### CHELSA data file errors
The `download_chelsa.py` script uses an outdated link. If you get "unsupported file format" errors, or the CHELSA tif-files download in less than 1 second, download the files manually with the `chelsa_paths.txt` file:
```
wget --no-host-directories --force-directories --input-file=chelsa_paths.txt
```

If the files are located in sub folders, extract them all to  the same `climate/chelsa/` folder.

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

If the files are located in sub folders, extract them all to  the same `climate/chelsa/` folder.

### Clipping data for a new region
You can now crop and automatically pre-process climate and topography data for selected regions. Suggested workflow:

- Create a bounding box in ArcGIS
    - Export its extent in EPSG format (e.g. `-52549.60008263553 4495896.221676036 856472.3595563626 4927057.129636544` )
- Create a polygon bounding box in ArcGIS to limit the area
    - Export its shapefile
    - Place the shapefile in data/raw/location_boundaries/'area_name'
- Process the data with the extent information as described in example below.

#### Example: The Caucasus mountain range
```shell
python clip_glacial_index_method.py --crs "EPSG:6933" --bounds 3813003.992500 4767963.246100 4748752.838900 5133150.315100 --polygon ../../data/raw/location_boundaries/5_caucasus/caucasus_bb.shp --output_dir caucasus
```

This will generate and place new files under the `caucasus/` directory like specified above. The new files will be all the data required to run the model:
```shell
/
└── data/
    ├── processed/
    │   └── caucasus/
    │       ├── dT_composite_at_latitude.nc
    │       ├── dT_epica.nc
    │       ├── localised_lapse_rate.nc
    │       ├── localised_lapse_rate.txt
    │       ├── modeled_anomaly_clipped.nc
    │       ├── present_day_observed_atmosphere.nc
    │       ├── projection.txt
    │       └── topography.nc
```

After pre processing with `clip_glacial_index_method.py` run `./make_new_simulation_directory.sh caucasus_test ../../data/processed/caucasus` from the run_sripts folder to generate a simulation directory automatically. The script `make_new_simulation_directory.sh` will create a new directory `igm_run/caucasus_test/` and fill it with links to the required scrips (from the `simulation_default_files/` dir) and links to the data folder. 


## Running IGM with paleo data
Redefine your `params.json` and run the script `paleo_igm.sh` with data and file structure in the example above.

## Custom Modules
The `modules_custom` directory contains custom modules that are used by IGM to load the paleo climate data inputs. These modules include:
- `paleo_clim.py`: A module for initializing and updating the paleo climate variables using the Glacial Index Method.
- `paleo_smb.py`: A module for calculating surface mass balance.  

### Climate module: `paleo_clim.py`
//TODO

### Surface Mass Balance: `paleo_smb.py`
//TODO
