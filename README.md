# paleo-glacier
Everything related to automated paleo-glacier modelling.

## glacier_data
Holds glacier input data downloading and pre-processing.

### example run of pre processing python script.
The first time you run the script, it will download the data from the internet and store it in the pism_data directory.
The total amount of data is ~18GB, so it will take a while to download.
From the pism_data repository, run the following command to download and pre-process the data.
```bash
python3 pre_process.py
```

#### example clipping of the Caucasus Mountains
```bash
python3 pre_process.py --crs "EPSG:32638" --bounds -52549.60008263553 4495896.221676036 856472.3595563626 4927057.129636544 --output_dir caucasus
```

#### example clipping of the Rwenori Mountains
```bash
python3 pre_process.py --crs "EPSG:32635" --bounds 778879.15975354 -35049.69269163 884033.3405611  120171.97724387 --output_dir Rwenzori
```

#### output of help for pre_process.py
```bash
python3 pre_process.py --help
```
```
usage: pre_process.py [-h] [--crs CRS] [--bounds BOUNDS [BOUNDS ...]] [--resolution RESOLUTION]
                      [--dT_output_filename DT_OUTPUT_FILENAME]
                      [--atm_output_filename ATM_OUTPUT_FILENAME]
                      [--boot_output_filename BOOT_OUTPUT_FILENAME] [--output_dir OUTPUT_DIR]

Clip input data

options:
  -h, --help            show this help message and exit
  --crs CRS             Coordinate Reference System for the output data, needs to be in the format EPSG:XXXX with UTM projection
  --bounds BOUNDS [BOUNDS ...]
                        Bounds for clipping the data in the format: xmin, ymin, xmax, ymax
  --resolution RESOLUTION
                        Resolution in meters per pixel
  --dT_output_filename DT_OUTPUT_FILENAME
                        Output filename for clipped dT data
  --atm_output_filename ATM_OUTPUT_FILENAME
                        Output filename for clipped atmosphere data
  --boot_output_filename BOOT_OUTPUT_FILENAME
                        Output filename for clipped bootstrap data
  --output_dir OUTPUT_DIR
                        Directory to output the clipped data to
```

## IGM run
