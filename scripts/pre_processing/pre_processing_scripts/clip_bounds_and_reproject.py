import xarray as xr
import affine


def clip_and_reproject_data_array(
    da: xr.DataArray, crs: str, bounds: list[int], resolution: int
):
    """
    Reprojects a data array to a new coordinate reference system (CRS) and
    clips it to the specified bounds.

    Parameters:
        da (xr.DataArray): The input data array to be reprojected.
        crs (str): The target CRS to reproject the data array to.
        bounds (list[int]): The bounding box coordinates [west, south, east, north]
            to clip the data array to.
        resolution (int): The resolution of the output data array.

    Returns:
        xr.DataArray: The reprojected and clipped data array.
    """

    # clip the data array to the bounds
    da = da.rio.clip_box(*bounds, crs=crs)

    # compute affine transform
    west, south, east, north = bounds
    transform = affine.Affine(resolution, 0, west, 0, resolution, south)

    # compute output shape
    cols = int((east - west) / resolution)
    rows = int((north - south) / resolution)
    shape = (rows, cols)

    # return reprojected data with new crs
    return da.rio.reproject(crs, transform=transform, resampling=1, shape=shape)
