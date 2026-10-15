#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: Sandor Istvan Maho


This is the CLIO launch script

"""


import os
import sys
import glob
import json
import runpy
import tempfile
import pathlib
import csv
import time


"""  
+++++++++++++++++++++++++++++++
CONFIG (specified by user)
+++++++++++++++++++++++++++++++
"""

config = {
    "workdir": "/path/to/your/CLIO/installation/",
    "expname": "abt3",
    "IFS_path": "/path/to/OpenIFS/initial/files/",
    "grid_type": "TL639",
    "cmip_path": "/path/to/CMIP6/data/",
    "model": "EC-Earth3",
    "variant_lab": "r1i1p1f1",
    "exp_cmip": "historical",
    "date_yr": "2008",
    "date_mo": "1",
    "date_dd": "9",
    "date_hr": "12",
    "CL_length":"15",
    "if_CMIP_in_IFS_model_level":False,
    "use_linear_hybrid2hybrid":False,
    "ML_input":  "/path/to/your/model/level/definitions",
    "ML_input_sep": ",",
    "in_HPC":"false",
    "ERA5_source":False,
    "update_SH":True,
    "update_GG":False,
    "update_UA":True,
    "update_CL":False
}



""" 
++++++++++++++++++++++++++
PC mode: in_HPC:'false'
++++++++++++++++++++++++++

Make sure you have CDO and ecCodes installed

Make sure you have set the CDO path in the bash scripts

Make sure you run the code in a conda virtual environment
with all the necessary packages

