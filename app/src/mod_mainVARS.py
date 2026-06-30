# -*- coding: utf-8 -*-
"""
author: Sandor Istvan Maho


This script modifies initial conditions in file ICMSH*INIT based on CMIP6 climate data

"""

import xarray as xr
import subprocess
import os
import glob
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import textwrap
import tempfile
import gc
import cftime

#submodules

import mod_simple_plots as spl
import mod_outputOIFS as opi
import mod_spectral_filter as spf
import mod_vert_interpol as vip


import json
import importlib.util
import time



"""################################################ """
""" +++++++++++++ some specifics here +++++++++++++ """

sp_filter_ON = True  #turn on spectral filter module

cutoff_wavenumber = 255  #for spectral filter

lnsp_wavenumber = 36 #CMIP6 lnsp update wavenumber limit


compare_sp_plots = True  #enable plotting for sanity check

check_interpolation = True #enable plotting for sanity check


""" +++++++++++++++++++++++++++++++++++++++++++++++ """
"""################################################ """ 




# Dynamically import shared list module (from temp .py file)
spec = importlib.util.spec_from_file_location("shared_lists", shared_list_module)
shared_lists = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared_lists)

# Access the lists
json_path_ICMSH = shared_lists.json_path1
cmip_var_names_ICMSH = shared_lists.cmip_vars_ICMSH
essential_scripts_ICMSH = shared_lists.essential_scripts1



# Load config
with open(json_path_ICMSH) as f:
    config = json.load(f)


globals().update(config)




if grid_type == 'TL639':
    N_sp=639
elif grid_type == 'TL255':
    N_sp=255
elif grid_type == 'TL159':
    N_sp=159
elif grid_type == 'TL1279':
    N_sp=1279
elif grid_type == 'TL399':
    N_sp=399
else:
    print(f"Error: Unsupported grid type {grid_type}.")
    sys.exit(1)



def fix_time_name_ERA5(ds):
    
    ds = ds.rename({"valid_time": "time"})

    if "unlimited_dims" in ds.encoding:
        ds.encoding["unlimited_dims"] = {
            d for d in ds.encoding["unlimited_dims"]
            if d in ds.dims
        }
    
    return ds






subprocess.run(['bash', essential_scripts_ICMSH[0], expname, IFS_path, in_HPC])



'''-----------------------------------import OIFS input data---------------------------------------'''

ini_nc_str =["ds_lnsp",
             "ds_t",
             "ds_u",
             "ds_v"]


OIFS_nc_files = [workdir+"temp_lnsp_GG.nc",
                 workdir+"temp_t_GG.nc",
                 workdir+"temp_u_GG.nc",
                 workdir+"temp_v_GG.nc"]


dsets_IFS_dry = {}


for i in range(len(ini_nc_str)):
    dsets_IFS_dry[ini_nc_str[i]]=xr.open_dataset(OIFS_nc_files[i])


slice_u = dsets_IFS_dry["ds_u"].u.isel(time=0).mean(dim="longitude")  #adjust dimension names as needed

#detect number of model levels
if len(slice_u.level.values)==91:
    numLEV=91
elif len(slice_u.level.values)==137:
    numLEV=137
else:
    print(f"Error: Unsupported number of levels {len(slice_u.level.values)}")
    sys.exit(1)  






'''-----------------------------------import CMIP6 data---------------------------------------'''

sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"
 

dsets_CMIP_dry = {}
dsets_CMIP_dry_old = {}


for var in cmip_var_names_ICMSH:
    #Create wildcard pattern
    ofile=workdir+"temp_cmip6_"+var+".nc"
    pattern = f"{var}_*{model}_*{exp_cmip}_*{variant_lab}_*{date_yr}*.nc"
    #Full search path
    search_path = os.path.join(cmip_path, pattern)
    
    matches = glob.glob(search_path)
    
    if len(matches) != 1:
        print(f"Error: Expected exactly 1 match for {var}, but found {len(matches)}.")
        sys.exit(1)
    
    
    print(f"Loading file for {var}: {matches[0]}")
    
    subprocess.run(['bash', essential_scripts_ICMSH[1], matches[0], ofile, grid_type, sel_date, in_HPC], check=True)


    if ERA5_source:
    
        dsets_CMIP_dry_old[var] = xr.open_dataset(ofile)
        dsets_CMIP_dry[var]=fix_time_name_ERA5(dsets_CMIP_dry_old[var])
    
    else:
        dsets_CMIP_dry[var]=xr.open_dataset(ofile)




