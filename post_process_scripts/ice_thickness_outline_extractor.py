#!/usr/bin/env python

"""
Ice Thickness Outline Extractor

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

def process_tif_file(file_path, output_folder, target_crs=None):
    """
    Process a single GeoTIFF file to extract ice thickness outlines.
    
    Args:
        file_path: Path to the GeoTIFF file
        output_folder: Folder where to save the output shapefile
        target_crs: Target CRS for the output shapefile. If None, use the CRS from the input file
    """
    # Extract the base filename and year
    base_name = os.path.basename(file_path)
    year_str = extract_year_from_filename(base_name)
    
    if not year_str:
        print(f"Couldn't extract year from {base_name}. Skipping...")
        return
    
    print(f"Processing {base_name} (Year: {year_str})...")
    
    # Open the raster file
    with rasterio.open(file_path) as src:
        # Read the data
        raster_data = src.read(1)
        
        # Create a mask where ice thickness > 0
        mask = raster_data > 0

        # Get the shapes of areas where ice exists
        shapes = features.shapes(
            raster_data.astype(np.int16), 
            mask=mask, 
            transform=src.transform
        )
        
        # Convert the shapes to geometries
        geometries = [shape(geometry) for geometry, value in shapes]
        
        if not geometries:
            print(f"No ice found in {base_name}. Skipping...")
            return
        
        # Get CRS from either the source file or the specified target CRS
        crs = target_crs if target_crs else src.crs
        
        # Create a GeoDataFrame with the geometries
        gdf = gpd.GeoDataFrame({
            'geometry': geometries,
            'year': year_str
        }, crs=crs)
        
        # Reproject if target_crs is specified and different from source CRS
        if target_crs and src.crs and src.crs != target_crs:
            print(f"Reprojecting from {src.crs} to {target_crs}")
            gdf = gdf.to_crs(target_crs)
        
        # Dissolve to get a single outline
        gdf_dissolved = gdf.dissolve(by='year')
        
        # Create output filename
        output_filename = f"ice_outline_{year_str}.shp"
        output_path = os.path.join(output_folder, output_filename)
        
        # Save as shapefile, explicitly setting the CRS
        gdf_dissolved.to_file(output_path, driver="ESRI Shapefile")
        print(f"Saved outline to {output_path} with CRS: {gdf_dissolved.crs}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Extract ice thickness outlines from GeoTIFF files.')
    parser.add_argument('-i', '--input', required=True, help='Input folder containing thk-*.tif files')
    parser.add_argument('-o', '--output', help='Output folder for shapefiles (defaults to input folder if not specified)')
    parser.add_argument('-c', '--crs', help='Target CRS for output shapefiles (e.g., "EPSG:3413")')
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    input_folder = args.input
    output_folder = args.output if args.output else input_folder
    target_crs = args.crs
    
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
        process_tif_file(file_path, output_folder, target_crs)
    
    print("Processing complete!")

if __name__ == "__main__":
    main()
