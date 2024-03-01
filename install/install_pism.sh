#/bin/sh

# This shell script installs all requirements for pism.

set -e

# install dependencies for debian-based systems
sudo apt-get update
sudo apt-get install -y \
    cmake \
    g++ \
    git \
    libfftw3-dev \
    libgsl-dev \
    libudunits2-dev \
    cdo \
    libproj-dev \
    libx11-dev

# install petsc
$(pwd)/base/build_petsc.sh

# install hdf5
$(pwd)/shared/build_hdf5.sh

# install netcdf
$(pwd)/shared/build_netcdf.sh

# install PnetCDF
$(pwd)/shared/build_PnetCDF.sh

# install NCAR ParallelIO
$(pwd)/shared/build_NCAR_ParallelIO.sh

# install pism
$(pwd)/base/build_pism.sh

# add petsc to the path
echo "export PETSC_DIR=$HOME/local/petsc" >> ~/.bashrc
# add pism to the path
echo "export PATH=$HOME/local/pism/bin:$PATH" >> ~/.bashrc
