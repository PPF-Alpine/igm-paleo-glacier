from pathlib import Path
import xarray as xr
import numpy as np
from time import perf_counter
import os
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask

from .clip_bounds import reproject_data_array 

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHELSA_DIR = Path("chelsa")
PBCOR_PATH = Path("pbcor/CHELSA_V12.nc")


def save_clipped_atmosphere(
    crs: str, bounds: list[int], output_filepath: Path, polygon=None, resolution: int = 1000
):
    """Create and save a clipped atmosphere dataset to a netCDF file.

    Parameters:
        crs (str): The coordinate reference system of the dataset.
        bounds (list[int]): The bounding box coordinates [xmin, ymin, xmax, ymax].
        output_filepath (Path): The path to save the netCDF file.
        polygon (.shp): Shape file for clipping further within the bounds.
        resolution (int, optional): The resolution of the clipped dataset. Defaults to 1000.
    """
    # Create xarray and save to netcdf

    # Fix for rasterio using incorrect SRS source for GTiff files.
    os.environ["GTIFF_SRS_SOURCE"] = "EPSG"

    ds = create_cliped_atmosphere(crs, bounds, resolution, polygon=polygon, apply_pbcor=True)

    ds.to_netcdf(
        output_filepath, encoding={key: {"dtype": "f4"} for key in ds.data_vars.keys()}
    )


def create_cliped_atmosphere(
    crs: str,
    bounds: list[int],
    resolution: int,
    polygon=None,
    apply_pbcor: bool = False,
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
                read_chelsa_var(chelsa_dir=CHELSA_DIR, variable="tas"),
                crs,
                bounds,
                resolution,
            ),
            "precipitation": reproject_data_array(
                read_chelsa_var(chelsa_dir=CHELSA_DIR, variable="pr"),
                crs,
                bounds,
                resolution,
            ),
            "elevation": reproject_data_array(
                xr.open_dataarray(
                    CHELSA_DIR / "dem_latlong.nc", decode_coords="all"
                ).isel(lat=slice(None, None, -1)),
                crs,
                bounds,
                resolution,
            ),
        }
    )
    if apply_pbcor:
        da_precipitation_cor = reproject_data_array(
            read_pbcor_precipitation(PBCOR_PATH), crs, bounds, resolution
        )
        # apply the correction factor to the precipitation data
        ds["precipitation"] *= da_precipitation_cor
    
    logger.info(f"DEBUG: output of polygon is - {polygon}")
    logger.info(f"DEBUG: polygon type is - {type(polygon)}")

    # Apply no precipitation polygon zone
    if polygon is not None:
        # If polygon is a file path, load:
        if isinstance(polygon, (str, Path)):
            logger.info(f"Loading polygon shapefile from {polygon}")
            gdf = gpd.read_file(polygon)
        else:
            # assuming it is already a GeoDataFrame
            gdf = polygon

        # Ensure that the polygon is in the same CRS as the dataset.
        if gdf.crs != crs:
            logger.info(f"Reprojecting polygon from {gdf.crs} to {crs}")
            gdf = gdf.to_crs(crs)

        # Create a mask from the polygon
        # Get the x and y coordinates from the dataset
        x_coords = ds.x.values
        y_coords = ds.y.values
        
        y_ascending = y_coords[0] < y_coords[-1]
        logger.info(f"Y coordinates are in {'ascending' if y_ascending else 'descending'} order")

        # Create a meshgrid for coordinates
        #xx, yy = np.meshgrid(x_coords, y_coords)

        # Create a mask where True is the outside of the polygon and False is inside
        mask = np.ones((len(y_coords), len(x_coords)), dtype=bool)


        # Create a mask array with same shape as data
        height, width = len(y_coords), len(x_coords)
        mask = np.ones((height, width), dtype=bool)  # Initialize as all True

        # Create rasterio transform
        transform = rasterio.transform.from_origin(
            x_coords.min(),  # left
            y_coords.max() if y_ascending else y_coords.min(),  # top
            (x_coords.max() - x_coords.min()) / (width - 1),  # pixel width
            (y_coords.max() - y_coords.min()) / (height - 1)  # pixel height
        )
    
        logger.info(f"Transform: {transform}")
        logger.info(f"Mask shape: {mask.shape}")

        for idx, geom in enumerate(gdf.geometry):
            logger.info(f"Processing geometry {idx+1}/{len(gdf.geometry)}")

            # Create a mask for this geometry (True = outside polygon)
            geom_mask = geometry_mask(
                    [geom],
                    out_shape=(height, width),
                    transform = transform,
                    invert=False # Make False = outside the polygon
            )
            # If the mask needs to be flipped to match dataset orientation
            if y_ascending:
                logger.info("Flipping mask to match dataset orientation")
                geom_mask = np.flipud(geom_mask)
            
            # Update the overall mask (This works as intended) 
            mask = mask & (~geom_mask) 
                        
        # Convert maks to xarray format matching our dataset dimensions
        mask_da = xr.DataArray(
                mask,
                dims=['y', 'x'],
                coords={'y': y_coords, 'x': x_coords}

        )

        # Expand mask to include time dimension 
        mask_expanded = mask_da.expand_dims(dim={"time": ds.time})

        # Apply maks to precipitation (set precip to zero where)
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


def read_pbcor_precipitation(pbcor_path: Path) -> xr.DataArray:
    """
    Read the PBCOR corr_fac_monthly data from the specified path.

    Parameters:
        pbcor_path (Path): The path to the PBCOR data file.

    Returns:
        xr.DataArray: The PBCOR variable precipitation data as a DataArray.
    """
    start = perf_counter()
    logger.info(f"Reading precipitation correction factor from {pbcor_path}")
    da = xr.open_dataset(pbcor_path, decode_coords="all").corr_fac_monthly
    # change from lon/lat to x/y coordinates names
    da = da.rename({"lon": "x", "lat": "y"})

    # Fill the missing values with 1.0
    da = da.fillna(1.0).rio.write_crs("WGS84")

    logger.info(
        f"Read precipitation correction factor from PBCOR in {perf_counter() - start:.2f} seconds"
    )
    return da


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
        crs=crs, bounds=bounds, resolution=1000, apply_pbcor=True
    )

    # save to netcdf with float dtypes for all keys.
    ds.to_netcdf(
        "atm.nc", encoding={key: {"dtype": "f4"} for key in ds.data_vars.keys()}
    )


if __name__ == "__main__":
    dev()
