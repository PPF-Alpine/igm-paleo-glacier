# Install NCAR ParallelIO in ~/local/parallelio
# using parallel NetCDF and PnetCDF installed in ~/local/netcdf
# and ~/local/pnetcdf. Uses ~/local/build/parallelio
# as a build directory.

netcdf_prefix=~/local/netcdf
pnetcdf_prefix=~/local/pnetcdf

version=2_6_2
prefix=$HOME/local/parallelio
build_dir=~/local/build/parallelio
url=https://github.com/NCAR/ParallelIO/archive/refs/tags/pio${version}.tar.gz

mkdir -p ${build_dir}
pushd ${build_dir}

wget -nc ${url}
tar zxf pio${version}.tar.gz -C ${build_dir} --strip-components 1

CC=mpicc cmake \
  -DCMAKE_C_FLAGS="-fPIC" \
  -DCMAKE_INSTALL_PREFIX=${prefix} \
  -DNetCDF_PATH=${netcdf_prefix} \
  -DPnetCDF_PATH=${pnetcdf_prefix} \
  -DPIO_ENABLE_FORTRAN=0 \
  -DPIO_ENABLE_TIMING=0 \
  .

make install

popd
