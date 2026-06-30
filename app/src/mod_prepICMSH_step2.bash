#!/bin/bash
set -e
set -x

workdir="$1"
in_HPC="$2"

if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"

   $CLEAN_ENV cdo merge "${workdir}temp_ua_chname.nc" "${workdir}temp_va_chname.nc" "${workdir}temp_uv_chname.nc"
   $CLEAN_ENV cdo uv2dv,linear "${workdir}temp_uv_chname.nc" "${workdir}temp_dv_renamed_SP.nc"

   $CLEAN_ENV cdo selcode,138 "${workdir}temp_dv_renamed_SP.nc" "${workdir}temp_vor_renamed_SP.nc"
   $CLEAN_ENV cdo selcode,155 "${workdir}temp_dv_renamed_SP.nc" "${workdir}temp_div_renamed_SP.nc"

else

   cdo -L merge "${workdir}temp_ua_chname.nc" "${workdir}temp_va_chname.nc" "${workdir}temp_uv_chname.nc"
   cdo -L uv2dv,linear "${workdir}temp_uv_chname.nc" "${workdir}temp_dv_renamed_SP.nc"

   cdo -L selcode,138 "${workdir}temp_dv_renamed_SP.nc" "${workdir}temp_vor_renamed_SP.nc"
   cdo -L selcode,155 "${workdir}temp_dv_renamed_SP.nc" "${workdir}temp_div_renamed_SP.nc"

fi



rm -f ${workdir}temp_uv_chname.nc
rm -f ${workdir}temp_dv_renamed_SP.nc
