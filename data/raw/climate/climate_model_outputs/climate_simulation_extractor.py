#!/usr/bin/env python3
"""
Climate Data Extractor for CMIP6 NetCDF files

This script can extract specific years or year ranges from climate model output files
and optionally compute monthly averages across multiple years.

Usage examples:
    # Extract last year
    python climate_extractor.py input.nc --mode last_year

    # Extract specific year
    python climate_extractor.py input.nc --mode specific_year --year 2340

    # Extract and average a year range
    python climate_extractor.py input.nc --mode year_range --start_year 2340 --end_year 2349

Author: Generated for paleoclimate data analysis
"""

import xarray as xr
import argparse
import sys
from pathlib import Path
import numpy as np
try:
    import cftime
except ImportError:
    cftime = None


def get_available_years(ds):
    """Get the range of available years in the dataset."""
    # Handle both cftime and standard datetime objects
    time_values = ds.time.values
    
    if hasattr(time_values[0], 'year'):
        # cftime objects
        years = [t.year for t in time_values]
    else:
        # numpy datetime64 or standard datetime
        years = ds.time.dt.year.values
    
    return int(min(years)), int(max(years))


def extract_last_year(ds, var_name):
    """Extract the last complete year of data."""
    years = ds.time.dt.year.values
    last_year = int(years.max())
    
    # Select all months from the last year
    last_year_data = ds.sel(time=ds.time.dt.year == last_year)
    
    print(f"Extracted last year: {last_year}")
    print(f"Number of time steps: {len(last_year_data.time)}")
    
    return last_year_data


def extract_specific_year(ds, var_name, target_year):
    """Extract a specific year of data."""
    # Handle cftime objects
    time_values = ds.time.values
    if hasattr(time_values[0], 'year'):
        # cftime objects
        years = [t.year for t in time_values]
        min_year, max_year = min(years), max(years)
        # Create boolean mask for target year
        year_mask = np.array([t.year == target_year for t in time_values])
    else:
        # numpy datetime64 or standard datetime
        years = ds.time.dt.year.values
        min_year, max_year = int(years.min()), int(years.max())
        year_mask = ds.time.dt.year == target_year
    
    if target_year < min_year or target_year > max_year:
        raise ValueError(f"Year {target_year} not available. Data spans {min_year}-{max_year}")
    
    # Select all months from the target year
    year_data = ds.isel(time=year_mask)
    
    # Fix bounds variables - they should maintain their original 2D structure
    bounds_vars = ['lat_bnds', 'lon_bnds']
    for bvar in bounds_vars:
        if bvar in year_data.data_vars and bvar in ds.data_vars:
            # Use original bounds (2D structure) instead of time-selected ones
            year_data[bvar] = ds[bvar]
    
    print(f"Extracted year: {target_year}")
    print(f"Number of time steps: {len(year_data.time)}")
    
    return year_data


