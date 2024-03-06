from pathlib import Path
from tqdm import tqdm
import pandas as pd
import urllib.request
import xarray as xr
import numpy as np

import logging

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
    logger.info("Converting EPICA data to pandas DataFrame.")
    # Convert the data to a pandas dataframe
    df = pd.read_csv(
        epica_dir / EPICA_URL.split("/")[-1],
        skiprows=91,
        delim_whitespace=True,
    )

    if plot:
        plot_epica(df)  # Plot the data

    logger.info("Converting EPICA data to yearly netCDF data.")
    # Negate the age column to get the time column
    df["time"] = df["Age"] * -1
    # Extract yearly temperature data by interpolating the temperature at each year
    dt = []
    df_index = 12

    d_t_range = np.arange(-130000, -38)

    for time in tqdm(d_t_range[:-1], leave=False):
        # Check to see if the time is within the range of the current and next time
        if time < df.iloc[df_index + 1]["time"]:
            # If not, increment the index
            df_index += 1
        # Get the upper and lower bounds of the time
        upper = df.iloc[df_index]
        lower = df.iloc[df_index + 1]

        # Calculate the temperature at the time by doing a linear interpolation
        delta_T = lower["Temperature"] + (
            upper["Temperature"] - lower["Temperature"]
        ) * (time - lower["time"]) / (upper["time"] - lower["time"])

        # recalculate the delta_T from celsius to kelvin
        delta_T += 273.15

        dt.append(
            {
                "time": time,
                "delta_T": delta_T,
            }
        )

    # Create a new DataFrame
    df_dt = pd.DataFrame(dt)
    # Use the Age column as the index
    df_dt = df_dt.set_index("time")
    df_dt.sort_index(inplace=True)

    # Create xray Dataset from Pandas DataFrame
    ds = xr.Dataset.from_dataframe(df_dt)
    # Add attributes to the dataset
    bounds = np.stack((d_t_range[:-1], d_t_range[1:])).T
    ds = ds.assign_coords(
        time=(("time"), d_t_range[:-1]), time_bounds=(("time", "nv"), bounds)
    )
    ds.time.attrs.update(
        units="365 days since 1950-1-1",
        standard_name="time",
        long_name="Time (years since 1950)",
        calendar="365_day",
        bounds="time_bounds",
    )
    ds.delta_T.attrs.update(
        units="degC",
        long_name="Temperature (variation from 1950-1980 avg.) (Celsius)",
    )
    # Save to netCDF
    ds.to_netcdf(
        output_filepath,
        encoding={"time": {"dtype": "i4"}, "delta_T": {"dtype": "f4"}},
    )


def plot_epica(df):
    import seaborn as sns
    from matplotlib import pyplot as plt

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
    download_epica_to_netcdf(Path("dT_epica.nc"), plot=True)
