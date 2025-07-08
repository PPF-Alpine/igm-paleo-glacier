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

# Define paths to use
IGM_RUN_DIR="../../igm_run"

# New folder directories:
NEW_FOLDER_DIR="${IGM_RUN_DIR}/${NEW_FOLDER_NAME}"
DATA_DIR="${NEW_FOLDER_DIR}/data"
MODULES_CUSTOM_DIR="${NEW_FOLDER_DIR}/modules_custom"
POST_PROCESS_DIR="${NEW_FOLDER_DIR}/post_process_scripts"

# Relative paths from new folder
BASE_PATH="../.."  # Go up to base level from new folder 
SIM_DEFAULT_FILE_PATH="${BASE_PATH}/scripts/make_simulation_directory/simulation_default_files"
MODULES_CUSTOM_PATH="${SIM_DEFAULT_FILE_PATH}/modules_custom"
POST_PROCESS_PATH="${BASE_PATH}/scripts/post_process"

# Check if the new folder already exists
if [ -d "$NEW_FOLDER_DIR" ]; then
    echo "Error: The folder ${NEW_FOLDER_DIR} already exists in ${IGM_RUN_DIR}"
    exit 1
fi

# Check if the path to copy data from exists
if [ ! -d "$DATA_PATH" ]; then
    echo "Error: The data path ${DATA_PATH} does not exist"
    exit 1
fi

# Create the directory structure
echo "Creating directory structure..."
mkdir -p "$NEW_FOLDER_DIR"

echo "Creating symlinks to custom modules, post prosessing and climate data"
# Create symbolic link to custom module folder:
ln -s "$MODULES_CUSTOM_PATH" "$MODULES_CUSTOM_DIR" 

# Create symbolic link to clipped climate data:
ln -s "$2" "$DATA_DIR"

# Copy post process scripts to the new folder
ln -s "${POST_PROCESS_PATH}" "$POST_PROCESS_DIR" 

# Copy contents from run_scripts except for this script
echo "Copying run scripts..."
cp "${SIM_DEFAULT_FILE_PATH}"/params.json "$NEW_FOLDER_DIR/"
cp "${SIM_DEFAULT_FILE_PATH}"/estimate_sim_eta.sh "$NEW_FOLDER_DIR/"

cp "${SIM_DEFAULT_FILE_PATH}"/paleo_igm.sh "$NEW_FOLDER_DIR/"
cp "${SIM_DEFAULT_FILE_PATH}"/paleo_post_interrupt.sh "$NEW_FOLDER_DIR/"


echo "Setup complete! New simulation directory created at: ${NEW_FOLDER_DIR}"
echo "Directory structure:"
echo "- ${NEW_FOLDER_NAME}/"
echo "  ├── data/         (link to ${DATA_PATH})"
echo "  ├── post_process_scripts/ (link to ${POST_PROCESS_DIR})"
echo "  ├── modules_custom/ (link to $MODULES_CUSTOM_DIR)"
echo "  └── run scripts (copied from ${SIM_DEFAULT_FILE_PATH})"

exit 0
