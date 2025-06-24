from pathlib import Path
import xarray as xr
from time import perf_counter

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEBCO_PATH = Path("../../gebco/GEBCO_2023_sub_ice_topo.nc")


def save_clipped_bootstrap(
    bounds: list[float], output_filepath: Path, resolution: int = 1000
):
    """Create and save a clipped bootstrap dataset to a netCDF file.
    Clips from the GEBCO dataset as found at gebco/GEBCO_2023_sub_ice_topo.nc

    Parameters:
        bounds (list[int]): The bounding box coordinates [west, south, east, north]
            to clip the data array to.
        output_filepath (Path): The path to save the netCDF file to.
        resolution (int): The resolution of the output data array.
    """
    # Create xarray and save to netcdf

    xr.Dataset(
        {"topg": create_cliped_bootstrap(GEBCO_PATH, bounds, output_filepath, resolution)}
    ).to_netcdf(
        output_filepath,
    )


def create_cliped_bootstrap(
    gebco_path: Path, bounds: list[float], outputh_filepath, resolution: int
):
    """Create a clipped version of the GEBCO dataset.

    Parameters:
        gebco_path (Path): The path to the GEBCO dataset.
        bounds (list[int]): The bounding box coordinates [west, south, east, north]
            to clip the data array to.
        resolution (int): The resolution of the output data array.

    Returns:
        xr.DataArray: The reprojected and clipped data array.
    """

    start = perf_counter()
    gebco_da = xr.open_dataarray(gebco_path, decode_coords="all", decode_cf=True).rio.write_crs( "WGS84")
    logger.info(f"Original GEBCO data size: {gebco_da.shape}") 
    # Extract bounds
    west, south, east, north = bounds

    logger.info(f"bounds are {bounds}")
    logger.info(f"west south east north are {west}, {south}, {east}, {north}")
    # Clip the data array using coordinate selection
    # Assuming the coordinate names are 'lon' and 'lat' (adjust if different)
    clipped_da = gebco_da.sel(
        lon=slice(west, east),
        lat=slice(south, north)
    )
    logger.info(f"Clipped GEBCO data size: {clipped_da.shape}")
    gebco_da.attrs.update(standard_name="bedrock_altitude")

    logger.info(
        f"Loading and clipping GEBCO took {perf_counter() - start:.2f} seconds."
    )
    return clipped_da


def dev():
    bounds = [-74.507665, 9.180996, -71.911844, 11.570751]
    output_path = Path("./test_topography.nc")
    save_clipped_bootstrap(bounds, output_path, 1000)


if __name__ == "__main__":
    dev()
