#!/bin/bash

# This script will run the `igm_run` command, measure time, and log output in a igm_run_log.txt file.
# It will also create a unique result folder based on the current directory name.
# - Author: sjurbarndon@proton.me

set -e  # Exit on any command failure

# Get the name of the current directory
parent_dir=$(basename "$PWD")
base_result_folder="${parent_dir}_result"
result_folder="$base_result_folder"

# Find a unique folder name
counter=1
while [ -d "$result_folder" ]; do
    result_folder="${base_result_folder}_$counter"
    ((counter++))
done

# Set log file name based on result folder name
log_file="${result_folder}.log"


# Log start time
echo "Starting igm_runt $(date)" | tee -a "$log_file"

# Start igm_run command with timer.
PYTHONUNBUFFERED=1 /usr/bin/time -f "\nTime stats:\nUser time: %U seconds\nSystem time: %S seconds\nElapsed time: %E (hh:mm:ss), %e seconds (raw)\nCPU usage: %P\nMax memory: %M KB\nPage faults: %F major, %R minor\nSwaps: %W\n" igm_run 2>&1 | tee -a "$log_file"


# If we reached this point, igm_run was successful
echo "igm_run completed successfully at $(date)" | tee -a "$log_file"

# Create result folder
mkdir -p "$result_folder"
echo "Created result folder: $result_folder" | tee -a "$log_file"

# Move log file into result folder
mv "$log_file" "$result_folder/"
log_file="$result_folder/$(basename "$log_file")"  # Update path for continued logging
echo "Moved log file into result folder" | tee -a "$log_file"

	
# Move/copy output files
{   [ -f params.json ] && cp params.json "$result_folder/" && echo "Copied params.json"  | tee -a "$log_file"
    [ -f params_saved.json ] && mv params_saved.json "$result_folder/" && echo "Moved params_saved.json" | tee -a "$log_file"
    [ -f output.nc ] && mv output.nc "$result_folder/" && echo "Moved output.nc" | tee -a "$log_file"
    [ -f output_ts.nc ] && mv output_ts.nc "$result_folder/" && echo "Moved output_ts.nc" | tee -a "$log_file"
    [ -f computational-pie.png ] && mv computational-pie.png "$result_folder/" && echo "Moved computational-pie.png" | tee -a "$log_file"
    [ -f memory-pie.png ] && mv memory-pie.png "$result_folder/" && echo "Moved memory-pie.png" | tee -a "$log_file"
    [ -f computational-statistics.txt ] && mv computational-statistics.txt "$result_folder/" && echo "Moved computational-statistics.txt" | tee -a "$log_file"

    # Move .tif files
    tif_files_found=$(find . -maxdepth 1 -type f -name "*.tif")
    if [ -n "$tif_files_found" ]; then
        find . -maxdepth 1 -type f -name "*.tif" -exec mv {} "$result_folder/" \;
        echo "Moved all .tif files to $result_folder/" | tee -a "$log_file"
    else
        echo "No .tif files found to move." | tee -a "$log_file"
    fi
} || echo "Some files were not found or could not be moved." | tee -a "$log_file"

echo "All post-run steps completed." | tee -a "$log_file"
