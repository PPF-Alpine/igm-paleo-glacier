import os
import glob
import re
import argparse
import rasterio
import numpy as np
from pathlib import Path
from rasterio import features
import geopandas as gpd
from shapely.geometry import shape

from post_processing_scripts import (
    save_results_as_csv, 
    extract_outline_as_shapefile,
    plot_volume_extent_time,     
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

    print(f"Post Processing Started. Input: {args.input_folder}, output: {output_folder}, threshold: {threshold}")
    
    # Validate input folder
    if not os.path.isdir(input_folder):
        print(f"Error: {input_folder} is not a valid directory.")
        return
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output directory: {output_folder}")


    #TODO: fix path names to this local place in stead of inside the scripts so that they can be printed correctly here.
    # Generate shape files from the igm outputs
    extract_outline_as_shapefile(input_folder, output_folder, input_crs, target_crs, threshold)
    print(f"Ice extent outline extracted as shapefiles to {output_folder}")

    # Extract the result data for extent and volume and create a csv file 
    save_results_as_csv(path_to_logfile=os.path.join(input_folder, ".."), shape_files_path=output_folder, output_folder=os.path.join(input_folder, ".."))
    print(f"Result statistics saved to CSV in {output_folder}")

    # Plot the results 
    plot_volume_extent_time(os.path.join(input_folder, "../glacier_extent_and_volume.csv"), save_path=os.path.join(input_folder, ".."))
    print(f"Result volume and extent plotted and saved in {input_folder}")


if __name__ == "__main__":
    main()
