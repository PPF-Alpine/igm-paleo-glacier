#!/usr/bin/env python3

# Copyright (C) 2021-2023 Guillaume Jouvet <guillaume.jouvet@unil.ch>
# Published under the GNU GPL (Version 3), check at the LICENSE file
# Modified for use with PISM input data by Abe Wiersma

import numpy as np
import matplotlib.pyplot as plt
import datetime, time, os
import math
import tensorflow as tf
import json


def params(parser):
    parser.add_argument(
        "--smb_oggm_update_freq",
        type=float,
        default=1,
        help="Update the mass balance each X years ",
    )
    parser.add_argument(
        "--smb_oggm_ice_density",
        type=float,
        default=910.0,
        help="Density of ice for conversion of SMB into ice equivalent",
    )
    parser.add_argument(
        "--smb_oggm_wat_density",
        type=float,
        default=1000.0,
        help="Density of water",
    )

    # Default global parameters
    parser.add_argument(
        "--temp_default_gradient",
        type=float,
        default=-0.0065,
        help="Default temperature gradient (based on Schuster et al., 2023), unit: K/km",
    )
    parser.add_argument(
        "--temp_all_solid",
        type=float,
        default=0.0,
        help="Temperature threshold for solid precipitation, unit: celcius",
    )
    parser.add_argument(
        "--temp_all_liq",
        type=float,
        default=2.0,
        help="Temperature threshold for liquid precipitation, unit: celcius",
    )
    parser.add_argument(
        "--temp_melt",
        type=float,
        default=-1.0,
        help="Temperature threshold for melt, unit: celcius",
    )

    # Location specific parameters
    parser.add_argument(
        "--melt_f",
        type=float,
        default=1.0,
        help="Melt factor, unit: mm water / (celcius day)",
    )


def initialize(params, state):
    state.tcomp_smb_oggm = []
    state.tlast_mb = tf.Variable(-1.0e5000)

    params.thr_temp_snow = params.temp_all_solid
    params.thr_temp_rain = params.temp_all_liq


def update(params, state):
    #    mass balance forced by climate with accumulation and temperature-index melt model
    #    Input:  state.precipitation [Unit: kg * m^(-2) * y^(-1)]
    #            state.air_temp      [Unit: °C           ]
    #    Output  state.smb           [Unit: m ice eq. / y]

    #   This mass balance routine implements the surface mass balance model of OGGM

    # update smb each X years
    if (state.t - state.tlast_mb) >= params.smb_oggm_update_freq:
        if hasattr(state, "logger"):
            state.logger.info(
                "Construct mass balance at time : " + str(state.t.numpy())
            )

        state.tcomp_smb_oggm.append(time.time())

        # keep solid precipitation when temperature < thr_temp_snow
        # with linear transition to 0 between thr_temp_snow and thr_temp_rain
        accumulation = tf.where(
            state.air_temp <= params.thr_temp_snow,
            state.precipitation,
            tf.where(
                state.air_temp >= params.thr_temp_rain,
                0.0,
                state.precipitation
                * (params.thr_temp_rain - state.air_temp)
                / (params.thr_temp_rain - params.thr_temp_snow),
            ),
        )
        accumulation /= accumulation.shape[
            0
        ]  # unit to [ kg * m^(-2) * y^(-1) ] -> [ kg * m^(-2) water ]

        accumulation /= params.smb_oggm_wat_density  # unit [ m water ]

        ablation = params.melt_f * tf.clip_by_value(
            state.air_temp - params.temp_melt, 0, 10**10
        )  # unit: [ mm * day^(-1) water ]

        ablation *= 365.242198781 / 1000.0  # unit to [ m * y^(-1) water ]

        ablation /= ablation.shape[0]  # unit to [ m  water ]

        # sum accumulation and ablation over the year, and conversion to ice equivalent
        state.smb = tf.math.reduce_sum(accumulation - ablation, axis=0) * (
            params.smb_oggm_wat_density / params.smb_oggm_ice_density
        )

        if hasattr(state, "icemask"):
            state.smb = tf.where(
                (state.smb < 0) | (state.icemask > 0.5), state.smb, -10
            )

        state.tlast_mb.assign(state.t)

        state.tcomp_smb_oggm[-1] -= time.time()
        state.tcomp_smb_oggm[-1] *= -1


def finalize(params, state):
    pass