slice_rg = {}


for var in cmip_var_names_ICMSH:
    time0 = dsets_CMIP_dry[var][var].time.values[0]

    if isinstance(time0, cftime.datetime):
        dt = datetime.fromisoformat(sel_date)
        sel_date = type(time0)(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    slice_rg[var] = dsets_CMIP_dry[var][var].sel(time=sel_date, method='nearest')
    if 'plev' in slice_rg[var].dims:
       slice_rg[var]=slice_rg[var].rename({'plev': 'lev'})
    if 'level' in slice_rg[var].dims:
       slice_rg[var]=slice_rg[var].rename({'plev': 'lev'})
    if 'z' in slice_rg[var].dims:
       slice_rg[var]=slice_rg[var].rename({'plev': 'lev'})
    
    sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"


"""
# Plot

spl.general_surface_plot(slice_rg['ps'],c_levs=32,varname='surface pressure')

spl.cartopy_surface_plot(slice_rg['ps'],c_levs=32,varname='surface pressure',unit='Pascals')
"""



'''-----------------------------------save interpolated CMIP6 netcdf data---------------------------------------'''


if if_CMIP_in_IFS_model_level==False:

    for var in cmip_var_names_ICMSH:
        if var=='ps':
            sfname=workdir+"temp_ps_seldate.nc"
            sfname2=workdir+"temp_ps_seldate_orig.nc"
            lnsp_CMIP=np.log(slice_rg['ps'])
            
            slice_rg['ps'].to_netcdf(sfname2)
            
            
            lnsp_CMIP.attrs = dsets_IFS_dry['ds_lnsp'].attrs.copy()
            lnsp_CMIP.encoding = dsets_IFS_dry['ds_lnsp'].encoding.copy()
            
            lnsp_CMIP.to_netcdf(sfname)
            
            
        else:
            sfname=workdir+"temp_"+var+"_seldate.nc"
            slice_rg[var].to_netcdf(sfname)

else:
    
    for var,ifsID in zip(cmip_var_names_ICMSH,ini_nc_str):
        if var=='ps':
            sfname=workdir+"temp_ps_seldate.nc"
            sfname2=workdir+"temp_ps_seldate_orig.nc"
            lnsp_CMIP=np.log(slice_rg['ps'])
            
            slice_rg['ps'].to_netcdf(sfname2)
            
            lnsp_CMIP.attrs = dsets_IFS_dry['ds_lnsp'].attrs.copy()
            lnsp_CMIP.encoding = dsets_IFS_dry['ds_lnsp'].encoding.copy()
            
            lnsp_CMIP.to_netcdf(sfname)
            
        else:
            field_new = slice_rg[var].copy()
            #detect vertical coordinate name
            vert_names = ["lev", "level", "plev", "z"]
            vert_name = None
            for name in vert_names:
                if name in field_new.dims:
                    vert_name = name
                    break
            
            if vert_name is None:
                raise ValueError("No recognized vertical coordinate found in field_new")

            #change coordinate name to 'level'
            field_new = field_new.rename({vert_name: "level"})
            
            
            target_levels = dsets_IFS_dry[ifsID]["level"].values
        
            
            if field_new["level"].values[0] > field_new["level"].values[-1]:
                target_levels = target_levels[::-1]   # reverse order
            
            
            field_new = field_new.assign_coords(level=target_levels)

            #copy coordinate attributes
            field_new["level"].attrs = dsets_IFS_dry[ifsID]["level"].attrs
            
            
            sfname=workdir+"temp_"+var+"_seldate.nc"
            field_new.to_netcdf(sfname)



'''-----------------------------------vertical interpolartion module (if applicable)---------------------------------------'''


if if_CMIP_in_IFS_model_level==False:
    if use_linear_hybrid2hybrid:
        
        if numLEV==91:
            L_ifs=np.loadtxt(workdir+"aux/L91_model_levels.txt",skiprows=2)
            L_ifs = np.round(L_ifs, decimals=6)
            #this file contains the L91 ml definitions
            
        elif numLEV==137:
            L_ifs=np.loadtxt(workdir+"aux/L137_model_levels.txt",skiprows=2)
            L_ifs = np.round(L_ifs, decimals=6)
            #this file contains the L137 ml definitions
            
        
        for var in cmip_var_names_ICMSH:
              
            
            if not (var=='ps'):
                
                
                print(f"interpolate vertically (ml->ml): {var}")
                
                
                filT = f"temp_{var}_seldate.nc"
                filP = "temp_ps_seldate_orig.nc"
                outf = f"temp_{var}_vertint_seldate.nc"
                
                ds_ps = xr.open_dataset(filP)
                ds_t = xr.open_dataset(filT)

                sel_t = ds_t[var]
                sel_ps = ds_ps['ps']
        
                sel_t_interpol=vip.ml2ml_vert_interpol(numLEV,ML_input,ML_input_sep,workdir,sel_t,sel_ps)
                
                sel_t_interpol.to_netcdf(workdir+outf)
    
    else:
        
        if numLEV==91:
            L_ifs=np.loadtxt(workdir+"aux/L91_model_levels.txt",skiprows=2)
            L_ifs = np.round(L_ifs, decimals=6)
            #this file contains the L91 ml definitions
            
        elif numLEV==137:
            L_ifs=np.loadtxt(workdir+"aux/L137_model_levels.txt",skiprows=2)
            L_ifs = np.round(L_ifs, decimals=6)
            #this file contains the L137 ml definitions
            
        
        for var in cmip_var_names_ICMSH:
              
            
            if not (var=='ps'):
                
                
                print(f"interpolate vertically (pl->ml): {var}")
                
                
                filT = f"temp_{var}_seldate.nc"
                filP = "temp_ps_seldate_orig.nc"
                outf = f"temp_{var}_vertint_seldate.nc"
                
                ds_ps = xr.open_dataset(filP)
                ds_t = xr.open_dataset(filT)

                sel_t = ds_t[var]
                sel_ps = ds_ps['ps']
                
                sel_t_interpol=vip.pl2ml_vert_interpol(numLEV,workdir,sel_t,sel_ps,var)
        
                
                sel_t_interpol.to_netcdf(workdir+outf)
            
            
else:
    print('+++++++++++++++++++++++++++++++++++++++++')
    print('input CMIP in IFS standard model levels')
    print('vertical interpolation omitted')
    print('+++++++++++++++++++++++++++++++++++++++++')
    time.sleep(5)




'''-----------------------------------Plotting module (check interpolation)---------------------------------------'''


if check_interpolation:

    slice_IFS_to_comp = dsets_IFS_dry["ds_lnsp"].lnsp.isel(time=0)
    ds_tint = xr.open_dataset(workdir+"temp_ps_seldate.nc")
    slice_CMIPint_to_comp = ds_tint.ps 
    
    savepath=f"{workdir}plots/comp_lnsp.png"
    
    spl.compare_cartopy_surface(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='lnsp',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
    
    
    
    slice_IFS_to_comp = dsets_IFS_dry["ds_t"].t.isel(time=0).mean(dim="longitude")  # adjust dimension names as needed
    if if_CMIP_in_IFS_model_level==False:
        ds_tint = xr.open_dataset(workdir+"temp_ta_vertint_seldate.nc")
        lon_dim = [d for d in ds_tint.dims if "lon" in d.lower()][0]
        slice_CMIPint_to_comp=ds_tint.ta.mean(dim=lon_dim)
    else:
        ds_tint = xr.open_dataset(workdir+"temp_ta_seldate.nc")
        slice_CMIPint_to_comp=ds_tint.ta.mean(dim="lon") 
    
    
    savepath=f"{workdir}plots/compT.png"
    savepath2=f"{workdir}plots/Tsurf.png"
    
    
    
    if if_CMIP_in_IFS_model_level==False:
    
        spl.compare_general_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='t',dset_name1='IFS',dset_name2='CMIP6',unit='air temperature [K]',c_levs=32, save_plot=savepath)
        #spl.cartopy_surface_plot(ds_tint.var1.isel(level=90),c_levs=32,varname='temp',unit='K')
        #spl.cartopy_surface_plot(dsets_IFS_dry["ds_t"].t.isel(time=0,level=90),c_levs=32,varname='temp',unit='K',save_plot=savepath2)
    
    else:
        
        spl.compare_general_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='t',dset_name1='IFS',dset_name2='CMIP6',unit='air temperature [K]',c_levs=32, save_plot=savepath)
        #spl.cartopy_surface_plot(ds_tint.ta.isel(level=90),c_levs=32,varname='temp',unit='K')
        #spl.cartopy_surface_plot(dsets_IFS_dry["ds_t"].t.isel(time=0,level=90),c_levs=32,varname='temp',unit='K',save_plot=savepath2)
        
        
    
    slice_IFS_to_comp = dsets_IFS_dry["ds_u"].u.isel(time=0).mean(dim="longitude")  # adjust dimension names as needed
    if if_CMIP_in_IFS_model_level==False:
        ds_tint = xr.open_dataset(workdir+"temp_ua_vertint_seldate.nc")
        lon_dim = [d for d in ds_tint.dims if "lon" in d.lower()][0]
        slice_CMIPint_to_comp=ds_tint.ua.mean(dim=lon_dim) 
    else:
        ds_tint = xr.open_dataset(workdir+"temp_ua_seldate.nc")
        slice_CMIPint_to_comp=ds_tint.ua.mean(dim="lon") 
    
    
    savepath=f"{workdir}plots/compU.png"
    
    if if_CMIP_in_IFS_model_level==False:
        spl.compare_wind_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='u',dset_name1='IFS',dset_name2='CMIP6',c_levs=32, save_plot=savepath)
        #spl.cartopy_surface_plot(ds_tint.var1.isel(level=90),c_levs=32,varname='u',unit='m/s')
    else:
        spl.compare_wind_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='u',dset_name1='IFS',dset_name2='CMIP6',c_levs=32, save_plot=savepath)
        #spl.cartopy_surface_plot(ds_tint.ua.isel(level=90),c_levs=32,varname='u',unit='m/s')
    
    
    
    
    
    
    savepath=f"{workdir}plots/compV.png"
    slice_IFS_to_comp = dsets_IFS_dry["ds_v"].v.isel(time=0).mean(dim="longitude")  # adjust dimension names as needed
    if if_CMIP_in_IFS_model_level==False:
        ds_tint = xr.open_dataset(workdir+"temp_va_vertint_seldate.nc")
        lon_dim = [d for d in ds_tint.dims if "lon" in d.lower()][0]
        slice_CMIPint_to_comp=ds_tint.va.mean(dim=lon_dim) 
    else:
        ds_tint = xr.open_dataset(workdir+"temp_va_seldate.nc")
        slice_CMIPint_to_comp=ds_tint.va.mean(dim="lon")
    
    
    if if_CMIP_in_IFS_model_level==False:
        spl.compare_wind_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='v',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
       #spl.cartopy_surface_plot(ds_tint.var1.isel(level=90),c_levs=32,varname='v',unit='m/s')
    else:
        spl.compare_wind_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='v',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        #spl.cartopy_surface_plot(ds_tint.va.isel(level=90),c_levs=32,varname='v',unit='m/s')





