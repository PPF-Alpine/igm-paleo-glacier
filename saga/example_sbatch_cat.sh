#!/bin/bash

#SBATCH --account=nn11012k
#SBATCH --job-name=test-sbatch-echo
#SBATCH --qos=devel
#SBATCH --ntasks=1
#SBATCH --mem=1G
#SBATCH --time=00:00:10
#SBATCH --output=log.echo.txt
#SBATCH --error=err.echo.txt

# it is good to have the following lines in any bash script
set -o errexit  # make bash exit on any error
set -o nounset  # treat unset variables as errors

module restore

echo "Working" > ~/sbatch_test.txt