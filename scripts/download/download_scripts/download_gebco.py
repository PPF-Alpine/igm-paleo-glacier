from pathlib import Path
from tqdm import tqdm
import requests
import zipfile
import tempfile

GEBCO_URL = (
    "https://www.bodc.ac.uk/data/open_download/gebco/gebco_2023_sub_ice_topo/zip/"
        "https://dap.ceda.ac.uk/bodc/gebco/global/gebco_2024/ice_surface_elevation/netcdf/GEBCO_2024_CF.nc"
)


def download_and_extract_gebco(save_directory: Path):
    response = requests.get(GEBCO_URL, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 KB

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / "gebco.zip"

        with open(temp_file_path, "wb") as temp_file:
            progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)
            for data in response.iter_content(block_size):
                temp_file.write(data)
                progress_bar.update(len(data))
            progress_bar.close()

        # unzip the file
        with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
            # extract the contents of the zip file to a new directory called gebco
            zip_ref.extractall(save_directory)

