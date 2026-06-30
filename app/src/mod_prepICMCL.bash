#!/bin/bash
set -e
set -x

var_cmip="$1"
var="$2"
workdir="$3"
paramID="$4"
in_HPC="$5"

if [ "$in_HPC" == "false" ]; then

   # Define a clean environment with necessary minimal paths
   #export CLEAN_ENV="env -i PATH=/usr/bin:/bin:/usr/local/bin:/usr/sbin:/usr/local/sbin"
   export CLEAN_ENV="env -i PATH=$PATH"

fi


if [ "$in_HPC" == "false" ]; then

   #this worked for GRIB edition 1
   $CLEAN_ENV cdo chname,"$var_cmip","$var" "${workdir}temp_${var_cmip}_to_CL.nc" "${workdir}temp_${var}_CL_chname.nc"
   $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_CL_chname.nc" "${workdir}temp_${var}_CL.grib"
   
   #this is the solution for edition 2
   #$CLEAN_ENV cdo chname,"$var_cmip","$var" "temp_${var_cmip}_to_CL.nc" "temp_${var}_CL_chname.nc"
   #$CLEAN_ENV cdo -f grb2 -setname,"$var" "temp_${var}_CL_chname.nc" "${workdir}temp_${var}_CL.grib"
   $CLEAN_ENV cdo griddes temp_sst.grib > target_grid.txt
   $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_CL.grib" "${workdir}tmp_CL_rg.grib"
   grib_set -s paramId="$paramID" "${workdir}tmp_CL_rg.grib" "${workdir}temp_${var}_renamed_CL.grib"

else

   cdo chname,"$var_cmip","$var" "${workdir}temp_${var_cmip}_to_CL.nc" "${workdir}temp_${var}_CL_chname.nc"
   cdo -v -f grb -copy "${workdir}temp_${var}_CL_chname.nc" "${workdir}temp_${var}_CL.grib"
   #cdo -f grb2 -setname,"$var" "${workdir}temp_${var_cmip}_to_CL.nc" "${workdir}temp_${var}_CL.grib"
   cdo griddes temp_sst.grib > target_grid.txt
   #cdo setmisstoc,0 "${workdir}temp_${var}_CL.grib" "${workdir}temp_${var}_CL_nomiss.grib"
   cdo remapbil,target_grid.txt "${workdir}temp_${var}_CL.grib" "${workdir}tmp_CL_rg.grib"
   grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}tmp_CL_rg.grib" "${workdir}temp_${var}_renamed_CL.grib"

fi


#rm "${workdir}temp_${var}_CL_chname.nc"
#rm "${workdir}temp_${var}_CL.grib"
#rm "${workdir}tmp_CL_rg.grib"
