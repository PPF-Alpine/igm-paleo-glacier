#!/usr/bin/env python3

# Copyright (C) 2021-2023 Guillaume Jouvet <guillaume.jouvet@unil.ch>
# Published under the GNU GPL (Version 3), check at the LICENSE file
# Adapted for paleo climate simulations by Sjur Barndon

import numpy as np
import os
import tensorflow as tf
import time
import logging
from netCDF4 import Dataset
from scipy.interpolate import interp1d
import scipy.ndimage
import numpy as np

def params(parser):
    # CLIMATE PARAMETERS
    parser.add_argument(
        "--paleo_clim_update_freq", 
        type=float,
        default=1,
        help="Update the climate each X years",
    )
    parser.add_argument(
        "--obs_atmosphere_file",
        type=str,
        default="present_day_observation_atmosphere.nc",
        help="Name of the atmosphere input file for present day CHELSA temperature and precipitation data",
    )
    parser.add_argument(
        "--anomaly_atmosphere_file",
        type=str,
        default="modeled_anomaly_clipped.nc",
        help="Name of the atmosphere input file for the modeled anomaly climate. Calculated from ESM1-2 by subtracting Historical from LGM.",
    )
    parser.add_argument(
        "--delta_temperature_file",
        type=str,
        default="dT_epica.nc",
        help="Name of (1) EPICA or (2) Latitudinally weighted Core Composites input file. Both are delta temperature time series for the climate outside the given time frame (delta_temp), unit: years",
    )
    parser.add_argument(
        "--year_0",
        default=1950,
        type=int,
        help="Year 0 of the climate data",
    )
    parser.add_argument(
        "--LGM_precip_adjustment", 
        help="The adjusment factor for LGM preciptiation, defaults to 0.5", 
        type=float, 
        default=0.5,
    )
    parser.add_argument(
        "--polar_amplification_adjustment",
        help="Ajustment factor for the polar amplification. Defaults to 0.5 as is the global mean around the equator.",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--precipitation_scaling",
        type=float,
        default=1.0,
        help="Development scaling factor for precipitation (e.g., 0.5 for 50% reduction, 1.5 for 50% increase)",
    )
    parser.add_argument(
        "--temperature_scaling",
    type=float,
        default=1.0,
        help="Development parameter:  scaling factor for temperature (e.g., 0.5 for 50% reduction, 1.5 for 50% increase)",
)    
    parser.add_argument(
        "--temperature_addition",
        type=float,
        default=0.0,
        help="Development parameter: temperature additon (e.g., 5 for 5 degrees warming)",
    )

def initialize(params, state):
    # Load climate data from netcdf file present_day_observation_atmosphere.nc
    observed_atmosphere = Dataset( os.path.join("./data/", params.obs_atmosphere_file))
    observed_elevation = np.squeeze(observed_atmosphere.variables["elevation"]).astype("float32")  # CHELSA Elevation that includes present day ice elevation.
    observed_precipitation = np.squeeze(observed_atmosphere.variables["precipitation"]).astype("float32")  # unit : kg * m^(-2) * month^(-1)
    observed_temperature= np.squeeze(observed_atmosphere.variables["air_temp"]).astype("float32")  # unit : degree Celsius
    observed_atmosphere_time = np.squeeze(observed_atmosphere.variables["time"]).astype("float32") # unit: years, TODO:  this is a test
    observed_atmosphere.close()

    # Add chelsa elvation to state
    state.observed_elevation = observed_elevation

    # Add the temperature data to the state
    state.temp_obs = (observed_temperature + params.temperature_addition) * params.temperature_scaling # Optional scaling/addition for testing

    # Add the precipitation data to the state
    # fix the units of precipitation, IGM expects kg * m^(-2) * y^(-1) instead of kg * m^(-2) * month^(-1)
    # The CHELSA data for precipitation is in monthly *amount*, not a rate. So it is correct to sum the months:
    # state.prec_obs = observed_precipitation.sum(axis=0) * params.precipitation_scaling # Optional scaling for testing

    # Skipping the above commented out sumation of the months to yearly.
    state.prec_obs =  observed_precipitation * params.precipitation_scaling 

    # Load the paleo climate temperature series
    # Either (1) EPICA signal from the dT_epica.nc file, or (2) the Latitudinally weighted core composites.
    delta_temperature_signal = Dataset(os.path.join("./data/", params.delta_temperature_file))

    # Access the variable data as numpy arrays
    delta_T_raw = np.squeeze(delta_temperature_signal.variables['delta_T'][:])

    # Adjust for polar amplification:
    delta_T_data = delta_T_raw * params.polar_amplification_adjustment 

    time_data = np.squeeze(delta_temperature_signal.variables['time'][:])

    # Get the LGM_precip_adjustment:
    state.pr_adj_LGM = params.LGM_precip_adjustment

    # Find minimum temperature, corresponding to the 0 value in the glacial index
    #TODO: This should perhaps be set to a spesific LGM year e.g. 21000 BP
    minimum_temperature = np.nanmin(delta_T_data)

    # Find the closest index and value for the present(1950)/historical, corresponding to the 1 value in the glacial index
    # TODO: This should perhaps be 1850, i.e preindustrial
    closest_1950_index = np.argmin(np.abs(time_data - 0))
    temperature_1950 = delta_T_data[closest_1950_index]

    # Create normalized glacial index
    glacial_index = (delta_T_data - minimum_temperature) / (temperature_1950 - minimum_temperature)

    # Convert time from "years before present (1950) / BP" to "calander years"
    calendar_years = time_data - params.year_0

    # Function to interpolate and set delta_T during update/simulation
    # simulation_time is state.t, left and right values will be used beyond the time series data.
    state.glacial_index_at_runtime = lambda simulation_time: np.interp(simulation_time, calendar_years, glacial_index, left=glacial_index[0], right=glacial_index[-1] ) 
    state.dT_at_runtime = lambda simulation_time: np.interp(simulation_time, calendar_years, delta_T_data, left=delta_T_data[0], right=delta_T_data[-1] )

    delta_temperature_signal.close()
   
    # intitalize air_temp and precipitation fields. The final precipitation and temperature must have shape (12,ny,nx)
    number_months = 12
    state.air_temp = tf.Variable(
        tf.zeros((number_months, state.y.shape[0], state.x.shape[0])),
        dtype="float32", trainable=False
    )
    state.precipitation = tf.Variable(
        tf.zeros((number_months, state.y.shape[0], state.x.shape[0])),
        dtype="float32", trainable=False
    )

    state.tlast_clim_oggm = tf.Variable(-(10**10), dtype="float32", trainable=False)
    state.tcomp_clim_oggm = []

    # List all loggers after importing IGM
    # print("THIS IS HERE")
    # for name in logging.root.manager.loggerDict:
    #     print(name)

