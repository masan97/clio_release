#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: Sandor Istvan Maho


This script modifies initial conditions in file ICMGG*INIUA based on CMIP6 climate data

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
import cftime

#submodules

import mod_simple_plots as spl
import mod_outputOIFS as opi
import mod_vert_interpol as vip


import json
import importlib.util
import time


"""################################################ """
""" +++++++++++++ some specifics here +++++++++++++ """

check_interpolation = True #enable plotting for sanity check


""" +++++++++++++++++++++++++++++++++++++++++++++++ """
"""################################################ """ 


# Dynamically import shared list module (from temp .py file)
spec = importlib.util.spec_from_file_location("shared_lists", shared_list_module)
shared_lists = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared_lists)

# Access the lists
json_path_ICMUA = shared_lists.json_path3
cmip_var_names_ICMUA = shared_lists.cmip_vars_ICMUA
essential_scripts_ICMUA = shared_lists.essential_scripts3


print(json_path_ICMUA)
print(cmip_var_names_ICMUA)
print(essential_scripts_ICMUA[0])

# Load config
with open(json_path_ICMUA) as f:
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


subprocess.run(['bash', essential_scripts_ICMUA[7], expname, IFS_path, in_HPC])




nc_str =["q",
         "clwc",
         "ciwc",
         "cc",
         "cswc",
         "crwc"
         ]


OIFS_nc_files = []


for string in nc_str:
    OIFS_nc_files.append(workdir+f"temp_{string}_GG.nc")
    


dsets_IFS_UA = {}

for item,ncs in zip(OIFS_nc_files,nc_str):
    dsets_IFS_UA[ncs]=xr.open_dataset(item)
        



slice_IFS_UA = {}

for item,name in zip(nc_str,OIFS_nc_files):
    slice_IFS_UA[item] = dsets_IFS_UA[item][item].isel(time=0)
    

#detect number of model levels
if len(slice_IFS_UA['q'].level.values)==91:
    numLEV=91
elif len(slice_IFS_UA['q'].level.values)==137:
    numLEV=137


#Plotting
#spl.general_vertical_plot(slice_IFS_UA['q'].mean(dim="longitude"),c_levs=32,varname='specific humidity')
#spl.general_vertical_plot(slice_IFS_UA['cc'].mean(dim="longitude"),c_levs=32,varname='cloud cover')
#spl.general_vertical_plot(slice_IFS_UA['clwc'].mean(dim="longitude"),c_levs=32,varname='cloud liquid water content')
#spl.general_vertical_plot(slice_IFS_UA['ciwc'].mean(dim="longitude"),c_levs=32,varname='cloud ice water content')



'''-----------------------------------import CMIP6 data---------------------------------------'''




sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"


dsets_CMIP_UA = {}
dsets_CMIP_UA_old = {}


for var in cmip_var_names_ICMUA:
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
    
    subprocess.run(['bash', essential_scripts_ICMUA[1], matches[0], ofile, grid_type, sel_date, in_HPC], check=True)

    if ERA5_source:
        
        dsets_CMIP_UA_old[var] = xr.open_dataset(ofile)
        dsets_CMIP_UA[var]=fix_time_name_ERA5(dsets_CMIP_UA_old[var])
    
    else:
        dsets_CMIP_UA[var]=xr.open_dataset(ofile)
    



slice_rg = {}


