#!/bin/bash

#SBATCH --account=nn11012k
#SBATCH --job-name=pism-test
#SBATCH --partition=devel
#SBATCH --mem=2G
#SBATCH --ntasks=2
#SBATCH --time=00:02:00

# it is good to have the following lines in any bash script
set -o errexit  # make bash exit on any error
set -o nounset  # treat unset variables as errors

module restore
module load PETSc/3.19.2-foss-2022b-ind64
module load UDUNITS/2.2.28-GCCcore-12.2.0
module load GSL/2.7-GCC-12.2.0

# Run the PISM test
pismv -test G -y 200