def extract_year_range_average(ds, var_name, start_year, end_year):
    """Extract a year range and compute monthly averages."""
    # Handle cftime objects
    time_values = ds.time.values
    if hasattr(time_values[0], 'year'):
        # cftime objects
        years = [t.year for t in time_values]
        min_year, max_year = min(years), max(years)
        # Create boolean mask for year range
        year_range_mask = np.array([start_year <= t.year <= end_year for t in time_values])
    else:
        # numpy datetime64 or standard datetime
        years = ds.time.dt.year.values
        min_year, max_year = int(years.min()), int(years.max())
        year_range_mask = (ds.time.dt.year >= start_year) & (ds.time.dt.year <= end_year)
    
    if start_year < min_year or end_year > max_year:
        raise ValueError(f"Year range {start_year}-{end_year} not fully available. "
                        f"Data spans {min_year}-{max_year}")
    
    if start_year >= end_year:
        raise ValueError("Start year must be less than end year")
    
    # Select the year range
    year_range_data = ds.isel(time=year_range_mask)
    
    # Group by month and compute mean across years
    # For cftime objects, we need to extract month differently
    if hasattr(time_values[0], 'month'):
        # Create month coordinate manually for cftime
        months = [t.month for t in year_range_data.time.values]
        year_range_data = year_range_data.assign_coords(month=('time', months))
        monthly_avg = year_range_data.groupby('month').mean('time')
    else:
        # Standard datetime handling
        monthly_avg = year_range_data.groupby('time.month').mean('time')
    
    # Create new time coordinate maintaining cftime consistency
    middle_year = start_year + (end_year - start_year) // 2
    
    # Use the same calendar and time type as the original data
    if hasattr(time_values[0], 'month'):
        # Import cftime to create proper time objects
        if cftime is None:
            raise ImportError("cftime is required for paleoclimate data. Install with: pip install cftime")
        
        calendar_type = ds.time.attrs.get('calendar', 'standard')
        
        # Create cftime objects for each month
        new_times = []
        for month in range(1, 13):
            new_times.append(cftime.datetime(middle_year, month, 15, calendar=calendar_type))
    else:
        new_times = [np.datetime64(f'{middle_year:04d}-{month:02d}-15') for month in range(1, 13)]
    
    # Assign new time coordinate
    monthly_avg = monthly_avg.rename({'month': 'time'}).assign_coords(time=new_times)
    
    # Fix bounds variables - they should not have a time dimension for monthly averages
    bounds_vars = ['lat_bnds', 'lon_bnds', 'time_bnds']
    for bvar in bounds_vars:
        if bvar in monthly_avg.data_vars and bvar in ds.data_vars:
            # Use original bounds (2D structure) instead of time-averaged ones
            if bvar != 'time_bnds':  # lat_bnds and lon_bnds should be 2D
                monthly_avg[bvar] = ds[bvar]
            # For time_bnds, create new bounds for the monthly averages
            elif bvar == 'time_bnds':
                if hasattr(time_values[0], 'month'):
                    if cftime is None:
                        raise ImportError("cftime is required for paleoclimate data. Install with: pip install cftime")
                    
                    calendar_type = ds.time.attrs.get('calendar', 'standard')
                    time_bounds = []
                    for month in range(1, 13):
                        # Start of month
                        start_bound = cftime.datetime(middle_year, month, 1, calendar=calendar_type)
                        # End of month (approximate)
                        if month == 12:
                            end_bound = cftime.datetime(middle_year + 1, 1, 1, calendar=calendar_type)
                        else:
                            end_bound = cftime.datetime(middle_year, month + 1, 1, calendar=calendar_type)
                        time_bounds.append([start_bound, end_bound])
                    
                    monthly_avg[bvar] = (['time', 'bnds'], time_bounds)
    
    print(f"Extracted and averaged years: {start_year}-{end_year}")
    print(f"Number of years averaged: {end_year - start_year + 1}")
    print(f"Output time steps: {len(monthly_avg.time)} (monthly averages)")
    
    return monthly_avg


def auto_detect_variable(ds):
    """Automatically detect the main climate variable in the dataset."""
    # Common climate variable names
    climate_vars = ['pr', 'tas', 'tasmax', 'tasmin', 'huss', 'ps', 'uas', 'vas', 'ts']
    
    for var in climate_vars:
        if var in ds.data_vars:
            return var
    
    # If no common variable found, look for variables with 3D structure (time, lat, lon)
    for var_name, var in ds.data_vars.items():
        if len(var.dims) == 3 and 'time' in var.dims:
            return var_name
    
    raise ValueError("Could not automatically detect climate variable. "
                    "Please specify using --variable option.")


def create_output_filename(input_file, mode, year=None, start_year=None, end_year=None):
    """Create an appropriate output filename based on the operation."""
    input_path = Path(input_file)
    stem = input_path.stem
    
    if mode == 'last_year':
        suffix = "_last_year"
    elif mode == 'specific_year':
        suffix = f"_{year}"
    elif mode == 'year_range':
        suffix = f"_{start_year}-{end_year}_monthly_avg"
    
    return input_path.parent / f"{stem}{suffix}.nc"


