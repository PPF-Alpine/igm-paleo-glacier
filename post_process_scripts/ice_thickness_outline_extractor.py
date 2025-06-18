#!/usr/bin/env python

"""
Ice Thickness Outline Extractor Version 2 (Testing)

This script processes ice thickness GeoTIFF files (thk-*.tif) in a specified folder,
extracts outlines where ice exists (non-zero values), and saves them as shapefiles
for use in ArcGIS.

Usage:
    python script.py -i INPUT_FOLDER [-o OUTPUT_FOLDER] [-c CRS_EPSG]

Examples:
    python script.py -i /path/to/tif/files
    python script.py -i /path/to/tif/files -o /path/to/output -c EPSG:3413

Dependencies:
- rasterio
- numpy
- geopandas
- shapely
- argparse
- os
- glob
- re
"""

import os
import glob
import re
import argparse
import rasterio
import numpy as np
from rasterio import features
import geopandas as gpd
from shapely.geometry import shape

def extract_year_from_filename(filename):
    """Extract year from filename following the pattern thk-XXXXX.tif."""
    match = re.search(r'thk-(-?\d+)', filename)
    if match:
        return match.group(1)
    return None

def is_valid_year_difference(start_year, end_year=1950):
    """
    Check if the difference between end_year and start_year is a multiple of 1000.
    """
    if start_year is None:
        return False
    return (end_year - start_year) % 1000 == 0

def convert_year_to_timestep(year):
    """Converts the year to time step format for the purpose of naming. e.g.:
    - ICE0000.shp (present-day: the year 1950) 
	- ICE0001.shp (100 years ago)
	- ICE0010.shp (1000 years ago)
	- ICE0100.shp (10.000 years ago) 
	- ICE1300.shp (130.000 years ago) 

    This function requires that the data has a start year with a difference to end year being a multiplum of 1000.
    E.g start year must be -128050 in stead of -130000. 
    """
    present_year = 1950
    time_step_name_format = 0 
    year = int(year)
    if year < 0:
        time_step_name_format = abs(year) + present_year
    else:
        time_step_name_format = present_year - year

    timestep_number = time_step_name_format/100
    return timestep_number

def set_name_with_timestep_format(time_step):
    """Takes the time_step string and creates a unique name with the timestep format: ICE0010"""
    time_step = int(time_step)
    with_leading_zeros = ("{:04d}".format(time_step))
    time_step_format_new_name = "ICE" + with_leading_zeros
    return time_step_format_new_name


def process_tif_file(file_path, output_folder, input_crs, threshold=2, target_crs="EPSG:4326"):
    """
    Process a single GeoTIFF file to extract ice thickness outlines.
    
    Args:
        file_path: Path to the GeoTIFF file
        output_folder: Folder where to save the output shapefile
        input_crs: Source CRS from the data files.
        target_crs: Target CRS for the output shapefile. If None, use the CRS from the input file
    """
    # Extract the base filename and year
    base_name = os.path.basename(file_path)
    year_string = extract_year_from_filename(base_name)
    time_step_string = convert_year_to_timestep(year_string)
    new_name = set_name_with_timestep_format(time_step_string)

    if not year_string:
        print(f"Couldn't extract year from {base_name}. Skipping...")
        return
    
    print(f"Processing {base_name} (Year: {year_string})...")
    
    # Open the raster file
    with rasterio.open(file_path) as raster_file:
        # Read the data
        raster_data = raster_file.read(1)
        
        # Create a mask where ice thickness > threshold value
        print(f"Processing raster file with the ice thinckness threshold of {threshold}")
        ice_mask = (raster_data > threshold) & (raster_data != raster_file.nodata)

        # Use the original data values, but set areas below threshold to 0
        masked_data = np.where(ice_mask, raster_data, 0)

        # Get the shapes of areas where ice exists
        shapes = features.shapes(
            source=ice_mask.astype(np.uint8), 
            mask=ice_mask, 
            transform=raster_file.transform,
            connectivity=4
        )
        
        # Convert the shapes to geometries (Only if ice is present - checking if value is 1)
        geometries = [shape(geometry) for geometry, value in shapes if value == 1]
        
        if not geometries:
            print(f"No ice found in {base_name}. Skipping...")
            return
        
    # Create a GeoDataFrame with the geometries
    gdf = gpd.GeoDataFrame({
        'geometry': geometries,
        'year': year_string
    }, crs=input_crs)
    
    # Reproject to target_crs if specified and different from source
    if target_crs and (target_crs != input_crs):
        print(f"Reprojecting from {input_crs} to {target_crs}...")
        gdf = gdf.to_crs(target_crs)

    # Create output filename
    output_filename = new_name + ".shp"
    output_path = os.path.join(output_folder, output_filename)
    
    # Save as shapefile, explicitly setting the CRS
    gdf.to_file(output_path, driver="ESRI Shapefile")
    print(f"Saved outline to {output_path} with CRS: {gdf.crs}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract ice thickness outlines from GeoTIFF files.')
    parser.add_argument('-i', '--input_folder', required=True, help='Input folder containing thk-*.tif files')
    parser.add_argument('-o', '--output_folder', help='Output folder for shapefiles (defaults to input folder if not specified)')
    parser.add_argument('-c', '--input_crs', required=True, help='Input CRS for data (e.g., "EPSG:32638")')
    parser.add_argument('-t', '--threshold', type=float, help='Threshold value to remove low ice thickness values')
    parser.add_argument('-r', '--target_crs', help='Target CRS for output shapefiles (default "EPSG:4326")')
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    input_folder = args.input_folder
    output_folder = args.output_folder if args.output_folder else input_folder
    input_crs = args.input_crs
    threshold = float(args.threshold) if args.threshold is not None else 2
    target_crs = args.target_crs
    
    # Validate input folder
    if not os.path.isdir(input_folder):
        print(f"Error: {input_folder} is not a valid directory.")
        return
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")
    
    # Find all thk-*.tif files
    pattern = os.path.join(input_folder, "thk-*.tif")
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files matching the pattern 'thk-*.tif' found in {input_folder}")
        return
    
    print(f"Found {len(files)} files to process.")
    print(f"Target CRS: {target_crs if target_crs else 'Using CRS from input files'}")
    
    # Process each file
    for file_path in files:
        process_tif_file(file_path, output_folder, input_crs, threshold=threshold, target_crs=target_crs)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()
