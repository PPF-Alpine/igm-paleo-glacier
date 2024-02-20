# Install Petsc 3.20.4 in ~/local/petsc,
# using ~/local/build/petsc as a build directory.

version=3.20.4

url=https://web.cels.anl.gov/projects/petsc/download/release-snapshots/petsc-${version}.tar.gz

petsc_prefix=$HOME/local/petsc
PETSC_DIR=$HOME/local/petsc
PETSC_ARCH="linux-opt"
build_dir=~/local/build/petsc/

mkdir -p ${build_dir}
pushd ${build_dir}

wget -nc ${url}
tar xzf petsc-${version}.tar.gz

pushd petsc-${version}

./configure \
  COPTFLAGS="-g -O3" \
  --prefix=${petsc_prefix} \
  --with-cc=mpicc \
  --with-cxx=mpicxx \
  --with-fc=mpifort \
  --with-shared-libraries \
  --with-debugging=0 \
  --with-petsc4py \
  --with-x=0 \
  --download-f2cblaslapack

export PYTHONPATH=${petsc_prefix}/lib
make all
make install
make PETSC_DIR=${petsc_prefix} PETSC_ARCH="" check

popd
popd