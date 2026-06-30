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
import subprocess
import xarray as xr
import numpy as np


"""  
+++++++++++++++++++++++++++++++
DO NOT CHANGE ANYTHING
+++++++++++++++++++++++++++++++
"""

config = {
    "workdir": "$input1/app/",
    "expname": "abzf",
    "IFS_path": "$input1/INPUT_GRIB/TL399/",
    "grid_type": "TL399",
    "cmip_path": "$input1/app/test/TEST1.0/r0i0p0f0/2100",
    "model": "TEST1.0",
    "variant_lab": "r0i0p0f0",
    "exp_cmip": "test",
    "date_yr": "2100",
    "date_mo": "01",
    "date_dd": "01",
    "date_hr": "12",
    "CL_length":"15",
    "if_CMIP_in_IFS_model_level":False,
    "use_linear_hybrid2hybrid":True,
    "ML_input":  "$input1/app/test/ECHAM_ml95_definitions.csv",
    "ML_input_sep": ";",
    "in_HPC":"$input2",
    "ERA5_source":False,
    "update_SH":True,
    "update_GG":True,
    "update_UA":True,
    "update_CL":True
}


if len(sys.argv) < 3:
    print("Usage: python3 CLIO_test.py <input1> <input2>")
    sys.exit(1)

input_path = sys.argv[1]
input2_path = sys.argv[2]

def replace_placeholders(value):
    if isinstance(value, str):
        value = value.replace("$input1", input_path)
        value = value.replace("$input2", input2_path)
    return value

for key in config:
    config[key] = replace_placeholders(config[key])

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


sel_date=date_yr+"-"+date_mo+"-"+date_dd+"T"+date_hr+":00:00"


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
print('CLIO run successfully, now testing...')
print('++++++++++++++++++++++++')

time.sleep(3)

subprocess.run(['bash', config["workdir"]+'test/mod_testing_fields.bash',config["expname"],  config["IFS_path"], config["in_HPC"]])


print('++++++++++++++++++++++++++++++++')


field_list=["vo","d","t","lnsp","q","sst","stl3","stl2","skt","licd","istl1","istl2","stl1","ci"]


original_fields={}
updated_fields={}

for var in field_list:

	updated_fields[var]=xr.open_dataset(f"temp_{var}_update.nc")
	if var=='ci' or var=='stl1':
	    original_fields[var]=xr.open_dataset(f"temp_ICMCL_{var}_GG.nc")
	else:
	    original_fields[var]=xr.open_dataset(f"temp_{var}_GG.nc")
	    

pass_count=0


"""+++++++++++++++++++++++++++++++++ TEST 1 ++++++++++++++++++++++++++++++++ """
test1_array=(original_fields['vo'].vo.isel(time=0).median(dim=('longitude','latitude'))==updated_fields['vo'].vo.isel(time=0).median(dim=('longitude','latitude'))).values

if test1_array.sum() == 0:
    print("Test 1 passed")
    pass_count+=1
else:
    print("Test 1 failed")


"""+++++++++++++++++++++++++++++++++ TEST 2 ++++++++++++++++++++++++++++++++ """
test2_array=(original_fields['d'].d.isel(time=0).median(dim=('longitude','latitude'))==updated_fields['d'].d.isel(time=0).median(dim=('longitude','latitude'))).values

if test2_array.sum() == 0:
    print("Test 2 passed")
    pass_count+=1
else:
    print("Test 2 failed")

"""+++++++++++++++++++++++++++++++++ TEST 3 ++++++++++++++++++++++++++++++++ """
test3_array=(np.abs(original_fields['t'].t.isel(time=0).mean(dim=('longitude','latitude'))-updated_fields['t'].t.isel(time=0).mean(dim=('longitude','latitude'))))


if (test3_array == 0).any():
    print("Test 3 failed")
else:
    print("Test 3 passed")
    pass_count+=1



