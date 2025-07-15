from pathlib import Path
from pyproj import Transformer
import pandas as pd
import geopandas as gpd 
import urllib.request
import xarray as xr
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

import logging
from scipy.interpolate import interp1d

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_delta_temperature(antarctic_composite_path: Path, greenland_composite_path: Path, output_filepath: Path, polar_amplification_adjustment_factor: float, polygon=None ):

    normalized_latitude = calculate_pole_distances_from_shapefile(polygon)
    logger.info(f"Polygon center pole distance={normalized_latitude:.6f}")

    antarctic_delta_temperature = load_core_data(antarctic_composite_path, -140000) 

    temperature_shift_degrees = 31 #TODO: Find out if this is the correct approach.
    greenland_delta_temperature = load_core_data(greenland_composite_path, -140000, temperature_shift_degrees)

    #Greenland core reaches 129.081 ka BP
    #antarctic_core reaches 799.99 ka BP

    # combine the two cores using the latitude weighted value
    combined_core = combine_weighted_delta_temperature_cores(
        antarctic_delta_temperature, 
        greenland_delta_temperature, 
        normalized_latitude, 
        polar_amplification_adjustment_factor
    )

    # reverse the order of the dataset to start at the oldest time
    combined_core_chronological = combined_core.iloc[::-1]

    #Save to netcdf
    save_core_to_netcdf(combined_core_chronological, output_filepath)

    
def calculate_pole_distances_from_shapefile(shapefile_path):
   """
   Calculate normalized pole distances for polygon centroids from a shapefile.
   
   Args:
       shapefile_path: Path to the polygon shapefile
   
   Returns:
       None (logs results)
   """
   try:
       # Read shapefile
       logger.info(f"Reading shapefile: {shapefile_path}")
       gdf = gpd.read_file(shapefile_path)
       
       # Get centroids andtransform to lat/lon (assuming input is EPSG:6933)
       logger.info("Calculating centroids and transforming to lat/lon...")
       centroids = gdf.centroid.to_crs('EPSG:4326')
      
       # Calculate pole distances
       logger.info("Calculating normalized pole distances...")
       for idx, centroid in enumerate(centroids):
           lat = centroid.y
           # Normalize latitude to 0-1 scale
           # 0 = South Pole (-90°), 1 = North Pole (+90°), 0.5 = Equator (0°)
           pole_distance = (lat + 90) / 180
           
           return pole_distance
                   
   except Exception as e:
       logger.error(f"Error processing shapefile: {e}")

def load_core_data(core_path_csv, oldest_year, temperature_shift=0):
    """
    Load temperature CSV with Age [ka BP] and convert to years since 1950
    
    Returns:
        pd.DataFrame: Index = years_since_1950, Columns = temperature values
    """
    df = pd.read_csv(core_path_csv)
    
    # Convert Age [ka BP] to years since 1950
    # ka BP * 1000 = years before 1950
    # 1950 - (years before 1950) = years since 1950
    df['actual_year'] = 1950 - (df['Age [ka BP]'] * 1000)
    
    # Set as index and sort (oldest to newest)
    df.set_index('actual_year', inplace=True)
    df.sort_index(inplace=True)

    # Remove everything older than the oldest_year variable
    df = df[df.index >= oldest_year]

    # Remove duplicate indices (keep first occurrence)
    df = df[~df.index.duplicated(keep='first')]

    # rename the temperature column
    df.rename(columns={ df.columns[1]: "dT" }, inplace=True)

    df["dT"] = df["dT"] + temperature_shift

    # Remove the original Age column if it exists
    if 'Age [ka BP]' in df.columns:
        df.drop('Age [ka BP]', axis=1, inplace=True)

    # Create yearly index from min to max year
    min_year = int(df.index.min())
    max_year = int(df.index.max())
    yearly_index = pd.Index(range(min_year, max_year + 1), name='actual_year')
    
    # Reindex to yearly resolution with linear interpolation
    df_yearly = df.reindex(yearly_index).interpolate(method='linear')

    # Drop all rows with NaN
    df_yearly = df_yearly.dropna()
    # Remove years after 1950
    df_yearly = df_yearly[df_yearly.index <= 1950]

    df_yearly.sort_index(ascending=False, inplace=True)
    return df_yearly

def combine_weighted_delta_temperature_cores(antarctic_core, greenland_core, weight_value, polar_amplification_adjustment_facor):
   
    combined_temperature = (antarctic_core["dT"] * (1-weight_value) + greenland_core["dT"] * weight_value)/2 

    # Fill in antarcica core with polar amplification adjustment where the Greenland core does not have any data
    # The Greenland core goes back to ~130ka, before this only the Antarcica composite * adjustment (0,5) will be used
    combined_temperature = combined_temperature.fillna(antarctic_core["dT"] * polar_amplification_adjustment_facor)

    #Create and return new DataFrame 
    combined_temperature_df = pd.DataFrame({'dT': combined_temperature}, index=antarctic_core.index)

    return combined_temperature_df

def save_core_to_netcdf(core_dataframe, output_filepath):
    
     # Extract time and data from DataFrame
    time_values = core_dataframe.index.values  # Actual_year values
    delta_T_values = core_dataframe['dT'].values  # Temperature data

    # Create xarray Dataset
    ds = xr.Dataset(
        {
            "delta_T": ("time", delta_T_values),
        },
        coords={"time": time_values},
    )
    
    # Add time bounds (if needed)
    bounds = np.stack((time_values, time_values)).T
    ds = ds.assign_coords(
        time=(("time",), time_values), 
        time_bounds=(("time", "nv"), bounds)
    )
    
    # Add attributes to time coordinate
    ds.time.attrs.update(
        units="365 days since 1950-1-1",
        standard_name="time",
        long_name="Time (years since 1950)",
        calendar="365_day",
        bounds="time_bounds",
    )
    
    # Add attributes to temperature variable
    ds.delta_T.attrs.update(
        units="Kelvin",
        long_name="Temperature (variation from 1950-1980 avg.) (Delta T (K))",
    )
    
    # Save to netCDF
    ds.to_netcdf(
        output_filepath,
        encoding={"time": {"dtype": "i4"}, "delta_T": {"dtype": "f4"}},
    )
    
    logger.info(f"netCDF saved to: {output_filepath}")
