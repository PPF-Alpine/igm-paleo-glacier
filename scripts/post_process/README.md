# Paleo IGM post processing scripts

## Overview
This directory `post_process/` contains all the post processing scripts. A complete post processing can be done by calling the main `post_process_igm.py` script. Although this should already be executed by the run script that initiates the simulation.  

The scripts in `post_process/post_processing_scripts/` should be mostly modular, and can be executed after a simulation has ended. Some script depend on being executed in order because it is using the output from the previous script (E.g. `ice_outline_shapefiles.py` provides output for `the gather_plotting_data.py` providing `.csv` files for `plot_result_data.py`).

## ice_outline_shapefiles.py
This script take all the ice thickness GeoTIFF-files (e.g. thk-001950.tif) in the specified folder, converts them to an outline shape file (set of files), and names them for the year. 

> [!NOTE]
> This should be used to store the IGM output at a lower data storage requirement and for use in the ecology model.  

### Aguments
The script takes input parameters as command-line aguments:

-i or --input: Required parameter for the input folder path
-o or --output: Optional parameter for the output folder (defaults to input folder)
-c or --crs: Optional parameter to specify the target CRS

### Example
```shell
python3 ice_outline_shapefiles.py --input ../igm_run/simian_small_ethiopia/simian_small_ethiopia_result_1/ --output ./data/ --crs "EPSG:20138"
```