def update(params, state):
    if (state.t - state.tlast_clim_oggm) >= params.paleo_clim_update_freq:
        if hasattr(state, "logger"):
            state.logger.info("update climate at time : " + str(state.t.numpy()))

        try: 
            glacial_index_at_runtime = state.glacial_index_at_runtime(state.t.numpy())
            delta_temperature_at_runtime = state.dT_at_runtime(state.t.numpy())
        except ValueError:
            logger.error("No more delta temperature data at this time value.")
            return
        
        state.tcomp_clim_oggm.append(time.time())

        # Compute the precipitation variable with the glacial index method: temperature = observed * (G + adjustment * (1-G)) 
        state.precipitation = tf.convert_to_tensor(state.prec_obs * (glacial_index_at_runtime + state.pr_adj_LGM *(1-glacial_index_at_runtime)), dtype="float32")

        # Set the temperature variable 
        state.air_temp = tf.convert_to_tensor(state.temp_obs + delta_temperature_at_runtime, dtype="float32")

        # vertical correction (lapse rates)
        # temp_corr_addi = params.temp_default_gradient * state.usurf
        # temp_corr_addi = params.temp_default_gradient * state.thk
        temp_corr_addi = params.temp_default_gradient * (state.usurf - state.observed_elevation)
        temp_corr_addi = tf.expand_dims(temp_corr_addi, axis=0)
        temp_corr_addi = tf.tile(temp_corr_addi, (12, 1, 1))

        # the final precipitation and temperature must have shape (12,ny,nx)
        state.air_temp = state.air_temp + temp_corr_addi

        state.meanprec = tf.math.reduce_mean(state.precipitation, axis=0)
        state.meantemp = tf.math.reduce_mean(state.air_temp, axis=0)

        # Debug prints
        # print(f"meanprec shape: {state.meanprec.shape}, dtype: {state.meanprec.dtype}")
        # print(f"meantemp shape: {state.meantemp.shape}, dtype: {state.meantemp.dtype}")
        # print(f"precipitation shape: {state.precipitation.shape}")
        # print(f"air_temp shape: {state.air_temp.shape}")

        # TODO: convert temperature and precipitation resulting data to correct output format for netcdf file for validation:
        # ValueError: cannot reshape array of size 4095300 into shape (1,10,365,935)
        # ValueError: operands could not be broadcast together with remapped shapes [original->remapped]: (12,365,935)  and requested shape (1,10,365,935)
        state.out_temperature =  state.air_temp
        state.out_precipitation =  state.precipitation
        #This can then be output to the nc result file for quick lookup

        state.tlast_clim_oggm.assign(state.t)

        state.tcomp_clim_oggm[-1] -= time.time()
        state.tcomp_clim_oggm[-1] *= -1


def finalize(params, state):
    pass