for var in cmip_var_names_ICMUA:
    time0 = dsets_CMIP_UA[var][var].time.values[0]

    if isinstance(time0, cftime.datetime):
        dt = datetime.fromisoformat(sel_date)
        sel_date = type(time0)(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    slice_rg[var] = dsets_CMIP_UA[var].sel(time=sel_date, method='nearest')
   
    if 'plev' in slice_rg[var].dims:
       slice_rg[var]=slice_rg[var].rename({'plev': 'lev'})
    if 'level' in slice_rg[var].dims:
       slice_rg[var]=slice_rg[var].rename({'plev': 'lev'})
    if 'z' in slice_rg[var].dims:
       slice_rg[var]=slice_rg[var].rename({'plev': 'lev'})
    sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"
   


'''-----------------------------------Zero clw and/or cli fields if not included in CMIP6---------------------------------------'''


if 'clw' not in cmip_var_names_ICMUA:
    modded_clw = slice_IFS_UA['clwc']*0
if 'cli' not in cmip_var_names_ICMUA:
    modded_cli = slice_IFS_UA['ciwc']*0
if 'cc' not in cmip_var_names_ICMUA:
    modded_cc = slice_IFS_UA['cc']*0
if 'crwc' not in cmip_var_names_ICMUA:
    modded_crwc = slice_IFS_UA['crwc']*0
if 'cswc' not in cmip_var_names_ICMUA:
    modded_cswc = slice_IFS_UA['cswc']*0

'''-----------------------------------Assign vertical coordinate to match with IFS---------------------------------------'''



def copy_vert_coord(arr,mask_arr):
    field_new = arr.copy()
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
    
    
    target_levels = mask_arr["level"].values
    
    
    if field_new["level"].values[0] > field_new["level"].values[-1]:
        target_levels = target_levels[::-1]   #reverse order
    
    
    field_new = field_new.assign_coords(level=target_levels)
    
    # copy coordinate attributes
    field_new["level"].attrs = mask_arr["level"].attrs

    return field_new


def add_hybrid(arr):

    arr_mod = arr.rename({"level": "hybrid"})

    arr_mod = arr_mod.assign_coords(
        hybrid=arr_mod["hybrid"].assign_attrs(
            long_name="hybrid model level",
            units="1",
            positive="down",
            standard_name="atmosphere_hybrid_sigma_pressure_coordinate",
        )
    )

    return arr_mod



'''-----------------------------------save horizontally interpolated CMIP6 netcdf data---------------------------------------'''


modded_field_list = []
is_in_CMIP6 = []

for var in nc_str:
    if var=='q':
        is_in_CMIP6.append('True')
        
        if if_CMIP_in_IFS_model_level==True:
            sfname=workdir+"temp_hus_seldate.nc"
            q_field=copy_vert_coord(slice_rg['hus'].hus,dsets_IFS_UA['q'])
            q_field.to_netcdf(sfname)
            modded_field_list.append(sfname)
        else:
            sfname=workdir+"temp_hus_seldate.nc"
            slice_rg['hus'].to_netcdf(sfname)
            modded_field_list.append(workdir+"temp_hus_vertint_seldate.nc")
        
    elif var=='clwc':
        if 'clw' not in cmip_var_names_ICMUA:
            sfname=workdir+"temp_clw_seldate.nc"
            is_in_CMIP6.append('False')
            modded_field_list.append(sfname)
            modded_clw=add_hybrid(modded_clw)
            modded_clw.to_netcdf(sfname)
        else:
            is_in_CMIP6.append('True')
            
            if if_CMIP_in_IFS_model_level==True:
                sfname=workdir+"temp_clw_seldate.nc"
                clw_field=copy_vert_coord(slice_rg['clw'],dsets_IFS_UA['clwc'])
                clw_field.to_netcdf(sfname)
                modded_field_list.append(sfname)
            else:
                sfname=workdir+"temp_clw_seldate.nc"
                slice_rg['clw'].to_netcdf(sfname)
                modded_field_list.append(workdir+"temp_clw_vertint_seldate.nc")
               
            
    elif var=='ciwc':
        if 'cli' not in cmip_var_names_ICMUA:
            is_in_CMIP6.append('False')
            sfname=workdir+"temp_cli_seldate.nc"
            modded_field_list.append(sfname)
            modded_cli=add_hybrid(modded_cli)
            modded_cli.to_netcdf(sfname)
        else:
            is_in_CMIP6.append('True')
            
            if if_CMIP_in_IFS_model_level==True:
                sfname=workdir+"temp_cli_seldate.nc"
                cli_field=copy_vert_coord(slice_rg['cli'],dsets_IFS_UA['ciwc'])
                cli_field.to_netcdf(sfname)
                modded_field_list.append(sfname)
            else:
                print('cli interpol')
                sfname=workdir+"temp_cli_seldate.nc"
                slice_rg['cli'].to_netcdf(sfname)
                modded_field_list.append(workdir+"temp_cli_vertint_seldate.nc")
             
            
    elif var=='cc':
        if 'cc' not in cmip_var_names_ICMUA:
            is_in_CMIP6.append('False')
            sfname=workdir+"temp_cc_seldate.nc"
            modded_field_list.append(sfname)
            modded_cc=add_hybrid(modded_cc)
            modded_cc.to_netcdf(sfname)
        else:
            is_in_CMIP6.append('True')
            
            if if_CMIP_in_IFS_model_level==True:
                sfname=workdir+"temp_cc_seldate.nc"
                cc_field=copy_vert_coord(slice_rg['cc'],dsets_IFS_UA['cc'])
                cc_field.to_netcdf(sfname)
                modded_field_list.append(sfname)
            else:
                sfname=workdir+"temp_cc_seldate.nc"
                slice_rg['cc'].to_netcdf(sfname)
                modded_field_list.append(workdir+"temp_cc_vertint_seldate.nc")
            
    elif var=='cswc':
        if 'cswc' not in cmip_var_names_ICMUA:
            is_in_CMIP6.append('False')
            sfname=workdir+"temp_cswc_seldate.nc"
            modded_field_list.append(sfname)
            modded_cswc=add_hybrid(modded_cswc)
            modded_cswc.to_netcdf(sfname)
        else:
            is_in_CMIP6.append('True')
            
            if if_CMIP_in_IFS_model_level==True:
                sfname=workdir+"temp_cswc_seldate.nc"
                cswc_field=copy_vert_coord(slice_rg['cswc'],dsets_IFS_UA['cswc'])
                cswc_field.to_netcdf(sfname)
                modded_field_list.append(sfname)
            
            else:
                sfname=workdir+"temp_cswc_seldate.nc"
                slice_rg['cswc'].to_netcdf(sfname)
                modded_field_list.append(workdir+"temp_cswc_vertint_seldate.nc")
                
            
    elif var=='crwc':
        if 'crwc' not in cmip_var_names_ICMUA:
            is_in_CMIP6.append('False')
            sfname=workdir+"temp_crwc_seldate.nc"
            modded_field_list.append(sfname)
            modded_crwc=add_hybrid(modded_crwc)
            modded_crwc.to_netcdf(sfname)
        else:
            is_in_CMIP6.append('True')
            
            if if_CMIP_in_IFS_model_level==True:
                sfname=workdir+"temp_crwc_seldate.nc"
                crwc_field=copy_vert_coord(slice_rg['crwc'],dsets_IFS_UA['crwc'])
                crwc_field.to_netcdf(sfname)
                modded_field_list.append(sfname)
            else:
                sfname=workdir+"temp_crwc_seldate.nc"
                slice_rg['crwc'].to_netcdf(sfname)
                modded_field_list.append(workdir+"temp_crwc_vertint_seldate.nc")
                
            







'''-----------------------------------vertical interpolation module---------------------------------------'''


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
            
        
        for var in cmip_var_names_ICMUA:
                
                
            print(f"interpolate vertically (ml->ml):: {var}")
                
                
            filT = f"temp_{var}_seldate.nc"
            filP = "temp_ps_seldate_orig.nc"
            outf = f"temp_{var}_vertint_seldate.nc"
                
            ds_ps = xr.open_dataset(filP)
            ds_t = xr.open_dataset(filT)

            sel_t = ds_t[var]
            sel_ps = ds_ps['ps']
        
            sel_t_interpol=vip.ml2ml_vert_interpol(numLEV,ML_input,ML_input_sep,workdir,sel_t,sel_ps)

            sel_t_interpol[var] = sel_t_interpol[var].where(sel_t_interpol[var] >= 0, 0)
            
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
            
        
        for var in cmip_var_names_ICMUA:
              
                
                
            print(f"interpolate vertically (pl->ml):: {var}")
                
                
            filT = f"temp_{var}_seldate.nc"
            filP = "temp_ps_seldate_orig.nc"
            outf = f"temp_{var}_vertint_seldate.nc"
                
            ds_ps = xr.open_dataset(filP)
            ds_t = xr.open_dataset(filT)

            sel_t = ds_t[var]
            sel_ps = ds_ps['ps']
                
            sel_t_interpol=vip.pl2ml_vert_interpol(numLEV,workdir,sel_t,sel_ps,var)

            sel_t_interpol[var] = sel_t_interpol[var].where(sel_t_interpol[var] >= 0, 0)
            
            sel_t_interpol.to_netcdf(workdir+outf)
        
    
            
else:
    print('+++++++++++++++++++++++++++++++++++++++++')
    print('input CMIP in IFS standard model levels')
    print('vertical interpolation omitted')
    print('+++++++++++++++++++++++++++++++++++++++++')
    time.sleep(5)



'''-----------------------------------Plotting module (check interpolation)---------------------------------------'''


if check_interpolation:


    slice_IFS_to_comp = slice_IFS_UA["q"].mean(dim="longitude")  #adjust dimension names as needed
    if if_CMIP_in_IFS_model_level==False:
        ds_tint = xr.open_dataset(workdir+"temp_hus_vertint_seldate.nc")
        lon_dim = [d for d in ds_tint.dims if "lon" in d.lower()][0]
        slice_CMIPint_to_comp=ds_tint.hus.mean(dim=lon_dim)
    else:
        slice_CMIPint_to_comp=slice_rg['hus'].hus.mean(dim="lon")
    
    
    savepath=f"{workdir}plots/comp_hus.png"
    spl.compare_general_vertical(slice_IFS_to_comp,slice_CMIPint_to_comp,varname='q',dset_name1='IFS',dset_name2='CMIP6',unit="kg/kg",c_levs=32, save_plot=savepath)



    

'''-----------------------------------Conversion to GRIB format---------------------------------------'''




paramID_names = ['133',
                 '246',
                 '247',
                 '248',
                 '76',
                 '75'
                 ]
                
    
for var, ParamID, fil, if_CMIP in zip(nc_str, paramID_names, modded_field_list,is_in_CMIP6):
    print(f"{var}:{ParamID}:{fil}:{if_CMIP}")
    if os.path.exists(fil):
            subprocess.run(['bash', essential_scripts_ICMUA[8], var, ParamID, workdir, fil, if_CMIP, in_HPC], check=True)
    else:
        print(f"{fil} not found, abort")
        sys.exit(1)


'''-----------------------------------Update initial files---------------------------------------'''




origfile=f"{IFS_path}ICMGG{expname}INIUA"
outfile=f"{IFS_path}ICMGG{expname}INIUAmod"          


UA_for_update = []
for ID in nc_str:
    UA_for_update.append(workdir+f"temp_{ID}_renamed.grib")    

         
opi.update_ICMUA(origfile,
                 UA_for_update[0],
                 UA_for_update[1],
                 UA_for_update[2],
                 UA_for_update[3],
                 UA_for_update[4],
                 UA_for_update[5],
                 outfile)



            
