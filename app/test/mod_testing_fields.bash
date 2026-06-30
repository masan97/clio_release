#!/bin/bash

set -x

exp="$1"  # First command-line argument
inipath="$2"
in_HPC="$3"

if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"
fi


# Define the input string arrays
ifs_inp_str1=("ICMGG" "ICMGG" "ICMSH" "ICMCL")
ifs_inp_str2=("INITmod" "INIUAmod" "INITmod" "INITmod")

infile=()

for i in "${!ifs_inp_str1[@]}"; do
    infile[$i]="${inipath}${ifs_inp_str1[$i]}${exp}${ifs_inp_str2[$i]}"
    echo "filename: ${infile[$i]}"
done

SH_vars=("vo" "d" "t" "lnsp")

var_GG=("sst" "stl2" "stl3" "skt" "licd" "istl1" "istl2")

var_CL=("stl1" "ci")

for vr in "${var_GG[@]}"; do

       grib_copy -w shortName=$vr "${infile[0]}" temp_${vr}.grib
       
       if [ "$in_HPC" == "false" ]; then
           $CLEAN_ENV cdo setgridtype,regular temp_${vr}.grib temp_${vr}_r.grib
       else
           cdo setgridtype,regular temp_${vr}.grib temp_${vr}_r.grib
       fi
       grib_to_netcdf temp_${vr}_r.grib -o temp_${vr}_update.nc
       
       rm temp_${vr}_r.grib
       rm temp_${vr}.grib
    
done


for vr in "${var_CL[@]}"; do

       grib_copy -w shortName=$vr "${infile[3]}" temp_${vr}.grib
       
       if [ "$in_HPC" == "false" ]; then
           $CLEAN_ENV cdo setgridtype,regular temp_${vr}.grib temp_${vr}_r.grib
       else
           cdo setgridtype,regular temp_${vr}.grib temp_${vr}_r.grib
       fi
       grib_to_netcdf temp_${vr}_r.grib -o temp_${vr}_update.nc
       
       rm temp_${vr}_r.grib
       rm temp_${vr}.grib
    
done


echo "grib operations with: ${infile[1]} involving q"
    
grib_copy -w shortName=q "${infile[1]}" temp_q.grib
    
if [ "$in_HPC" == "false" ]; then
   $CLEAN_ENV cdo setgridtype,regular temp_q.grib temp_q_r.grib
else
   cdo setgridtype,regular temp_q.grib temp_q_r.grib
fi
    

grib_to_netcdf temp_q_r.grib -o temp_q_update.nc
    
rm temp_q_r.grib
rm temp_q.grib


for i in "${!SH_vars[@]}"; do
    var="${SH_vars[$i]}"
    echo "grib operations with: ${infile[2]} involving ${var}"

    grib_copy -w shortName=${var} "${infile[2]}" temp_${var}.grib

   
    if [ "$in_HPC" == "false" ]; then
        $CLEAN_ENV cdo sp2gp,type=linear temp_${var}.grib temp_${var}_gp.grib
    else
        cdo sp2gp,type=linear temp_${var}.grib temp_${var}_gp.grib
    fi

    grib_to_netcdf temp_${var}_gp.grib -o temp_${var}_update.nc
    
    rm temp_${var}_gp.grib
    rm temp_${var}.grib
    
done


#licd original

grib_copy -w shortName=licd "${inipath}ICMGG${exp}INIT" temp_licd.grib

if [ "$in_HPC" == "false" ]; then
       $CLEAN_ENV cdo setgridtype,regular temp_licd.grib temp_licd_r.grib
else
       cdo setgridtype,regular temp_licd.grib temp_licd_r.grib
fi
grib_to_netcdf temp_licd_r.grib -o temp_licd_GG.nc
       
rm temp_licd_r.grib
rm temp_licd.grib


