#!/usr/bin/env python3

# Copyright (C) 2021-2023 Guillaume Jouvet <guillaume.jouvet@unil.ch>
# Published under the GNU GPL (Version 3), check at the LICENSE file
# Modified for use with paleo climate input data and lapse rate data, sjurbarndon@proton.me

import numpy as np
import matplotlib.pyplot as plt
import datetime, time, os
import math
import tensorflow as tf
import json


def params(parser):
        
    # Default global parameters
    parser.add_argument(
        "--smb_paleo_update_freq",
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
    parser.add_argument(
        "--smb_temp_solid_precipitation",
        type=float,
        default=0.0,
        help="Temperature threshold for solid precipitation, unit: celcius",
    )
    parser.add_argument(
        "--smb_temp_liquid_precipitation",
        type=float,
        default=2.0,
        help="Temperature threshold for liquid precipitation, unit: celcius",
    )

    # Temperature gradient or melt factor argument:
    parser.add_argument(
        "--temp_default_gradient",
        type=float,
        default=-0.0065,
        help="Default temperature gradient or lapse rate (based on Schuster et al., 2023), unit: K/km",
    )

    # Melt factors for snow and ice
    parser.add_argument(
        "--smb_accpdd_melt_factor_snow",
        type=float,
        default=0.003 * 365.242198781,
        help="Degree-day factor for snow (water eq.) (unit: meter / (Kelvin year))",
    )
    parser.add_argument(
        "--smb_accpdd_melt_factor_ice",
        type=float,
        default=0.008 * 365.242198781,
        help="Degree-day factor for ice (water eq.) (unit: meter / (Kelvin year))",
    )
    parser.add_argument(
        "--smb_accpdd_shift_hydro_year",
        type=float,
        default=0.75,
        help="This serves to start Oct 1. the acc/melt computation (0.75)",
    )
    parser.add_argument(
        "--smb_accpdd_refreeze_factor",
        type=float,
        default=0.6,
        help="Refreezing factor",
    )

def initialize(params, state):
    state.tcomp_smb_paleo = []
    state.tlast_mb = tf.Variable(-1.0e5000)

    params.thr_temp_snow = params.smb_temp_solid_precipitation
    params.thr_temp_rain = params.smb_temp_liquid_precipitation


def update(params, state):
    #    mass balance forced by climate with accumulation and temperature-index melt model
    #    Input:  state.precipitation [Unit: kg * m^(-2) * y^(-1)]
    #            state.air_temp      [Unit: °C           ]
    #    Output  state.smb           [Unit: m ice eq. / y]

    #   This mass balance routine implements the surface mass balance model of OGGM

    # update smb each X years
    if (state.t - state.tlast_mb) >= params.smb_paleo_update_freq:
        if hasattr(state, "logger"):
            state.logger.info(
                "Construct mass balance at time : " + str(state.t.numpy())
            )

        state.tcomp_smb_paleo.append(time.time())
        
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
        # Find the positive degree day air temperatures. Sets all temps to the positive value or zero
        pos_temp_year = tf.where(state.air_temp > 0.0, state.air_temp, 0.0)
        pos_temp_year /= pos_temp_year.shape[0] # This sets unit from [ °C ] to [ °C y]

        accumulation /= accumulation.shape[0]  # unit to [ kg * m^(-2) * y^(-1) ] -> [ kg * m^(-2) water ]
        accumulation /= params.smb_oggm_wat_density  # unit [ m water ]

        # ablation = params.melt_f * tf.clip_by_value(
        #     state.air_temp - params.temp_melt, 0, 10**10
        # )  # unit: [ mm * day^(-1) water ]
        #
        # ablation *= 365.242198781 / 1000.0  # unit to [ m * y^(-1) water ]
        #
        # ablation /= ablation.shape[0]  # unit to [ m  water ]

        ablation = []
        snow_depth = tf.zeros((state.air_temp.shape[1], state.air_temp.shape[2]))

        for kk in range(state.air_temp.shape[0]):
            # shift to hydro year, i.e. start Oct. 1
            k = (
                kk + int(state.air_temp.shape[0] * params.smb_accpdd_shift_hydro_year)
            ) % (state.air_temp.shape[0])

            # add accumulation to the snow depth
            snow_depth += accumulation[k]

            # the ablation (unit is m water eq.) is the product of positive temp  with melt
            # factors for ice, or snow, or a fraction of the two if all snow has melted
            ablation.append(
                tf.where(
                    snow_depth == 0,
                    pos_temp_year[k] * params.smb_accpdd_melt_factor_ice,
                    tf.where(
                        pos_temp_year[k] * params.smb_accpdd_melt_factor_snow
                        < snow_depth,
                        pos_temp_year[k] * params.smb_accpdd_melt_factor_snow,
                        snow_depth + ( pos_temp_year[k] - snow_depth 
                        / params.smb_accpdd_melt_factor_snow) * params.smb_accpdd_melt_factor_ice,
                    ),
                )
            )

            # remove snow melt to snow depth, and cap it as snow_depth can not be negative
            snow_depth = tf.clip_by_value(snow_depth - ablation[-1], 0.0, 1.0e10)



        ablation = (1 - params.smb_accpdd_refreeze_factor) * tf.stack(ablation, axis=0)

        # sum accumulation and ablation over the year, and conversion to ice equivalent
        state.smb = tf.math.reduce_sum(accumulation - ablation, axis=0) * (
            params.smb_oggm_wat_density / params.smb_oggm_ice_density
        )

        if hasattr(state, "icemask"):
            state.smb = tf.where(
                (state.smb < 0) | (state.icemask > 0.5), state.smb, -10
            )

        state.tlast_mb.assign(state.t)

        state.tcomp_smb_paleo[-1] -= time.time()
        state.tcomp_smb_paleo[-1] *= -1


def finalize(params, state):
    pass
