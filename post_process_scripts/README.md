# Paleo IGM post processing scripts

## ice_thicness_outline_extractor.py
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
python3 ice_thicness_outline_extractor.py --input ../igm_run/simian_small_ethiopia/simian_small_ethiopia_result_1/ --output ./data/ --crs "EPSG:20138"
```




