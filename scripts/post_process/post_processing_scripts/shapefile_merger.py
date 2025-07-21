import os
import glob
from pathlib import Path
import geopandas as gpd
from shapely.ops import unary_union
import pandas as pd
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def merge_shapefiles(input_folders, output_folder, file_pattern="ICE*.shp"):
    """
    Merge shapefiles with the same names from multiple folders.
    
    Parameters:
    -----------
    input_folders : list
        List of folder paths containing shapefiles to merge
    output_folder : str
        Path to output folder where merged shapefiles will be saved
    file_pattern : str
        Pattern to match shapefile names (default: "ICE*.shp")
    """
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Dictionary to store shapefiles grouped by filename
    shapefile_groups = defaultdict(list)
    
    # Scan all input folders for shapefiles
    logger.info(f"Scanning {len(input_folders)} folders for shapefiles...")
    
    for folder in input_folders:
        if not os.path.exists(folder):
            logger.warning(f"Folder does not exist: {folder}")
            continue
            
        # Find all shapefiles matching the pattern
        shapefile_paths = glob.glob(os.path.join(folder, file_pattern))
        
        for shapefile_path in shapefile_paths:
            filename = os.path.basename(shapefile_path)
            base_name = os.path.splitext(filename)[0]  # Remove .shp extension
            shapefile_groups[base_name].append(shapefile_path)
            
        logger.info(f"Found {len(shapefile_paths)} shapefiles in {folder}")
    
    logger.info(f"Total unique shapefile names found: {len(shapefile_groups)}")
    
    # Process each group of shapefiles
    for base_name, shapefile_paths in shapefile_groups.items():
        if len(shapefile_paths) == 1:
            logger.info(f"Only one file found for {base_name}, skipping merge")
            continue
            
        logger.info(f"Merging {len(shapefile_paths)} files for {base_name}")
        
        try:
            merge_single_shapefile_group(base_name, shapefile_paths, output_folder)
        except Exception as e:
            logger.error(f"Error merging {base_name}: {str(e)}")
            continue
    
    logger.info("Merge process completed!")

def merge_single_shapefile_group(base_name, shapefile_paths, output_folder):
    """
    Merge a group of shapefiles with the same name into a single shapefile.
    
    Parameters:
    -----------
    base_name : str
        Base name of the shapefile (without extension)
    shapefile_paths : list
        List of paths to shapefiles to merge
    output_folder : str
        Output folder path
    """
    
    gdfs = []
    
    # Read all shapefiles
    for shapefile_path in shapefile_paths:
        try:
            gdf = gpd.read_file(shapefile_path)
            
            # Ensure CRS is EPSG:4326
            if gdf.crs is None:
                logger.warning(f"No CRS found for {shapefile_path}, assuming EPSG:4326")
                gdf.set_crs("EPSG:4326", inplace=True)
            elif gdf.crs.to_string() != "EPSG:4326":
                logger.info(f"Reprojecting {shapefile_path} from {gdf.crs} to EPSG:4326")
                gdf = gdf.to_crs("EPSG:4326")
            
            gdfs.append(gdf)
            logger.debug(f"Loaded {len(gdf)} features from {shapefile_path}")
            
        except Exception as e:
            logger.error(f"Error reading {shapefile_path}: {str(e)}")
            continue
    
    if not gdfs:
        logger.error(f"No valid shapefiles could be loaded for {base_name}")
        return
    
    # Combine all GeoDataFrames
    combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    
    # Ensure CRS is set
    combined_gdf.set_crs("EPSG:4326", inplace=True, allow_override=True)
    
    logger.info(f"Combined GeoDataFrame has {len(combined_gdf)} features")
    
    # Method 1: Simple union of all geometries (fastest, creates single feature)
    # This merges all overlapping areas into one continuous extent
    all_geoms = combined_gdf.geometry.tolist()
    merged_geometry = unary_union(all_geoms)
    
    # Create new GeoDataFrame with merged geometry
    merged_gdf = gpd.GeoDataFrame(
        {'id': [1], 'source': [f'merged_from_{len(shapefile_paths)}_files']},
        geometry=[merged_geometry],
        crs="EPSG:4326"
    )
    
    # Alternative Method 2: Dissolve while preserving attributes
    # Uncomment the following lines if you want to preserve original attributes
    # and have multiple features in the output (one per original non-overlapping area)
    """
    # Add a common field for dissolving
    combined_gdf['merge_field'] = 1
    
    # Dissolve all features together, merging overlapping areas
    merged_gdf = combined_gdf.dissolve(by='merge_field', as_index=False)
    
    # Clean up the merge field
    merged_gdf.drop('merge_field', axis=1, inplace=True)
    """
    
    # Save merged shapefile
    output_path = os.path.join(output_folder, f"{base_name}.shp")
    merged_gdf.to_file(output_path)
    
    logger.info(f"Saved merged shapefile: {output_path} ({len(merged_gdf)} features)")

def main():
    """
    Main function to configure and run the shapefile merger.
    Modify the paths below according to your setup.
    """
    
    # Configuration - MODIFY THESE PATHS
    input_folders = [
        r"northern_andes_eastern_cordillera",
        r"northern_andes_ecuadorian_cordilleras",
        r"northern_andes_western_and_central_cordillera",
    ]
    
    output_folder = r"C:\path\to\output\merged_shapefiles"  # Replace with your output path
    
    # Optional: modify the file pattern if needed
    file_pattern = "ICE*.shp"  # This will match ICE0000.shp, ICE0010.shp, etc.
    
    # Validate input folders
    valid_folders = []
    for folder in input_folders:
        if os.path.exists(folder):
            valid_folders.append(folder)
            logger.info(f"Input folder: {folder}")
        else:
            logger.warning(f"Input folder does not exist: {folder}")
    
    if len(valid_folders) < 2:
        logger.error("Need at least 2 valid input folders to perform merge")
        return
    
    logger.info(f"Output folder: {output_folder}")
    
    # Run the merge
    merge_shapefiles(valid_folders, output_folder, file_pattern)

if __name__ == "__main__":
    main()

# Example usage for different scenarios:

def example_usage():
    """
    Example usage scenarios for different folder structures.
    """
    
    # Example 1: Basic usage with two folders
    folders = [
        r"C:\ice_data\dataset1",
        r"C:\ice_data\dataset2"
    ]
    output = r"C:\ice_data\merged"
    merge_shapefiles(folders, output)
    
    # Example 2: Multiple folders with custom pattern
    folders = [
        r"C:\ice_data\2020",
        r"C:\ice_data\2021", 
        r"C:\ice_data\2022",
        r"C:\ice_data\2023"
    ]
    output = r"C:\ice_data\combined_years"
    merge_shapefiles(folders, output, "ICE*.shp")
    
    # Example 3: Using relative paths
    current_dir = os.getcwd()
    folders = [
        os.path.join(current_dir, "data", "folder1"),
        os.path.join(current_dir, "data", "folder2"),
        os.path.join(current_dir, "data", "folder3")
    ]
    output = os.path.join(current_dir, "output", "merged")
    merge_shapefiles(folders, output)