'''-----------------------------------Conversion to GRIB format---------------------------------------'''



paramID_names=['152',
               '130',
               '131',
               '132']



for var, ParamID in zip(cmip_var_names_ICMSH, paramID_names):
    if if_CMIP_in_IFS_model_level==False:
        subprocess.run(['bash', essential_scripts_ICMSH[2], var, ParamID, workdir,"False", in_HPC], check=True)
    else:
        subprocess.run(['bash', essential_scripts_ICMSH[2], var, ParamID, workdir,"True", in_HPC], check=True)
    

subprocess.run(['bash', essential_scripts_ICMSH[3], workdir, in_HPC], check=True)


subprocess.run(['bash', essential_scripts_ICMSH[4], workdir, in_HPC], check=True)


'''-----------------------------------spectral filter module and update initial files---------------------------------------'''


if sp_filter_ON:
    print('+++++++ spectral filter module in use +++++++')
    t_mod=spf.apply_high_n_taper_3d("temp_ta_renamed_SP.grib",'t',N_sp,cutoff_wavenumber,compare_sp_plots,workdir)
    
    vor_mod=spf.apply_high_n_taper_3d("temp_vor_renamed2_SP.grib",'vo',N_sp,cutoff_wavenumber,compare_sp_plots,workdir)
    
    div_mod=spf.apply_high_n_taper_3d("temp_div_renamed2_SP.grib",'d',N_sp,cutoff_wavenumber,compare_sp_plots,workdir)
    
    
    #If lnsp_orig.grib is used in function apply_add_coeffs, then the function adds together the CMIP6 lnsp (zw:0-36) and the original OIFS grib file (zw:37-N_sp)
    #this is disabled, since ERA5 monthly mean data used instead
    #ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib","lnsp_orig.grib",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,IFS_path)
    
    if grid_type == 'TL639':
    
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F320_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    elif grid_type == 'TL1279':
    
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F640_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    elif grid_type == 'TL255':
        
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F128_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    elif grid_type == 'TL159':
        
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F80_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
        
    elif grid_type == 'TL399':
         
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F200_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
        
        
    else:
        
        print(f"Unsupported grid type {grid_type}")
    
    #this is not needed
    #ps_mod=spf.apply_high_n_taper_2d("temp_ps_renamed_SP.grib",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir)
    
    origfile=f"{IFS_path}ICMSH{expname}INIT"
    
    

    #update GRIB files
    opi.update_ICMSH(origfile,t_mod,vor_mod,div_mod,ps_mod,f"{IFS_path}ICMSH{expname}INITmod")

    