"""+++++++++++++++++++++++++++++++++ TEST 4 ++++++++++++++++++++++++++++++++ """
test4_array=(updated_fields['lnsp'].lnsp.isel(time=0).mean(dim=('longitude'))/original_fields['lnsp'].lnsp.isel(time=0).mean(dim=('longitude')))


if ((test4_array < 0.9) | (test4_array > 1.1)).any():
    print("Test 4 failed")
else:
    print("Test 4 passed")
    pass_count+= 1



"""+++++++++++++++++++++++++++++++++ TEST 5 ++++++++++++++++++++++++++++++++ """
test5_array=updated_fields['q'].q.isel(time=0).median(dim=('longitude','latitude'))

if (np.round(test5_array,decimals=3) == 10.0).all():
    print("Test 5 passed")
    pass_count+=1
else:
    print("Test 5 failed")



"""+++++++++++++++++++++++++++++++++ TEST 6 ++++++++++++++++++++++++++++++++ """
test6_subset=updated_fields['sst'].sst.isel(time=0)


lat_min=-60
lat_max=25
lon_min=180
lon_max=190

if test6_subset.latitude[0].values < test6_subset.latitude[-1].values:

    test6_array=test6_subset.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max))

else:

    test6_array=test6_subset.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max))

if (np.round(test6_array-273.15) == 25.0).all():
    print("Test 6 passed")
    pass_count += 1
else:
    print("Test 6 failed")



"""+++++++++++++++++++++++++++++++++ TEST 7 ++++++++++++++++++++++++++++++++ """

lat_min=50
lat_max=60
lon_min=30
lon_max=50

test7_orig_l2=original_fields['stl2'].stl2.isel(time=0)
test7_orig_l3=original_fields['stl3'].stl3.isel(time=0)

test7_updt_l2=updated_fields['stl2'].stl2.isel(time=0)
test7_updt_l3=updated_fields['stl3'].stl3.isel(time=0)



if test7_orig_l2.latitude[0].values < test7_orig_l2.latitude[-1].values:

    test7_orig_l2_subset=test7_orig_l2.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()
    test7_orig_l3_subset=test7_orig_l3.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()

    test7_updt_l2_subset=test7_updt_l2.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()
    test7_updt_l3_subset=test7_updt_l3.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()

else:

    test7_orig_l2_subset=test7_orig_l2.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()
    test7_orig_l3_subset=test7_orig_l3.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()

    test7_updt_l2_subset=test7_updt_l2.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()
    test7_updt_l3_subset=test7_updt_l3.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()


if (test7_orig_l2_subset != test7_updt_l2_subset) & (test7_orig_l3_subset != test7_updt_l3_subset):
    if test7_updt_l2_subset==test7_updt_l3_subset:
        print("Test 7 passed")
        pass_count += 1
    else:
        print("Test 7 failed")
else:
    print("Test 7 failed")


"""+++++++++++++++++++++++++++++++++ TEST 8 ++++++++++++++++++++++++++++++++ """

#land-sea mask
fname_lsm="temp_lsm_GG.nc"
ds_lsm=xr.open_dataset(fname_lsm)	   
ocean_mask=ds_lsm.lsm.isel(time=0)==0
land_mask=ds_lsm.lsm.isel(time=0)==1

test8_array_1=np.round(np.nanmedian(updated_fields['skt'].skt.isel(time=0).where(ocean_mask).values)-273.15)
test8_array_2=np.nanmedian(updated_fields['skt'].skt.isel(time=0).where(land_mask).values)


if (test8_array_1==25.0) & (test8_array_2==280.0):
    print("Test 8 passed")
    pass_count += 1
else:
    print("Test 8 failed")


"""+++++++++++++++++++++++++++++++++ TEST 9 ++++++++++++++++++++++++++++++++ """
test9_array=(updated_fields['licd'].licd.isel(time=0).mean(skipna=True)==original_fields['licd'].licd.isel(time=0).mean(skipna=True))

if test9_array.values==False:
    print("Test 9 passed")
    pass_count+= 1
else:
    print("Test 9 failed")




"""+++++++++++++++++++++++++++++++++ TEST 10 ++++++++++++++++++++++++++++++++ """


