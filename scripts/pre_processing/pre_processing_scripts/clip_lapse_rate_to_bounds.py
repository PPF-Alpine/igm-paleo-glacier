# Takes a GeoTIFF containing global lapse rate calculations (by Eline Rentier), 
# and clip the data to the provided bounding polygon / box. 
# sjurbarndon@proton.me

from pathlib import Path
import xarray as xr
import numpy as np
import os
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask

from .clip_bounds import reproject_data_array 
from .clip_polygon import make_mask_from_polygon
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_clipped_lapse_rate(crs: str, bounds: list[int], lapse_rate_filepath: Path, output_filepath: Path, polygon=None, resolution: int = 1000):
    """Create and save an average value of clipped lapse rate data.
    Parameters:
        crs (str): The coordinate reference system of the dataset.
        bounds (list[int]): The bounding box coordinates [xmin, ymin, xmax, ymax].
        output_filepath (Path): The path to save the netCDF file.
        polygon (.shp): Shape file for optionally clipping further within the bounds.
        resolution (int, optional): The resolution of the clipped dataset. Defaults to 1000.
    """
    
    lapse_rate_filepath
    # Create an xarray and save to netCDF
    os.environ["GTIFF_SRS_SOURCE"] = "EPSG"
    clipped_lapse_rate = create_clipped_lapse_rate(crs, bounds, lapse_rate_filepath, resolution, polygon=polygon)

    # Create full paths for both files
    nc_path = output_filepath.with_suffix(".nc")
    txt_path = output_filepath.with_suffix(".txt")

    clipped_lapse_rate.to_netcdf(
        nc_path,
        encoding={"lapse_rate": {"dtype": "f4"}}
    )
    local_average = calculate_local_average(clipped_lapse_rate)
    local_average_string = f"{local_average}"
    with open(txt_path, "w") as file:
        file.write(local_average_string)
    #TODO: this file path might need a tweak or two

def create_clipped_lapse_rate(crs: str, bounds: list[int], lapse_rate_filepath: Path, resolution: int, polygon=None) -> xr.Dataset:
    """Create a clipped lapse rate data xarray.

     Args:
        crs (str): The coordinate reference system.
        bounds (list[int]): The bounds of the clipped area.
        resolution (int): The resolution of the clipped data.
        polygon (path to shapefile): Shapefile defining area of simulation by setting all precipitation outside it to zero.

    Returns:
        xr.Dataset: The clipped atmosphere dataset.
    """

    # Returns an xarray DataArray instead of Dataset
    lapse_rates = reproject_data_array(
        read_lapse_rate_data(lapse_rate_dir=lapse_rate_filepath),
        crs,
        bounds,
        resolution,
    )
    # Create a mask from the provided polygon shape file:
    mask = make_mask_from_polygon(crs, lapse_rates, polygon)    

    # Set lapse rate outside the mask to nan:
    lapse_rates_masked = lapse_rates.where(mask, np.nan)

    return lapse_rates_masked
   
def read_lapse_rate_data(lapse_rate_dir: Path) -> xr.DataArray:
    """Reads the lapse rate GeoTIFF file"""
    try:
        # Load the lapse rate data
        lapse_rate = xr.open_dataarray(lapse_rate_dir)
        
        # Add meaningful attributes
        lapse_rate.name = "lapse_rate"
        
        # Check the data
        print(f"Loaded array with shape: {lapse_rate.shape}")
        print(f"Coordinate system: {lapse_rate.spatial_ref}")
        print(f"Data range: {lapse_rate.min().item():.3f} to {lapse_rate.max().item():.3f}")
        print(f"Number of valid pixels: {(~np.isnan(lapse_rate)).sum().item()}")
    
    except Exception as e:
        print(f"Error loading file: {e}")
    return lapse_rate

def calculate_local_average(lapse_rates_array: xr.DataArray) -> int:
    local_average = lapse_rates_array.mean(skipna=True).item()
    print(f"local average calculated as: {local_average} K/km")
    local_average_in_k_per_m  = local_average/1000
    print(f"local average per meter: {local_average_in_k_per_m} K/m")
    return local_average_in_k_per_m

def dev():
    """Development function to test clipping lapse rate dataset."""
    lapse_rate_dir = Path(LAPSE_RATE_DIR)
    if not lapse_rate_dir.exists():
        raise FileNotFoundError(
            "Lapse rate directory not found. Please download the data first."
        )

    # UTM-32 projection, WGS 84 datum
    crs = "EPSG:32638"
    # west, south, east, north bounds of the alps.
    bounds = [
        -52549.60008263553,
        4495896.221676036,
        856472.3595563626,
        4927057.129636544,
    ]

    save_clipped_lapse_rate(crs, bounds, resolution=1000, output_filepath=".")

if __name__ == "__main__":
    dev()
