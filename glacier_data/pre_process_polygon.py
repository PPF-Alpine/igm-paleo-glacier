import argparse
from pathlib import Path

from pre_process import (
    download_chelsa,
    download_and_extract_gebco,
    download_and_extract_pbcor,
    download_epica,
    epica_to_netcdf,
    save_clipped_atmosphere,
    save_clipped_bootstrap,
    save_clipped_lapse_rate,
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clip_data(args: argparse.Namespace):
    if not (args.output_dir / args.dT_output_filename).exists():
        # Epica isn't clipped because there is no x,y data, just a time series.
        epica_to_netcdf(
            epica_dir=Path("epica"),
            output_filepath=(args.output_dir / args.dT_output_filename),
        )
    
    # Clip the input data
    save_clipped_atmosphere(
        crs=args.crs,
        bounds=args.bounds,
        polygon=args.polygon,
        output_filepath=(args.output_dir / args.atm_output_filename),
        resolution=args.resolution,
    )
    save_clipped_bootstrap(
        crs=args.crs,
        bounds=args.bounds,
        output_filepath=(args.output_dir / args.boot_output_filename),
        resolution=args.resolution,
    )
    save_clipped_lapse_rate(
        crs=args.crs,
        bounds=args.bounds,
        polygon=args.polygon,
        output_filepath=(args.output_dir / "localised_lapse_rate"),
        resolution=args.resolution,
    )

def check_available_files():
    # Check if input data is available
    if not Path("chelsa").exists():
        download_chelsa()

    if not Path("gebco").exists():
        download_and_extract_gebco()

    if not Path("pbcor").exists():
        download_and_extract_pbcor()

    if not Path("epica").exists():
        download_epica(epica_dir=Path("epica"))

    if not Path("global_lapse_rate").exists(): #TODO: This should actually check if a GeoTiff file is present in stead.
        raise Exception("Global lapse rate GeoTiff required")

def check_args(args: argparse.Namespace) -> argparse.Namespace:
    if not args.crs:
        raise ValueError("CRS is required")

    if not args.bounds:
        raise ValueError("Bounds are required")

    if len(args.bounds) != 4:
        raise ValueError("Bounds must be in the format: xmin, ymin, xmax, ymax")

    if args.output_dir.exists() and not args.output_dir.is_dir():
        raise ValueError("Output directory must be a directory")

    if not args.polygon:
        raise ValueError("Please provide a .shp file path argument and keep all shapefile parts in the same directory.")
    
    if not args.polygon.exists():
        raise ValueError("Provided polygon path does not exist.")

    if args.polygon.exists():
        logger.info(f"DEBUG: polygon exists = {args.polygon}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    return args

def save_projection(args: argparse.Namespace):
    save_path = args.output_dir
    file_name = "projection.txt"
    complete_name = Path(save_path) / file_name
    file1 = open(complete_name, "w")
    file1.write(args.crs) 
    file1.close()
    

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
        type=float,
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
    parser.add_argument(
        "--output_dir",
        help="Directory to output the clipped data to",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
            "--polygon",
            help="Shape file for setting the climate data bounds as a .shp file. Directory must also contain the other shape file parts (.shx, .prj, ...).",
            type=Path,
            default=None,
    )

    # Check if the required files are present
    check_available_files()

    # Check the provided arguments
    args = parser.parse_args()

    # If there are no arguments, print the help message
    if not args.crs or not args.bounds:
        parser.print_help()
        exit(1)

    # Check the provided arguments
    args = check_args(args)

    # Log the provided arguments
    logger.info(f"Clipping data with the following arguments: {args}")

    # # Call the clip_data function with the provided arguments
    clip_data(args=args)

    # Save projection for later automation with shape file result generation
    save_projection(args=args)
