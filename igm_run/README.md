# IGM Run
## Overview
IGM is a glacier modelling tool that simulates the dynamics of glaciers and ice sheets. This folder contains an example of how to run IGM using Python scripts. The modules_custom directory contains custom modules that are used by igm to run from pism inputs.

## Requirements
- Python 3.10+
- `igm_model`

note: consider installing `igm` from source as it's a developing project with frequent updates.

## Installation

1. Clone the repository or download the script files.
2. Install the required Python packages using `pip`:

    ```sh
    pip install igm_model
    ```

    Alternatively, you can install the required package the source code:

    ```sh
    git clone https://github.com/jouvetg/igm.git
    cd igm
    pip install -e .
    ```

## Usage

1. Place your glacier data in the `example/data` directory. The data should be in a format that IGM can read.
2. adjust parameters in the `example/params.json` file to suit your glacier model.
3. Run the `igm_run` script from the example dir to start the simulation:
    ```sh
    igm_run
    ```

## Directory Structure
```
.
├── [README.md]
└── example
    ├── data
    │   └── PUT_GLACIER_DATA_HERE.md
    ├── modules_custom
    │   ├── clim_pism.py
    │   ├── plot-climate-forcing.py
    │   └── smb_pism.py
    └── params.json
```

### modules_custom
The `modules_custom` directory contains custom modules that are used by IGM to run from PISM inputs. These modules include:
- `clim_pism.py`: A module for handling climate data from PISM.
- `plot_smb.py`: A module for plotting surface mass balance data.
- `plot-climate-forcing.py`: A module for plotting climate forcing data.
- `smb_pism.py`: A module for calculating surface mass balance using data in the PISM format.