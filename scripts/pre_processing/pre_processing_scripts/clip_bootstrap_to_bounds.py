from pathlib import Path
import xarray as xr
from time import perf_counter
import numpy as np

from .clip_bounds_and_reproject import clip_and_reproject_data_array 

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_clipped_bootstrap(
        crs: str, bounds: list[int], gebco_filepath: Path, output_filepath: Path, resolution: int = 1000
):
    """Create and save a clipped bootstrap dataset to a netCDF file.
    Clips from the GEBCO dataset as found at gebco/GEBCO_2023_sub_ice_topo.nc

    Parameters:
        crs (str): The target CRS to reproject the data array to.
        bounds (list[int]): The bounding box coordinates [west, south, east, north]
            to clip the data array to.
        output_filepath (Path): The path to save the netCDF file to.
        resolution (int): The resolution of the output data array.
    """

    # Preload GEBCO 2025 data: 
    gebco_da = create_cliped_bootstrap(gebco_filepath, crs, bounds, resolution)


    # Remove the fill values and missing values attibutes to set the enconding later
    if '_FillValue' in gebco_da.attrs:
        del gebco_da.attrs['_FillValue']
    if 'missing_value' in gebco_da.attrs:
        del gebco_da.attrs['missing_value']

    
    # **Explicitly set encoding to force integer format**
    encoding = {
        'topg': {
            'dtype': 'int16',
            '_FillValue': -32767,
        }
    }
    
    # Create xarray and save to netcdf with explicit encoding
    xr.Dataset({"topg": gebco_da}).to_netcdf(
        output_filepath,
        encoding=encoding
    )

def create_cliped_bootstrap(
    gebco_path: Path, crs: str, bounds: list[int], resolution: int
):
    """Create a clipped version of the GEBCO dataset.

    Parameters:
        gebco_path (Path): The path to the GEBCO dataset.
        crs (str): The target CRS to reproject the data array to.
        bounds (list[int]): The bounding box coordinates [west, south, east, north]
            to clip the data array to.
        resolution (int): The resolution of the output data array.

    Returns:
        xr.DataArray: The reprojected and clipped data array.
    """
    
    start = perf_counter()

    loaded_da = xr.open_dataarray(gebco_path, decode_coords="all", decode_cf=True).rio.write_crs("WGS84")
    gebco_da = clip_and_reproject_data_array(loaded_da, crs, bounds, resolution)

   # **FORCE to int16 and handle any edge cases**
    print(f"Before conversion - Data type: {gebco_da.dtype}")
    
    # Convert to int16, replacing any potential NaN/inf with NoData
    gebco_da = gebco_da.fillna(-32767)  # Handle any NaN
    gebco_da = gebco_da.where(~np.isinf(gebco_da), -32767)  # Handle any inf values
    gebco_da = gebco_da.astype('int16')  # Force to int16
    
    print(f"After conversion - Data type: {gebco_da.dtype}")
    print(f"Final data range: {gebco_da.min().values} to {gebco_da.max().values}")
    
    gebco_da.attrs.update(standard_name="bedrock_altitude")
    logger.info(
        f"Loading and clipping GEBCO took {perf_counter() - start:.2f} seconds."
    )
    return gebco_da


def dev():
    # UTM-32 projection, WGS 84 datum
    crs = "EPSG:32632"
    # west, south, east, north bounds of the alps.
    bounds = [150e3, 4820e3, 1050e3, 5420e3]

    gebco_dir = Path("gebco")
    if not gebco_dir.exists():
        raise FileNotFoundError(
            "GEBCO directory not found. Please download the data first."
        )
    gebco_path = gebco_dir / "GEBCO_2023_sub_ice_topo.nc"
    gebco_da = create_cliped_bootstrap(gebco_path, crs, bounds, 1000)

    ds = xr.Dataset({"bedrock": gebco_da})
    # save to netcdf with float dtypes for all keys.
    ds.to_netcdf(
        "bootstrap.nc",
    )


if __name__ == "__main__":
    dev()
