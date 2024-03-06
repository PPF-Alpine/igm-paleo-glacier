#!/bin/sh
#
#SBATCH --account=nn11012k
#SBATCH --time=00:10:00
#SBATCH --job-name=pism-test
#SBATCH --qos=devel
#SBATCH --mem-per-cpu=4G
#SBATCH --ntasks=2
#SBATCH --output=log.caucasus.txt
#SBATCH --error=err.caucasus.txt

# it is good to have the following lines in any bash script
set -o errexit  # make bash exit on any error
set -o nounset  # treat unset variables as errors

module restore
module load PETSc/3.19.2-foss-2022b-ind64
module load UDUNITS/2.2.28-GCCcore-12.2.0
module load GSL/2.7-GCC-12.2.0

# start and end
ys=-120000
ye=-119999

# run PISM
srun $HOME/local/pism/bin/pismr \
    -i boot.nc -bootstrap \
        -Mz 51 -Lz 5000 -Mbz 31 -Lbz 3000 \
        -ys $ys -ye $ye -o out.caucasus.nc \
    -atmosphere given,elevation_change,delta_T \
        -atmosphere.given.periodic \
        -atmosphere_delta_T_file $HOME/caucasus/dT_epica.nc \
        -atmosphere_given_file $HOME/caucasus/atm.nc \
        -atmosphere_lapse_rate_file $HOME/caucasus/atm.nc \
        -temp_lapse_rate 6.0 \
        -timestep_hit_multiples 1 \
    -surface pdd \
        -surface.pdd.std_dev.periodic \
    -config_override $HOME/caucasus/config.nc \
    -ts_file ts.caucasus.nc -ts_times 1 \
    -extra_file ex.caucasus.nc -extra_times 100 \
    -extra_vars lat,lon,rank,bmelt,climatic_mass_balance,diffusivity,hardav,\
mask,pdd_fluxes,tauc,tempicethk_basal,temppabase,tempsurf,thk,tillwat,topg,\
usurf,velbase,velsurf

# unimplemented yet
#     -atmosphere given,elevation_change,delta_T \
#         -pdd_sd_file alpcyc.1km.in.new.nc \
#         -pdd_sd_file $SD_FILE \