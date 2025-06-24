from pathlib import Path
import urllib.request
import numpy as np
import logging
from scipy.interpolate import interp1d

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EPICA_URL = "ftp://ftp.ncdc.noaa.gov/pub/data/paleo/icecore/antarctica/epica_domec/edc3deuttemp2007.txt"


def download_epica(epica_dir: Path):
    """
    Download the EPICA data from the NOAA FTP server and save it to the specified directory.

    Parameters:
        epica_dir (Path): The directory to save the EPICA data.
    """
    epica_dir.mkdir(parents=True, exist_ok=True)

    # Download the csv-like file from the EPICA endpoint
    logger.info("Downloading EPICA data")
    file_content = urllib.request.urlopen(EPICA_URL)

    epica_filename = EPICA_URL.split("/")[-1]

    with open(epica_dir / epica_filename, "wb") as f:
        f.write(file_content.read())


def epica_to_yearly_csv(epica_dir: Path):
    """
    Convert EPICA data to yearly CSV files with different intervals.

    Parameters:
        epica_dir (Path): The directory containing the downloaded EPICA data file.
    """
    epica_filename = EPICA_URL.split("/")[-1]
    epica_filepath = epica_dir / epica_filename

    # Check if the file exists, if not, download it
    if not epica_filepath.exists():
        logger.info("EPICA data file not found, downloading...")
        download_epica(epica_dir)

    logger.info("Reading EPICA data into list.")
    # Read the data into a list
    data = np.genfromtxt(epica_filepath, skip_header=92, usecols=(2, 4), invalid_raise=False, missing_values=np.nan)
    # Remove rows with NaN values
    data = data[~np.isnan(data).any(axis=1)]
    print(data)

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

    # Combine the time and temperature data
    dt = np.column_stack((d_t_range, delta_T))

    # Output the data to CSV files with different intervals
    np.savetxt(epica_dir / "epica_data.csv", dt, fmt='%d,%.6f', delimiter=",", header="time,delta_T", comments='')
    np.savetxt(epica_dir / "epica_data_100.csv", dt[::100], fmt='%d,%.6f', delimiter=",", header="time,delta_T", comments='')
    np.savetxt(epica_dir / "epica_data_1000.csv", dt[::1000], fmt='%d,%.6f', delimiter=",", header="time,delta_T", comments='')

if __name__ == "__main__":
    epica_to_yearly_csv(Path("./epica")) 