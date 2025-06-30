#!/bin/bash

# Script to create a new simulation directory with a specific structure
# Usage: ./make_simulation_directory.sh <new_folder_name> <path_to_copy_data_from>

# Check if correct number of arguments provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <new_folder_name> <path_to_copy_data_from>"
    exit 1
fi

    
# Store arguments
NEW_FOLDER_NAME="$1"
DATA_PATH="$2"

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define paths
BASE_DIR="${SCRIPT_DIR}/.."  # Go up one level from run_scripts
IGM_RUN_DIR="${BASE_DIR}/igm_run"
NEW_FOLDER_PATH="${IGM_RUN_DIR}/${NEW_FOLDER_NAME}"
DATA_DIR="${NEW_FOLDER_PATH}/data"
MODULES_CUSTOM_DIR="${NEW_FOLDER_PATH}/modules_custom"
POST_PROCESS_DIR="${NEW_FOLDER_PATH}/post_process_scripts"

# Check if the new folder already exists
if [ -d "$NEW_FOLDER_PATH" ]; then
    echo "Error: The folder ${NEW_FOLDER_NAME} already exists in ${IGM_RUN_DIR}"
    exit 1
fi

# Check if the path to copy data from exists
if [ ! -d "$DATA_PATH" ]; then
    echo "Error: The data path ${DATA_PATH} does not exist"
    exit 1
fi

# Create the directory structure
echo "Creating directory structure..."
mkdir -p "$NEW_FOLDER_PATH"
mkdir -p "$DATA_DIR"
mkdir -p "$POST_PROCESS_DIR"

# Copy modules_custom folder from base directory:
if [ -d "${BASE_DIR}/modules_custom" ]; then
    echo "Copying modules_custom folder..."
    cp -r "${BASE_DIR}/modules_custom" "$MODULES_CUSTOM_DIR"
else
    echo "Warning: modules_custom folder not found in ${BASE_DIR}"
    mkdir -p "$MODULES_CUSTOM_DIR"  # Create an empty one if source doesn't exist
fi

# Copy contents from run_scripts except for this script
echo "Copying run scripts..."
# for file in "${SCRIPT_DIR}"/*; do
#     # Skip the script itself
#     if [ "$(basename "$file")" != "$(basename "$0")" ]; then
#         cp -r "$file" "$NEW_FOLDER_PATH/"
#     fi
# done
cp "${SCRIPT_DIR}"/params.json "$NEW_FOLDER_PATH/"
cp "${SCRIPT_DIR}"/estimate_sim_eta.sh "$NEW_FOLDER_PATH/"

# Check for localised verisions of the run scripts and file management:
if [ -f "${SCRIPT_DIR}/paleo_igm.local.sh" ]; then
  echo "Copying local versions of run_scripts."
  cp "${SCRIPT_DIR}"/paleo_igm.local.sh "$NEW_FOLDER_PATH/paleo_igm.sh"
  cp "${SCRIPT_DIR}"/paleo_post_interrupt.local.sh "$NEW_FOLDER_PATH/paleo_post_interrupt.sh"
else
  echo "Copying standard versions of run_scripts."
  cp "${SCRIPT_DIR}"/paleo_igm.sh "$NEW_FOLDER_PATH/"
  cp "${SCRIPT_DIR}"/paleo_post_interrupt.sh "$NEW_FOLDER_PATH/"
fi

# Copy post process scripts to the new folder
cp "${BASE_DIR}"/post_process_scripts/ice_thickness_outline_extractor.py "$POST_PROCESS_DIR" 

# Copy everything from the specified path to the data subfolder
echo "Copying data from ${DATA_PATH}..."
cp -r "${DATA_PATH}"/* "$DATA_DIR/"

echo "Setup complete! New simulation directory created at: ${NEW_FOLDER_PATH}"
echo "Directory structure:"
echo "- ${NEW_FOLDER_NAME}/"
echo "  ├── data/         (populated with data from ${DATA_PATH})"
echo "  ├── post_process_scripts/         (populated with data from ${POST_PROCESS_DIR})"
echo "  ├── modules_custom/ (copied from ${BASE_DIR}/modules_custom/)"
echo "  └── run scripts (copied from ${BASE_DIR}/run_scripts/)"

exit 0
