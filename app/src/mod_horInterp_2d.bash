#!/bin/bash

set -e


input_file="$1"
output_file="$2"
grid_type="$3"
in_HPC="$4"

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
  TCo1279)

    if [ "$in_HPC" == "false" ]; then

      export CLEAN_ENV="env -i PATH=$PATH"
      $CLEAN_ENV cdo griddes temp_stl1_GG.nc >temp_TCo_grid.txt
    
    else

      cdo griddes temp_stl1_GG.nc >temp_TCo_grid.txt
    fi

    target_grid=temp_TCo_grid.txt
    ;;
  TCo319)
    if [ "$in_HPC" == "false" ]; then

      export CLEAN_ENV="env -i PATH=$PATH"
      $CLEAN_ENV cdo griddes temp_stl1_GG.nc >temp_TCo_grid.txt
    
    else

      cdo griddes temp_stl1_GG.nc >temp_TCo_grid.txt
    fi

    target_grid=temp_TCo_grid.txt
    ;;
  TCo639)
    if [ "$in_HPC" == "false" ]; then

      export CLEAN_ENV="env -i PATH=$PATH"
      $CLEAN_ENV cdo griddes temp_stl1_GG.nc >temp_TCo_grid.txt
    
    else

      cdo griddes temp_stl1_GG.nc >temp_TCo_grid.txt
    fi

    target_grid=temp_TCo_grid.txt
    ;;
  *)
    echo "Error: Unsupported grid type '$grid_type'."
    exit 1
    ;;
esac



if [ "$in_HPC" == "false" ]; then

   export CLEAN_ENV="env -i PATH=$PATH"
   $CLEAN_ENV cdo remapbil,"$target_grid" "$input_file" "$output_file"

else
   cdo remapbil,"$target_grid" "$input_file" "$output_file"
   
fi









