from pathlib import Path
import pandas as pd
import urllib.request
import xarray as xr
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

import logging
from scipy.interpolate import interp1d

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EPICA_URL = "ftp://ftp.ncdc.noaa.gov/pub/data/paleo/icecore/antarctica/epica_domec/edc3deuttemp2007.txt"


def download_epica(epica_dir: Path):
    """
    Download the EPICA data from the NOAA FTP server.

    Parameters:
        epica_dir (Path): The directory to save the EPICA data.
    """

    epica_dir.mkdir(parents=True, exist_ok=True)

    # Download the csv-like file from the epica endpoint
    # Open the file using urlopen
    logger.info("Downloading EPICA data")
    file_content = urllib.request.urlopen(EPICA_URL)

    epica_filename = EPICA_URL.split("/")[-1]

    with open(epica_dir / epica_filename, "wb") as f:
        f.write(file_content.read())


def epica_to_netcdf(epica_dir: Path, output_filepath: Path, plot=False):
    """
    Convert EPICA data to yearly netCDF data.

    Args:
        epica_filepath (Path): The file path of the EPICA data file.
        output_filepath (Path): The file path to save the netCDF output.
        plot (bool, optional): Whether to plot the data. Defaults to False.
    """
    logger.info("Reading EPICA data into list.")
    # Read the data into a list
    data = np.genfromtxt(epica_dir / EPICA_URL.split("/")[-1], skip_header=92, usecols=(2, 4), invalid_raise=False, missing_values=np.nan)
    # Remove rows with NaN values
    data = data[~np.isnan(data).any(axis=1)]

    logger.info("Converting EPICA data to yearly CSV data.")
    # Negate the age column to get the time column
    times = [-age for age, _ in data]
    temperatures = [temp for _, temp in data]

    # Extract yearly temperature data by interpolating the temperature at each year
    d_t_range = np.arange(-130000, -38)

    # Create an interpolation function
    interp_func = interp1d(times, temperatures, kind='linear', fill_value="extrapolate")

    # Interpolate the temperature at the given time using vectorized approach
    delta_T = interp_func(d_t_range)

    # Create xray Dataset
    logger.info("Creating xarray Dataset from numpy array.")
    ds = xr.Dataset(
        {
            "delta_T": ("time", delta_T),
        },
        coords={"time": d_t_range},
    )
    
    # Add attributes to the dataset
    bounds = np.stack((d_t_range, d_t_range)).T
    ds = ds.assign_coords(
            time=(("time",), d_t_range), time_bounds=(("time", "nv"), bounds)
        )
    ds.time.attrs.update(
        units="365 days since 1950-1-1",
        standard_name="time",
        long_name="Time (years since 1950)",
        calendar="365_day",
        bounds="time_bounds",
    )
    ds.delta_T.attrs.update(
        units="Kelvin",
        long_name="Temperature (variation from 1950-1980 avg.) (Delta T (K))",
    )
    # Save to netCDF
    ds.to_netcdf(
        output_filepath,
        encoding={"time": {"dtype": "i4"}, "delta_T": {"dtype": "f4"}},
    )


def plot_epica(df):
    # Set the theme
    sns.set_theme()
    # plot Age vs Temperature
    sns.lineplot(data=df, x="Age", y="Temperature")
    # set the title
    plt.title("EPICA \u0394T(C\u00b0) from 1000 year average")
    # set the x-axis label
    plt.xlabel("Age (years before 1950) kyr")
    # set the y-axis label
    plt.ylabel("Delta Temperature (C\u00b0)")

    # Divide the x-label by 1000 from 0 to 800000
    plt.xticks(
        ticks=[i for i in range(0, 800001, 100000)],
        labels=[f"{str(i)}ka" for i in range(0, 801, 100)],
    )

    # show the plot
    plt.show()


if __name__ == "__main__":
    epica_to_netcdf(Path("./epica"), Path("dT_epica.nc"), plot=False)
