#!/usr/bin/env python3

# Copyright (C) 2021-2023 Guillaume Jouvet <guillaume.jouvet@unil.ch>
# Published under the GNU GPL (Version 3), check at the LICENSE file
# Adapted for paleo climate simulations by Abe Wiersma and Sjur Barndon

import numpy as np
import os
import tensorflow as tf
import time
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
        default="dT_composite_at_latitude.nc",
        help="Name of (1) EPICA or (2) Latitudinally weighted Core Composites input file. Both are delta temperature time series for the climate outside the given time frame (delta_temp), unit: years",
    )
    parser.add_argument(
        "--year_0",
        default=1950,
        type=int,
        help="Year 0 of the climate data",
    )
    parser.add_argument(
        "--precipitation_scaling",
        type=float,
        default=1.0,
        help="Scaling factor for precipitation (e.g., 0.5 for 50% reduction, 1.5 for 50% increase)",
    )
    parser.add_argument(
        "--temperature_scaling",
    type=float,
        default=1.0,
        help="Scaling factor for temperature (e.g., 0.5 for 50% reduction, 1.5 for 50% increase)",
    )    
    parser.add_argument(
        "--temperature_addition",
        type=float,
        default=0.0,
        help="Temperature additon (e.g., 5 for 5 degrees warming)",
    )

def initialize(params, state):
    # Load climate data from netcdf file present_day_observation_atmosphere.nc
    observed_atmosphere = Dataset( os.path.join("./data/", params.obs_atmosphere_file))
    observed_precipitation = np.squeeze(observed_atmosphere.variables["precipitation"]).astype("float32")  # unit : kg * m^(-2) * month^(-1)
    observed_temperature= np.squeeze(observed_atmosphere.variables["air_temp"]).astype("float32")  # unit : degree Celsius
    observed_atmosphere.close()

    # Add the temperature data to the state
    state.temp = (observed_temperature + params.temperature_addition) * params.temperature_scaling # Optional scaling/addition for testing

    # Add the precipitation data to the state
    # fix the units of precipitation, IGM expects kg * m^(-2) * y^(-1) instead of kg * m^(-2) * month^(-1)
    # The CHELSA data for precipitation is in monthly *amount*, not a rate. So it is correct to sum the months:
    state.prec = observed_precipitation.sum(axis=0) * params.precipitation_scaling # Optional scaling for testing

    # Load climate anomaly data
    modeled_anomaly = Dataset(os.path.join("./data/", params.anomaly_atmosphere_file))
    anomaly_precipitation = np.squeeze(modeled_anomaly.variables["precipitation"]).astype("float32")
    anomaly_temperature = np.squeeze(modeled_anomaly.variables["air_temp"]).astype("float32")
    modeled_anomaly.close()

    # Add the modelled temperature and precipitation to the state
    state.anomaly_temperature = anomaly_temperature 
    state.anomaly_precipitation = anomaly_precipitation


    print(f"SHAPE OF TEMPERATURE: {state.temp.shape}")
    print(f"SHAPE OF PRECIPITATION: {state.prec.shape}")
    print(f"SHAPE OF ANOMALY TEMP:{state.anomaly_temperature.shape}")
    print(f"SHAPE OF ANOMALY PREC:{state.anomaly_precipitation.shape}")

    target_y, target_x = state.temp.shape[1], state.temp.shape[2]  # (365, 935)

    if state.anomaly_temperature.shape[1:] != (target_y, target_x):
        # Crop to match - take the first 365 rows and 935 columns
        state.anomaly_temperature = state.anomaly_temperature[:, :target_y, :target_x]
        state.anomaly_precipitation = state.anomaly_precipitation[:, :target_y, :target_x]
        
        print(f"Cropped anomaly data from {state.anomaly_temperature.shape} to match base climate")
        print(f"New anomaly temp shape: {state.anomaly_temperature.shape}")
        print(f"New anomaly prec shape: {state.anomaly_precipitation.shape}")

    # Load the paleo climate temperature series
    # Either (1) EPICA signal from the dT_epica.nc file, or (2) the Latitudinally weighted core composites.
    delta_temperature_signal = Dataset(os.path.join("./data/", params.delta_temperature_file))

    # Access the variable data as numpy arrays
    delta_T_data = delta_temperature_signal.variables['delta_T'][:]
    time_data = delta_temperature_signal.variables['time'][:]
    state.delta_temperature_time_data = time_data

    # Find minimum temperature
    min_temp = np.nanmin(delta_T_data)

    # Find 1950 value (time=0 corresponds to 1950 based on your time units)
    temp_1950_idx = np.where(time_data == 0)[0][0]  # Find index where time=0 (1950)
    temp_1950 = delta_T_data[temp_1950_idx]

    # Create normalized index
    normalized_index = (delta_T_data - min_temp) / (temp_1950 - min_temp)
    state.glacial_index = normalized_index
 

    # TODO: unomment the things below and use it to have the opton to still use EPICA, args must be updated...

    # extract time BP, change to AD (1950 is present for EPICA)
    # time = np.squeeze(delta_temperature_signal.variables["time"]).astype("int")  # unit : years
    # time = time - params.year_0
    # extract the dT, i.e. global temp. difference
    # dT = np.squeeze(delta_temperature_signal.variables["delta_T"]).astype("float32")  # unit : degree Kelvin
    delta_temperature_signal.close()

    # dT is a function of time, we need to interpolate it
    # to get the dT at the time of the simulation
    # state.dT = lambda t: np.interp(t, time, dT, left=dT[0], right=dT[-1])

    # Set year 0 of the climate data as based on input parameter
    # params.yr_0 = params.year_0

   
   
    # intitalize air_temp and precipitation fields
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




