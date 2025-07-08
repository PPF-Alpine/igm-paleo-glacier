from pathlib import Path

from download_scripts import (
    download_chelsa,
    download_and_extract_gebco,
    download_and_extract_pbcor,
    download_epica,
    epica_to_netcdf,
    #TODO: add download core composites and climate models
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
# Define data storage path:
CLIMATE_DOWNLOAD_PATH =  Path("../../data/raw/climate/")

def download_if_files_do_not_exist():

    # Download CHELSA 
    chelsa_path = Path(CLIMATE_DOWNLOAD_PATH) / "chelsa"
    if not chelsa_path.exists():
        logger.info("Chelsa folder doesn't exist, downloading...")
        chelsa_path.mkdir(parents=True, exist_ok=True)
        download_chelsa(chelsa_path)  # TODO: pass the path here
    elif not any(chelsa_path.iterdir()):
        logger.info("Chelsa folder is empty, downloading...")
        download_chelsa(chelsa_path)  # TODO: pass the path here
    else:
        logger.info(f"The chelsa path already exists and contains files.")

    # Check and download gebco
    gebco_path = Path(CLIMATE_DOWNLOAD_PATH) / "gebco"
    if not gebco_path.exists():
        logger.info("GEBCO folder doesn't exist, downloading...")
        gebco_path.mkdir(parents=True, exist_ok=True)
        download_and_extract_gebco(gebco_path)
    elif not any(gebco_path.iterdir()):
        logger.info("GEBCO folder is empty, downloading...")
        download_and_extract_gebco(gebco_path)
    else:
        logger.info("The GEBCO path already exists and contains files.")
    
    # Check and download pbcor
    pbcor_path = Path(CLIMATE_DOWNLOAD_PATH) / "pbcor"
    if not pbcor_path.exists():
        logger.info("PBCOR folder doesn't exist, downloading...")
        pbcor_path.mkdir(parents=True, exist_ok=True)
        download_and_extract_pbcor(pbcor_path)
    elif not any(pbcor_path.iterdir()):
        logger.info("PBCOR folder is empty, downloading...")
        download_and_extract_pbcor(pbcor_path)
    else:
        logger.info("The PBCOR path already exists and contains files.")

    # Check and download epica
    epica_path = Path(CLIMATE_DOWNLOAD_PATH) / "epica"
    if not epica_path.exists():
        logger.info("EPICA folder doesn't exist, downloading...")
        epica_path.mkdir(parents=True, exist_ok=True)
        download_epica(epica_path)
    elif not any(epica_path.iterdir()):
        logger.info("EPICA folder is empty, downloading...")
        download_epica(epica_path)
    else:
        logger.info("The EPICA path already exists and contains files.")

    # Check global_lapse_rate (This should not be download in this script)
    lapse_rate_path = Path(CLIMATE_DOWNLOAD_PATH) / "global_lapse_rate"
    if not lapse_rate_path.exists():
        logger.info("Global lapse rate folder doesn't exist. Creating...")
        lapse_rate_path.mkdir(parents=True, exist_ok=True)
    elif not any(lapse_rate_path.iterdir()):
        logger.info("Global lapse rate folder is empty. File is needed.")
    else:
        logger.info("The global lapse rate path and file exists and contains files (OK)!")

if __name__ == "__main__":
    download_if_files_do_not_exist()
