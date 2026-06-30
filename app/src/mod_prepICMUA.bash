#!/bin/bash
set -e


rm -f target_grid.txt
var="$1"
paramID="$2"
workdir="$3"
input_file="$4"
in_CMIP6="$5"
in_HPC="$6"

if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"
fi



if [[ "$var" == "q" ]]; then
	if [ "$in_HPC" == "false" ]; then
	    $CLEAN_ENV cdo chname,hus,q -chcode,-1,133 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    $CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	 else
	    cdo -L chname,hus,q -chcode,-1,133 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    cdo griddes temp_q.grib > target_grid.txt
	    cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	 fi
	 
	

elif [[ "$var" == "clwc" ]]; then

	if [[ "$in_CMIP6" == "True" ]]; then
	    		
	    	if [ "$in_HPC" == "false" ]; then
	    	
	    		$CLEAN_ENV cdo chname,clw,clwc -chcode,-1,246 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    		$CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    		$CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    		$CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    		grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	else
	    	        cdo -L chname,clw,clwc -chcode,-1,246 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    		cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    		cdo griddes temp_q.grib > target_grid.txt
	    		cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    		grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	
	    	fi
	
	elif [[ "$in_CMIP6" == "False" ]]; then
	
	        if [ "$in_HPC" == "false" ]; then
	
		    $CLEAN_ENV cdo chcode,-1,246 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    	    $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    	    $CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    	    $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    	    grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	else
	    	    cdo -L chcode,-1,246 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    	    cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    	    cdo griddes temp_q.grib > target_grid.txt
	    	    cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    	    grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	fi
	
	
	fi

elif [[ "$var" == "ciwc" ]]; then

	if [[ "$in_CMIP6" == "True" ]]; then
	
		if [ "$in_HPC" == "false" ]; then
	    	
	    		$CLEAN_ENV cdo chname,cli,ciwc -chcode,-1,247 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    		$CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    		$CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    		$CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    		grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	else
	    	        cdo -L chname,cli,ciwc -chcode,-1,247 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    		cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    		cdo griddes temp_q.grib > target_grid.txt
	    		cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    		grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	
	    	fi
	
	elif [[ "$in_CMIP6" == "False" ]]; then
	
	        if [ "$in_HPC" == "false" ]; then
		    $CLEAN_ENV cdo chcode,-1,247 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    	    $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    	    $CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    	    $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    	    grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	else
	    	    cdo -L chcode,-1,247 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    	    cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    	    cdo griddes temp_q.grib > target_grid.txt
	    	    cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    	    grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	    	fi
	    	
	
	fi

elif [[ "$var" == "cc" ]]; then

        if [ "$in_HPC" == "false" ]; then

	    $CLEAN_ENV cdo chcode,-1,248 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    $CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	else
	    cdo -L chcode,-1,248 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    cdo griddes temp_q.grib > target_grid.txt
	    cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	fi
	

elif [[ "$var" == "cswc" ]]; then

        if [ "$in_HPC" == "false" ]; then

	    $CLEAN_ENV cdo chcode,-1,76 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    $CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	else
	    cdo -L chcode,-1,76 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    cdo griddes temp_q.grib > target_grid.txt
	    cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	fi

	
elif [[ "$var" == "crwc" ]]; then

        if [ "$in_HPC" == "false" ]; then

	    $CLEAN_ENV cdo chcode,-1,75 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    $CLEAN_ENV cdo griddes temp_q.grib > target_grid.txt
	    $CLEAN_ENV cdo remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	else
	    cdo -L chcode,-1,75 "${input_file}" "${workdir}temp_${var}_chname.nc"
	    cdo -L -v -f grb -copy "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname.grib"
	    cdo griddes temp_q.grib > target_grid.txt
	    cdo -L remapbil,target_grid.txt "${workdir}temp_${var}_chname.grib" "${workdir}temp_${var}_rg.grib"
	    grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_rg.grib" "${workdir}temp_${var}_renamed.grib"
	fi
	
fi

rm ${workdir}temp_${var}_chname.nc
rm ${workdir}temp_${var}_chname.grib
rm ${workdir}temp_${var}_rg.grib


