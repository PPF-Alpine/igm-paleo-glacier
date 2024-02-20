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
$(pwd)/build/build_petsc.sh

# install hdf5
$(pwd)/build/build_hdf5.sh

# install netcdf
$(pwd)/build/build_netcdf.sh

# install PnetCDF
$(pwd)/build/build_PnetCDF.sh

# install NCAR ParallelIO
$(pwd)/build/build_NCAR_ParallelIO.sh

# install pism
$(pwd)/build/build_pism.sh

# add petsc to the path
echo "export PETSC_DIR=$HOME/local/petsc" >> ~/.bashrc
# add pism to the path
echo "export PATH=$HOME/local/pism/bin:$PATH" >> ~/.bashrc
