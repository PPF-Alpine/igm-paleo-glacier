from pathlib import Path
import xarray as xr
import geopandas as gpd
import rioxarray
from time import perf_counter

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clip_with_polygon(da: xr.DataArray, polygon_path: Path, crs: str = None):
    """
    Clip a data array using a polygon from a shapefile or GeoJSON
    
    Parameters:
    -----------
    da : xr.DataArray
        The input data array to be clipped
    polygon_path : Path
        Path to the polygon file (shapefile or GeoJSON)
    crs : str, optional
        CRS to reproject the polygon to if different from the data array
        
    Returns:
    --------
    xr.DataArray
        The clipped data array
    """
    start = perf_counter()
    
    # Read the polygon
    gdf = gpd.read_file(polygon_path)
    logger.info(f"Loaded polygon from {polygon_path}, CRS: {gdf.crs}")
    
    # Make sure the data array has spatial coordinates and CRS
    if not hasattr(da, 'rio'):
        raise ValueError("Data array does not have rioxarray extension")
    
    if not da.rio.crs:
        raise ValueError("Data array does not have a CRS set")
    
    # If CRS was provided, convert GeoDataFrame to that CRS, otherwise use the data array's CRS
    target_crs = crs if crs else da.rio.crs
    logger.info(f"Target CRS: {target_crs}")
    
    # Check if the GeoDataFrame has a CRS, if not, assign the target CRS
    if gdf.crs is None:
        logger.warning(f"Shapefile has no CRS defined. Assuming it's already in the target CRS: {target_crs}")
        gdf.set_crs(target_crs, inplace=True)
    elif target_crs != gdf.crs:
        logger.info(f"Reprojecting from {gdf.crs} to {target_crs}")
        gdf = gdf.to_crs(target_crs)
    
    # Clip the data array with the polygon
    clipped_da = da.rio.clip(gdf.geometry, crs=target_crs)
    
    logger.info(f"Clipping with polygon took {perf_counter() - start:.2f} seconds")
    
    return clipped_da


def save_clipped_atmosphere_with_polygon(polygon_path, crs, output_filepath, resolution=1000):
    """
    Clip atmosphere data using a polygon from a shapefile or GeoJSON
    
    Parameters:
    -----------
    polygon_path : Path
        Path to the polygon file (shapefile or GeoJSON)
    crs : str
        CRS for the output data
    output_filepath : Path
        Path to save the clipped data
    resolution : int, default=1000
        Resolution in meters per pixel
    """
    from .clip_atmosphere_to_bounds import create_cliped_atmosphere, CHELSA_DIR, PBCOR_PATH
    import os
    
    # Fix for rasterio using incorrect SRS source for GTiff files.
    os.environ["GTIFF_SRS_SOURCE"] = "EPSG"
    
    # Get bounds from the polygon file for initial rough clipping (to reduce memory usage)
    gdf = gpd.read_file(polygon_path)
    logger.info(f"Read polygon with CRS: {gdf.crs}")
    
    # Check if the GeoDataFrame has a CRS, if not, assign the target CRS
    if gdf.crs is None:
        logger.warning(f"Shapefile has no CRS defined. Assuming it's already in the target CRS: {crs}")
        gdf.set_crs(crs, inplace=True)
    elif crs != gdf.crs:
        logger.info(f"Reprojecting polygon from {gdf.crs} to {crs}")
        gdf = gdf.to_crs(crs)
    
    # Get bounds for rough initial clipping
    minx, miny, maxx, maxy = gdf.total_bounds
    bounds = [minx, miny, maxx, maxy]
    logger.info(f"Calculated bounds: {bounds}")
    
    # Check if bounds are valid
    if minx >= maxx or miny >= maxy:
        raise ValueError(f"Invalid bounds calculated from polygon: {bounds}")
    
    # Check for very small bounds that might result in 0x0 dimensions
    width = maxx - minx
    height = maxy - miny
    logger.info(f"Bounds width: {width}, height: {height}")
    
    if width < 0.001 or height < 0.001:  # Arbitrary small threshold for EPSG:4326
        raise ValueError(f"Bounds are too small, might result in 0x0 dimensions: width={width}, height={height}")
    
    # Create the clipped atmosphere dataset using the existing function
    logger.info(f"Creating clipped atmosphere with crs={crs}, bounds={bounds}, resolution={resolution}")
    ds = create_cliped_atmosphere(crs=crs, bounds=bounds, resolution=resolution, apply_pbcor=True)
    
    # Further clip using the exact polygon
    clipped_ds = xr.Dataset()
    for var in ds.data_vars:
        clipped_ds[var] = clip_with_polygon(ds[var], polygon_path, crs)
    
    # Copy coordinates and attributes
    clipped_ds.coords["time"] = ds.coords["time"]
    if "time_bounds" in ds.coords:
        clipped_ds.coords["time_bounds"] = ds.coords["time_bounds"]
    
    # Preserve variable attributes
    for var in clipped_ds.data_vars:
        clipped_ds[var].attrs = ds[var].attrs
    
    # Save to file
    clipped_ds.to_netcdf(
        output_filepath, encoding={key: {"dtype": "f4"} for key in clipped_ds.data_vars.keys()}
    )
    
    logger.info(f"Saved clipped atmosphere data to {output_filepath}")


