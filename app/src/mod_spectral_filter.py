#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 13:46:36 2025

@author: sandorma
"""

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import metview as mv


def read_Comp_SP_coeff_2d(workdir,inputfile,var):
    
    ''' for example for lnsp (DIM: sp coeff) '''
    
    ds = xr.open_dataset(workdir+inputfile)

    var_flat = ds[var].values  # shape (410240,)
    var_complex = var_flat.view(np.complex64)  # fast way if dtype is float32
    
    return var_complex


def read_Comp_SP_coeff_sp_mon(workdir,inputfile,var,mon):
    
    ''' for lnsp ERA5 mon means (DIM: sp coeff) '''
    
    ds = xr.open_dataset(workdir+inputfile)
    ds_sel = ds.where(ds.valid_time.dt.month == int(mon), drop=True)
    var_flat = ds_sel['sp'].isel(valid_time=0).values
    var_complex = var_flat.view(np.complex64)  # fast way if dtype is float32
    
    return var_complex



def read_Comp_SP_coeff_3d(workdir,inputfile,var):
    
    ''' for example for t (DIM: sp coeff x level) '''
    
    ds = xr.open_dataset(workdir+inputfile)

    var_flat = ds[var].values  # shape (410240,)
    
    #first dimension: level
    #second dimension: sp coeff
    
    real = var_flat[:, 0::2]  # take even columns
    imag = var_flat[:, 1::2]  # take odd columns

    var_complex = real + 1j * imag
    
    nlev = len(real[:,0])
    
    
    return var_complex, nlev



def spectral_taper(coeffs_nm, cutoff=300, alpha=1e-4):
    """
    Apply a high-wavenumber spectral taper to a(n,m) coefficient array.
    
    Parameters:
    coeffs_nm :
        Spherical harmonic coefficients (n,m) complex array
    cutoff : int
        Wavenumber above which to damp
    alpha : float
        Exponential taper factor,, 1e-4 as default
    """
    N = coeffs_nm.shape[0]-1
    filtered = coeffs_nm.copy()
    
    for n in range(N+1):
        for m in range(n+1):
            if m > cutoff:
                taper = np.exp(-alpha*(m - cutoff)**2)
                filtered[n,m] *= taper
                
    return filtered



def apply_high_n_taper_2d(inputfile,var,N,cutoff,compare_spectrum,workdir):
    """
    Use a high-wavenumber spectral taper to filter a spectral grib file (2D atm data, like lnsp ...).
    
    Parameters:
    inputfile :
        GRIB file containing the spherical harmonic coefficients
    var : str
        variable to extract
    N : int
        spectral truncation, i.e. 159,255,639,etc.
    
    cutoff : int 
        cut-off wavenumber, beyond this the taper is applied, has to be smaller than N
    
    compare_spectrum : logical
        compares the original spectrum with the tapared one and saves this plot to workdir
        
    workdir :
        working directory, where the software is
    
    """
    
    if cutoff>N:
        raise ValueError("cutoff ({cutoff}) has to be smaller than N ({N}).")
    
    
    var_cmplx=read_Comp_SP_coeff_2d(workdir,inputfile,var)
    
    
    coeffs_nm = np.zeros((N+1, N+1), dtype=complex)
    
    k = 0
    for n in range(N+1):
        for m in range(n+1):
            coeffs_nm[n, m] = var_cmplx[k]
            k += 1
        
    if compare_spectrum:
    
        E_m_orig = np.zeros(N+1)
        
        for m in range(N+1):
            E_m_orig[m] = np.sum([np.abs(coeffs_nm[n, m])**2 for n in range(m, N+1)])


    coeffs_nm_filtered = spectral_taper(coeffs_nm, cutoff)

    if compare_spectrum:

        E_m_filt = np.zeros(N+1)
    
        for m in range(N+1):
            E_m_filt[m] = np.sum([np.abs(coeffs_nm_filtered[n, m])**2 for n in range(m, N+1)])
    
    
        zw = np.arange(1,N+1)
    
        fig, ax = plt.subplots(1,1,figsize=(6, 5),constrained_layout=True)
        #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)


        ax.loglog(zw,E_m_orig[1:],linewidth=5,color='navy',label='orig')
        ax.loglog(zw,E_m_filt[1:],linewidth=2,color='red',label='filt')
        ax.set_xlabel('zonal wavenumber')
        ax.set_ylabel('spectral power')
        ax.set_title(f'{var}')
        omin=np.nanmin(E_m_orig[1:])
        fmin=np.nanmin(E_m_filt[1:])
        if omin<fmin:
            Amin=omin
        else:
            Amin=fmin
        omax=np.nanmax(E_m_orig[1:])
        fmax=np.nanmax(E_m_filt[1:])
        if omax>fmax:
            Amax=omax
        else:
            Amax=fmax
        # compute powers of 10 that enclose the range
        ymin = 10**np.floor(np.log10(Amin))
        ymax = 10**np.ceil(np.log10(Amax))

        ax.set_ylim([ymin,ymax])
        ax.set_aspect('auto')
        ax.grid(False)
        ax.legend()

        for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(1.2)
        
        plt.savefig(f"{workdir}plots/compare_{var}_filt_spectrum.png",dpi=600,bbox_inches='tight')
        plt.show()
        plt.close()
        
        
        print(f'-+-+-+---figure saved as compare_{var}_filt_spectrum.png-+-+-+---')
        
        
    
    var_cmplx_filtered = np.zeros_like(var_cmplx, dtype=complex)

    k = 0
    for n in range(N+1):
        for m in range(n+1):
            var_cmplx_filtered[k] = coeffs_nm_filtered[n, m]
            k += 1

    ncoeff = len(var_cmplx_filtered)

    var_filtered_flat = np.zeros((2*ncoeff), dtype=np.float32)
    
    var_filtered_flat[0::2] = var_cmplx_filtered.real.astype(np.float32)
    var_filtered_flat[1::2] = var_cmplx_filtered.imag.astype(np.float32)
    
    
    
    var_orig_grib = mv.read(workdir+inputfile)  # original modified lnsp GRIB
    var_filtered_grib = mv.set_values(var_orig_grib, var_filtered_flat)
    ofile=workdir+f"temp_{var}_filtered_SP.grib"
    mv.write(ofile, var_filtered_grib)


    print(f'Writing {ofile}  successful')
    
    return ofile
    
    



def apply_high_n_taper_3d(inputfile,var,N,cutoff,compare_spectrum,workdir):
    """
    Use a high-wavenumber spectral taper to filter a spectral grib file (3D atm data, like t, vor, div ...).
    
    Parameters:
    inputfile :
        GRIB file containing the spherical harmonic coefficients
    var : str
        variable to extract
    N : int
        spectral truncation, i.e. 159,255,639,etc.
    
    cutoff : int 
        cut-off wavenumber, beyond this the taper is applied, has to be smaller than N
    
    compare_spectrum : logical
        compares the original spectrum with the tapared one and saves this plot to workdir
        
    workdir :
        working directory, where the software is
    
    """
    
    if cutoff>N:
        raise ValueError("cutoff ({cutoff}) has to be smaller than N ({N}).")
    
    
    var_cmplx,nlev=read_Comp_SP_coeff_3d(workdir,inputfile,var)
    
    
    coeffs_nm = np.zeros((nlev,N+1, N+1), dtype=complex)
    
    
    for l in range(nlev):
        k = 0
        for n in range(N+1):
            for m in range(n+1):
                coeffs_nm[l, n, m] = var_cmplx[l,k]
                k += 1
        
    if compare_spectrum:
        
        sel_lev = 64 #around 500 hPa
    
        E_m_orig = np.zeros(N+1)
        
        for m in range(N+1):
            E_m_orig[m] = np.sum([np.abs(coeffs_nm[sel_lev,n, m])**2 for n in range(m, N+1)])

    coeffs_nm_filtered = np.copy(coeffs_nm)*0
    for l in range(nlev):
        coeffs_nm_filtered[l,:,:] = spectral_taper(coeffs_nm[l,:,:], cutoff)

    if compare_spectrum:

        E_m_filt = np.zeros(N+1)
    
        for m in range(N+1):
            E_m_filt[m] = np.sum([np.abs(coeffs_nm_filtered[sel_lev,n, m])**2 for n in range(m, N+1)])
    
    
        zw = np.arange(1,N+1)
    
        fig, ax = plt.subplots(1,1,figsize=(6, 5),constrained_layout=True)
        #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)


        ax.loglog(zw,E_m_orig[1:],color='navy',linewidth=6,label='orig')
        ax.loglog(zw,E_m_filt[1:],color='red',linewidth=2,label='filt')
        ax.set_xlabel('zonal wavenumber')
        ax.set_ylabel('spectral power')
        ax.set_title(f"{var}")
        omin=np.nanmin(E_m_orig[1:])
        fmin=np.nanmin(E_m_filt[1:])
        if omin<fmin:
            Amin=omin
        else:
            Amin=fmin
        omax=np.nanmax(E_m_orig[1:])
        fmax=np.nanmax(E_m_filt[1:])
        if omax>fmax:
            Amax=omax
        else:
            Amax=fmax
        # compute powers of 10 that enclose the range
        ymin = 10**np.floor(np.log10(Amin)+4)
        ymax = 10**np.ceil(np.log10(Amax))

        ax.set_ylim([ymin,ymax])
        ax.set_aspect('auto')
        ax.grid(False)

        for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(1.2)
        
        plt.savefig(f"{workdir}plots/compare_{var}_filt_spectrum.png",dpi=600,bbox_inches='tight')
        plt.legend()
        plt.show()
        plt.close()
        
        
        print(f'-+-+-+---figure saved as compare_{var}_filt_spectrum.png-+-+-+---')
        
        
        
    
    var_cmplx_filtered = np.zeros_like(var_cmplx, dtype=complex)

    for l in range(nlev):
        k = 0
        for n in range(N+1):
            for m in range(n+1):
                var_cmplx_filtered[l, k] = coeffs_nm_filtered[l, n, m]
                k += 1

    nlev, ncoeff = var_cmplx_filtered.shape

    var_filtered_flat = np.zeros((nlev, 2*ncoeff), dtype=np.float32)
    
    var_filtered_flat[:, 0::2] = var_cmplx_filtered.real.astype(np.float32)
    var_filtered_flat[:, 1::2] = var_cmplx_filtered.imag.astype(np.float32)


    var_orig_grib = mv.read(workdir+inputfile)  # original modified lnsp GRIB
    
    
    new_fields = []
    for lev in range(len(var_orig_grib)):
        grib_field = var_orig_grib[lev]                     # one GRIB message
        arr = var_filtered_flat[lev, :]          # 1D array for this level
        f = mv.set_values(grib_field, arr)       # replace values
        new_fields.append(f)
        
        
    # merge them back into one fieldset
    var_filtered_grib = mv.merge(new_fields)

    ofile = workdir+f"temp_{var}_filtered_SP.grib"
    mv.write(ofile, var_filtered_grib)
    


    print(f'Writing {ofile}  successful')
    
    return ofile
    
    

def apply_add_coeffs(inputfile,era5_lnsp,var,N,cutoff,compare_spectrum,workdir,mon):
    """
    Use a high-wavenumber spectral taper to filter a spectral grib file (2D atm data, like lnsp ...).
    
    Parameters:
    inputfile :
        GRIB file containing the spherical harmonic coefficients
    var : str
        variable to extract
    N : int
        spectral truncation, i.e. 159,255,639,etc.
    
    cutoff : int 
        cut-off wavenumber, beyond this the taper is applied, has to be smaller than N
    
    compare_spectrum : logical
        compares the original spectrum with the tapared one and saves this plot to workdir
        
    workdir :
        working directory, where the software is
    
    """
    
    if cutoff>N:
        raise ValueError("cutoff ({cutoff}) has to be smaller than N ({N}).")
    
    
    var_cmplx=read_Comp_SP_coeff_2d(workdir,inputfile,var)
    #var_cmplx_orig=read_Comp_SP_coeff_2d(IFS_path,origfile,var)
    
    var_cmplx_orig=read_Comp_SP_coeff_sp_mon(workdir,era5_lnsp,'sp',mon)
    
    coeffs_nm = np.zeros((N+1, N+1), dtype=complex)
    coeffs_nm_orig = np.zeros((N+1, N+1), dtype=complex)
    coeffs_nm_add = np.zeros((N+1, N+1), dtype=complex)
    
    k = 0
    for n in range(N+1):
        for m in range(n+1):
            coeffs_nm[n, m] = var_cmplx[k]
            coeffs_nm_orig[n, m] = var_cmplx_orig[k]
            k += 1
        
    if compare_spectrum:
    
        E_m_cmip = np.zeros(N+1)
        E_m_orig = np.zeros(N+1)
        
        for m in range(N+1):
            E_m_cmip[m] = np.sum([np.abs(coeffs_nm[n, m])**2 for n in range(m, N+1)])
            E_m_orig[m] = np.sum([np.abs(coeffs_nm_orig[n, m])**2 for n in range(m, N+1)])
    
    
    k = 0
    for n in range(N+1):
        for m in range(n+1):
            if m > cutoff:
                coeffs_nm_add[n, m] = var_cmplx_orig[k]
            else:
                coeffs_nm_add[n, m] = var_cmplx[k]
            k += 1



    if compare_spectrum:

        E_m_add = np.zeros(N+1)
    
        for m in range(N+1):
            E_m_add[m] = np.sum([np.abs(coeffs_nm_add[n, m])**2 for n in range(m, N+1)])
    
    
        zw = np.arange(1,N+1)
    
        fig, ax = plt.subplots(1,1,figsize=(6, 5),constrained_layout=True)
        #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)
        
        ax.loglog(zw,E_m_cmip[1:],linewidth=6,color='navy',label='cmip')
        ax.loglog(zw,E_m_orig[1:],linewidth=3,color='green',label='orig')
        ax.loglog(zw,E_m_add[1:],linewidth=1.5,color='red',label='add')
        ax.set_xlabel('zonal wavenumber')
        ax.set_ylabel('spectral power')
        ax.set_title(f'{var}')
        omin=np.nanmin(E_m_cmip[1:])
        fmin=np.nanmin(E_m_add[1:])
        if omin<fmin:
            Amin=omin
        else:
            Amin=fmin
        omax=np.nanmax(E_m_cmip[1:])
        fmax=np.nanmax(E_m_add[1:])
        if omax>fmax:
            Amax=omax
        else:
            Amax=fmax
        # compute powers of 10 that enclose the range
        ymin = 10**np.floor(np.log10(Amin))
        ymax = 10**np.ceil(np.log10(Amax))
        ymin=1e-8

        ax.set_ylim([ymin,ymax])
        ax.set_aspect('auto')
        ax.grid(False)
        ax.legend()

        for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(1.2)
        
        plt.savefig(f"{workdir}plots/compare_{var}_add_spectrum.png",dpi=600,bbox_inches='tight')
        plt.show()
        plt.close()
        
        
        print(f'-+-+-+---figure saved as compare_{var}_filt_spectrum.png-+-+-+---')
        
        
    
    var_cmplx_add = np.zeros_like(var_cmplx, dtype=complex)

    k = 0
    for n in range(N+1):
        for m in range(n+1):
            var_cmplx_add[k] = coeffs_nm_add[n, m]
            k += 1

    ncoeff = len(var_cmplx_add)

    var_add_flat = np.zeros((2*ncoeff), dtype=np.float32)
    
    var_add_flat[0::2] = var_cmplx_add.real.astype(np.float32)
    var_add_flat[1::2] = var_cmplx_add.imag.astype(np.float32)
    
    
    
    var_orig_grib = mv.read(workdir+inputfile)  # original modified lnsp GRIB
    var_add_grib = mv.set_values(var_orig_grib, var_add_flat)
    ofile=workdir+f"temp_{var}_add_SP.grib"
    mv.write(ofile, var_add_grib)


    print(f'Writing {ofile}  successful')
    
    return ofile
    
    

