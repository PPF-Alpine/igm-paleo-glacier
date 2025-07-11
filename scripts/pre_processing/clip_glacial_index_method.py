import argparse
import geopandas as gpd
from pathlib import Path

from pre_processing_scripts import (
    epica_to_netcdf,
    save_delta_temperature,
    save_clipped_atmosphere,
    save_clipped_model_anomaly,
    save_clipped_bootstrap,
    save_clipped_lapse_rate,
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Paths to raw climate data and output location:
CLIMATE_DATA_PATH =  Path("../../data/raw/climate/")
LOCATION_BASE_PATH = Path("../../data/processed/")

def clip_data(args: argparse.Namespace):
    save_clipped_atmosphere(
        crs=args.crs,
        bounds=args.bounds,
        chelsa_filepath=(CLIMATE_DATA_PATH / "chelsa" ),
        pbcor_filepath=(CLIMATE_DATA_PATH / "pbcor/CHELSA_V12.nc" ),
        polygon=args.polygon,
        output_filepath=(LOCATION_BASE_PATH / args.output_dir / args.atm_output_filename),
        resolution=args.resolution,
    )

    save_clipped_model_anomaly(
        crs=args.crs,
        bounds=args.bounds,
        modeled_anomaly_filepath=(CLIMATE_DATA_PATH / "climate_model_outputs/modeled_anomaly.nc" ),
        output_filepath=(LOCATION_BASE_PATH / args.output_dir / args.modeled_anomaly_filename),
        resolution=args.resolution,
    )

    save_clipped_bootstrap(
        crs=args.crs,
        bounds=args.bounds,
        gebco_filepath=(CLIMATE_DATA_PATH / "gebco/GEBCO_2023_sub_ice_topo.nc"),
        output_filepath=(LOCATION_BASE_PATH / args.output_dir / args.boot_output_filename),
        resolution=args.resolution,
    )

    save_clipped_lapse_rate(
        crs=args.crs,
        bounds=args.bounds,
        polygon=args.polygon,
        lapse_rate_filepath=(CLIMATE_DATA_PATH / "global_lapse_rate/lapserate_3_iqr_fullrange.tif"),
        output_filepath=(LOCATION_BASE_PATH / args.output_dir / "localised_lapse_rate"),
        resolution=args.resolution,
    )

def convert_epica_to_netcdf(args: argparse.Namespace):
    if not (LOCATION_BASE_PATH / args.output_dir / args.dT_epica_filename).exists():
        epica_to_netcdf(
            epica_dir=Path(CLIMATE_DATA_PATH / "epica"), output_filepath=(LOCATION_BASE_PATH / args.output_dir / args.dT_epica_filename),
        )

def convert_core_composites_to_netcdf(args: argparse.Namespace):
    save_delta_temperature(
        polygon=args.polygon, 
        antarctic_composite_path=Path(CLIMATE_DATA_PATH / "core_composites/antarctica_core_composite.csv"),
        greenland_composite_path=Path(CLIMATE_DATA_PATH / "core_composites/greenland_core_composite.csv"),
        output_filepath=Path(LOCATION_BASE_PATH / args.output_dir / args.dT_composite_filename),
    )


def check_args(args: argparse.Namespace) -> argparse.Namespace:
    if not args.crs:
        raise ValueError("CRS is required")

    if not args.bounds:
        raise ValueError("Bounds are required")

    if len(args.bounds) != 4:
        raise ValueError("Bounds must be in the format: xmin, ymin, xmax, ymax")

    output_directory_test = LOCATION_BASE_PATH / args.output_dir
    if output_directory_test.exists() and not  output_directory_test.is_dir():
        raise ValueError("Output directory must be a directory")

    if not args.polygon:
        raise ValueError("Please provide a .shp file path argument and keep all shapefile parts in the same directory.")
    
    if not args.polygon.exists():
        raise ValueError("Provided polygon path does not exist.")

    if args.polygon.exists():
        logger.info(f"DEBUG: polygon exists = {args.polygon}")

    output_directory_test.mkdir(parents=True, exist_ok=True)

    return args

def save_projection(args: argparse.Namespace):
    save_path = LOCATION_BASE_PATH / args.output_dir
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
        "--dT_epica_filename",
        help="Output filename for clipped dT data",
        type=Path,
        default="dT_epica.nc",
    )
    parser.add_argument(
        "--dT_composite_filename",
        help="Output filename for processed dT core composite data",
        type=Path,
        default="dT_composite_at_latitude.nc",
    )
    parser.add_argument(
        "--modeled_anomaly_filename",
        help="Output filename for clipped modeled anomaly data. Taken from ESM.",
        type=Path,
        default="modeled_anomaly_clipped.nc",
    )
    parser.add_argument(
        "--atm_output_filename",
        help="Output filename for clipped present day observation atmosphere data. Taken from CHELSA.",
        type=Path,
        default="present_day_observation_atmosphere.nc",
    )
    parser.add_argument(
        "--boot_output_filename",
        help="Output filename for clipped bootstrap data",
        type=Path,
        default="topography.nc",
    )
    parser.add_argument(
        "--output_dir",
        help="Directory to output the clipped and/or processed data.",
        type=Path,
        default=Path("."),
    )
    parser.add_argument(
            "--polygon",
            help="Shape file for setting the climate data bounds as a .shp file. Directory must also contain the other shape file parts (.shx, .prj, ...).",
            type=Path,
            default=None,
    )
    
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

    # Convert epica
    convert_epica_to_netcdf(args=args)

    # Call the clip_data function with the provided arguments
    clip_data(args=args)

    # Convert the polar core composites 
    convert_core_composites_to_netcdf(args=args)

    # Save projection for later automation with shape file result generation
    save_projection(args=args)
