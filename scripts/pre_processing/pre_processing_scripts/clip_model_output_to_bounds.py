from pathlib import Path
import xarray as xr
import numpy as np
from time import perf_counter
import os
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask

from .clip_bounds import reproject_data_array 
from .clip_polygon import make_mask_from_polygon

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_clipped_model_atmosphere(
    crs: str, 
    bounds: list[int], 
    lgm_filepath: Path, 
    historical_filepath: Path, 
    output_filepath: Path, 
    polygon=None, 
    resolution: int = 1000
):
    """Create and save clipped model lgm/historical atmosphere dataset to a netCDF file.

    Parameters:
        crs (str): The coordinate reference system of the dataset.
        bounds (list[int]): The bounding box coordinates [xmin, ymin, xmax, ymax].
        lgm_filepath (Path): 
        historical_filepath (Path): 
        output_filepath (Path): The path to save the netCDF file.
        polygon (.shp): Shape file for clipping further within the bounds.
        resolution (int, optional): The resolution of the clipped dataset. Defaults to 1000.
    """
    # Create xarray and save to netcdf

    # Fix for rasterio using incorrect SRS source for GTiff files.
    os.environ["GTIFF_SRS_SOURCE"] = "EPSG"

    # Create and save clipped LGM atmosphere  
    ds = create_cliped_atmosphere(crs, bounds, lgm_filepath, resolution, polygon=polygon)
    ds.to_netcdf(
        output_filepath, encoding={key: {"dtype": "f4"} for key in ds.data_vars.keys()}
    )

    # Create and save clipped historical atmosphere  
    ds = create_cliped_atmosphere(crs, bounds, historical_filepath, resolution, polygon=polygon)
    ds.to_netcdf(
        output_filepath, encoding={key: {"dtype": "f4"} for key in ds.data_vars.keys()}
    )

def create_cliped_atmosphere( #TODO: This function is copied and needs to be heavily modiefied before testing
    crs: str,
    bounds: list[int],
    atmosphere_filepath: Path, 
    resolution: int,
    polygon=None,
) -> xr.Dataset:
    """
    Create a clipped atmosphere dataset.

    Args:
        crs (str): The coordinate reference system.
        bounds (list[int]): The bounds of the clipped area.
        resolution (int): The resolution of the clipped data.
        polygon (path to shapefile): Shapefile defining area of simulation by setting all precipitation outside it to zero.
        apply_pbcor (bool, optional): Whether to apply precipitation bias correction. Defaults to False.

    Returns:
        xr.Dataset: The clipped atmosphere dataset.
    """

    # combine into dataset
    ds = xr.Dataset(
        {
            "air_temp": reproject_data_array(
                read_chelsa_var(chelsa_dir=chelsa_filepath, variable="tas"),
                crs,
                bounds,
                resolution,
            ),
            "precipitation": reproject_data_array(
                read_chelsa_var(chelsa_dir=chelsa_filepath, variable="pr"),
                crs,
                bounds,
                resolution,
            ),
            "elevation": reproject_data_array(
                xr.open_dataarray(
                    chelsa_filepath / "dem_latlong.nc", decode_coords="all"
                ).isel(lat=slice(None, None, -1)),
                crs,
                bounds,
                resolution,
            ),
        }
    )

    # Apply no precipitation polygon zone
    polygon_mask = make_mask_from_polygon(crs, ds, polygon) 
    

    # Expand mask to include time dimension 
    mask_expanded = polygon_mask.expand_dims(dim={"time": ds.time})

    # Apply mask to precipitation (set precip to zero where)
    logger.info("Applying zero precipitation outside the shapefile.")

    # Create a copy of the precipitation data
    precip_masked = ds["precipitation"].copy(deep=True)

    # Set precipitation to zero outside the polygon.
    precip_masked = precip_masked.where(mask_expanded, 0)
    ds["precipitation"] = precip_masked

    # The time bounds are a function to map the monthly data to the start of each month,
    # with index 0 mapping to the first 31 days, index 1 to the next 28 days, etc..
    # The 0 is added to the start to make the bounds inclusive.
    months = np.array(
        [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], dtype=np.int32
    )
    months_cumsum = months.cumsum()
    bounds = np.stack((months_cumsum[:-1], months_cumsum[1:])).T

    # The time bounds map to the start of each month.
    ds = ds.assign_coords(
        time=(("time"), bounds[:, 0]), time_bounds=(("time", "nv"), bounds)
    )
    ds.time.attrs.update(
        bounds="time_bounds",
        units="days since 1-1-1",
        standard_name="time",
        calendar="noleap",
    )
    # convert precipitation to kg m-2 day-1 by equally distributing the monthly
    # values across the days.
    ds["precipitation"] /= xr.DataArray(months[1:], coords={"time": ds.time})

    # set variable attributes
    ds.air_temp.attrs.update(
        long_name="near-surface air temperature",
        standard_name="air_temperature",
        units="degC",
    )
    ds.precipitation.attrs.update(
        long_name="mean annual precipitation rate",
        standard_name="precipitation_flux",
        units="kg m-2 day-1",
    )
    ds.elevation.attrs.update(
        long_name="ice surface altitude", standard_name="surface_altitude", units="m"
    )

    return ds


def read_chelsa_var(chelsa_dir: Path, variable: str) -> xr.DataArray:
    """
    Read the CHLSA variable data from the specified directory.

    Parameters:
        chelsa_dir (Path): The directory containing the CHLSA data files.
        variable (str): The name of the variable to read.

    Returns:
        xr.DataArray: The CHLSA variable data as a DataArray.
    """
    chelsa_paths = list(
        chelsa_dir.glob(
            ("CHELSA_{variable}_*_1981-2010_V.2.1.tif").format(variable=variable)
        )
    )
    start = perf_counter()
    logger.info(f"Reading {variable} from {len(chelsa_paths)} CHELSA tiff files")
    ds = xr.open_mfdataset(
        chelsa_paths,
        combine="nested",
        concat_dim="time",
        decode_cf=True,
        coords="all",
    )
    logger.info(f"Read {variable} in {perf_counter() - start:.2f} seconds")
    return ds.band_data.squeeze()


def dev():
    """Development function to create and save the clipped atmosphere dataset."""
    chelsa_dir = Path("chelsa")
    if not chelsa_dir.exists():
        raise FileNotFoundError(
            "CHELSA directory not found. Please download the data first."
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

    # # UTM-32 projection, WGS 84 datum
    # crs = "EPSG:32632"
    # # west, south, east, north bounds of the alps.
    # bounds = [150e3, 4820e3, 1050e3, 5420e3]

    ds = create_cliped_atmosphere(
        crs=crs, bounds=bounds, resolution=1000 
    )

    # save to netcdf with float dtypes for all keys.
    ds.to_netcdf(
        "atm.nc", encoding={key: {"dtype": "f4"} for key in ds.data_vars.keys()}
    )

if __name__ == "__main__":
    dev()
