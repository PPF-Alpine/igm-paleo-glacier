#!/bin/bash

# Post-Interrupt Script for IGM Run
# Handles moving and logging files after an interrupted simulation
# - sjurbarndon@proton.me

# Exit on any command failure
set -e

# Assume the result folder is already created
result_folder=$(find . -maxdepth 1 -type d -name "*_result*" | sort -n | tail -n 1)

# If no result folder found, create one based on current directory
if [ -z "$result_folder" ]; then
    parent_dir=$(basename "$PWD")
    result_folder="${parent_dir}_result"
    mkdir -p "$result_folder"
fi

# Ensure we have an absolute path
result_folder=$(readlink -f "$result_folder")

# Find ALL log files in the current directory
log_files=($(find . -maxdepth 1 -type f -name "*.log"))

# If no log files exist, create a new one
if [ ${#log_files[@]} -eq 0 ]; then
    log_file="${result_folder}/interrupted_run.log"
    touch "$log_file"
else
    # Move ALL log files to the result folder
    for file in "${log_files[@]}"; do
        # Skip if already in result folder
        if [[ "$file" != "$result_folder/"* ]]; then
            mv "$file" "$result_folder/"
        fi
    done
    
    # Use the most recent log file
    log_file="$result_folder/$(basename "${log_files[-1]}")"
fi

# Add interrupt message to the log
echo "" >> "$log_file"
echo "!!! RUN INTERRUPTED AT $(date) !!!" >> "$log_file"
echo "Simulation was stopped before completion." >> "$log_file"
echo "Using existing result folder: $result_folder" >> "$log_file"
echo "Attempting to salvage and organize run files..." >> "$log_file"

# Move/copy output files
{   
    # Ensure log gets updated even if some files are missing
    echo "Attempting to move run files..." | tee -a "$log_file"

    # Copy configuration files
    [ -f params.json ] && cp params.json "$result_folder/" && echo "Copied params.json"  | tee -a "$log_file"
    [ -f params_saved.json ] && mv params_saved.json "$result_folder/" && echo "Moved params_saved.json" | tee -a "$log_file"

    # Move NetCDF output files
    [ -f output.nc ] && mv output.nc "$result_folder/" && echo "Moved output.nc" | tee -a "$log_file"
    [ -f output_ts.nc ] && mv output_ts.nc "$result_folder/" && echo "Moved output_ts.nc" | tee -a "$log_file"

    # Move visualization files
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

    # Try to find and move any metrics log
    metrics_log=$(find . -maxdepth 1 -type f -name "*_metrics.log" | sort -n | tail -n 1)
    if [ -n "$metrics_log" ]; then
        mv "$metrics_log" "$result_folder/" && echo "Moved metrics log: $metrics_log" | tee -a "$log_file"
    fi
} || echo "Some files were not found or could not be moved." | tee -a "$log_file"

# Generate summary plots if possible
if command -v gnuplot &> /dev/null; then
    metrics_log=$(find "$result_folder" -type f -name "*_metrics.log" | head -n 1)
    
    if [ -n "$metrics_log" ]; then
        echo "Generating resource usage plots..." | tee -a "$log_file"
        
        # Extract GPU memory usage data from metrics log for plotting
        grep -E "GPU:" "$metrics_log" | awk -F'[(/)]' '{print $1}' | sed 's/.*GPU: //g' > "$result_folder/gpu_mem.dat"
        
        # Create basic gnuplot script for GPU memory usage
        cat > "$result_folder/plot_gpu.gnu" << 'EOL'
set terminal png size 1200,600
set output "gpu_usage.png"
set title "GPU Memory Usage During Interrupted IGM Run"
set xlabel "Sample"
set ylabel "Memory Usage (MB)"
set grid
plot "gpu_mem.dat" using 1 with lines title "GPU Memory"
EOL
        
        # Run gnuplot if data file exists and has content
        if [ -s "$result_folder/gpu_mem.dat" ]; then
            (cd "$result_folder" && gnuplot plot_gpu.gnu)
            echo "Created GPU memory usage plot" | tee -a "$log_file"
        else
            echo "Not enough GPU data to create plot" | tee -a "$log_file"
        fi
    else
        echo "No metrics log found for plotting" | tee -a "$log_file"
    fi
else
    echo "gnuplot not found - skipping plot generation" | tee -a "$log_file"
fi

echo "Post-interrupt file organization completed." | tee -a "$log_file"
echo "Interrupted run files are available in: $result_folder" | tee -a "$log_file"
