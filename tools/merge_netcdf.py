import numpy as np
from netCDF4 import Dataset

def merge_netcdf(files, output_file, year_ranges):
    nc = Dataset(output_file, 'w', format='NETCDF4')

    # Open the first file to get the dimensions and variables
    with Dataset(files[0], 'r') as src:
        x_dim = src.dimensions['x'].size
        y_dim = src.dimensions['y'].size
        variables = {var: src.variables[var] for var in src.variables}

        nc.createDimension("time", None)
        E = nc.createVariable("time", np.dtype("float32").char, ("time",))
        E.units = "yr"
        E.long_name = "time"
        E.axis = "T"

        nc.createDimension("y", y_dim)
        E = nc.createVariable("y", np.dtype("float32").char, ("y",))
        E.units = "m"
        E.long_name = "y"
        E.axis = "Y"

        nc.createDimension("x", x_dim)
        E = nc.createVariable("x", np.dtype("float32").char, ("x",))
        E.units = "m"
        E.long_name = "x"
        E.axis = "X"

        # Copy the variables from the first file
        for var in variables:
            if var in ['x', 'y', 'z', 'time']:
                continue
            E = nc.createVariable(
                var, np.dtype("float32").char, ("time", "y", "x")
            )

    for var_name, var in nc.variables.items():
        if 'time' in var.dimensions:
            data = []
            for f, year_range in zip(files, year_ranges):
                with Dataset(f) as src:
                    times = src.variables['time'][:]
                    time_indices = [i for i, t in enumerate(times) if year_range[0] <= t <= year_range[1]]
                    data.append(src.variables[var_name][time_indices])
            nc.variables[var_name][:] = np.concatenate(data, axis=0)
        else:
            # print(f"Skipping variable {var_name} because it does not have a time dimension")
            pass
    
    nc.close()

if __name__ == "__main__":
    files = ['run_2/run_2.nc', 'run_2/run_2_continued_49400.nc']  # List of input NetCDF files
    output_file = 'merged_output.nc'  # Output NetCDF file
    year_ranges = [(-130000, -48200), (-48100, 1950)]  # Example: select year ranges from each file
    print('Merging NetCDF files, on year ranges:', year_ranges)
    merge_netcdf(files, output_file, year_ranges)