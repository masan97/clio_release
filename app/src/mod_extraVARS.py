#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: Sandor Istvan Maho


This script modifies initial conditions in file ICMGG*INIT and ICMCL*INIT based on CMIP6 climate data


"""

import xarray as xr
import subprocess
import os
import glob
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import pandas as pd
import textwrap
import tempfile
import gc
import time
import cftime

#submodules

import mod_simple_plots as spl
import mod_outputOIFS as opi


import json
import importlib.util



"""################################################ """
""" +++++++++++++ some specifics here +++++++++++++ """

check_surface_update = False #enable plotting for sanity check

""" +++++++++++++++++++++++++++++++++++++++++++++++ """
"""################################################ """ 




# Dynamically import shared list module (from temp .py file)
spec = importlib.util.spec_from_file_location("shared_lists", shared_list_module)
shared_lists = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared_lists)

# Access the lists
json_path_ICMGG = shared_lists.json_path2
cmip_var_names_ICMGG = shared_lists.cmip_vars_ICMGG
essential_scripts_ICMGG = shared_lists.essential_scripts2
essential_files = shared_lists.essential_files2

OIFS_CL_increment = 24 #timestep in ICMCL* file, this is always 24 hrs

# Load config
with open(json_path_ICMGG) as f:
    config = json.load(f)


globals().update(config)


def fix_time_name_ERA5(ds):
    
    ds = ds.rename({"valid_time": "time"})

    if "unlimited_dims" in ds.encoding:
        ds.encoding["unlimited_dims"] = {
            d for d in ds.encoding["unlimited_dims"]
            if d in ds.dims
        }
    
    return ds

'''-----------------------------------import OIFS input data---------------------------------------'''

subprocess.run(['bash', essential_scripts_ICMGG[5], expname, IFS_path, in_HPC])




nc_str =["sst",
         "ci",
         "stl1",
         "stl2",
         "stl3",
         "stl4",
         "istl1",
         "istl2",
         "istl3",
         "istl4",
         "swvl1",
         "swvl2",
         "swvl3",
         "swvl4",
         "sd",
         "tsn",
         "asn",
         "rsn",
         "skt"]


OIFS_nc_files = []


for string in nc_str:
    OIFS_nc_files.append(workdir+f"temp_{string}_GG.nc")
    


dsets_IFS_suf = {}

for item,ncs in zip(OIFS_nc_files,nc_str):
        if os.path.exists(item):
            dsets_IFS_suf[ncs]=xr.open_dataset(item)
        else:
            print(f"{item} not found, continue")
            continue


slice_IFS_suf = {}

for item,name in zip(nc_str,OIFS_nc_files):
    if os.path.exists(name):
        if item=='ci':
            slice_IFS_suf[item] = dsets_IFS_suf[item]['siconc'].isel(time=0)
            continue
        slice_IFS_suf[item] = dsets_IFS_suf[item][item].isel(time=0)
    else:
        continue


'''-----------------------------------import CMIP6 input data---------------------------------------'''



sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"


dsets_CMIP_suf = {}
dsets_CMIP_suf_tmp = {}
dsets_CMIP_suf_old = {}


for var in cmip_var_names_ICMGG:
    if ((var=='cli') or (var=='clw') or (var=='crwc') or (var=='cswc') or (var=='cc')):
        continue
    #Create the wildcard pattern
    ofile=workdir+"temp_cmip6_"+var+".nc"
    pattern = f"{var}_*{model}_*{exp_cmip}_*{variant_lab}_*{date_yr}*.nc"
    #Full search path
    search_path = os.path.join(cmip_path, pattern)
    
    matches = glob.glob(search_path)
    
    if len(matches) != 1:
        print(f"Error: Expected exactly 1 match for {var}, but found {len(matches)}.")
        sys.exit(1) 
    
    
    print(f"Loading file for {var}: {matches[0]}")
    
    dsets_CMIP_suf_old[var] = xr.open_dataset(matches[0])
    
    
    subprocess.run(['bash', essential_scripts_ICMGG[11], matches[0], ofile, grid_type, in_HPC], check=True)


    if ERA5_source:
    
        dsets_CMIP_suf_tmp[var] = xr.open_dataset(ofile)

        dsets_CMIP_suf[var]=fix_time_name_ERA5(dsets_CMIP_suf_tmp[var])
    
    else:
        dsets_CMIP_suf[var] = xr.open_dataset(ofile)        




    
slice_rg = {}
slice_rg_rn = {}


