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

def save_delta_temperature(model_directory: Path, output_filepath: Path, polygon=None ):

    # normalized_latitude = calculate_normalized_pole_distance(latitude)
    normalized_latitude = calculate_pole_distances_from_shapefile(polygon)
    logger.info(f"Polygon center pole distance={normalized_latitude:.6f}")

    #TODO: calc weighted delta temperatures
    #TODO: save to output_filepath

    
    
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
       
       # Get centroids and transform to lat/lon (assuming input is EPSG:6933)
       logger.info("Calculating centroids and transforming to lat/lon...")
       centroids = gdf.centroid.to_crs('EPSG:4326')
       
       # Calculate pole distances
       logger.info("Calculating normalized pole distances...")
       for idx, centroid in enumerate(centroids):
           lat = centroid.y
           # Normalize latitude to -1 to 1 scale
           # 0 = equator, +1 = North Pole, -1 = South Pole
           pole_distance = lat / 90
           
           return pole_distance
           
   except Exception as e:
       logger.error(f"Error processing shapefile: {e}")

