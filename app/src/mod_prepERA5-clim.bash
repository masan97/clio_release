#!/bin/bash

set -e

var="$1"
workdir="$2"
paramID="$3"
in_HPC="$4"


if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"


   $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_cmip6_${var}.nc" "${workdir}temp_${var}_seldate.grib"
   $CLEAN_ENV cdo griddes temp_sst.grib > target_grid.txt
   $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_seldate.grib" "${workdir}temp_${var}_seldate_rg.grib"

else
   cdo -v -f grb -copy "${workdir}temp_cmip6_${var}.nc" "${workdir}temp_${var}_seldate-rawcopy.grib"
   grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_seldate-rawcopy.grib" "${workdir}temp_${var}_seldate.grib"
   cdo griddes temp_sst.grib > target_grid.txt
   cdo remapbil,target_grid.txt "${workdir}temp_${var}_seldate.grib" "${workdir}temp_${var}_seldate_rg.grib"
   rm "${workdir}temp_${var}_seldate-rawcopy.grib"
fi

rm "${workdir}temp_${var}_seldate.grib"

