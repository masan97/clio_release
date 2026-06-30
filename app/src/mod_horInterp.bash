#!/bin/bash

set -e


input_file="$1"
output_file="$2"
grid_type="$3"
seldate="$4"
in_HPC="$5"

# Determine target grid from grid_type
case "$grid_type" in
  TL639)
    target_grid="N320"
    ;;
  TL1279)
    target_grid="N640"
    ;;
  TL255)
    target_grid="N128"
    ;;
  TL159)
    target_grid="N80"
    ;;
  TL399)
    target_grid="N200"
    ;;
  *)
    echo "Error: Unsupported grid type '$grid_type'."
    exit 1
    ;;
esac



if [ "$in_HPC" == "false" ]; then

   export CLEAN_ENV="env -i PATH=$PATH"
   #export CLEAN_ENV="env -i PATH=/usr/bin:/bin:/usr/local/bin:/usr/sbin:/usr/local/sbin"
   $CLEAN_ENV cdo seldate,"$seldate" "$input_file" tmp_seldate.nc
   $CLEAN_ENV cdo remapnn,"$target_grid" tmp_seldate.nc "$output_file"
   rm tmp_seldate.nc

else
   cdo seldate,"$seldate" "$input_file" tmp_seldate.nc
   cdo remapnn,"$target_grid" tmp_seldate.nc "$output_file"
   rm tmp_seldate.nc
fi









