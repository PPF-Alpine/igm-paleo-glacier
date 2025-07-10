from pathlib import Path
import xarray as xr
import rioxarray as rxr
import numpy as np
from time import perf_counter
import os
import geopandas as gpd
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_mask

from .clip_bounds_and_reproject import clip_and_reproject_data_array 

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_clipped_model_anomaly(
    crs: str, 
    bounds: list[int], 
    modeled_anomaly_filepath: Path, 
    output_filepath: Path, 
    resolution: int = 1000
):
    """Create and save clipped model lgm/historical atmosphere dataset to a netCDF file.

    Parameters:
        crs (str): The coordinate reference system of the dataset.
        bounds (list[int]): The bounding box coordinates [xmin, ymin, xmax, ymax].
        lgm_filepath (Path): 
        historical_filepath (Path): 
        output_filepath (Path): The path to save the netCDF file.
        resolution (int, optional): The resolution of the clipped dataset. Defaults to 1000.
    """
    # Create xarray and save to netcdf

    # Fix for rasterio using incorrect SRS source for GTiff files.
    os.environ["GTIFF_SRS_SOURCE"] = "EPSG"

    # Create and save clipped atmosphere  
    anomaly_atmosphere = clip_atmosphere_to_bounds(crs, bounds, modeled_anomaly_filepath, resolution)
    anomaly_atmosphere.to_netcdf(
        output_filepath, encoding={key: {"dtype": "f4"} for key in anomaly_atmosphere.data_vars.keys()}
    )
