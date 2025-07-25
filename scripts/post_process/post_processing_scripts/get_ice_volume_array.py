import glob
import re
import numpy as np
import os

def get_ice_volumes_with_path(log_dir=None):
    """
    Finds *.log files (excluding *metrics.log) in specified directory,
    extracts the last number from lines matching IGM timestamp pattern,
    and returns them as a numpy array.
    """
    if log_dir is None:
    # Default to parent directory of script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.dirname(script_dir)
    
    print(f"Looking for log files in: {log_dir}")
    
    # Use os.path.join for cross-platform compatibility
    log_pattern = os.path.join(log_dir, "*.log")
    all_log_files = glob.glob(log_pattern)
    
    # Filter out metrics.log files
    log_files = [f for f in all_log_files if not f.endswith("metrics.log")]
    
    print(f"Found log files: {log_files}")
    
    if not log_files:
        print("No suitable .log files found")
        all_files = os.listdir(log_dir)
        print(f"All files in {log_dir}: {all_files}")
        return np.array([]), np.array([])
    
    # Pattern to match IGM lines with timestamp
    igm_pattern = r'IGM\s+\d{2}:\d{2}:\d{2}\s+:'
    
    years = []
    volumes = []
    
    for log_file in log_files:
        print(f"Processing log file: {log_file}")
        try:
            with open(log_file, 'r') as f:
                line_count = 0
                matching_lines = 0
                for line in f:
                    line_count += 1
                    if re.search(igm_pattern, line):
                        matching_lines += 1
                        # Split line by | and get parts
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                try:
                                    # Extract year (second column) and volume (last column)
                                    year = int(float(parts[1].strip()))
                                    volume = float(parts[3].strip())
                                    years.append(year)
                                    volumes.append(volume)
                                except ValueError:
                                    print(f"Could not parse year/volume in line: {line.strip()}")
                                    continue
                        else:
                            # Fallback to original method if no | separator
                            parts = line.strip().split()
                            if parts:
                                try:
                                    volume = float(parts[-1])
                                    volumes.append(volume)
                                    # You'd need to extract year differently here
                                except ValueError:
                                    print(f"Could not convert last value to float in line: {line.strip()}")
                                    continue
                print(f"Processed {line_count} lines, found {matching_lines} matching IGM lines")
        except IOError:
            print(f"Could not read file: {log_file}")
            continue
    
    print(f"Total values extracted: {len(volumes)}")
    return np.array(years), np.array(volumes)