def save_clipped_bootstrap_with_polygon(polygon_path, crs, output_filepath, resolution=1000):
    """
    Clip bootstrap data using a polygon from a shapefile or GeoJSON
    
    Parameters:
    -----------
    polygon_path : Path
        Path to the polygon file (shapefile or GeoJSON)
    crs : str
        CRS for the output data
    output_filepath : Path
        Path to save the clipped data
    resolution : int, default=1000
        Resolution in meters per pixel
    """
    from .clip_bootstrap_to_bounds import create_cliped_bootstrap, GEBCO_PATH
    
    # Get bounds from the polygon file for initial rough clipping (to reduce memory usage)
    gdf = gpd.read_file(polygon_path)
    logger.info(f"Read polygon with CRS: {gdf.crs}")
    
    # Check if the GeoDataFrame has a CRS, if not, assign the target CRS
    if gdf.crs is None:
        logger.warning(f"Shapefile has no CRS defined. Assuming it's already in the target CRS: {crs}")
        gdf.set_crs(crs, inplace=True)
    elif crs != gdf.crs:
        logger.info(f"Reprojecting polygon from {gdf.crs} to {crs}")
        gdf = gdf.to_crs(crs)
    
    # Get bounds for rough initial clipping
    minx, miny, maxx, maxy = gdf.total_bounds
    bounds = [minx, miny, maxx, maxy]
    logger.info(f"Calculated bounds: {bounds}")
    
    # Check if bounds are valid
    if minx >= maxx or miny >= maxy:
        raise ValueError(f"Invalid bounds calculated from polygon: {bounds}")
    
    # Check for very small bounds that might result in 0x0 dimensions
    width = maxx - minx
    height = maxy - miny
    logger.info(f"Bounds width: {width}, height: {height}")
    
    if width < 0.001 or height < 0.001:  # Arbitrary small threshold for EPSG:4326
        raise ValueError(f"Bounds are too small, might result in 0x0 dimensions: width={width}, height={height}")
    
    # Create the clipped bootstrap data using the existing function
    logger.info(f"Creating clipped bootstrap with crs={crs}, bounds={bounds}, resolution={resolution}")
    topg_da = create_cliped_bootstrap(GEBCO_PATH, crs, bounds, resolution)
    
    # Further clip using the exact polygon
    clipped_topg = clip_with_polygon(topg_da, polygon_path, crs)
    
    # Create a dataset and save to file
    xr.Dataset({"topg": clipped_topg}).to_netcdf(output_filepath)
    
    logger.info(f"Saved clipped bootstrap data to {output_filepath}")