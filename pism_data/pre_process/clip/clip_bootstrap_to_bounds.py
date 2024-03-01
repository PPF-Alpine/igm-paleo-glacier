from pathlib import Path
import xarray as xr
from time import perf_counter

from .clip_bounds import reproject_data_array

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEBCO_PATH = Path("gebco/GEBCO_2023_sub_ice_topo.nc")


def save_clipped_bootstrap(
    crs: str, bounds: list[int], output_filepath: Path, resolution: int = 1000
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
    # Create xarray and save to netcdf

    xr.Dataset(
        {"bedrock": create_cliped_bootstrap(GEBCO_PATH, crs, bounds, resolution)}
    ).to_netcdf(
        output_filepath,
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
    gebco_da = reproject_data_array(
        # open the data array and set the CRS to WGS84
        xr.open_dataarray(gebco_path, decode_coords="all", decode_cf=True).rio.set_crs(
            "WGS84"
        ),
        crs,
        bounds,
        resolution,
    )
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
