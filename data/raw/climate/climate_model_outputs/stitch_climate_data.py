#!/usr/bin/env python3
"""
Climate Data Stitcher for CMIP6 NetCDF files

This script stitches together multiple NetCDF files containing consecutive time periods
into a single continuous time series. Designed to work with CMIP6 climate model output
where each file typically contains 20 years of monthly data.

Usage examples:
    # Stitch files using command line arguments
    python stitch_climate_data.py file1.nc file2.nc file3.nc --output combined.nc

    # Stitch files using a pattern
    python stitch_climate_data.py --pattern "pr_*_233*.nc" --output combined.nc

    # Stitch files from a directory
    python stitch_climate_data.py --directory /path/to/files --pattern "pr_*.nc"

Author: Generated for paleoclimate data analysis
"""

import xarray as xr
import argparse
import sys
import glob
from pathlib import Path
import numpy as np
from datetime import datetime


def validate_files_compatibility(file_paths):
    """Check that all files have compatible dimensions and variables."""
    print("Validating file compatibility...")
    
    reference_ds = None
    file_info = []
    
    for i, file_path in enumerate(file_paths):
        try:
            ds = xr.open_dataset(file_path, use_cftime=True)
            
            # Get time range for this file
            time_start = ds.time.values[0]
            time_end = ds.time.values[-1]
            years = ds.time.dt.year.values
            year_range = f"{int(years.min())}-{int(years.max())}"
            
            file_info.append({
                'file': Path(file_path).name,
                'time_start': time_start,
                'time_end': time_end,
                'year_range': year_range,
                'n_timesteps': len(ds.time),
                'dataset': ds
            })
            
            if reference_ds is None:
                reference_ds = ds
                ref_vars = set(ds.data_vars.keys())
                ref_dims = {dim: size for dim, size in ds.sizes.items() if dim != 'time'}
                print(f"Reference file: {Path(file_path).name}")
                print(f"  Variables: {list(ref_vars)}")
                print(f"  Spatial dimensions: {ref_dims}")
            else:
                # Check compatibility
                current_vars = set(ds.data_vars.keys())
                current_dims = {dim: size for dim, size in ds.sizes.items() if dim != 'time'}
                
                if current_vars != ref_vars:
                    raise ValueError(f"Variable mismatch in {file_path}. "
                                   f"Expected: {ref_vars}, Got: {current_vars}")
                
                if current_dims != ref_dims:
                    raise ValueError(f"Dimension mismatch in {file_path}. "
                                   f"Expected: {ref_dims}, Got: {current_dims}")
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            raise
    
    return file_info


def sort_files_by_time(file_info):
    """Sort files by their starting time."""
    return sorted(file_info, key=lambda x: x['time_start'])


def check_time_continuity(sorted_file_info, allow_gaps=False):
    """Check for gaps or overlaps in time series."""
    print("\nChecking time continuity...")
    
    issues = []
    
    for i in range(len(sorted_file_info) - 1):
        current_end = sorted_file_info[i]['time_end']
        next_start = sorted_file_info[i+1]['time_start']
        
        # Work with cftime objects directly
        # Check for overlaps (current end >= next start)
        if current_end >= next_start:
            overlap_msg = (f"Overlap detected between {sorted_file_info[i]['file']} "
                         f"and {sorted_file_info[i+1]['file']}")
            issues.append(overlap_msg)
        elif not allow_gaps:
            # For gaps, calculate difference in a way that works with cftime
            # Convert to total seconds and then to days for comparison
            try:
                time_diff = next_start - current_end
                if hasattr(time_diff, 'total_seconds'):
                    gap_days = time_diff.total_seconds() / (24 * 3600)
                elif hasattr(time_diff, 'days'):
                    gap_days = time_diff.days
                else:
                    # Fallback: just check if there's a significant gap by comparing years
                    current_year = getattr(current_end, 'year', current_end.dt.year.values[0])
                    next_year = getattr(next_start, 'year', next_start.dt.year.values[0])
                    gap_days = (next_year - current_year) * 365  # Rough estimate
                
                if gap_days > 35:  # More than a month gap
                    gap_msg = (f"Gap detected between {sorted_file_info[i]['file']} "
                             f"and {sorted_file_info[i+1]['file']}: ~{gap_days:.0f} days")
                    issues.append(gap_msg)
            except Exception as e:
                # If we can't calculate the gap, just warn
                gap_msg = (f"Could not verify time gap between {sorted_file_info[i]['file']} "
                         f"and {sorted_file_info[i+1]['file']}: {e}")
                issues.append(gap_msg)
    
    return issues


