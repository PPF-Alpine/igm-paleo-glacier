# helper function for creating a mask from a polygon
# sjurbarndon@proton.me 

import xarray as xr
import numpy as np
import os
import geopandas as gpd
import rasterio
from pathlib import Path
from rasterio.features import geometry_mask
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_mask_from_polygon(crs: str,  dataset: xr.DataArray, polygon=None) -> xr.DataArray :
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
        x_coords = dataset.x.values
        y_coords = dataset.y.values
        
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

        return mask_da