lat_min=80
lat_max=90
lon_min=0
lon_max=170

test10_orig_l1=original_fields['istl1'].istl1.isel(time=0)
test10_orig_l2=original_fields['istl2'].istl2.isel(time=0)

test10_updt_l1=updated_fields['istl1'].istl1.isel(time=0)
test10_updt_l2=updated_fields['istl2'].istl2.isel(time=0)


if test10_orig_l1.latitude[0].values < test10_orig_l1.latitude[-1].values:

    test10_orig_l1_subset=test10_orig_l1.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()
    test10_orig_l2_subset=test10_orig_l2.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()

    test10_updt_l1_subset=test10_updt_l1.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()
    test10_updt_l2_subset=test10_updt_l2.sel(latitude=slice(lat_min,lat_max),longitude=slice(lon_min,lon_max)).median()

else:

    test10_orig_l1_subset=test10_orig_l1.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()
    test10_orig_l2_subset=test10_orig_l2.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()

    test10_updt_l1_subset=test10_updt_l1.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()
    test10_updt_l2_subset=test10_updt_l2.sel(latitude=slice(lat_max,lat_min),longitude=slice(lon_min,lon_max)).median()

if (test10_orig_l1_subset != test10_updt_l1_subset) & (test10_orig_l2_subset != test10_updt_l2_subset):
    if test10_updt_l1_subset!=test10_updt_l2_subset:
        print("Test 10 passed")
        pass_count += 1
    else:
        print("Test 10 failed")

else:
    print("Test 10 failed")


"""+++++++++++++++++++++++++++++++++ TEST 11 ++++++++++++++++++++++++++++++++ """


ref = updated_fields['stl1'].stl1.isel(time=0)

if ((original_fields['stl1'].stl1.isel(time=0).mean(dim='longitude') != updated_fields['stl1'].stl1.isel(time=0).mean(dim='longitude'))).all():
    if (updated_fields['stl1'].stl1 == ref).all():
        print("Test 11 passed")
        pass_count += 1
    else:
        print("Test 11 failed")
else:
    print("Test 11 failed")


"""+++++++++++++++++++++++++++++++++ TEST 12 ++++++++++++++++++++++++++++++++ """


ref = updated_fields['ci'].siconc.isel(time=0)

if ((original_fields['ci'].siconc.isel(time=0).mean(dim='longitude') != updated_fields['ci'].siconc.isel(time=0).mean(dim='longitude'))).all():
    if (updated_fields['ci'].siconc == ref).all():
        print("Test 12 passed")
        pass_count += 1
    else:
        print("Test 12 failed")
else:
    print("Test 12 failed")




"""+++++++++++++++++++++++++++++++++ TEST 13 ++++++++++++++++++++++++++++++++ """
if np.isnan(updated_fields['d'].d.isel(time=0)).any():
    print("Test 13 failed")
else:
    print("Test 13 passed")
    pass_count += 1


"""+++++++++++++++++++++++++++++++++ TEST 14 ++++++++++++++++++++++++++++++++ """
if np.isnan(updated_fields['vo'].vo.isel(time=0)).any():
    print("Test 14 failed")
else:
    print("Test 14 passed")
    pass_count += 1


"""+++++++++++++++++++++++++++++++++ TEST 15 ++++++++++++++++++++++++++++++++ """
if np.isnan(updated_fields['t'].t.isel(time=0)).any():
    print("Test 15 failed")
else:
    print("Test 15 passed")
    pass_count += 1


"""+++++++++++++++++++++++++++++++++ TEST 16 ++++++++++++++++++++++++++++++++ """
if np.isnan(updated_fields['lnsp'].lnsp.isel(time=0)).any():
    print("Test 16 failed")
else:
    print("Test 16 passed")
    pass_count += 1



print(f"Tests passed: {pass_count} out of 16")
print('++++++++++++++++++++++++++++++++')
print('++++  CLIO testing finished ++++')
print('++++++++++++++++++++++++++++++++')