for var in cmip_var_names_ICMGG:
    if ((var=='cli') or (var=='clw') or (var=='crwc') or (var=='cswc') or (var=='cc')):
        continue
    
    time0 = dsets_CMIP_suf[var][var].time.values[0]

    if isinstance(time0, cftime.datetime):
        dt = datetime.fromisoformat(sel_date)
        sel_date = type(time0)(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    slice_rg[var] = dsets_CMIP_suf[var][var].sel(time=sel_date, method='nearest')

    if grid_type not in ['TCo319','TCo639','TCo1279']:
   
        slice_rg_rn[var]=slice_rg[var].rename({'lat': 'latitude','lon': 'longitude'})
    
    else:
        slice_rg_rn[var]=slice_rg[var]

    sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"



'''-----------------------------------Udate ICMCL files (stl1 and ci only)---------------------------------------'''


if not update_CL:
    print('Nothing to be done for CL file')
    time.sleep(3)
    
else:

    dset_CL = {}
    
    CL_vars = ['stl1','ci','al','lai_lv','lai_hv']
    
    
    for vr in CL_vars:

        item=workdir+f"temp_ICMCL_{vr}_GG.nc"
        dset_CL[vr]=xr.open_dataset(item)



    if len(dset_CL['ci'].time.values) != int(CL_length):
        print(f"Error: Data length {len(CL_time_selection)} not matching with the CL_length {CL_length}.")
        sys.exit(1)



    Date_yr = int(date_yr)
    Date_mo = int(date_mo)
    Date_dd = int(date_dd)
    Date_hr = int(date_hr)

    #create start datetime
    start_date = np.datetime64(f"{Date_yr:04d}-{Date_mo:02d}-{Date_dd:02d}T{Date_hr:02d}:00")

    #create array of 10 timestamps with 12-hour spacing
    dt_for_CL_time = np.timedelta64(OIFS_CL_increment, 'h')
    CL_time = start_date + np.arange(int(CL_length)) * dt_for_CL_time


    if 'siconca' in cmip_var_names_ICMGG:
        
        time0 = dsets_CMIP_suf['siconca'].time.values[0]

        if isinstance(time0, cftime.datetime):
            CL_time2 = []

            for t in CL_time:
                dt = t.astype('datetime64[s]').tolist()

                CL_time2.append(type(time0)(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second))

    
            sel_siconca_for_CL = dsets_CMIP_suf['siconca'].sel(time=CL_time2, method="nearest")
            
        else:

            sel_siconca_for_CL = dsets_CMIP_suf['siconca'].sel(time=CL_time, method="nearest")

        if not ERA5_source:
        
            siconca_to_CL = sel_siconca_for_CL.siconca/100
        
        else:

            siconca_to_CL = sel_siconca_for_CL.siconca
        
        
        #make sure lengths match
        if len(siconca_to_CL.time) != len(dset_CL['ci'].time):
            print(f"Warning: Length mismatch — using first {len(siconca_to_CL.time)} times from dset_CL['ci']")
            new_time = dset_CL['ci'].time.isel(time=slice(0, len(siconca_to_CL.time)))
        else:
            new_time = dset_CL['ci'].time
            
        siconca_to_CL = siconca_to_CL.assign_coords(time=new_time)

    
        
    else:
        fname_sea_ice = f"{workdir}temp_siconc.nc"
        ds_ice = xr.open_dataset(f"{essential_files[11]}")
        
        
        
        #time array used for selecting dates (i.e. there might be data from 2 months, not just one)
        sel_months = pd.to_datetime(CL_time).month
        ds_ice_year=ds_ice.valid_time.dt.year.values[0]
        sel_dates = pd.to_datetime({"year": ds_ice_year,"month": sel_months,"day": 1}).values
        
        ds_ERA5_siconc = ds_ice['siconc'].sel(valid_time=sel_dates,method='nearest')
            
        ds_ERA5_siconc.to_netcdf(fname_sea_ice)
            
        ofile=workdir+"temp_cmip6_siconc_CL.nc"
             
        subprocess.run(['bash', essential_scripts_ICMGG[11], fname_sea_ice, ofile, grid_type, in_HPC], check=True)
            
        ds_ERA5_interp_siconca=xr.open_dataset(ofile)
        
        siconca_to_CL=ds_ERA5_interp_siconca.siconc
        
        #rename time dimension
        siconca_to_CL = siconca_to_CL.rename({"valid_time": "time"})
        
        
        #change the times of the ci array
        #Make sure lengths match
        if len(siconca_to_CL.time) != len(dset_CL['ci'].time):
            print(f"Warning: Length mismatch — using first {len(siconca_to_CL.time)} times from dset_CL['ci']")
            new_time = dset_CL['ci'].time.isel(time=slice(0, len(siconca_to_CL.time)))
        else:
            new_time = dset_CL['ci'].time

        #Replace the time coordinate
        siconca_to_CL = siconca_to_CL.assign_coords(time=new_time)
        
        
        
    #stl1 is sst, not soil temp

    time0 = dsets_CMIP_suf['tos'].time.values[0]

    if isinstance(time0, cftime.datetime):
        CL_time2 = []

        for t in CL_time:
            dt = t.astype('datetime64[s]').tolist()

            CL_time2.append(type(time0)(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second))

    
        sel_tos_for_CL = dsets_CMIP_suf['tos'].sel(time=CL_time2, method="nearest")
            
    else:
        sel_tos_for_CL = dsets_CMIP_suf['tos'].sel(time=CL_time, method="nearest")

    if not ERA5_source:

        sel_tos_for_CL['tos'] += 273.15
    
        
    

    

    tos_to_CL=sel_tos_for_CL['tos']
    
    
    # Replace the time coordinate
    new_time = dset_CL['stl1'].time
    tos_to_CL = tos_to_CL.assign_coords(time=new_time)

    tos_to_CL = tos_to_CL.fillna(273.15)



    #ALBEDO
    
    fname_al = f"{workdir}temp_al.nc"
    ds_al = xr.open_dataset(f"{essential_files[19]}")
    
    
    #time array used for selecting dates (i.e. there might be data from 2 months, not just one)
    sel_months = pd.to_datetime(CL_time).month
    ds_al_year=ds_al.valid_time.dt.year.values[0]
    sel_dates = pd.to_datetime({"year": ds_al_year,"month": sel_months,"day": 1}).values
    
    ds_ERA5_al = ds_al['fal'].sel(valid_time=sel_dates,method='nearest')
        
    ds_ERA5_al.to_netcdf(fname_al)
        
    ofile=workdir+"temp_cmip6_al_CL.nc"
         
    subprocess.run(['bash', essential_scripts_ICMGG[11], fname_al, ofile, grid_type, in_HPC], check=True)
        
    ds_ERA5_interp_al=xr.open_dataset(ofile)
    
    al_to_CL=ds_ERA5_interp_al.fal
    
    # rename time dimension
    al_to_CL = al_to_CL.rename({"valid_time": "time"})
    
    
    #siconca_to_CL = siconca_to_CL.assign_coords(time=CL_time)
    #siconca_to_CL = fix_time_encoding(siconca_to_CL,dset_CL['ci'])
    
    #change the times of the ci array
    # Make sure lengths match
    if len(al_to_CL.time) != len(dset_CL['al'].time):
        print(f"Warning: Length mismatch — using first {len(al_to_CL.time)} times from dset_CL['al']")
        new_time = dset_CL['al'].time.isel(time=slice(0, len(al_to_CL.time)))
    else:
        new_time = dset_CL['al'].time

    # Replace the time coordinate
    al_to_CL = al_to_CL.assign_coords(time=new_time)
    
    
    
    
    #LAI_LV & LAI_HV
    fnames_lai = [f"{workdir}temp_lai_lv.nc",f"{workdir}temp_lai_hv.nc"]
    ds_lai = xr.open_dataset(f"{essential_files[18]}")
    
    ds_ERA5_lai= {}
    ds_ERA5_interp={}
    for i,lai in enumerate(['lai_lv','lai_hv']):
        
        ds_ERA5_lai[lai] = ds_lai[lai].sel(valid_time=sel_dates,method='nearest')
        
        ds_ERA5_lai[lai].to_netcdf(fnames_lai[i])
        
        ofile=workdir+f"temp_cmip6_{lai}_CL.nc"
             
        subprocess.run(['bash', essential_scripts_ICMGG[11], fnames_lai[i], ofile, grid_type, in_HPC], check=True)
        
        ds_ERA5_interp[lai]=xr.open_dataset(ofile)
    
    lai_lv_to_CL=ds_ERA5_interp['lai_lv'].lai_lv
    lai_hv_to_CL=ds_ERA5_interp['lai_hv'].lai_hv
    
    # rename time dimension
    lai_lv_to_CL = lai_lv_to_CL.rename({"valid_time": "time"})
    lai_hv_to_CL = lai_hv_to_CL.rename({"valid_time": "time"})
    

    # Make sure lengths match
    if len(lai_lv_to_CL.time) != len(dset_CL['lai_lv'].time):
        print(f"Warning: Length mismatch — using first {len(lai_lv_to_CL.time)} times from dset_CL['lai_lv']")
        new_time = dset_CL['lai_lv'].time.isel(time=slice(0, len(lai_lv_to_CL.time)))
    else:
        new_time = dset_CL['lai_lv'].time

    # Replace the time coordinate
    lai_lv_to_CL = lai_lv_to_CL.assign_coords(time=new_time)
    lai_hv_to_CL = lai_hv_to_CL.assign_coords(time=new_time)
    

    #plotting
    #spl.general_surface_plot(sel_tos_for_CL['tos'].isel(time=2),c_levs=32,varname='tos')
    #spl.general_surface_plot(tos_to_CL.isel(time=2),c_levs=32,varname='tos')


    #save to netcdf
    

    #fix grib attributes for siconca
    siconca_to_CL = siconca_to_CL.fillna(0)
    siconca_to_CL.rename('siconc')
    siconca_to_CL.attrs = {
    "long_name": "Sea ice area fraction",
    "standard_name": "sea_ice_area_fraction",
    "units": "1",
    "GRIB_paramId": 31,
    "GRIB_shortName": "ci",
    "GRIB_name": "Sea ice area fraction"}
    
    sfname=workdir+"temp_siconca_to_CL.nc"
    siconca_to_CL.to_netcdf(sfname)

    sfname=workdir+"temp_tos_to_CL.nc"
    tos_to_CL.to_netcdf(sfname)
    
    sfname=workdir+"temp_fal_to_CL.nc"
    al_to_CL.to_netcdf(sfname)
    
    sfname=workdir+"temp_lai_lv_to_CL.nc"
    lai_lv_to_CL.to_netcdf(sfname)

    sfname=workdir+"temp_lai_hv_to_CL.nc"
    lai_hv_to_CL.to_netcdf(sfname)

    subprocess.run(['bash', essential_scripts_ICMGG[9],"siconca","ci",workdir,"31",in_HPC], check=True)
    subprocess.run(['bash', essential_scripts_ICMGG[9],"tos","stl1",workdir,"139",in_HPC], check=True)
    subprocess.run(['bash', essential_scripts_ICMGG[9],"fal","al",workdir,"174",in_HPC], check=True)
    subprocess.run(['bash', essential_scripts_ICMGG[9],"lai_lv","lai_lv",workdir,"66",in_HPC], check=True)
    subprocess.run(['bash', essential_scripts_ICMGG[9],"lai_hv","lai_hv",workdir,"67",in_HPC], check=True)
    
        


    origfile=f"{IFS_path}ICMCL{expname}INIT"
    outfile=f"{IFS_path}ICMCL{expname}INITmod"


    opi.update_ICMCL(origfile,
                     workdir+"temp_ci_renamed_CL.grib",
                     workdir+"temp_stl1_renamed_CL.grib",
                     workdir+"temp_al_renamed_CL.grib",
                     workdir+"temp_lai_lv_renamed_CL.grib",
                     workdir+"temp_lai_hv_renamed_CL.grib",
                     outfile)



'''-----------------------------------update ICMGG*INIT file---------------------------------------'''
if not update_GG:
    print('Nothing to be done for GG file')
    time.sleep(3)
    
else:

       
    
    
    '''-----------------------------------Create the data arrays for the update---------------------------------------'''
    
    cmip_file_IDs = []  #this is used for a bash script, the name string of netcdf files are saved here
    paramID_names = []  #GRIB IDs
    cmip_IDs = [] #CMIP varnames
    OIFS_IDs = [] #OIFS varnames 
    
    #SST
    
    if not ERA5_source:
        tos_Kel = slice_rg_rn['tos']+273.15
    else:
        tos_Kel = slice_rg_rn['tos']

    
    tos_filled = tos_Kel.fillna(xr.DataArray(slice_IFS_suf['sst'].values,
                                                dims=tos_Kel.dims,
                                                coords=tos_Kel.coords))
   

    #save to netcdf
    sfname=workdir+"temp_tos_seldate.nc"
    tos_filled.to_netcdf(sfname)
    cmip_file_IDs.append('tos')
    paramID_names.append('34')
    cmip_IDs.append('tos')
    OIFS_IDs.append('sst')
    
    
    
    #SEA ICE
    
    if "siconca" in cmip_var_names_ICMGG:
        
        print("CMIP6 siconca is used")

        if not ERA5_source:
    
            siconca_ref=slice_rg['siconca']/100
        
        else:

            siconca_ref=slice_rg['siconca']
        
        siconca_ref = siconca_ref.fillna(0)

        
        cmip_IDs.append('siconca')
        
    else:
        
        print("ERA5 30-yr mean siconc is used")
        
        fname_sea_ice = f"{workdir}temp_siconc.nc"
        ds_ice = xr.open_dataset(f"{essential_files[11]}")
        
        ds_ERA5_siconc = ds_ice['siconc'].sel(valid_time=ds_ice.valid_time.dt.month == int(date_mo)).squeeze()
            
        ds_ERA5_siconc.to_netcdf(fname_sea_ice)
            
        ofile=workdir+"temp_cmip6_siconc.nc"
             
        subprocess.run(['bash', essential_scripts_ICMGG[11], fname_sea_ice, ofile, grid_type, in_HPC], check=True)
            
        ds_ERA5_interp_siconca=xr.open_dataset(ofile)
        
        siconca_ref=ds_ERA5_interp_siconca['siconc']

        siconca_ref = siconca_ref.fillna(0)
        
        cmip_IDs.append('siconc')
    
    sfname=workdir+"temp_siconca_seldate.nc"
    siconca_ref.to_netcdf(sfname)
    
    cmip_file_IDs.append('siconca')
    paramID_names.append('31')
    OIFS_IDs.append('ci')
    
    
    if "siconca" in cmip_var_names_ICMGG:
        
        if "sitemptop" in cmip_var_names_ICMGG:
            
            print("CMIP6 sitemptop is used for all four ice layers assuming linear temperature profile")
            
    
            sitemptop_filled = slice_rg_rn['sitemptop'].fillna(xr.DataArray(slice_IFS_suf['istl1'].values,
                                                     dims=slice_rg_rn['sitemptop'].dims,
                                                     coords=slice_rg_rn['sitemptop'].coords))
            
            
            #sea ice freezing temp: 271.45=273.15-1.7
            sitemptop_filled_l2 = (sitemptop_filled+0.6).where(
                (sitemptop_filled + 0.6) <= 271.45,
                other=sitemptop_filled
            )
        
        
        
        
            # Step 1: apply +5, but keep original if it exceeds 273.15
            sitemptop_filled_l3 = (sitemptop_filled + 2.6).where((sitemptop_filled + 2.6) <= 271.45, other=sitemptop_filled)
            
            sitemptop_filled_l4 = (sitemptop_filled + 4.6).where((sitemptop_filled + 4.6) <= 271.45, other=sitemptop_filled)
            
            cmip_IDs.append('sitemptop')
            cmip_IDs.append('sitemptop')
            cmip_IDs.append('sitemptop')
            cmip_IDs.append('sitemptop')

        else:
        
            print("ERA5 30-yr mean istl1-4 are used")
            
            
            ds_ice = xr.open_dataset(f"{essential_files[11]}")
            era5_T_seaice=['istl1','istl2','istl3','istl4']
            
            era5_seaice_fnames = [f"{workdir}temp_{era5_T_seaice[0]}.nc",
                                  f"{workdir}temp_{era5_T_seaice[1]}.nc",
                                  f"{workdir}temp_{era5_T_seaice[2]}.nc",
                                  f"{workdir}temp_{era5_T_seaice[3]}.nc"]
           
            ds_ERA5_clim = {}
            ds_ERA5_clim_interp={}
            
            for i,var in enumerate(era5_T_seaice):
                ds_ERA5_clim[var] = ds_ice[var].sel(valid_time=ds_ice.valid_time.dt.month == int(date_mo)).squeeze()
                
                ds_ERA5_clim[var].to_netcdf(era5_seaice_fnames[i])
                
                ofile=workdir+"temp_cmip6_"+var+".nc"
                 
                subprocess.run(['bash', essential_scripts_ICMGG[11], era5_seaice_fnames[i], ofile, grid_type, in_HPC], check=True)
                
                ds_ERA5_clim_interp[var]=xr.open_dataset(ofile)
            
            cmip_IDs.append('istl1')
            cmip_IDs.append('istl2')
            cmip_IDs.append('istl3')
            cmip_IDs.append('istl4')
            
            sitemptop_filled=ds_ERA5_clim_interp[era5_T_seaice[0]]
            sitemptop_filled_l2=ds_ERA5_clim_interp[era5_T_seaice[1]]
            sitemptop_filled_l3=ds_ERA5_clim_interp[era5_T_seaice[2]]
            sitemptop_filled_l4=ds_ERA5_clim_interp[era5_T_seaice[3]]
                        
    else:
        
        print("ERA5 30-yr mean istl1-4 are used")
            
            
        ds_ice = xr.open_dataset(f"{essential_files[11]}")
        era5_T_seaice=['istl1','istl2','istl3','istl4']
            
        era5_seaice_fnames = [f"{workdir}temp_{era5_T_seaice[0]}.nc",
                              f"{workdir}temp_{era5_T_seaice[1]}.nc",
                              f"{workdir}temp_{era5_T_seaice[2]}.nc",
                              f"{workdir}temp_{era5_T_seaice[3]}.nc"]
           
        ds_ERA5_clim = {}
        ds_ERA5_clim_interp={}
            
        for i,var in enumerate(era5_T_seaice):
            ds_ERA5_clim[var] = ds_ice[var].sel(valid_time=ds_ice.valid_time.dt.month == int(date_mo)).squeeze()
                
            ds_ERA5_clim[var].to_netcdf(era5_seaice_fnames[i])
                
            ofile=workdir+"temp_cmip6_"+var+".nc"
                 
            subprocess.run(['bash', essential_scripts_ICMGG[11], era5_seaice_fnames[i], ofile, grid_type, in_HPC], check=True)
                
            ds_ERA5_clim_interp[var]=xr.open_dataset(ofile)
            
        cmip_IDs.append('istl1')
        cmip_IDs.append('istl2')
        cmip_IDs.append('istl3')
        cmip_IDs.append('istl4')
            
        sitemptop_filled=ds_ERA5_clim_interp[era5_T_seaice[0]]
        sitemptop_filled_l2=ds_ERA5_clim_interp[era5_T_seaice[1]]
        sitemptop_filled_l3=ds_ERA5_clim_interp[era5_T_seaice[2]]
        sitemptop_filled_l4=ds_ERA5_clim_interp[era5_T_seaice[3]]
    
    #save to netcdf
    sfname=workdir+"temp_sitemptop_l1_seldate.nc"
    sitemptop_filled.to_netcdf(sfname)
    sfname=workdir+"temp_sitemptop_l2_seldate.nc"
    sitemptop_filled_l2.to_netcdf(sfname)
    sfname=workdir+"temp_sitemptop_l3_seldate.nc"
    sitemptop_filled_l3.to_netcdf(sfname)
    sfname=workdir+"temp_sitemptop_l4_seldate.nc"
    sitemptop_filled_l4.to_netcdf(sfname)
    
    cmip_file_IDs.append('sitemptop_l1') #layer 1
    cmip_file_IDs.append('sitemptop_l2') #layer 2
    cmip_file_IDs.append('sitemptop_l3') #layer 3
    cmip_file_IDs.append('sitemptop_l4') #layer 4
    
    paramID_names.append('35')
    paramID_names.append('36')
    paramID_names.append('37')
    paramID_names.append('38')
    
    
    OIFS_IDs.append('istl1')
    OIFS_IDs.append('istl2')
    OIFS_IDs.append('istl3')
    OIFS_IDs.append('istl4')
            
    
    
    
    #SOIL
    
    if "tsl" in cmip_var_names_ICMGG:
        
        print("CMIP6 tsl is used for all four soil layers")
        
        tsl_filled = slice_rg_rn['tsl'].fillna(xr.DataArray(slice_IFS_suf['stl1'].values,
                                                 dims=slice_rg_rn['tsl'].dims,
                                                 coords=slice_rg_rn['tsl'].coords))
        
        sfname=workdir+"temp_tsl_seldate.nc"
        tsl_filled.to_netcdf(sfname)
        cmip_file_IDs.append('tsl') #layer 1
        cmip_file_IDs.append('tsl') #same for layer 2
        cmip_file_IDs.append('tsl') #same for layer 3
        cmip_file_IDs.append('tsl') #same for layer 4
        
        paramID_names.append('139')
        paramID_names.append('170')
        paramID_names.append('183')
        paramID_names.append('236')
        
        cmip_IDs.append('tsl')
        cmip_IDs.append('tsl')
        cmip_IDs.append('tsl')
        cmip_IDs.append('tsl')
        
        OIFS_IDs.append('stl1')
        OIFS_IDs.append('stl2')
        OIFS_IDs.append('stl3')
        OIFS_IDs.append('stl4')
        
    else:
        
        print("ERA5 30-yr mean stl1-4 are used")
        
        era5_soil=['stl1','stl2','stl3','stl4']
        
        fnames_soil = [f"{workdir}temp_stl1.nc",
                      f"{workdir}temp_stl2.nc",
                      f"{workdir}temp_stl3.nc",
                      f"{workdir}temp_stl4.nc"]
        
        ds_soil = xr.open_dataset(f"{essential_files[12]}")
        
        
        ds_ERA5_clim = {}
        ds_ERA5_clim_interp={}
            
        for i,var in enumerate(era5_soil):
            ds_ERA5_clim[var] = ds_soil[var].sel(valid_time=ds_soil.valid_time.dt.month == int(date_mo)).squeeze()
                
            ds_ERA5_clim[var].to_netcdf(fnames_soil[i])
                
            ofile=workdir+"temp_cmip6_"+var+".nc"
                 
            subprocess.run(['bash', essential_scripts_ICMGG[11], fnames_soil[i], ofile, grid_type, in_HPC], check=True)
                
            ds_ERA5_clim_interp[var]=xr.open_dataset(ofile)
        
        tsl_filled=ds_ERA5_clim_interp[era5_soil[0]]
        tsl_filled_l2=ds_ERA5_clim_interp[era5_soil[1]]
        tsl_filled_l3=ds_ERA5_clim_interp[era5_soil[2]]
        tsl_filled_l4=ds_ERA5_clim_interp[era5_soil[3]]
        
        sfname=workdir+"temp_tsl_seldate.nc"
        tsl_filled.to_netcdf(sfname)
        sfname=workdir+"temp_tsl2_seldate.nc"
        tsl_filled_l2.to_netcdf(sfname)
        sfname=workdir+"temp_tsl3_seldate.nc"
        tsl_filled_l3.to_netcdf(sfname)
        sfname=workdir+"temp_tsl4_seldate.nc"
        tsl_filled_l4.to_netcdf(sfname)
        
        cmip_file_IDs.append('tsl') #layer 1
        cmip_file_IDs.append('tsl2') #layer 2
        cmip_file_IDs.append('tsl3') #layer 3
        cmip_file_IDs.append('tsl4') #layer 4
        
        paramID_names.append('139')
        paramID_names.append('170')
        paramID_names.append('183')
        paramID_names.append('236')
        
        cmip_IDs.append('stl1')
        cmip_IDs.append('stl2')
        cmip_IDs.append('stl3')
        cmip_IDs.append('stl4')
        
        OIFS_IDs.append('stl1')
        OIFS_IDs.append('stl2')
        OIFS_IDs.append('stl3')
        OIFS_IDs.append('stl4')
        
    
    if "mrsos" in cmip_var_names_ICMGG:
        
        print("CMIP6 mrsos is used for all four soil layers")

        if not ERA5_source:
        
            mrsos_mod = slice_rg_rn['mrsos']/0.1/1300

        else:

            mrsos_mod = slice_rg_rn['mrsos']

        mrsos_filled = mrsos_mod.fillna(xr.DataArray(slice_IFS_suf['swvl1'].values,
                                                 dims=slice_rg_rn['mrsos'].dims,
                                                 coords=slice_rg_rn['mrsos'].coords))
        
        sfname=workdir+"temp_mrsos_seldate.nc"
        mrsos_filled.to_netcdf(sfname)
        
        cmip_file_IDs.append('mrsos') #layer 1
        cmip_file_IDs.append('mrsos') #layer 2
        cmip_file_IDs.append('mrsos') #layer 3
        cmip_file_IDs.append('mrsos') #layer 4
        
        paramID_names.append('39')
        paramID_names.append('40')
        paramID_names.append('41')
        paramID_names.append('42')
        
        cmip_IDs.append('mrsos')
        cmip_IDs.append('mrsos')
        cmip_IDs.append('mrsos')
        cmip_IDs.append('mrsos')
        
        OIFS_IDs.append('swvl1')
        OIFS_IDs.append('swvl2')
        OIFS_IDs.append('swvl3')
        OIFS_IDs.append('swvl4')
    
    else:
        
        print("ERA5 30-yr mean swvl1-4 are used")
        
        era5_sw=['swvl1','swvl2','swvl3','swvl4']
        
        fnames_sw = [f"{workdir}temp_swv1.nc",
                      f"{workdir}temp_swvl2.nc",
                      f"{workdir}temp_swvl3.nc",
                      f"{workdir}temp_swvl4.nc"]
        
        ds_soil = xr.open_dataset(f"{essential_files[13]}")
        
        
        ds_ERA5_clim = {}
        ds_ERA5_clim_interp={}
            
        for i,var in enumerate(era5_sw):
            ds_ERA5_clim[var] = ds_soil[var].sel(valid_time=ds_soil.valid_time.dt.month == int(date_mo)).squeeze()
                
            ds_ERA5_clim[var].to_netcdf(fnames_sw[i])
                
            ofile=workdir+"temp_cmip6_"+var+".nc"
                 
            subprocess.run(['bash', essential_scripts_ICMGG[11], fnames_sw[i], ofile, grid_type, in_HPC], check=True)
                
            ds_ERA5_clim_interp[var]=xr.open_dataset(ofile)
        
        swvl_filled=ds_ERA5_clim_interp[era5_sw[0]]
        swvl_filled_l2=ds_ERA5_clim_interp[era5_sw[1]]
        swvl_filled_l3=ds_ERA5_clim_interp[era5_sw[2]]
        swvl_filled_l4=ds_ERA5_clim_interp[era5_sw[3]]
        
        sfname=workdir+"temp_mrsos_seldate.nc"
        swvl_filled.to_netcdf(sfname)
        sfname=workdir+"temp_mrsos2_seldate.nc"
        swvl_filled_l2.to_netcdf(sfname)
        sfname=workdir+"temp_mrsos3_seldate.nc"
        swvl_filled_l3.to_netcdf(sfname)
        sfname=workdir+"temp_mrsos4_seldate.nc"
        swvl_filled_l4.to_netcdf(sfname)
        
        cmip_file_IDs.append('mrsos') #layer 1
        cmip_file_IDs.append('mrsos2') #layer 2
        cmip_file_IDs.append('mrsos3') #layer 3
        cmip_file_IDs.append('mrsos4') #layer 4
        
        paramID_names.append('39')
        paramID_names.append('40')
        paramID_names.append('41')
        paramID_names.append('42')
        
        cmip_IDs.append('swvl1')
        cmip_IDs.append('swvl2')
        cmip_IDs.append('swvl3')
        cmip_IDs.append('swvl4')
        
        OIFS_IDs.append('swvl1')
        OIFS_IDs.append('swvl2')
        OIFS_IDs.append('swvl3')
        OIFS_IDs.append('swvl4')
    
    
    #SNOW
    if "snw" in cmip_var_names_ICMGG:
        
        print("CMIP6 snw is used")
        
        snd_ifs=slice_IFS_suf['sd'].isel(level=0)
        snd_mod = slice_rg_rn['snw']
        snd_filled = snd_mod.fillna(0)
        
        cmip_IDs.append('snw')
    
    else:
        
        print("ERA5 30-yr mean sd is used")
        
        fname_snow = f"{workdir}temp_sd.nc"
        ds_snow = xr.open_dataset(f"{essential_files[14]}")
        
        ds_ERA5_snow = ds_snow['sd'].sel(valid_time=ds_snow.valid_time.dt.month == int(date_mo)).squeeze()
            
        ds_ERA5_snow.to_netcdf(fname_snow)
            
        ofile=workdir+"temp_cmip6_snw.nc"
             
        subprocess.run(['bash', essential_scripts_ICMGG[11], fname_snow, ofile, grid_type, in_HPC], check=True)
            
        ds_ERA5_interp_snow=xr.open_dataset(ofile)
        
        snd_filled=ds_ERA5_interp_snow['sd']
        
        cmip_IDs.append('sd')
        
    sfname=workdir+"temp_snw_seldate.nc"
    snd_filled.to_netcdf(sfname)
    
    cmip_file_IDs.append('snw')
    paramID_names.append('141')
    OIFS_IDs.append('sd')
        
        
    
    
    if "snw" in cmip_var_names_ICMGG:
        if "tsn" in cmip_var_names_ICMGG:
            
            print("CMIP6 tsn is used")
            
            tsn_ifs = slice_IFS_suf['tsn'].isel(level=0)
            tsn_mod = slice_rg_rn['tsn']
            
            tsn_filled = tsn_mod.fillna(xr.DataArray(slice_IFS_suf['tsn'].isel(level=0).values,
                                                     dims=tsn_mod.dims,
                                                     coords=tsn_mod.coords))
        else:
            
            print("ERA5 30-yr mean global mean tsn is used")
            
            nan_mask_cmip = xr.where(~np.isnan(snd_mod), True, False)
            zero_mask_cmip = snd_mod != 0
            nan_mask_cmip2 = nan_mask_cmip & zero_mask_cmip
            tsn_filled=xr.where(nan_mask_cmip2,254.3,273.15) #254.3 is 30-yr global mean
        
        
        cmip_IDs.append('tsn')
    
    else:
        if "tsn" not in cmip_var_names_ICMGG:
            
            print("ERA5 30-yr mean tsn is used")
            
            fname_snow = f"{workdir}temp_tsn.nc"
            ds_snow = xr.open_dataset(f"{essential_files[14]}")
            
            ds_ERA5_snow = ds_snow['tsn'].sel(valid_time=ds_snow.valid_time.dt.month == int(date_mo)).squeeze()
                
            ds_ERA5_snow.to_netcdf(fname_snow)
                
            ofile=workdir+"temp_cmip6_tsn.nc"
                 
            subprocess.run(['bash', essential_scripts_ICMGG[11], fname_snow, ofile, grid_type, in_HPC], check=True)
                
            ds_ERA5_interp_snow=xr.open_dataset(ofile)
            
            tsn_filled=ds_ERA5_interp_snow['tsn']
            
            cmip_IDs.append('tsn')
    
    sfname=workdir+"temp_tsn_seldate.nc"
    tsn_filled.to_netcdf(sfname)
    
    cmip_file_IDs.append('tsn')
    paramID_names.append('238')
    OIFS_IDs.append('tsn')
    
    
    
    
    """   NOTE   """
    #it is assumed that there is no albsn and snow density data from CMIP6,
    #so the ERA5 values will be used
    """ END NOTE """
    
    era5_snow=['asn','rsn']
    
    fnames_snow = [f"{workdir}temp_asn.nc",
                   f"{workdir}temp_rsn.nc"]
    
    print("ERA5 30-yr mean rsn and asn are used")
    
    ds_snow = xr.open_dataset(f"{essential_files[14]}")
    
    
    ds_ERA5_clim = {}
    ds_ERA5_clim_interp={}
        
    for i,var in enumerate(era5_snow):
        ds_ERA5_clim[var] = ds_snow[var].sel(valid_time=ds_snow.valid_time.dt.month == int(date_mo)).squeeze()
            
        ds_ERA5_clim[var].to_netcdf(fnames_snow[i])
            
        ofile=workdir+"temp_cmip6_"+var+".nc"
             
        subprocess.run(['bash', essential_scripts_ICMGG[11], fnames_snow[i], ofile, grid_type, in_HPC], check=True)
            
        ds_ERA5_clim_interp[var]=xr.open_dataset(ofile)
    
    asn_filled=ds_ERA5_clim_interp[era5_snow[0]]
    rsn_filled=ds_ERA5_clim_interp[era5_snow[1]]
    
        
    sfname=workdir+"temp_asn_seldate.nc"
    asn_filled.to_netcdf(sfname)
    
    cmip_file_IDs.append('asn')
    paramID_names.append('32')
    OIFS_IDs.append('asn')
    cmip_IDs.append('asn')
        
    sfname=workdir+"temp_rsn_seldate.nc"
    rsn_filled.to_netcdf(sfname)
    
    cmip_file_IDs.append('rsn')
    paramID_names.append('33')
    OIFS_IDs.append('rsn')
    cmip_IDs.append('rsn')
    
    
    #SKIN TEMPERATURE
    if "ts" in cmip_var_names_ICMGG:
        
        ts_sel = slice_rg_rn['ts']
        
        #save to netcdf
        sfname=workdir+"temp_ts_seldate.nc"
        ts_sel.to_netcdf(sfname)
        cmip_file_IDs.append('ts')
        paramID_names.append('235')
        cmip_IDs.append('ts')
        OIFS_IDs.append('skt')
            
    
    elif ("tsl" in cmip_var_names_ICMGG) and ("sitemptop" in cmip_var_names_ICMGG) and ("ts" not in cmip_var_names_ICMGG):
        
        
        skt_global = (
            slice_rg_rn['sitemptop']
            .combine_first(tos_Kel)
            .combine_first(slice_rg_rn['tsl']))
        
        skt_sorted = skt_global.sortby("latitude") #for interpolation lat needs to be reordered

        skt_filled = (
            skt_sorted
            .interpolate_na(dim="longitude", method="linear", fill_value="extrapolate")
            .interpolate_na(dim="latitude", method="linear", fill_value="extrapolate"))
        
        skt_filled = skt_filled.sortby("latitude", ascending=False)
        
        skt_filled.attrs.update({
            "standard_name": "surface_temperature",
            "long_name": "Surface Temperature",
            "units": "K"})
        
        skt_filled = skt_filled.rename("ts")
        
        sfname=workdir+"temp_ts_seldate.nc"
        skt_filled.to_netcdf(sfname)
        cmip_file_IDs.append('ts')
        paramID_names.append('235')
        cmip_IDs.append('ts')
        OIFS_IDs.append('skt')
        
    elif ("tsl" in cmip_var_names_ICMGG) and ("ts" not in cmip_var_names_ICMGG):
        
        
        skt_global = (
            tos_Kel
            .combine_first(slice_rg_rn['tsl']))
        
        skt_sorted = skt_global.sortby("latitude") #for interpolation lat needs to be reordered

        skt_filled = (
            skt_sorted
            .interpolate_na(dim="longitude", method="linear", fill_value="extrapolate")
            .interpolate_na(dim="latitude", method="linear", fill_value="extrapolate"))
        
        skt_filled = skt_filled.sortby("latitude", ascending=False)
        
        skt_filled.attrs.update({
            "standard_name": "surface_temperature",
            "long_name": "Surface Temperature",
            "units": "K"})
        
        skt_filled = skt_filled.rename("ts")
        
        sfname=workdir+"temp_ts_seldate.nc"
        skt_filled.to_netcdf(sfname)
        cmip_file_IDs.append('ts')
        paramID_names.append('235')
        cmip_IDs.append('ts')
        OIFS_IDs.append('skt')
        
        
    else:
        print("ERA5 30-yr mean skin temp is used")
        
        fname_era = f"{workdir}temp_skt.nc"
        ds_era = xr.open_dataset(f"{essential_files[17]}")
        
        ds_ERA5_extra = ds_era['skt'].sel(valid_time=ds_era.valid_time.dt.month == int(date_mo)).squeeze()
            
        ds_ERA5_extra.to_netcdf(fname_era)
            
        ofile=workdir+"temp_cmip6_skt.nc"
             
        subprocess.run(['bash', essential_scripts_ICMGG[11], fname_era, ofile, grid_type, in_HPC], check=True)
        
        ds_ERA5_interp_skt=xr.open_dataset(ofile)
        
        skt_ref=ds_ERA5_interp_skt['skt']
        
        cmip_IDs.append('skt')
    
        sfname=workdir+"temp_skt_seldate.nc"
        skt_ref.to_netcdf(sfname)
    
        cmip_file_IDs.append('skt')
        paramID_names.append('235')
        OIFS_IDs.append('skt')
        
        
    
    '''-----------------------------------Plotting module (check interpolation)---------------------------------------'''
    
    
    if check_surface_update:
    
        savepath=f"{workdir}plots/comp_SST.png"
        spl.compare_cartopy_surface(slice_IFS_suf['sst'],tos_filled,varname='SST',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_SST.png"
        spl.compare_cartopy_surface(slice_IFS_suf['ci'],siconca_ref,varname='sea ice content',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_ISTL1.png"
        spl.compare_cartopy_surface(slice_IFS_suf['istl1'],sitemptop_filled,varname='T ice',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_ISTL4.png"
        spl.compare_cartopy_surface(slice_IFS_suf['istl4'],sitemptop_filled_l4,varname='T ice',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_TSN.png"
        spl.compare_cartopy_surface(slice_IFS_suf['tsn'].isel(level=0),tsn_filled,varname='snow temp',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_SD.png"
        spl.compare_cartopy_surface(slice_IFS_suf['sd'].isel(level=0),snd_filled,varname='snow depth',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_ASN.png"
        spl.compare_cartopy_surface(slice_IFS_suf['asn'].isel(level=0),asn_filled,varname='snow albedo',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
        savepath=f"{workdir}plots/comp_RSN.png"
        spl.compare_cartopy_surface(slice_IFS_suf['rsn'].isel(level=0),rsn_filled,varname='snow density',dset_name1='IFS',dset_name2='CMIP6',c_levs=32,save_plot=savepath)
        
    
    
    '''----------------------------------- ERA5 climatologies --------------------------------------- '''
    
    #LAKE VARS
    era5_lake = ["lmlt","lmld","lblt","ltlt","lshf","lict","licd"]
    
    lake_params = ["228008","228009","228010","228011","228012","228013","228014"]
    
    era5_lake_fnames = [f"{workdir}temp_{era5_lake[0]}.nc",
                        f"{workdir}temp_{era5_lake[1]}.nc",
                        f"{workdir}temp_{era5_lake[2]}.nc",
                        f"{workdir}temp_{era5_lake[3]}.nc",
                        f"{workdir}temp_{era5_lake[4]}.nc",
                        f"{workdir}temp_{era5_lake[5]}.nc",
                        f"{workdir}temp_{era5_lake[6]}.nc"]
    
    
    ds_lake = xr.open_dataset(f"{essential_files[10]}")
   
    
    ds_ERA5_clim = {}
    lake_files = []
    
    for i,var in enumerate(era5_lake):
        ds_ERA5_clim[var] = ds_lake[var].sel(valid_time=ds_lake.valid_time.dt.month == int(date_mo)).squeeze()
        
        ds_ERA5_clim[var].to_netcdf(era5_lake_fnames[i])
        
        ofile=workdir+"temp_cmip6_"+var+".nc"
         
        subprocess.run(['bash', essential_scripts_ICMGG[11], era5_lake_fnames[i], ofile, grid_type, in_HPC], check=True)
        
        subprocess.run(['bash', essential_scripts_ICMGG[10], var, workdir, lake_params[i], in_HPC], check=True)
        
        lake_files.append(f"{workdir}temp_{var}_seldate_rg.grib")
    
    
    era5_supplements = []
    
    #CHARNOCK
    fname_era = f"{workdir}temp_chnk.nc"
    ds_era = xr.open_dataset(f"{essential_files[15]}")
    
    ds_ERA5_extra = ds_era['chnk'].sel(valid_time=ds_era.valid_time.dt.month == int(date_mo)).squeeze()
        
    ds_ERA5_extra.to_netcdf(fname_era)
        
    ofile=workdir+"temp_cmip6_chnk.nc"
         
    subprocess.run(['bash', essential_scripts_ICMGG[11], fname_era, ofile, grid_type, in_HPC], check=True)
    
    subprocess.run(['bash', essential_scripts_ICMGG[10], 'chnk', workdir, '148', in_HPC], check=True)
    
    era5_supplements.append(f"{workdir}temp_chnk_seldate_rg.grib")
    
    
    #SRC
    fname_era = f"{workdir}temp_src.nc"
    ds_era = xr.open_dataset(f"{essential_files[16]}")
    
    ds_ERA5_extra = ds_era['src'].sel(valid_time=ds_era.valid_time.dt.month == int(date_mo)).squeeze()
        
    ds_ERA5_extra.to_netcdf(fname_era)
        
    ofile=workdir+"temp_cmip6_src.nc"
         
    subprocess.run(['bash', essential_scripts_ICMGG[11], fname_era, ofile, grid_type, in_HPC], check=True)
    
    subprocess.run(['bash', essential_scripts_ICMGG[10], 'src', workdir, '198', in_HPC], check=True)
    
    era5_supplements.append(f"{workdir}temp_src_seldate_rg.grib")
    
    
    #LAI_HV and LAI_LV (leaf area index, high veg, low veg)
    ds_lai= xr.open_dataset(f"{essential_files[18]}")
    
    era5_lai_fnames = [f"{workdir}temp_lai_lv.nc",f"{workdir}temp_lai_hv.nc"]
    
    lai_params = ['66','67']
    
    
    for i,var in enumerate(['lai_lv','lai_hv']):
        ds_ERA5_clim[var] = ds_lai[var].sel(valid_time=ds_lai.valid_time.dt.month == int(date_mo)).squeeze()
        
        ds_ERA5_clim[var].to_netcdf(era5_lai_fnames[i])
        
        ofile=workdir+"temp_cmip6_"+var+".nc"
         
        subprocess.run(['bash', essential_scripts_ICMGG[11], era5_lai_fnames[i], ofile, grid_type, in_HPC], check=True)
        
        subprocess.run(['bash', essential_scripts_ICMGG[10], var, workdir, lai_params[i], in_HPC], check=True)
        
        era5_supplements.append(f"{workdir}temp_{var}_seldate_rg.grib")
    
    #ALBEDO
    fname_era = f"{workdir}temp_fal.nc"
    ds_era = xr.open_dataset(f"{essential_files[19]}")
    
    
    ds_ERA5_extra = (ds_era.sel(valid_time=ds_era.valid_time.dt.month == int(date_mo)).rename({'fal': 'al'})['al'].squeeze())
    
    ds_ERA5_extra.attrs = {
    "long_name": "Albedo (climatological)",
    "standard_name": "surface_albedo",
    "units": "1",
    "GRIB_paramId": 174,
    "GRIB_shortName": "al",
    "GRIB_name": "Albedo"}
        
    ds_ERA5_extra.to_netcdf(fname_era)
        
    ofile=workdir+"temp_cmip6_al.nc"
         
    subprocess.run(['bash', essential_scripts_ICMGG[11], fname_era, ofile, grid_type, in_HPC], check=True)
    
    subprocess.run(['bash', essential_scripts_ICMGG[10], 'al', workdir, '174', in_HPC], check=True)
    
    era5_supplements.append(f"{workdir}temp_al_seldate_rg.grib")
    
    
    
    '''-----------------------------------Conversion to GRIB format---------------------------------------'''
    
    
    print('--------------------------------')
    print('OIFS_IDs, paramID_names, cmip_file_IDs, cmip_IDs')
    for i in range(len(OIFS_IDs)):
        print(f'{OIFS_IDs[i]}, {paramID_names[i]}, {cmip_file_IDs[i]}, {cmip_IDs[i]}')
    
    print(OIFS_IDs)
    print(paramID_names)
    print(cmip_file_IDs)
    print(cmip_IDs)

    
    
    for var, ParamID, c_ID, var2 in zip(OIFS_IDs, paramID_names, cmip_file_IDs, cmip_IDs):
        fil=workdir+'temp_'+c_ID+'_seldate.nc'
        if os.path.exists(fil):
            subprocess.run(['bash', essential_scripts_ICMGG[6], var, var2, c_ID, ParamID, workdir, in_HPC], check=True)
        else:
            print(f"{fil} not found, continue")
            continue
        
    
    '''-----------------------------------Udate initial files---------------------------------------'''
    
    
    origfile=f"{IFS_path}ICMGG{expname}INIT"
    outfile=f"{IFS_path}ICMGG{expname}INITmod"
    
    grb_updt = [None] * len(paramID_names)
    
    i=-1
    for c_ID,var in zip(cmip_file_IDs,nc_str):
        i=i+1
        mod_grib=f"{workdir}temp_{var}_renamed.grib"
        if os.path.exists(mod_grib):
            grb_updt[i]=mod_grib
        else:
            grb_updt[i]=""
            
    
    
    
    print(grb_updt)
    print(lake_files)
    print(era5_supplements)
        
            
    
    opi.update_ICMGG(origfile,outfile,grb_updt[0],grb_updt[1],grb_updt[2],grb_updt[3],grb_updt[4],grb_updt[5],
                     f_istl1=grb_updt[6],f_istl2=grb_updt[7],f_istl3=grb_updt[8],f_istl4=grb_updt[9],
                     f_swvl1=grb_updt[10],f_swvl2=grb_updt[11],f_swvl3=grb_updt[12],f_swvl4=grb_updt[13],
                     f_sd=grb_updt[14],f_tsn=grb_updt[15],f_asn=grb_updt[16],f_rsn=grb_updt[17], f_skt=grb_updt[18],
                     f_lmlt=lake_files[0], f_lmld=lake_files[1], f_lblt=lake_files[2], f_ltlt=lake_files[3],
                     f_lshf=lake_files[4], f_lict=lake_files[5], f_licd=lake_files[6],
                     f_char=era5_supplements[0], f_src=era5_supplements[1],
                     f_lailv=era5_supplements[2], f_laihv=era5_supplements[3], f_al=era5_supplements[4])








'''-----------------------------------Clear memory---------------------------------------'''


for name in ["dsets_IFS_suf", "dsets_CMIP_suf", "dsets_CMIP_suf_tmp", "dsets_CMIP_suf_old", "dset_CL",
             "ds_ERA5_clim"]:
    if name in globals():
        for ds in globals()[name].values():
            try:
                ds.close()
            except Exception:
                pass

large_vars = [
    "dsets_IFS_suf", "dsets_CMIP_suf", "dsets_CMIP_suf_tmp", "dsets_CMIP_suf_old", "dset_CL",
    "slice_rg", "slice_rg_rn", "slice_IFS_suf",
    "nan_mask_cmip", "zero_mask_cmip", "nan_mask_cmip2", "nan_mask_ifs",
    "masked_asn_ifs_l1", "masked_rsn_ifs_l1", "asn_ifs_l1_mask", "rsn_ifs_l1_mask",
    "tsl_filled", "mrsos_mod", "mrsos_filled", "snd_ifs", "snd_mod", "snd_filled",
    "tsn_ifs", "tsn_mod", "tsn_filled", "tos_Kel", "tos_filled", "siconca_ref",
    "sitemtop_filled", "sitemtop_filled_l2", "stl1_da", "stl1_aligned","stl1_aligned_da",
    "tos_to_CL", "siconca_to_CL", "sel_siconca_for_CL", "sel_tos_for_CL", "ds_lake", "ds_ERA5_clim"
]
for var in large_vars:
    if var in globals():
        del globals()[var]

gc.collect()

