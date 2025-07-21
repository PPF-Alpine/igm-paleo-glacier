import os
import glob
import re
import argparse
import rasterio
import numpy as np
from rasterio import features
import geopandas as gpd
from shapely.geometry import shape

from post_processing_scripts import (
    save_result_as_csv  
    extract_outline_as_shapefile
    plot_ice_extent_and_volume        
)

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


    # Generate shape files from the igm outputs
    extract_outline_as_shapefile(input_folder, output_folder, input_crs, target_crs, threshold)

    # Extract the result data for extent and volume and create a csv file 
    save_result_as_csv()

    # Plot the results 
    plot_ice_extent_and_volume()

