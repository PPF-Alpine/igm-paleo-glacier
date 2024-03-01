#!/bin/sh

# This has failed so far on saga.

# it is good to have the following lines in any bash script
set -o errexit  # make bash exit on any error
set -o nounset  # treat unset variables as errors

module reset
module load CUDA/11.7.0
module load OpenMPI/4.1.4-NVHPC-22.7-CUDA-11.7.0
module load OpenBLAS/0.3.20-NVHPC-22.7-CUDA-11.7.0
module load Python/3.10.4-GCCcore-11.3.0

version=3.20.4

url=https://web.cels.anl.gov/projects/petsc/download/release-snapshots/petsc-${version}.tar.gz

petsc_prefix=$HOME/local-cuda/petsc
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
  --with-x=0 \
  --with-cuda \
  --with-cuda-dir=/cluster/software/CUDA/11.7.0/

make all
make install
make PETSC_DIR=${petsc_prefix} PETSC_ARCH="" check

popd
popd