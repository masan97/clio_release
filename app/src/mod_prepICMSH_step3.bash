#!/bin/bash
set -e
set -x

workdir="$1"
in_HPC="$2"

if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"
fi





if [ "$in_HPC" == "false" ]; then
   #t

   $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_ta_chname_SP.nc" "${workdir}temp_ta_chname_SP.grib"
   grib_set -s paramId=130 "${workdir}temp_ta_chname_SP.grib" "${workdir}temp_ta_renamed_SP.grib"


   #vor-div

   $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_vor_renamed_SP.nc" "${workdir}temp_vor_renamed_SP.grib"
   $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_div_renamed_SP.nc" "${workdir}temp_div_renamed_SP.grib"

   grib_set -s paramId=138 "${workdir}temp_vor_renamed_SP.grib" "${workdir}temp_vor_renamed2_SP.grib"
   grib_set -s paramId=155 "${workdir}temp_div_renamed_SP.grib" "${workdir}temp_div_renamed2_SP.grib"
else
   #t

   cdo -v -f grb -copy "${workdir}temp_ta_chname_SP.nc" "${workdir}temp_ta_chname_SP.grib"
   grib_set -s paramId=130 "${workdir}temp_ta_chname_SP.grib" "${workdir}temp_ta_renamed_SP.grib"


   #vor-div

   cdo -v -f grb -copy "${workdir}temp_vor_renamed_SP.nc" "${workdir}temp_vor_renamed_SP.grib"
   cdo -v -f grb -copy "${workdir}temp_div_renamed_SP.nc" "${workdir}temp_div_renamed_SP.grib"

   grib_set -s centre=98,table2Version=128,paramId=138 "${workdir}temp_vor_renamed_SP.grib" "${workdir}temp_vor_renamed2_SP.grib"
   grib_set -s centre=98,table2Version=128,paramId=155 "${workdir}temp_div_renamed_SP.grib" "${workdir}temp_div_renamed2_SP.grib"
	
fi


rm -f "${workdir}temp_${var}_chname_SP.nc"
rm -f "${workdir}temp_${var}_chname_SP.grib"