"""



# Save config to file

#add src/ directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

config_path = pathlib.Path(config["workdir"]) / "config.json"
config_path.parent.mkdir(parents=True, exist_ok=True)
with open(config_path, "w") as f:
    json.dump(config, f, indent=2)


globals().update(config)

'''  _______ main script ________ '''



essential_scripts=[workdir+"src/mod_inputOIFS_prepare.bash",
                   workdir+"src/mod_horInterp.bash",
                   workdir+"src/mod_prepICMSH_step1.bash",
                   workdir+"src/mod_prepICMSH_step2.bash",
                   workdir+"src/mod_prepICMSH_step3.bash",
                   workdir+"src/mod_inputOIFS_extra_prepare.bash",
                   workdir+"src/mod_prepICMGG.bash",
                   workdir+"src/mod_inputOIFS_UA_prepare.bash",
                   workdir+'src/mod_prepICMUA.bash',
                   workdir+'src/mod_prepICMCL.bash',
                   workdir+'src/mod_prepERA5-clim.bash',
                   workdir+'src/mod_horInterp_2d.bash',
                   workdir+"src/mod_prepICMSH_step1-TCO.bash",
                   workdir+"src/mod_simple_plots.py",
                   workdir+"src/mod_outputOIFS.py",
                   workdir+"src/mod_mainVARS.py",
                   workdir+'src/mod_extraVARS.py',
                   workdir+'src/mod_UpperAtmosVARS.py',
                   workdir+'src/mod_spectral_filter.py']

essential_files=[workdir+"aux/L91_model_levels.txt",
                 workdir+"aux/L137_model_levels.txt",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_F640_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_F320_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_F200_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_F128_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_F80_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_TCO319_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_TCO639_SP.nc",
                 workdir+"aux/lnsp_1981-2010_0UTC_ymonmean_TCO1279_SP.nc",
                 workdir+"aux/lake_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/sea_ice_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/stl_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/swvl_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/snow_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/charnock_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/src_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/skt_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/veg_1981-2010_ymonmean_ERA5.nc",
                 workdir+"aux/alb_1981-2010_ymonmean_ERA5.nc"]



for item in essential_scripts:
    os.chmod(item, 0o755)

# Check if the script exists
for item in essential_scripts:
    if not os.path.exists(item):
        print(f"Error: Script '{item}' not found.")
        sys.exit(1)  # Exit with error code 1

for item in essential_files:
    if not os.path.exists(item):
        print(f"Error: Script '{item}' not found.")
        sys.exit(1)  # Exit with error code 1


''' check CMIP6 files '''



#importing CMIP6 input data to datasets, each variable has its own dataset

cmip_var_names = ["ps",
                  "ta",
                  "ua",
                  "va",
                  "hus",
                  "tos",
                  "siconca",
                  "tsl",
                  "sitemptop",
                  "mrsos",
                  "snw",
                  "tsn",
                  "ts",
                  "clw",
                  "cli",
                  "cc",
                  "cswc",
                  "crwc"]

#up to (cli) the naming follows CMIP6, (cc,cswc,crwc) are only possible from ERA5 not from CMIP6 





no_finds=[]


for var in cmip_var_names[:6]:
    # Create the wildcard pattern
    pattern = f"{var}_*{model}_*{exp_cmip}_*{variant_lab}_*{date_yr}*.nc"
    # Full search path
    search_path = os.path.join(cmip_path, pattern)
    
    matches = glob.glob(search_path)
    
    if len(matches) != 1:
        print(f"Error: Expected exactly 1 match for {var}, but found {len(matches)}.")
        sys.exit(1)  # Or raise an error: raise RuntimeError(...)
    
    
    print(f"File exists for {var}: {matches[0]}")


for var in cmip_var_names[6:]:
    pattern = f"{var}_*{model}_*{exp_cmip}_*{variant_lab}_*{date_yr}*.nc"
    # Full search path
    search_path = os.path.join(cmip_path, pattern)
    
    matches = glob.glob(search_path)
    
    if len(matches) != 1:
        print(f"No file found for {var}")
        no_finds.append(var)
    else:
        print(f"File exists for {var}: {matches[0]}")


cmip_vars_exist=[item for item in cmip_var_names if item not in no_finds]

essential_cmip_vars=["ps","ta","ua","va","hus","tos"]

missing_vars = [var for var in essential_cmip_vars if var not in cmip_vars_exist]

if missing_vars:
    print(f"Error: Missing essential CMIP variables: {missing_vars}")
    sys.exit(1)

''' MOD vor,div,t,lnsp,q '''

json_path=workdir+'config.json'


# Save lists into a temporary Python file that submodule can import
with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp:
    temp.write(f"cmip_vars_ICMSH = {cmip_vars_exist[:4]}\n")
    temp.write(f"json_path1 = {repr(json_path)}\n")  # FIXED LINE
    temp.write(f"essential_scripts1 = {repr(essential_scripts)}\n")
    temp_path = temp.name


# Import this temp module from within mod_mainVARS.py
# Run the submodule




print('init END')




time.sleep(5)  # pauses execution for 5 seconds

if update_SH:
    namespace = runpy.run_path(config["workdir"] + "/src/mod_mainVARS.py", init_globals={"shared_list_module": temp_path})

    print('++++++++++++++++++++++++')
    print('mainVARS done!')
    print('++++++++++++++++++++++++')

else:
    print('Nothing to be done for SH file, move forward...')
    time.sleep(3)




''' MOD extra vars '''


# Save to CSV
with open(workdir+'temp_cmip_vars_extra.csv', 'w', newline='\n') as f:
    writer = csv.writer(f)
    for var in cmip_vars_exist[5:]:
        if ((var=='cli') or (var=='clw') or (var=='crwc') or (var=='cswc') or (var=='cc')):
            continue
        writer.writerow([var])


# Save lists into a temporary Python file that submodule can import
with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp:
    temp.write(f"cmip_vars_ICMGG = {cmip_vars_exist[5:]}\n")
    temp.write(f"json_path2 = {repr(json_path)}\n")  # FIXED LINE
    temp.write(f"essential_scripts2 = {repr(essential_scripts)}\n")
    temp.write(f"essential_files2 = {repr(essential_files)}\n")
    temp_path = temp.name


if update_GG or update_CL:
    namespace = runpy.run_path(config["workdir"] + "/src/mod_extraVARS.py", init_globals={"shared_list_module": temp_path})

    print('++++++++++++++++++++++++')
    print('extraVARS done!')
    print('++++++++++++++++++++++++')
    
else:
    print('Nothing to be done for GG and CL files, move forward...')
    time.sleep(3)



''' another one for ICMUA, if vars are not there fill with zeroes  '''

UA_vars=[]
for var in cmip_vars_exist:
    if var=="hus":
        UA_vars.append(var)
    elif var=="clw":
        UA_vars.append(var)
    elif var=="cli":
        UA_vars.append(var)
    elif var=="cc":
        UA_vars.append(var)
    elif var=="cswc":
        UA_vars.append(var)
    elif var=="crwc":
        UA_vars.append(var)


# Save lists into a temporary Python file that submodule can import
with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp:
    temp.write(f"cmip_vars_ICMUA = {UA_vars}\n")
    temp.write(f"json_path3 = {repr(json_path)}\n")  # FIXED LINE
    temp.write(f"essential_scripts3 = {repr(essential_scripts)}\n")
    temp_path = temp.name

if update_UA:
    namespace = runpy.run_path(config["workdir"] + "/src/mod_UpperAtmosVARS.py", init_globals={"shared_list_module": temp_path})

    print('++++++++++++++++++++++++')
    print('UA vars done!')
    print('++++++++++++++++++++++++')

else:
    

    print('++++++++++++++++++++++++')
    print('Nothing to be done for UA file')
    print('++++++++++++++++++++++++')
    


print('++++++++++++++++++++++++')
print('CLIO run successfully')
print('++++++++++++++++++++++++')