def update(params, state):
    if (state.t - state.tlast_clim_oggm) >= params.paleo_clim_update_freq:
        if hasattr(state, "logger"):
            state.logger.info("update climate at time : " + str(state.t.numpy()))
        
        # try:
        #     dT = state.dT(state.t.numpy())
        # except ValueError:
        #     # break out of the loop if the dT is not available
        #     return

        # Find current time index (assuming you have current time available)
        current_time_idx = np.argmin(np.abs(state.delta_temperature_time_data - state.t))
        current_glacial_index = state.glacial_index[current_time_idx]

        state.tcomp_clim_oggm.append(time.time())

        # (state.prec + (1 - glacial_index) * state.anomaly_precipitation)
        state.precipitation = tf.convert_to_tensor(state.prec + (1 - current_time_idx) * state.anomaly_precipitation, dtype="float32")


        # If state.anomaly_temperature is 2D (ny, nx), add time dimension
        if state.anomaly_temperature.ndim == 2:
            anomaly_temp = state.anomaly_temperature[np.newaxis, :, :]  # (1, ny, nx)
        else:
            anomaly_temp = state.anomaly_temperature
        
        ####temp_modified = state.temp + (1 - current_glacial_index) * anomaly_temp
        state.air_temp = tf.convert_to_tensor(state.temp + (1 - current_glacial_index) * state.anomaly_temperature, dtype="float32")

        # The shape of state.temp is (12,ny,nx), all that is needed is to add the dT to the temperature
        # and to create a tensor from the numpy array

        # state.temp + (1 - glacial_index) * state.anomaly_temperature
        # state.air_temp = tf.convert_to_tensor(state.temp, dtype="float32")

        # vertical correction (lapse rates)
        temp_corr_addi = params.temp_default_gradient * state.usurf
        temp_corr_addi = tf.expand_dims(temp_corr_addi, axis=0)
        temp_corr_addi = tf.tile(temp_corr_addi, (12, 1, 1))

        # the final precipitation and temperature must have shape (12,ny,nx)
        state.air_temp = state.air_temp + temp_corr_addi

        state.meanprec = tf.math.reduce_mean(state.precipitation, axis=0)
        state.meantemp = tf.math.reduce_mean(state.air_temp, axis=0)

        state.tlast_clim_oggm.assign(state.t)

        state.tcomp_clim_oggm[-1] -= time.time()
        state.tcomp_clim_oggm[-1] *= -1


def finalize(params, state):
    pass