else:
    print('+++++++ spectral filter module ignored +++++++')

    
    slice_IFS_to_comp = dsets_IFS_dry["ds_lnsp"].lnsp.isel(time=0)
    ds_tint = xr.open_dataset(workdir+"temp_ps_seldate.nc")
    slice_CMIPint_to_comp = ds_tint.ps 
    
    
    origfile=f"{IFS_path}ICMSH{expname}INIT"
    t_mod=f"{workdir}temp_ta_renamed_SP.grib"
    vor_mod=f"{workdir}temp_vor_renamed2_SP.grib"
    div_mod=f"{workdir}temp_div_renamed2_SP.grib"
    #ps_mod=f"{workdir}temp_ps_renamed_SP.grib"
    
    
    if grid_type == 'TL639':
    
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F320_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    elif grid_type == 'TL1279':
    
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F640_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    elif grid_type == 'TL255':
        
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F128_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    elif grid_type == 'TL159':
        
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F80_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
        
    elif grid_type == 'TL399':
         
        ps_mod=spf.apply_add_coeffs("temp_ps_renamed_SP.grib",f"aux/lnsp_1981-2010_0UTC_ymonmean_F200_SP.nc",'lnsp',N_sp,lnsp_wavenumber,compare_sp_plots,workdir,date_mo)
    
    
    
    opi.update_ICMSH(origfile,t_mod,vor_mod,div_mod,ps_mod,f"{IFS_path}ICMSH{expname}INITmod")



'''-----------------------------------clean up---------------------------------------'''


for name in ["dsets_IFS_dry", "dsets_CMIP_dry", "dsets_CMIP_dry_old"]:
    if name in globals():
        for ds in globals()[name].values():
            try:
                ds.close()
            except Exception:
                pass

large_vars = [
    "dsets_IFS_dry", "dsets_CMIP_dry", "dsets_CMIP_dry_old",
    "slice_rg", "slice_u", "slice_IFS_to_comp",
    "slice_CMIPint_to_comp", "lnsp_CMIP", "field_new", "ds_tint",
    "ds_t_hy", "hyam", "hybm", "t_mod", "vor_mod", "div_mod",
    "ps_mod", "ds_t", "ds_ps", "sel_t", "sel_ps"
]
for var in large_vars:
    if var in globals():
        del globals()[var]

gc.collect()
