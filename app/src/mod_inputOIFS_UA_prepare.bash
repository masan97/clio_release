#!/bin/bash

set -x

exp="$1"  # First command-line argument
inipath="$2"
in_HPC="$3"

if [ "$in_HPC" == "false" ]; then
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

SH_vars=("q" "clwc" "ciwc" "cc" "cswc" "crwc")


for i in "${!SH_vars[@]}"; do
    var="${SH_vars[$i]}"
    echo "grib operations with: ${infile[1]} involving ${var}"
    
    grib_copy -w shortName=${var} "${infile[1]}" temp_${var}.grib
    
    if [ "$in_HPC" == "false" ]; then
       $CLEAN_ENV cdo setgridtype,regular temp_${var}.grib temp_${var}_r.grib
    else
       cdo setgridtype,regular temp_${var}.grib temp_${var}_r.grib
    fi
    

    grib_to_netcdf temp_${var}_r.grib -o temp_${var}_GG.nc
    
    rm temp_${var}_r.grib
   
done
	






