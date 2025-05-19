import rasterio
import pyproj
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import numpy as np

# Input raster file (ice thickness GeoTIFF)
raster_path = "thk-001950.tif"

# Output shapefile
output_shapefile = "caucasus_ice_extent_test_2.shp"

# Step 1: Open raster and read data
with rasterio.open(raster_path) as src:
    ice = src.read(1)  # read first band
    mask = ice > 0     # create mask where ice is present
    transform = src.transform

# Step 2: Extract shapes (polygons) from mask
polygons = shapes(ice, mask=mask, transform=transform)

# Step 3: Convert shapes to geometries
geometries = [shape(geom) for geom, val in polygons]

# Optional: merge multiple polygons into one multipolygon
gdf = gpd.GeoDataFrame(geometry=geometries, crs=src.crs)
gdf = gdf.dissolve()  # merge into a single extent
gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:32638")

# Step 4: Save to shapefile
gdf.to_file(output_shapefile)

print("Ice extent shapefile saved:", output_shapefile)

