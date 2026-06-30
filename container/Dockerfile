# FROM ubuntu:focal
FROM python:3.12-bookworm

# For installation
ARG HDF5_VERSION="1.14.6"
ARG NETCDF_C_VERSION="4.9.3"
ARG NETCDF_FORTRAN_VERSION="4.6.2"
ARG ECCODES_VERSION="2.41.0"
ARG CDO_VERSION="2.4.3"
ARG METVIEW_VERSION="2024.4.0"

ARG HDF5_DIR=/usr/local/hdf5
ARG NETCDF_C_DIR=/usr/local/netcdf-c
ARG NETCDF_FORTRAN_DIR=/usr/local/netcdf-fortran
ARG ECCODES_DIR=/usr/local/eccodes
ARG CDO_DIR=/usr/local/cdo
ARG METVIEW_DIR=/usr/local/metview

# For runtimes
ENV LD_LIBRARY_PATH=${HDF5_DIR}/lib
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${NETCDF_C_DIR}/lib
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${NETCDF_FORTRAN_DIR}/lib
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${ECCODES_DIR}/lib
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${CDO_DIR}/lib
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${METVIEW_DIR}/lib

# For metview
ENV RPC_PATH=/lib/x86_64-linux-gnu/

# Copy the tar ball and custom files
COPY To_containerise/. /tmp

# Base libraries
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install tzdata && apt-get -yq install \
    build-essential \
    tar nano \
    bzip2 \
    m4 \
    cmake libaec-dev \
    zlib1g-dev \
    gfortran \
    zlib1g-dev \
    libhdf5-serial-dev \
    hdf5-tools \
    libxml2-dev libcurl4-openssl-dev \
    python3-dev libproj-dev \
    gsl-bin libgsl-dev \
    antlr libantlr-dev libtirpc-dev libntirpc-dev \
    bison flex gcc-11 g++-11 libcairo2-dev libpango1.0-dev \
    rpcsvc-proto \
    udunits-bin libudunits2-0 libudunits2-dev

# Build HDF5
RUN cd /tmp && \
    tar xzvf hdf5-${HDF5_VERSION}.tar.gz && \
    cd hdf5-${HDF5_VERSION} && \
    ./configure --enable-fortran --prefix=${HDF5_DIR} && \
    make -j4 && make install && \
    for f in ${HDF5_DIR}/bin/* ; do ln -s $f /usr/local/bin ; done

# Build netcdf-c
RUN cd /tmp && \
    tar xzvf netcdf-c-${NETCDF_C_VERSION}.tar.gz && \
    cd netcdf-c-${NETCDF_C_VERSION} && \
    export LDFLAGS=-L${HDF5_DIR}/lib CPPFLAGS=-I${HDF5_DIR}/include && \
    ./configure --prefix=${NETCDF_C_DIR} --with-hdf5=${HDF5_DIR} && \
    make -j4 && make install && \
    for f in ${NETCDF_C_DIR}/bin/* ; do ln -s $f /usr/local/bin ; done

# Build netcdf-fortran
RUN cd /tmp && \
    tar xzvf netcdf-fortran-${NETCDF_FORTRAN_VERSION}.tar.gz && \
    cd netcdf-fortran-${NETCDF_FORTRAN_VERSION} && \
    export LDFLAGS=-L${NETCDF_C_DIR}/lib CPPFLAGS=-I${NETCDF_C_DIR}/include && \
    ./configure --prefix=${NETCDF_FORTRAN_DIR} && \
    make -j4 && make install && \
    for f in ${NETCDF_FORTRAN_DIR}/bin/* ; do ln -s $f /usr/local/bin ; done

# Build eccodes
RUN cd /tmp && \
    tar zxvf eccodes-${ECCODES_VERSION}-Source.tar.gz && \
    cd eccodes-${ECCODES_VERSION}-Source  && \
    mkdir build && cd build  && \
    cmake -DCMAKE_INSTALL_PREFIX=${ECCODES_DIR} .. && \
    make -j4 && make install && \
    for f in ${ECCODES_DIR}/bin/* ; do ln -s $f /usr/local/bin ; done

# Build CDO
RUN cd /tmp && \
    tar zxvf cdo-${CDO_VERSION}.tar.gz && \
    cd cdo-${CDO_VERSION} && \
    export CXXFLAGS=-std=c++20 CFLAGS=-std=gnu++20 && \
    ./configure --with-eccodes=${ECCODES_DIR} --with-netcdf=${NETCDF_C_DIR} \
                --with-hdf5=${HDF5_DIR} --enable-netcdf4 --enable-hdf5 \
                --prefix=${CDO_DIR} && \
    make -j4 && make install && \
    for f in ${CDO_DIR}/bin/* ; do ln -s $f /usr/local/bin ; done

# Build metview
RUN cd /tmp && \
    tar zxvf MetviewBundle-${METVIEW_VERSION}-Source.tar.gz && \
    cd MetviewBundle-${METVIEW_VERSION}-Source && \
    mkdir build && cd build && \
    export RPC_PATH=/lib/x86_64-linux-gnu/ && \
    cmake -DENABLE_UI=OFF -DCMAKE_BUILD_TYPE=Release \
          -DNETCDF_PATH=${NETCDF_C_DIR} -DCMAKE_INSTALL_PREFIX=${METVIEW_DIR} .. && \
    make -j4 && make install && \
    for f in ${METVIEW_DIR}/bin/* ; do ln -s $f /usr/local/bin ; done

# Build pip dependencies
RUN cd /tmp && \
    python3 -m pip install -r reqs-python.txt

# Refresh lib links and clean tmp
RUN /sbin/ldconfig
RUN rm -rf /tmp/*
