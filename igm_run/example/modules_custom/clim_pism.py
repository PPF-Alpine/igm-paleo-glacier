#!/usr/bin/env python3

# Copyright (C) 2021-2023 Guillaume Jouvet <guillaume.jouvet@unil.ch>
# Published under the GNU GPL (Version 3), check at the LICENSE file

import numpy as np
import os
import tensorflow as tf
import time
from netCDF4 import Dataset
from igm.modules.utils import interp1d_tf
from scipy.interpolate import interp1d


def params(parser):
    # CLIMATE PARAMETERS
    parser.add_argument(
        "--clim_pism_update_freq",
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
        "--year_0",
        default=1950,
        type=int,
        help="Year 0 of the climate data",
    )
    

def initialize(params, state):
    # load climate data from netcdf file climate_historical.nc
    nc = Dataset(
        os.path.join("./data/", params.pism_atm_file)
    )

    prcp = np.squeeze(nc.variables["precipitation"]).astype("float32")  # unit : kg * m^(-2)
    temp = np.squeeze(nc.variables["air_temp"]).astype("float32")  # unit : degree celcius
    time_bounds = np.squeeze(nc.variables["time_bounds"]).astype("int")  # unit : bounds for the precipitation and temperature data
    nc.close()

    # Set year 0 of the climate data as based on input parameter
    params.yr_0 = params.year_0

    # Add the temperature data to the state
    state.temp = temp

    # fix the units of precipitation, IGM expects kg * m^(-2) * y^(-1) instead of kg * m^(-2) * day^(-1)
    state.prec = prcp * time_bounds.max()

    # number of months
    nb_m = 12
    # intitalize air_temp and precipitation fields
    state.air_temp = tf.Variable(
        tf.zeros((nb_m, state.y.shape[0], state.x.shape[0])),
        dtype="float32", trainable=False
    )
    state.precipitation = tf.Variable(
        tf.zeros((nb_m, state.y.shape[0], state.x.shape[0])),
        dtype="float32", trainable=False
    )

    state.tlast_clim_oggm = tf.Variable(-(10**10), dtype="float32", trainable=False)
    state.tcomp_clim_oggm = []

    # load the EPICA signal from theparams,state official data
    ss = np.loadtxt('data/EDC_dD_temp_estim.tab',dtype=np.float32,skiprows=31)
    # extract time BP, change to AD (1950 is present for EPICA)
    time = ss[:,1] * -1000 + params.year_0
    # extract the dT, i.e. global temp. difference
    dT   = ss[:,3]          
    state.dT =  interp1d(time,dT, fill_value=(dT[0], dT[-1]), bounds_error=True)


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
