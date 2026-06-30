#!/bin/bash

set -x

exp="$1"  # First command-line argument
inipath="$2"
in_HPC="$3"

rm -f temp*
rm -f tmp*

if [ "$in_HPC" == "false" ]; then

   # Define a clean environment with necessary minimal paths
   export CLEAN_ENV="env -i PATH=$PATH"

fi



# Define the input string arrays
ifs_inp_str1=("ICMGG" "ICMGG" "ICMSH")
ifs_inp_str2=("INIT" "INIUA" "INIT")

infile=()

for i in "${!ifs_inp_str1[@]}"; do
    infile[$i]="${inipath}${ifs_inp_str1[$i]}${exp}${ifs_inp_str2[$i]}"
    echo "filename: ${infile[$i]}"
done

SH_vars=("lnsp" "t" "vo" "d")

for i in "${!SH_vars[@]}"; do
    var="${SH_vars[$i]}"
    echo "grib operations with: ${infile[2]} involving ${var}"

    grib_copy -w shortName=${var} "${infile[2]}" temp_${var}.grib

   
    if [ "$in_HPC" == "false" ]; then
        $CLEAN_ENV cdo sp2gp,type=linear temp_${var}.grib temp_${var}_gp.grib
    else
        cdo sp2gp,type=linear temp_${var}.grib temp_${var}_gp.grib
    fi

    grib_to_netcdf temp_${var}_gp.grib -o temp_${var}_GG.nc
    
    rm temp_${var}_gp.grib
done

# Merge & dv2uv steps
if [ "$in_HPC" == "false" ]; then
        $CLEAN_ENV cdo merge temp_d.grib temp_vo.grib temp_dv.grib
        $CLEAN_ENV cdo dv2uv,linear temp_dv.grib temp_uv.grib

else
        cdo merge temp_d.grib temp_vo.grib temp_dv.grib
        cdo dv2uv,linear temp_dv.grib temp_uv.grib
fi

# Adjust parameter names and convert to NetCDF
grib_set -w parameterName=131 -s shortName=u temp_uv.grib temp_u.grib
grib_set -w parameterName=132 -s shortName=v temp_uv.grib temp_v.grib

grib_to_netcdf temp_u.grib -o temp_u_GG.nc
grib_to_netcdf temp_v.grib -o temp_v_GG.nc


rm temp_dv.grib
rm temp_uv.grib
