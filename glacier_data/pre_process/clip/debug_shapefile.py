#!/usr/bin/env python3
"""
A simple script to check and debug a shapefile
"""

import geopandas as gpd
import os
import sys

def check_shapefile(shapefile_path):
    """Check a shapefile and print detailed information"""
    
    print(f"Checking shapefile: {shapefile_path}")
    
    # Check if file exists
    if not os.path.exists(shapefile_path):
        print(f"ERROR: File {shapefile_path} does not exist")
        return
    
    # Check for associated files
    dir_path = os.path.dirname(shapefile_path)
    base_name = os.path.basename(shapefile_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    extensions = ['.shp', '.shx', '.dbf', '.prj']
    missing_files = []
    
    for ext in extensions:
        expected_file = os.path.join(dir_path, name_without_ext + ext)
        if not os.path.exists(expected_file):
            missing_files.append(ext)
    
    if missing_files:
        print(f"WARNING: Missing associated files: {', '.join(missing_files)}")
    else:
        print("All required shapefile components exist")
    
    # Try to read the shapefile
    try:
        gdf = gpd.read_file(shapefile_path)
        print(f"Successfully loaded shapefile with {len(gdf)} features")
        
        # Check CRS
        print(f"CRS: {gdf.crs}")
        
        # Check geometry type
        geom_types = gdf.geometry.type.unique()
        print(f"Geometry types: {geom_types}")
        
        # Check bounds
        bounds = gdf.total_bounds
        print(f"Bounds: {bounds}")
        print(f"Width: {bounds[2] - bounds[0]}, Height: {bounds[3] - bounds[1]}")
        
        # Check for validity
        invalid_geoms = gdf[~gdf.geometry.is_valid]
        if len(invalid_geoms) > 0:
            print(f"WARNING: {len(invalid_geoms)} invalid geometries found")
        else:
            print("All geometries are valid")
        
        # Check for empty geometries
        empty_geoms = gdf[gdf.geometry.is_empty]
        if len(empty_geoms) > 0:
            print(f"WARNING: {len(empty_geoms)} empty geometries found")
        else:
            print("No empty geometries")
        
        # Print the first feature to check attributes
        if len(gdf) > 0:
            print("\nFirst feature attributes:")
            print(gdf.iloc[0])
        
    except Exception as e:
        print(f"ERROR reading shapefile: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_shapefile.py path/to/shapefile.shp")
    else:
        check_shapefile(sys.argv[1])