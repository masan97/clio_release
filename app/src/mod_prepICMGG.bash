#!/bin/bash
set -e


var="$1"
var_cmip="$2"
cmip_name="$3"
paramID="$4"
workdir="$5"
in_HPC="$6"

if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"

   $CLEAN_ENV cdo chname,"$var_cmip","$var" "${workdir}temp_${cmip_name}_seldate.nc" "${workdir}temp_${var}_chname.nc"
   $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_seldate.grib"
   $CLEAN_ENV cdo griddes temp_sst.grib > target_grid.txt
   $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_seldate.grib" "${workdir}tmp_rg.grib"
   grib_set -s paramId="$paramID" "${workdir}tmp_rg.grib" "${workdir}temp_${var}_renamed.grib"

else
   cdo chname,"$var_cmip","$var" "${workdir}temp_${cmip_name}_seldate.nc" "${workdir}temp_${var}_chname.nc"
   cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_seldate.grib"
   cdo griddes temp_sst.grib > target_grid.txt
   cdo remapbil,target_grid.txt "${workdir}temp_${var}_seldate.grib" "${workdir}tmp_rg.grib"
   grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}tmp_rg.grib" "${workdir}temp_${var}_renamed.grib"
fi

rm "${workdir}temp_${var}_chname.nc"
rm "${workdir}temp_${var}_seldate.grib"
rm "${workdir}tmp_rg.grib"
