# Install pism in ~/local/pism, using ~/local/build/pism as a build directory.


build=~/local/build/pism
prefix=$HOME/local/pism
pism_prefix=~/local/pism
url=https://github.com/pism/pism.git 

# only clone if the build directory does not exist
if [ ! -d ${build} ]; then
      git clone ${url} ${build}
fi
mkdir -p ${build}/build

pushd ${build}/build

export CC=mpicc
export CXX=mpicxx
cmake -DCMAKE_FIND_ROOT_PATH="~/local/hdf5/;~/local/netcdf;~/local/pnetcdf;~/local/parallelio;~/local/petsc" \
      -DCMAKE_INSTALL_PREFIX=~/local/pism\
      -DPism_USE_PNETCDF=ON \
      -DPism_USE_PARALLEL_NETCDF4=ON \
      -DPism_USE_PIO=ON \
      ..
make install

popd