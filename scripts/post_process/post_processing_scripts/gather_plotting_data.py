from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
import glob

from .get_ice_volume_array import get_ice_volumes_with_path

def save_results_as_csv(path_to_logfile: Path, shape_files_path: Path, output_folder: Path):

    # get the extent area
    extent_area_and_time = extract_shapefile_data(shape_files_path)
    
    # get the volume
    years, ice_volume_array = get_ice_volumes_with_path(path_to_logfile)


    print(f"ext: {extent_area_and_time}")
    print(f"vol: {ice_volume_array}")
    print(f"yer: {years}")

    # Create pandas DataFrame and combine the two data sets
    volume_df = pd.DataFrame({
        'time': years, 
        'volume': ice_volume_array
    })
    extent_df = pd.DataFrame(extent_area_and_time, columns=['filename', 'time', 'extent'])

    # Merge extent and volume in one DataFrame
    extent_and_volume_df = pd.merge(volume_df, extent_df[['time', 'extent']], on='time', how='left')

    # Fill missing extent values with 0
    extent_and_volume_df['extent'] = extent_and_volume_df['extent'].fillna(0.0)

    # Reorder the columns
    final_df = extent_and_volume_df[['time', 'volume', 'extent']]

    # Save to csv file  
    final_df.to_csv(Path(output_folder) / "glacier_extent_and_volume.csv")



# data = extract_shapefile_data("/path/to/your/shapefiles")
def extract_shapefile_data(folder_path):
    """
    Extract year and total area_km2 from all shapefiles in a folder.
    
    Args:
        folder_path (str): Path to folder containing shapefiles
        
    Returns:
        list: List of tuples (filename, year, total_area_km2)
    """
    results = []
    
    # Find all .shp files in the folder
    shp_pattern = os.path.join(folder_path, "*.shp")
    shapefiles = glob.glob(shp_pattern)
    
    for shp_file in shapefiles:
        try:
            # Read the shapefile
            gdf = gpd.read_file(shp_file)
            
            # Get filename without path and extension
            filename = os.path.splitext(os.path.basename(shp_file))[0]
            
            # Get year (assuming all rows have the same year, take the first one)
            year = int(gdf['year'].iloc[0])
            
            # Sum all area_km2 values
            total_area = gdf['area_km2'].sum()
            
            results.append((filename, year, total_area))
            print(f"Processed {filename}: Year {year}, Total Area {total_area:.2f} km²")
            
        except Exception as e:
            print(f"Error processing {shp_file}: {e}")
    
    return results

