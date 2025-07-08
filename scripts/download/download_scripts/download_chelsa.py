import requests
from tqdm import tqdm
from pathlib import Path
from time import perf_counter

BASE_URL = "https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL"

def download_chelsa(save_directory: Path):
    # download the temperature and precipitation data
    download_chelsa_var(save_directory=save_directory, variable="tas")             # download temperature
    download_chelsa_var(save_directory=save_directory, variable="pr")              # download precipitation
    # download the dem data
    download_chelsa_file(save_directory=save_directory, url=f"{BASE_URL}/input/dem_latlong.nc")


def download_chelsa_var(save_directory: Path, variable: str):
    # loop over the months and download the files
    for month_ix in range(1, 13):
        # create the url
        filename = "CHELSA_{variable}_{month:02d}_1981-2010_V.2.1.tif".format(
            variable=variable, month=month_ix
        )
        url = f"{BASE_URL}/climatologies/1981-2010/{variable}/{filename}"

        download_chelsa_file(save_directory, url)


def download_chelsa_file(save_directory: Path, url: str):
    """
    Download a file from the given URL and save it to the specified directory.

    Args:
        save_directory (Path): The directory where the file will be saved.
        url (str): The URL of the file to be downloaded.

    """

    # create the filename from the url
    filename = url.split("/")[-1]
    filepath = save_directory / filename

    # download the file
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 KB

    start = perf_counter()
    print(f"Downloading {filename}...")
    with open(filepath, "wb") as file:
        progress_bar = tqdm(total=total_size, unit="B", unit_scale=True, leave=False)
        for data in response.iter_content(block_size):
            file.write(data)
            progress_bar.update(len(data))
        progress_bar.close()

    print(
        f"File {filename} downloaded successfully in {perf_counter() - start:.2f} seconds!"
    )


