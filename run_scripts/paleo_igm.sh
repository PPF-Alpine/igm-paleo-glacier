#!/bin/bash

# This script will run the `igm_run` command, measure time, and log output in a igm_run_log.txt file.
# It will also create a unique result folder based on the current directory name.
# - sjurbarndon@proton.me

set -e  # Exit on any command failure

# --- CONFIGURATION ---
# Set to true to capture metrics at each IGM timestep line
CAPTURE_AT_TIMESTEPS=true
# Set interval in seconds for regular metric collection (used if CAPTURE_AT_TIMESTEPS=false)
METRICS_INTERVAL=60*10  # 10 minutes


# --- HELPER FUNCTIONS ---
# Function to get GPU metrics (using nvidia-smi)
get_gpu_metrics() {
    if command -v nvidia-smi &> /dev/null; then
        GPU_MEM=$(nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | tr ',' ' ' | awk '{print $1"MB/"$2"MB ("int($1*100/$2)"%)", "GPU util: "$3"%"}')
        echo "GPU: $GPU_MEM"
    else
        echo "GPU: No NVIDIA GPU detected"
    fi
}

# Function to get CPU metrics
get_cpu_metrics() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4"%"}')
    CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | tr -d ',')
    MEM_USAGE=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    echo "CPU: $CPU_USAGE, Load:$CPU_LOAD, Mem: $MEM_USAGE"
}

# Combined function to get all metrics
capture_metrics() {
    TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
    GPU_INFO=$(get_gpu_metrics)
    CPU_INFO=$(get_cpu_metrics)
    echo "[$TIMESTAMP] $GPU_INFO | $CPU_INFO" >> "$metrics_log"
    
    # If you want to see the metrics in the main log as well
    echo "[$TIMESTAMP] $GPU_INFO | $CPU_INFO" >> "$log_file"
}

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
metrics_log="${result_folder}_metrics.log"

# Create result folder early to store logs
mkdir -p "$result_folder"
echo "Created result folder: $result_folder" | tee -a "$log_file"

# Log start time
echo "Starting igm_run $(date)" | tee -a "$log_file"
echo "=== System Metrics Log ===" > "$metrics_log"
echo "Starting monitoring at $(date)" >> "$metrics_log"

# Capture initial metrics
capture_metrics

# Start background monitoring if not capturing at timesteps
if [ "$CAPTURE_AT_TIMESTEPS" = false ]; then
    {
        while true; do
            capture_metrics
            sleep $METRICS_INTERVAL
        done
    } &
    MONITOR_PID=$!
    # Make sure to kill the monitoring process when the script exits
    trap "kill $MONITOR_PID 2>/dev/null || true" EXIT
fi


# Start igm_run with output interception
if [ "$CAPTURE_AT_TIMESTEPS" = true ]; then
    # Run with output processing to capture metrics at each timestep
    PYTHONUNBUFFERED=1 /usr/bin/time -f "\nTime stats:\nUser time: %U seconds\nSystem time: %S seconds\nElapsed time: %E (hh:mm:ss), %e seconds (raw)\nCPU usage: %P\nMax memory: %M KB\nPage faults: %F major, %R minor\nSwaps: %W\n" igm_run 2>&1 | while IFS= read -r line; do
        echo "$line" | tee -a "$log_file"
        
        # Check if this is an IGM timestep line
        if [[ "$line" =~ ^IGM[[:space:]][0-9]+:[0-9]+:[0-9]+[[:space:]]+:[[:space:]]+[0-9]+ ]]; then
            capture_metrics
        fi
    done
else
    # Run without intercepting output
    PYTHONUNBUFFERED=1 /usr/bin/time -f "\nTime stats:\nUser time: %U seconds\nSystem time: %S seconds\nElapsed time: %E (hh:mm:ss), %e seconds (raw)\nCPU usage: %P\nMax memory: %M KB\nPage faults: %F major, %R minor\nSwaps: %W\n" igm_run 2>&1 | tee -a "$log_file"
    
    # Kill the monitoring process if it exists
    if [[ -n "$MONITOR_PID" ]]; then
        kill $MONITOR_PID 2>/dev/null || true
    fi
fi

# If we reached this point, igm_run was successful
echo "The igm_run completed successfully at $(date)" | tee -a "$log_file"
echo "Monitoring completed at $(date)" >> "$metrics_log"

# Move log file into result folder
mv "$log_file" "$result_folder/"
mv "$metrics_log" "$result_folder/"
log_file="$result_folder/$(basename "$log_file")"  # Update path for continued logging
echo "Moved log files into result folder" | tee -a "$log_file"

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

# Generate summary plots
if command -v gnuplot &> /dev/null; then
    echo "Generating resource usage plots..." | tee -a "$log_file"
    
    # Extract GPU memory usage data from metrics log for plotting
    grep -E "GPU:" "$result_folder/$metrics_log" | awk -F'[(/)]' '{print $1}' | sed 's/.*GPU: //g' > "$result_folder/gpu_mem.dat"
    
    # Create basic gnuplot script for GPU memory usage
    cat > "$result_folder/plot_gpu.gnu" << 'EOL'
set terminal png size 1200,600
set output "gpu_usage.png"
set title "GPU Memory Usage During IGM Run"
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
    echo "gnuplot not found - skipping plot generation" | tee -a "$log_file"
fi

echo "All post-run steps completed." | tee -a "$log_file"
echo "Resource usage metrics are available in: $result_folder/$(basename "$metrics_log")" | tee -a "$log_file"