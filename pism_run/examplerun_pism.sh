#/bin/sh

mpirun -n 2 pismr -verbose 5\
    -i boot.nc -bootstrap \
        -Mz 31 -Lz 3000 -Mbz 31 -Lbz 3000 \
        -ys 0 -ye 10 \
    -o out.alps.1km.nc \
        -o_format pio_netcdf4p \
        -output.pio.n_writers 2 \
    -atmosphere given,elevation_change \
        -atmosphere.given.periodic \
        -atmosphere_given_file atm.nc \
        -atmosphere_lapse_rate_file atm.nc \
        -temp_lapse_rate 6.0 \
    -surface pdd \
        -surface.pdd.std_dev.periodic \
    -config_override config.nc \
    -ts_file ts.alps.1km.nc \
        -ts_times 0:yearly:1000 \
        -ts_vars ice_volume_glacierized,ice_area_glacierized_grounded \
    -extra_file ex.alps.1km.nc \
        -extra_times 0:yearly:1000 \
        -extra_vars lat,lon,rank,mask,thk,topg,usurf,velsurf,climatic_mass_balance
 
#   > log.alps.1km.txt 2> err.alps.1km.txt

# dry run to ignore sea ice rendering

# extra_vars excluded to save space
# pdd_fluxes,tempicethk_basal,temppabase,velbase,bmelt,hardav,diffusivity,
# tauc,tempsurf,tillwat \