def create_combined_filename(file_info, output_dir=None):
    """Create an appropriate filename for the combined dataset."""
    # Get the pattern from the first file
    first_file = Path(file_info[0]['file'])
    
    # Extract the base pattern (everything before the time range)
    # Assuming format like: pr_Amon_MPI-ESM1-2-LR_lgm_r1i1p1f1_gn_233001-234912.nc
    name_parts = first_file.stem.split('_')
    
    # Find where the time range starts (usually the last part before .nc)
    if len(name_parts) >= 2:
        base_pattern = '_'.join(name_parts[:-1])
    else:
        base_pattern = first_file.stem
    
    # Get overall time range - handle cftime objects
    start_time = file_info[0]['time_start']
    end_time = file_info[-1]['time_end']
    
    if hasattr(start_time, 'year'):
        start_year = start_time.year
    else:
        start_year = int(start_time.dt.year.values[0])
        
    if hasattr(end_time, 'year'):
        end_year = end_time.year
    else:
        end_year = int(end_time.dt.year.values[-1])
    
    # Create new filename
    new_filename = f"{base_pattern}_{start_year:06d}-{end_year:06d}_combined.nc"
    
    if output_dir:
        return Path(output_dir) / new_filename
    else:
        return Path(file_info[0]['file']).parent / new_filename


def stitch_datasets(file_info, check_continuity=True, allow_gaps=False):
    """Stitch together the datasets along the time dimension."""
    print(f"\nStitching {len(file_info)} files...")
    
    # Sort files by time
    sorted_files = sort_files_by_time(file_info)
    
    # Print file order
    print("File order (by time):")
    for i, info in enumerate(sorted_files):
        print(f"  {i+1}. {info['file']} ({info['year_range']}, {info['n_timesteps']} timesteps)")
    
    # Check time continuity if requested
    if check_continuity:
        issues = check_time_continuity(sorted_files, allow_gaps)
        
        if issues:
            print("\nTime continuity issues found:")
            for issue in issues:
                print(f"  WARNING: {issue}")
            
            if not allow_gaps:
                response = input("\nContinue anyway? (y/n): ")
                if response.lower() != 'y':
                    print("Aborting.")
                    return None
    
    # Load and concatenate datasets
    print("\nLoading and concatenating datasets...")
    datasets = []
    
    for info in sorted_files:
        print(f"  Loading {info['file']}...")
        datasets.append(info['dataset'])
    
    # Concatenate along time dimension
    print("  Concatenating along time dimension...")
    
    # Handle coordinate bounds properly - they shouldn't be concatenated along time
    bounds_vars = []
    for ds in datasets:
        for var_name in ds.data_vars:
            if 'bnds' in var_name and 'time' not in ds[var_name].dims:
                bounds_vars.append(var_name)
    
    bounds_vars = list(set(bounds_vars))  # Remove duplicates
    
    if bounds_vars:
        print(f"  Found coordinate bounds variables: {bounds_vars}")
        print("  Handling bounds variables separately to maintain 2D structure...")
        
        # Separate main data from bounds
        main_datasets = []
        bounds_data = {}
        
        for ds in datasets:
            # Create dataset without bounds variables
            main_vars = {var: ds[var] for var in ds.data_vars if var not in bounds_vars}
            main_ds = ds.drop_vars(bounds_vars).copy()
            main_datasets.append(main_ds)
            
            # Store bounds from first dataset (they should be identical across files)
            if not bounds_data:
                for bvar in bounds_vars:
                    if bvar in ds.data_vars:
                        bounds_data[bvar] = ds[bvar]
        
        # Concatenate main data
        combined_ds = xr.concat(main_datasets, dim='time')
        
        # Add back the bounds variables (using the original 2D structure)
        for bvar, bdata in bounds_data.items():
            combined_ds[bvar] = bdata
            
    else:
        # No bounds variables found, concatenate normally
        combined_ds = xr.concat(datasets, dim='time')
    
    # Update global attributes
    combined_ds.attrs['title'] = combined_ds.attrs.get('title', '') + ' (Combined time series)'
    combined_ds.attrs['history'] = (f"{datetime.now().isoformat()}: Combined {len(datasets)} files "
                                   f"using stitch_climate_data.py")
    combined_ds.attrs['source_files'] = ', '.join([info['file'] for info in sorted_files])
    
    # Get final time range
    start_year = int(combined_ds.time.dt.year.values.min())
    end_year = int(combined_ds.time.dt.year.values.max())
    total_years = end_year - start_year + 1
    
    print(f"\nCombined dataset created:")
    print(f"  Time range: {start_year}-{end_year} ({total_years} years)")
    print(f"  Total timesteps: {len(combined_ds.time)}")
    print(f"  Variables: {list(combined_ds.data_vars.keys())}")
    
    return combined_ds


