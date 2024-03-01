import argparse
from pathlib import Path
from time import perf_counter

from download import (
    download_chelsa,
    download_and_extract_gebco,
    download_and_extract_pbcor,
    download_epica,
    epica_to_netcdf,
)
from clip import (
    save_clipped_atmosphere,
    save_clipped_bootstrap,
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clip_data(args: argparse.Namespace):
    # Check if input data is available
    if not Path("chelsa").exists():
        download_chelsa()

    if not Path("gebco").exists():
        download_and_extract_gebco()

    if not Path("pbcor").exists():
        download_and_extract_pbcor()

    if not Path("epica").exists():
        download_epica(epica_dir=Path("epica"))

    if not args.dT_output_filename.exists():
        # Epica isn't clipped because there is no x,y data, just a time series.
        epica_to_netcdf(
            epica_dir=Path("epica"), output_filepath=args.dT_output_filename
        )

    # Clip the input data
    save_clipped_atmosphere(
        crs=args.crs,
        bounds=args.bounds,
        output_filepath=args.atm_output_filename,
        resolution=args.resolution,
    )
    save_clipped_bootstrap(
        crs=args.crs,
        bounds=args.bounds,
        output_filepath=args.boot_output_filename,
        resolution=args.resolution,
    )


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Clip input data")
    parser.add_argument(
        "--crs", help="Coordinate Reference System for the output data.", type=str
    )
    parser.add_argument(
        "--bounds",
        nargs="+",
        help="Bounds for clipping the data in the format: xmin, ymin, xmax, ymax",
        type=int,
    )
    parser.add_argument(
        "--resolution", help="Resolution in meters per pixel", type=int, default=1000
    )
    parser.add_argument(
        "--dT_output_filename",
        help="Output filename for clipped dT data",
        type=Path,
        default="dT_epica.nc",
    )
    parser.add_argument(
        "--atm_output_filename",
        help="Output filename for clipped atmosphere data",
        type=Path,
        default="atm.nc",
    )
    parser.add_argument(
        "--boot_output_filename",
        help="Output filename for clipped bootstrap data",
        type=Path,
        default="boot.nc",
    )

    # Call the clip_data function with the provided arguments
    clip_data(args=parser.parse_args())
