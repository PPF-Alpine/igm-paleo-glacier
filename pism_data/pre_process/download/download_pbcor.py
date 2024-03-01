from pathlib import Path
from tqdm import tqdm
import requests
import zipfile
import tempfile

PBCOR_URL = "http://www.gloh2o.org/data/PBCOR_V1.0.zip"


def download_and_extract_pbcor(output_dir: Path = Path("pbcor")):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        filename = temp_dir_path / PBCOR_URL.split("/")[-1]

        response = requests.get(PBCOR_URL, stream=True)
        total_size = int(response.headers.get("content-length", 0))
        block_size = 1024  # 1 KB

        with open(filename, "wb") as file:
            progress_bar = tqdm(total=total_size, unit="B", unit_scale=True)
            for data in response.iter_content(block_size):
                file.write(data)
                progress_bar.update(len(data))
            progress_bar.close()

        # unzip the file
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(output_dir)


if __name__ == "__main__":
    download_and_extract_pbcor()
    print("File downloaded and extracted successfully!")
