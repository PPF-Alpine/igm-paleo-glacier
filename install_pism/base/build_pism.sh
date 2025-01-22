# Install pism in ~/local/pism, using ~/local/build/pism as a build directory.

set -o errexit  # make bash exit on any error
set -o nounset  # treat unset variables as errors

version=2.1
build_dir=~/local/build/pism
prefix=$HOME/local/pism
url=https://github.com/pism/pism/archive/refs/tags/v${version}.tar.gz
mkdir -p ${build_dir}

wget -nc ${url}
tar xzf v${version}.tar.gz -C ${build_dir} --strip-components 1

pushd ${build_dir}
rm -rf ${build_dir}/build
mkdir -p ${build_dir}/build
pushd ${build_dir}/build

export CC=mpicc
export CXX=mpicxx
cmake -DCMAKE_FIND_ROOT_PATH="~/local/hdf5/;~/local/netcdf;~/local/pnetcdf;~/local/parallelio;" \
      -DCMAKE_INSTALL_PREFIX="${prefix}"\
      -DPism_USE_PNETCDF=ON \
      -DPism_USE_PARALLEL_NETCDF4=ON \
      -DPism_USE_PIO=ON \
      ..
make install

popd