def clip_atmosphere_to_bounds(crs, bounds, modeled_anomaly_filepath, resolution):
    """
    Clip atmospheric NetCDF data to specified bounds and reproject to target CRS.
    
    Parameters:
    -----------
    crs : str or pyproj.CRS
        Target coordinate reference system (e.g., 'EPSG:4326' or 'EPSG:3857')
    bounds : tuple or list
        Bounds in the target CRS as (min_x, min_y, max_x, max_y)
    modeled_anomaly_filepath : str
        Path to the NetCDF file containing atmospheric data
    resolution : float
        Target resolution in meters (e.g., 1000 for 1km)
    
    Returns:
    --------
    xarray.Dataset
        Clipped and reprojected atmospheric data
    """
    
    # Load the NetCDF file
    ds = xr.open_dataset(modeled_anomaly_filepath)

    ds["pr"] *= 31556952.0  # unit to [ kg * m^(-2) * s^(-1) ] -> [ kg * m^(-2) * y^(-1) ]
    # TODO: change thte name to precipitation and temperature 
    
    # Identify spatial data variables (those with both lat and lon dimensions)
    spatial_vars = []
    for var in ds.data_vars:
        if 'lat' in ds[var].dims and 'lon' in ds[var].dims:
            spatial_vars.append(var)
    
    # Process only spatial variables
    if not spatial_vars:
        raise ValueError("No spatial variables found in the dataset")
    
    # Create a new dataset with only spatial variables and coordinates
    spatial_ds = ds[spatial_vars + ['lat', 'lon', 'time']]

    #TODO: Treat units here
    
    # Set the CRS for the spatial data
    spatial_ds = spatial_ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
    spatial_ds = spatial_ds.rio.write_crs("EPSG:4326")
    
    # If target CRS is different from source, convert bounds to lat/lon first
    if str(crs).upper() != "EPSG:4326":
        from pyproj import Transformer
        # Transform bounds from target CRS to lat/lon for initial clipping
        transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        min_x, min_y, max_x, max_y = bounds
        
        # Transform corners to get lat/lon bounding box
        corners = [
            (min_x, min_y),
            (min_x, max_y),
            (max_x, min_y),
            (max_x, max_y)
        ]
        
        transformed_corners = [transformer.transform(x, y) for x, y in corners]
        lons, lats = zip(*transformed_corners)
        
        # Get bounding box in lat/lon
        lon_bounds = (min(lons), max(lons))
        lat_bounds = (min(lats), max(lats))
        
        print(f"Original bounds in {crs}: {bounds}")
        print(f"Transformed to lat/lon: lon={lon_bounds}, lat={lat_bounds}")
        print(f"Data lon range: {spatial_ds.lon.min().values:.3f} to {spatial_ds.lon.max().values:.3f}")
        print(f"Data lat range: {spatial_ds.lat.min().values:.3f} to {spatial_ds.lat.max().values:.3f}")
        
        # Handle longitude coordinate system conversion
        lon_min, lon_max = lon_bounds
        lat_min, lat_max = lat_bounds
        
        # Check if data uses 0-360 longitude system
        if spatial_ds.lon.min().values >= 0 and spatial_ds.lon.max().values > 180:
            # Data is 0-360, convert negative longitudes to 0-360
            if lon_min < 0:
                lon_min = lon_min + 360
            if lon_max < 0:
                lon_max = lon_max + 360
            print(f"Converted to 0-360 system: lon=({lon_min}, {lon_max})")
        
        # Check if bounds overlap with data after conversion
        if (lon_max < spatial_ds.lon.min().values or 
            lon_min > spatial_ds.lon.max().values or
            lat_bounds[1] < spatial_ds.lat.min().values or 
            lat_bounds[0] > spatial_ds.lat.max().values):
            raise ValueError("Bounds do not overlap with data extent")
        
        # Expand bounds to ensure we get at least 3x3 pixels for reprojection
        # Calculate data resolution
        lon_res = abs(spatial_ds.lon.values[1] - spatial_ds.lon.values[0])
        lat_res = abs(spatial_ds.lat.values[1] - spatial_ds.lat.values[0])
        
        print(f"Data resolution: lon={lon_res:.3f}°, lat={lat_res:.3f}°")
        
        # Expand bounds by 2 pixels in each direction
        buffer_lon = 2 * lon_res
        buffer_lat = 2 * lat_res
        
        lon_min_expanded = lon_min - buffer_lon
        lon_max_expanded = lon_max + buffer_lon
        lat_min_expanded = lat_min - buffer_lat
        lat_max_expanded = lat_max + buffer_lat
        
        print(f"Expanded bounds: lon=({lon_min_expanded}, {lon_max_expanded}), lat=({lat_min_expanded}, {lat_max_expanded})")
        
        # Select data within expanded bounds
        lon_mask = (spatial_ds.lon >= lon_min_expanded) & (spatial_ds.lon <= lon_max_expanded)
        lat_mask = (spatial_ds.lat >= lat_min_expanded) & (spatial_ds.lat <= lat_max_expanded)
        
        spatial_ds = spatial_ds.sel(
            lon=spatial_ds.lon[lon_mask],
            lat=spatial_ds.lat[lat_mask]
        )
        
        print(f"After clipping: {spatial_ds.dims}")
        
        # Check if we still have data
        if spatial_ds.lon.size == 0 or spatial_ds.lat.size == 0:
            raise ValueError("No data remaining after initial clipping")
        
        # Now reproject the smaller dataset
        spatial_ds = spatial_ds.rio.reproject(crs, resolution=resolution)
        
        # Final precise clip in target CRS
        ds_clipped = spatial_ds.rio.clip_box(
            minx=min_x,
            miny=min_y,
            maxx=max_x,
            maxy=max_y,
            crs=crs
        )
    else:
        # Direct clipping in lat/lon
        min_x, min_y, max_x, max_y = bounds
        ds_clipped = spatial_ds.rio.clip_box(
            minx=min_x,
            miny=min_y,
            maxx=max_x,
            maxy=max_y,
            crs=crs
        )
    
    return ds_clipped


  
def create_cliped_atmosphere_old( #TODO: This function is copied and needs to be heavily modiefied before testing
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
    Returns:
        xr.Dataset: The clipped atmosphere dataset.
    """

    # combine into dataset
    ds = xr.Dataset(
        {
            "air_temp": clip_and_reproject_data_array(
                read_chelsa_var(chelsa_dir=chelsa_filepath, variable="tas"),
                crs,
                bounds,
                resolution,
            ),
            "precipitation": clip_and_reproject_data_array(
                read_chelsa_var(chelsa_dir=chelsa_filepath, variable="pr"),
                crs,
                bounds,
                resolution,
            ),
            "elevation": clip_and_reproject_data_array(
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
