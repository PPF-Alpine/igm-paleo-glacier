# EPICA Data Processing

This tool downloads and processes EPICA (European Project for Ice Coring in Antarctica) data, converting it to yearly CSV files with different intervals.

## Requirements
- Python 3.6+
- `numpy`
- `scipy`
- `urllib`
- `pathlib`
- `logging`

## Installation

1. Clone the repository or download the script files.
2. Install the required Python packages using `pip`:

    ```sh
    pip install numpy scipy
    ```

## Usage

Ensure you have an internet connection to download the EPICA data. Run the `epica_to_yearly_csv.py` script:

    ```sh
    python epica_to_yearly_csv.py
    ```

This will download the EPICA data and save it to the `./epica` directory. It will then process the data and generate the following CSV files in the same directory:

- `epica_data.csv`: Contains the interpolated temperature data for each year.
- `epica_data_100.csv`: Contains the interpolated temperature data for every 100 years.
- `epica_data_1000.csv`: Contains the interpolated temperature data for every 1000 years.

## Directory Structure
```
.
├── [epica_to_yearly_csv.py](http://_vscodecontentref_/2)
├── [README.md](http://_vscodecontentref_/3)
└── epica
    ├── epica_data.csv
    ├── epica_data_100.csv
    └── epica_data_1000.csv
```

# Merge NetCDF Files

## Requirements
- Python 3.6+
- `numpy`
- `netCDF4`

## Usage

Run the `merge_netcdf_files.py` script:

    ```sh
    python merge_netcdf_files.py
    ```

Change the file paths in the script to match the files you want to merge.

# License
TBD