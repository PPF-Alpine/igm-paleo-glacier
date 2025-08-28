#!/bin/bash

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <target_directory_name> <polar_amplification_adjustment>"
    echo "Example: $0 central_andes_north_simple 0.57"
    echo "This will create calibration folders based on the specified directory in igm_run/"
    echo "with the specified polar amplification adjustment value"
    exit 1
fi

# Get the target directory name and polar amplification from command line arguments
TARGET_DIR="$1"
TARGET_DIR_NAME=$(basename "$TARGET_DIR")
POLAR_AMP="$2"

# Validate polar amplification argument is a number
if ! [[ "$POLAR_AMP" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    echo "Error: polar_amplification_adjustment must be a number (e.g., 0.57)"
    exit 1
fi

# Set paths relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IGM_RUN_DIR="$SCRIPT_DIR/../../igm_run"
SOURCE_PATH="$IGM_RUN_DIR/$TARGET_DIR"

# Check if source directory exists
if [ ! -d "$SOURCE_PATH" ]; then
    echo "Error: Source directory '$SOURCE_PATH' does not exist"
    echo "Available directories in igm_run:"
    ls -1 "$IGM_RUN_DIR" 2>/dev/null || echo "igm_run directory not found"
    exit 1
fi

# Arrays for parameter values
lgm_precip=(1.53 1 2)
iflo_sliding=(0.0225 0.045 0.09)
smb_melt=(1 1.2 1.1)

# Load lapse rate from data/localised_lapse_rate.txt file
if [ -f "$SOURCE_PATH/data/localised_lapse_rate.txt" ]; then
    lapserate=$(cat "$SOURCE_PATH/data/localised_lapse_rate.txt")
    echo "Loaded lapse rate: $lapserate from $TARGET_DIR/data/localised_lapse_rate.txt"
else
    lapserate=0.004
    echo "Warning: $TARGET_DIR/data/localised_lapse_rate.txt not found, using default lapse rate: $lapserate"
fi

# Counter for folder numbering
counter=1

# Change to igm_run directory for operations
cd "$IGM_RUN_DIR"

# Generate all combinations
for lgm in "${lgm_precip[@]}"; do
    for iflo in "${iflo_sliding[@]}"; do
        for smb in "${smb_melt[@]}"; do
            # Create directory with preserved symlinks, excluding result_links/
            CALIBRATION_DIR="${TARGET_DIR_NAME}_calibration_$counter"
            cp -a "$TARGET_DIR" "$CALIBRATION_DIR"
            rm -rf "$CALIBRATION_DIR/result_links"
            
            # Update params.json with current parameter combination
            cat > "$CALIBRATION_DIR/params.json" << EOF
{
  "modules_preproc": [
    "load_ncdf"
  ],
  "modules_process": ["simplified_glacial_index_clim",
                      "paleo_smb",
                      "iceflow",
                      "time",
                      "thk",
                      "vert_flow",
                      "avalanche"
                     ],
  "modules_postproc": ["write_ncdf",
                       "write_tif",
                       "write_ts",
                       "print_info",
                       "print_comp"
                      ],
  "lncd_input_file": "data/topography.nc",
  "delta_temperature_file" : "dT_epica.nc",
   "wncd_vars_to_save": [
    "topg",
    "thk",
    "smb",
    "meantemp",
    "meanprec"
  ],
  "time_start": -140000.0,
  "time_end": 2000.0,
  "time_save": 100.0,
  "LGM_precip_adjustment" : $lgm,
  "iflo_init_slidingco" : $iflo,
  "smb_melt_factors_calibration": $smb,
  "polar_amplification_adjustment" : $POLAR_AMP,
  "temp_default_gradient": $lapserate,
  "precipitation_scaling": 1,
  "temperature_scaling": 1 
}
EOF
            
            echo "Created $CALIBRATION_DIR with LGM_precip=$lgm, iflo_sliding=$iflo, smb_melt=$smb, polar_amp=$POLAR_AMP"
            ((counter++))
        done
    done
done

# Create cleanup script
CLEANUP_SCRIPT="clean_${TARGET_DIR_NAME}_calibration.sh"
TOTAL_FOLDERS=$((counter-1))

cat > "$CLEANUP_SCRIPT" << EOF
#!/bin/bash

echo "Removing all ${TARGET_DIR_NAME} calibration directories..."

# Remove all calibration directories
for i in {1..$TOTAL_FOLDERS}; do
    if [ -d "${TARGET_DIR_NAME}_calibration_\$i" ]; then
        rm -rf "${TARGET_DIR_NAME}_calibration_\$i"
        echo "Removed ${TARGET_DIR_NAME}_calibration_\$i"
    fi
done

echo "Cleanup complete!"
EOF

# Make cleanup script executable
chmod +x "$CLEANUP_SCRIPT"

echo "Successfully created $TOTAL_FOLDERS calibration directories"
echo "Created cleanup script: $CLEANUP_SCRIPT"
