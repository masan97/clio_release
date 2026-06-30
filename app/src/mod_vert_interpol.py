#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 13:24:17 2026

@author: sandorma
"""

import numpy as np
import xarray as xr
from numpy import genfromtxt
import scipy.interpolate as intp
import sys


def read_hybrid_coeffs(lev_ifs,ml_input,separator,workdir):
    
    if lev_ifs==91:
        textfile_ifs=f"{workdir}/aux/L91_model_levels.txt"
    elif lev_ifs==137:
        textfile_ifs=f"{workdir}/aux/L137_model_levels.txt"
        
    L_ifs=np.loadtxt(textfile_ifs,skiprows=2)
    L_ifs = np.round(L_ifs, decimals=6)
    
    A_ifs = L_ifs[:,1]
    B_ifs = L_ifs[:,2]
    
    L_input = genfromtxt(ml_input, delimiter=separator, skip_header=2)

    A_input = L_input[:,1]
    B_input = L_input[:,2]
    
    return A_input, B_input, A_ifs, B_ifs


    
def ml2ml_vert_interpol(lev_ifs,ml_input,separator,workdir,ds_to_interpol,ds_ps):
    
    """ ds_ps : surface pressure input in (lat|lon)
        ds_to_interpol : the data to be interpolated; should have data format in (lev|lat|lon)
                         lev is assumed to be bottom-to-top, dimension names are assumed as
                                                             lev,lat,lon 
                                                 
        ml_input is the hybrid coeff input for the CMIP6 input, for MPI-ESM L95 there is a data file in aux/
        lev_ifs : number of ifs model levels
        separator : delimiter of the data entries of ml_input"""
    
    A_input, B_input, A_ifs, B_ifs = read_hybrid_coeffs(lev_ifs,ml_input,separator,workdir)
    
    
    
    #check A,B coeffs
    
    error_log=[]
    
    if A_input[0] > A_input[2]:
        err="Wrong hybrid A coefficients of your input, "
        error_log.append(err)
    
    if B_input[0] > B_input[-1]:
        err="Wrong hybrid B coefficients of your input, "
        error_log.append(err)
        
    if error_log:
        for err in error_log:
            print(err)
        sys.exit(1)
    
    
    data = ds_to_interpol.values      # (lev, lat, lon)
    ps   = ds_ps.values               # (lat, lon)

    nlev_out = lev_ifs 
    nlev_in, nlat, nlon = data.shape
    
    # reshape to 2D gridpoints
    data2 = data.reshape(nlev_in, -1) #flattten the array
    ps2   = ps.ravel() #flatten the array

    out = np.zeros((nlev_out, data2.shape[1]), dtype=data.dtype)
    
    for p in range(data2.shape[1]):

        sel_dat = data2[::-1, p] # flip vertical
        sel_ps  = ps2[p]

        pk_input = A_input + sel_ps * B_input
        pk_ifs   = A_ifs   + sel_ps * B_ifs

        out[:, p] = np.interp(pk_ifs, pk_input, sel_dat)

    out = out.reshape(nlev_out, nlat, nlon)
    #out = out[::-1, :, :]
    
    
    lev_name=[]
    for possible_lev in ['lev', 'plev','level']:
        if possible_lev in ds_to_interpol.coords:
            lev_name = possible_lev
            break
    
    lev_IDs = np.arange(1,len(A_ifs)+1)
    coords = dict(ds_to_interpol.coords)
    coords[lev_name] = lev_IDs

       
    da_out = xr.DataArray(
        out,
        coords=coords,
        dims=ds_to_interpol.dims,
        name=ds_to_interpol.name,
        attrs=ds_to_interpol.attrs,
    )
    

    da_out=da_out.rename({lev_name: "hybrid"})
    da_out=da_out.assign_coords(
        hybrid=("hybrid", lev_IDs, {
            "long_name": "hybrid model level",
            "units": "1",
            "positive": "down",
            "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate"
        })
    )
    
    ds_out = da_out.to_dataset()
    
    for v in ds_out.variables:
        if "coordinates" in ds_out[v].attrs:
            ds_out[v].attrs["coordinates"] = ds_out[v].attrs["coordinates"].replace("level", "hybrid")

    return ds_out


def read_IFS_hybrid_coeffs(lev_ifs,workdir):
    
    if lev_ifs==91:
        textfile_ifs=f"{workdir}/aux/L91_model_levels.txt"
    elif lev_ifs==137:
        textfile_ifs=f"{workdir}/aux/L137_model_levels.txt"
        
    L_ifs=np.loadtxt(textfile_ifs,skiprows=1)
    L_ifs = np.round(L_ifs, decimals=6)
    
    A_ifs = L_ifs[:,1]
    B_ifs = L_ifs[:,2]
    
    
    return A_ifs, B_ifs




def pl2ml_vert_interpol(lev_ifs,workdir,ds_to_interpol,ds_ps,varname):
    
    """ ds_ps : surface pressure (Pa) input in (lat|lon)
        ds_to_interpol : the data to be interpolated; should have data format in (lev|lat|lon)
                         lev is assumed to be bottom-to-top, in Pa, dimension names are assumed as
                                                             lev,lat,lon 
                                                 
        lev_ifs : number of ifs model levels"""
    
    A_ifs, B_ifs = read_IFS_hybrid_coeffs(lev_ifs,workdir)
    
    lat_name = None
    
    for possible_lat in ['latitude', 'lat', 'y']:
        if possible_lat in ds_to_interpol.coords:
            lat_name = possible_lat
            break
    
    lon_name = None
    
    for possible_lon in ['longitude', 'lon', 'x']:
        if possible_lon in ds_to_interpol.coords:
            lon_name = possible_lon
            break
    
    lev_name = None
    for possible_lev in ['lev', 'plev','level']:
        if possible_lev in ds_to_interpol.coords:
            lev_name = possible_lev
            break
    
    if lat_name is None or lon_name is None:
        raise ValueError("pl2ml_vert_interpol: Could not find valid latitude or longitude coordinates in DataArray.")
    
    nlats=len(ds_to_interpol[lat_name].values)
    nlons=len(ds_to_interpol[lon_name].values)
    
    lats=ds_to_interpol[lat_name]
    lons=ds_to_interpol[lon_name]
    
    ps = ds_ps.values               # (lat, lon)
    
    p_half = np.zeros((lev_ifs+1, nlats, nlons))
    #check = sp
    for k in range(lev_ifs+1):
        p_half[k,:,:] = (A_ifs[k] + B_ifs[k]*ps)/100 # (ps in Pa -> divide by 100 to get hPa)
    
    # Calculate pressure on model levels: p_model = ( p_half_above + p_half below )/2
    p_ml = (p_half[:-1,:,:] + p_half[1:,:,:])/2
    
    lev_IDs = np.arange(1,len(A_ifs))
    
    p_ml=xr.DataArray(p_ml,  dims=("model_level", "lat", "lon"), coords={"model_level": lev_IDs, "lat": lats, "lon": lons})
    
    def vertical_interp_1d(plev, temp_profile, p_target):
        f = intp.interp1d(plev, temp_profile, kind='linear', bounds_error=False, fill_value="extrapolate")
        return f(p_target)

    #ds_to_interpol levels in Pa, therefore: ds_to_interpol[lev_name]/100
    field_interp = xr.apply_ufunc(
        vertical_interp_1d,
        ds_to_interpol[lev_name]/100,
        ds_to_interpol,
        p_ml,
        input_core_dims=[[lev_name], [lev_name], ['model_level']],
        output_core_dims=[['hybrid']],
        vectorize=True,
        output_dtypes=[float],
    )
    
    field_interp = field_interp.transpose("hybrid", lat_name, lon_name)
    
    # convert to numpy for reconstruction
    out = field_interp.values

    

    # copy coordinates like ml2ml
    coords = dict(ds_to_interpol.coords)
    coords[lev_name] = lev_IDs

    da_out = xr.DataArray(
        out,
        coords=coords,
        dims=ds_to_interpol.dims,
        name=ds_to_interpol.name,
        attrs=ds_to_interpol.attrs,)

    # rename level coordinate to hybrid
    da_out = da_out.rename({lev_name: "hybrid"})

    da_out = da_out.assign_coords(
        hybrid=("hybrid", lev_IDs, {
            "long_name": "hybrid model level",
            "units": "1",
            "positive": "down",
            "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate"})
        )

    ds_out = da_out.to_dataset()

    # fix coordinate attribute references
    for v in ds_out.variables:
        if "coordinates" in ds_out[v].attrs:
            ds_out[v].attrs["coordinates"] = ds_out[v].attrs["coordinates"].replace("level", "hybrid")

    return ds_out
    
    