def main():
    parser = argparse.ArgumentParser(description='Stitch together NetCDF climate data files')
    
    # Input methods
    parser.add_argument('files', nargs='*', help='NetCDF files to stitch together')
    parser.add_argument('--pattern', help='File pattern to match (e.g., "pr_*.nc")')
    parser.add_argument('--directory', help='Directory to search for files')
    
    # Output options
    parser.add_argument('--output', help='Output file path (auto-generated if not provided)')
    parser.add_argument('--output_dir', help='Output directory (uses input directory if not provided)')
    
    # Processing options
    parser.add_argument('--no_time_check', action='store_true', 
                       help='Skip time continuity checking')
    parser.add_argument('--allow_gaps', action='store_true',
                       help='Allow gaps in time series')
    parser.add_argument('--dry_run', action='store_true',
                       help='Show what would be done without actually stitching')
    
    args = parser.parse_args()
    
    # Determine input files
    file_paths = []
    
    if args.files:
        file_paths.extend(args.files)
    
    if args.pattern:
        if args.directory:
            pattern_path = Path(args.directory) / args.pattern
        else:
            pattern_path = args.pattern
        
        matched_files = glob.glob(str(pattern_path))
        if not matched_files:
            print(f"No files found matching pattern: {pattern_path}")
            sys.exit(1)
        file_paths.extend(matched_files)
    
    if not file_paths:
        parser.error("No input files specified. Use either positional arguments, "
                    "--pattern, or --directory with --pattern")
    
    # Remove duplicates and sort
    file_paths = sorted(list(set(file_paths)))
    
    print(f"Found {len(file_paths)} files to process:")
    for fp in file_paths:
        print(f"  {fp}")
    
    if len(file_paths) < 2:
        print("Need at least 2 files to stitch together.")
        sys.exit(1)
    
    # Validate compatibility
    try:
        file_info = validate_files_compatibility(file_paths)
    except Exception as e:
        print(f"File validation failed: {e}")
        sys.exit(1)
    
    print("✓ All files are compatible")
    
    if args.dry_run:
        print("\nDry run - showing what would be done:")
        sorted_files = sort_files_by_time(file_info)
        output_file = create_combined_filename(sorted_files, args.output_dir)
        print(f"Would create: {output_file}")
        
        total_timesteps = sum(info['n_timesteps'] for info in sorted_files)
        
        # Handle cftime objects for year extraction
        start_time = sorted_files[0]['time_start']
        end_time = sorted_files[-1]['time_end']
        
        if hasattr(start_time, 'year'):
            start_year = start_time.year
        else:
            start_year = int(start_time.dt.year.values[0])
            
        if hasattr(end_time, 'year'):
            end_year = end_time.year
        else:
            end_year = int(end_time.dt.year.values[-1])
        
        print(f"Combined time range: {start_year}-{end_year}")
        print(f"Total timesteps: {total_timesteps}")
        return
    
    # Stitch datasets
    try:
        combined_ds = stitch_datasets(file_info, 
                                    check_continuity=not args.no_time_check,
                                    allow_gaps=args.allow_gaps)
        
        if combined_ds is None:
            print("Stitching aborted.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during stitching: {e}")
        sys.exit(1)
    
    # Determine output filename
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = create_combined_filename(file_info, args.output_dir)
    
    # Save combined dataset
    print(f"\nSaving combined dataset to: {output_file}")
    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        combined_ds.to_netcdf(output_file)
        print("✓ Successfully saved combined dataset")
        
        # Clean up
        for info in file_info:
            info['dataset'].close()
        combined_ds.close()
        
    except Exception as e:
        print(f"Error saving file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
