## Exporting polygons from ArcGIS
Create polygon by following same first steps as in  [[README IGM Model Extent In ArcGIS]].
Create Polygon instead of square. 

### Exporting to shapefile
1. Right click the item in the `Content` pane, and select `Data > Export Features`.
2. Select the export destination and filename under the `Output Feature Class` input box.
3. Under the `Environments` tab set the Output Coordinates System to match the polygon. 
4. Press OK. 

### Important note
It is critical that **all** the shape file parts is in the same directory as the resulting `.shp` file before running the `pre_process.py` script. This includes (at least) `.shp`, `.prj`, `.shx` and `.dbf` files. Probably a good idea to copy the rest over as well.

## Testing the clipping scripts
```shell
python pre_process.py --crs "EPSG:32611" --polygon_path ./sierra_nevada_usa_bounding.shp --output_dir sierra_nevada_polygon_test     
```

For comparison, here is the normal square bounding extent:
```shell
python3 pre_process.py --crs "EPSG:32611" --bounds 94279.447400 3955671.976000 494239.319400 4455521.841000  --output_dir sierra_nevada_square_bounds 
```

## Testing a new shape file with utm11 (EPSG:32611)
```shell
python pre_process.py --crs "EPSG:32611" --polygon_path ./new_sierra_nevada_polygon_bounds.shp --output_dir new_sierra_nevada_polygon_test     
```

Everything seems to look right, atmosphere data gets clipped to the correct polygon and seems ok. Even running my custom `.nc` boot file in a separate simulation with a simple smb works for the polygon clipping. 

## Testing polygon boot file with square (working) atm.nc and dT_epica.nc
INVALID_ARGUMENT: required broadcastable shapes                                                      


