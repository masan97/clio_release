#!/bin/bash

set -e

exp="$1"  # First command-line argument
inipath="$2"
in_HPC="$3"


if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"
fi

# Define the input string arrays
ifs_inp_str1=("ICMGG" "ICMGG" "ICMSH" "ICMCL")
ifs_inp_str2=("INIT" "INIUA" "INIT" "INIT")

infile=()

for i in "${!ifs_inp_str1[@]}"; do
    infile[$i]="${inipath}${ifs_inp_str1[$i]}${exp}${ifs_inp_str2[$i]}"
    echo "filename: ${infile[$i]}"
done




var="q"

echo "grib operations with: ${infile[1]} involving ${var}"

grib_copy -w shortName=${var} "${infile[1]}" temp_${var}.grib

if [ "$in_HPC" == "false" ]; then
    $CLEAN_ENV cdo setgridtype,regular temp_${var}.grib temp_${var}_r.grib
else
    cdo setgridtype,regular temp_${var}.grib temp_${var}_r.grib
fi
        
grib_to_netcdf temp_${var}_r.grib -o temp_${var}_GG.nc


mapfile -t var_GG < temp_cmip_vars_extra.csv


for i in "${!var_GG[@]}"; do
    var_GG[$i]=$(echo "${var_GG[$i]}" | tr -d '\r' | xargs)
done


var_GG=("sst" "ci" "stl1" "stl2" "stl3" "stl4" "istl1" "istl2" "istl3" "istl4" "swvl1" "swvl2" "swvl3" "swvl4" "sd" "tsn" "asn" "rsn" "skt" "lsm")

var_CL=("stl1" "ci" "al" "lai_lv" "lai_hv")

for vr in "${var_GG[@]}"; do

    grib_copy -w shortName=$vr "${infile[0]}" temp_${vr}.grib
        
    if [ "$in_HPC" == "false" ]; then
        $CLEAN_ENV cdo setgridtype,regular temp_${vr}.grib temp_${vr}_r.grib
    else
        cdo setgridtype,regular temp_${vr}.grib temp_${vr}_r.grib
    fi
    grib_to_netcdf temp_${vr}_r.grib -o temp_${vr}_GG.nc
        
    rm temp_${vr}_r.grib
done


#ICMCL

for vr in "${var_CL[@]}"; do

    grib_copy -w shortName=$vr "${infile[3]}" temp_ICMCL_${vr}.grib
        
    if [ "$in_HPC" == "false" ]; then
        $CLEAN_ENV cdo setgridtype,regular temp_ICMCL_${vr}.grib temp_ICMCL_${vr}_r.grib
    else
        cdo setgridtype,regular temp_ICMCL_${vr}.grib temp_ICMCL_${vr}_r.grib
    fi       
    grib_to_netcdf temp_ICMCL_${vr}_r.grib -o temp_ICMCL_${vr}_GG.nc

done



rm temp_ICMCL_stl1_r.grib
rm temp_ICMCL_ci_r.grib



