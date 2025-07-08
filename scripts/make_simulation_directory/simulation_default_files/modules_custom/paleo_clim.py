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


def params(parser):
    # CLIMATE PARAMETERS
    parser.add_argument(
        "--clim_pism_update_freq", #TODO: rename this to "paleo_clim_update_freq" 
        type=float,
        default=1,
        help="Update the climate each X years",
    )
    parser.add_argument(
        "--pism_atm_file",
        type=str,
        default="atm.nc",
        help="Name of the atmosphere input file for the climate outide the given datatime frame (time, delta_temp, prec_scali)",
    )
    parser.add_argument(
        "--dt_epica_file",
        type=str,
        default="dT_epica.nc",
        help="Name of the EPICA input file for the climate outside the given datatime frame (time, delta_temp, prec_scali)",
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
        default=1.0,
        help="Temperature additon (e.g., 5 for 5 degrees warming)",
    )

def initialize(params, state):
    # load climate data from netcdf file atm.nc
    atm_nc = Dataset(
        os.path.join("./data/", params.pism_atm_file)
    )
    prcp = np.squeeze(atm_nc.variables["precipitation"]).astype("float32")  # unit : kg * m^(-2) * day^(-1)
    temp = np.squeeze(atm_nc.variables["air_temp"]).astype("float32")  # unit : degree celcius
    time_bounds = np.squeeze(atm_nc.variables["time_bounds"]).astype("int")  # unit : bounds for the precipitation and temperature data
    atm_nc.close()

    # Set year 0 of the climate data as based on input parameter
    params.yr_0 = params.year_0

    # Add the temperature data to the state
    state.temp = (temp + params.temperature_addition) * params.temperature_scaling

    # fix the units of precipitation, IGM expects kg * m^(-2) * y^(-1) instead of kg * m^(-2) * day^(-1)
    state.prec = prcp * time_bounds.max() * params.precipitation_scaling

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

    # load the EPICA signal from the dT_epica.nc file
    epica_nc = Dataset(
        os.path.join("./data/", params.dt_epica_file)
    )
    # extract time BP, change to AD (1950 is present for EPICA)
    time = np.squeeze(epica_nc.variables["time"]).astype("int")  # unit : years
    time = time - params.yr_0
    # extract the dT, i.e. global temp. difference
    dT = np.squeeze(epica_nc.variables["delta_T"]).astype("float32")  # unit : degree Kelvin
    epica_nc.close()

    # dT is a function of time, we need to interpolate it
    # to get the dT at the time of the simulation
    state.dT = lambda t: np.interp(t, time, dT, left=dT[0], right=dT[-1])


def update(params, state):
    if (state.t - state.tlast_clim_oggm) >= params.clim_pism_update_freq:
        if hasattr(state, "logger"):
            state.logger.info("update climate at time : " + str(state.t.numpy()))
        
        try:
            dT = state.dT(state.t.numpy())
        except ValueError:
            # break out of the loop if the dT is not available
            return

        state.tcomp_clim_oggm.append(time.time())

        # We do a dummy update of the precipitation
        state.precipitation = tf.convert_to_tensor(state.prec * 1.0, dtype="float32")

        # The shape of state.temp is (12,ny,nx), all that is needed is to add the dT to the temperature
        # and to create a tensor from the numpy array
        state.air_temp = tf.convert_to_tensor(state.temp + dT, dtype="float32")

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