def main():
    parser = argparse.ArgumentParser(description='Extract climate data from NetCDF files')
    parser.add_argument('input_file', help='Input NetCDF file path')
    parser.add_argument('--mode', choices=['last_year', 'specific_year', 'year_range'], 
                       required=True, help='Extraction mode')
    parser.add_argument('--year', type=int, help='Specific year to extract (for specific_year mode)')
    parser.add_argument('--start_year', type=int, help='Start year for range (for year_range mode)')
    parser.add_argument('--end_year', type=int, help='End year for range (for year_range mode)')
    parser.add_argument('--variable', help='Variable name to extract (auto-detected if not provided)')
    parser.add_argument('--output', help='Output file path (auto-generated if not provided)')
    parser.add_argument('--info', action='store_true', help='Show dataset information and exit')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'specific_year' and args.year is None:
        parser.error("--year is required for specific_year mode")
    
    if args.mode == 'year_range' and (args.start_year is None or args.end_year is None):
        parser.error("--start_year and --end_year are required for year_range mode")
    
    # Load the dataset
    print(f"Loading dataset: {args.input_file}")
    try:
        ds = xr.open_dataset(args.input_file, use_cftime=True)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
    
    # Show dataset info if requested
    if args.info:
        print("\nDataset Information:")
        print(f"Dimensions: {dict(ds.sizes)}")
        print(f"Variables: {list(ds.data_vars.keys())}")
        min_year, max_year = get_available_years(ds)
        print(f"Time range: {min_year}-{max_year}")
        print(f"Calendar: {ds.time.attrs.get('calendar', 'standard')}")
        return
    
    # Auto-detect variable if not provided
    if args.variable is None:
        try:
            var_name = auto_detect_variable(ds)
            print(f"Auto-detected variable: {var_name}")
        except ValueError as e:
            print(f"Error: {e}")
            print(f"Available variables: {list(ds.data_vars.keys())}")
            sys.exit(1)
    else:
        var_name = args.variable
        if var_name not in ds.data_vars:
            print(f"Error: Variable '{var_name}' not found in dataset")
            print(f"Available variables: {list(ds.data_vars.keys())}")
            sys.exit(1)
    
    # Show available year range
    min_year, max_year = get_available_years(ds)
    print(f"Available years: {min_year}-{max_year}")
    
    # Extract data based on mode
    try:
        if args.mode == 'last_year':
            result = extract_last_year(ds, var_name)
        elif args.mode == 'specific_year':
            result = extract_specific_year(ds, var_name, args.year)
        elif args.mode == 'year_range':
            result = extract_year_range_average(ds, var_name, args.start_year, args.end_year)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Generate output filename
    if args.output is None:
        output_file = create_output_filename(args.input_file, args.mode, 
                                           args.year, args.start_year, args.end_year)
    else:
        output_file = Path(args.output)
    
    # Save the result
    print(f"Saving to: {output_file}")
    try:
        # Copy relevant attributes
        for attr in ['title', 'institution', 'source', 'experiment', 'references']:
            if attr in ds.attrs:
                result.attrs[attr] = ds.attrs[attr]
        
        # Add processing information
        if args.mode == 'year_range':
            result.attrs['processing_note'] = f"Monthly averages computed over {args.start_year}-{args.end_year}"
        else:
            result.attrs['processing_note'] = f"Extracted using mode: {args.mode}"
        
        result.to_netcdf(output_file)
        print("Successfully saved!")
        
        # Show summary of saved data
        print(f"\nSaved data summary:")
        print(f"Variable: {var_name}")
        print(f"Shape: {result[var_name].shape}")
        print(f"Time steps: {len(result.time)}")
        
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)
    
    finally:
        ds.close()


if __name__ == "__main__":
    main() 
