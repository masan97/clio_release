#!/bin/bash
set -e


var="$1"
paramID="$2"
workdir="$3"
in_model_level="$4"
in_HPC="$5"

if [ "$in_HPC" == "false" ]; then
   export CLEAN_ENV="env -i PATH=$PATH"
fi

if [[ "$in_model_level" == "True" ]]; then


	if [[ "$var" == "ps" ]]; then
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",lnsp "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       $CLEAN_ENV cdo gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	       $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname_SP.nc" "${workdir}temp_${var}_seldate.grib"
	       grib_set -s paramId="$paramID" "${workdir}temp_${var}_seldate.grib" "${workdir}temp_${var}_renamed_SP.grib"
	    else
	       cdo -L chname,"$var",lnsp "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       cdo -L gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	       cdo -L -v -f grb -copy "${workdir}temp_${var}_chname_SP.nc" "${workdir}temp_${var}_seldate.grib"
	       grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_seldate.grib" "${workdir}temp_${var}_renamed_SP.grib"
	    fi
	    

	elif [[ "$var" == "ua" ]]; then
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",u -chcode,1,131 "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    else
	       cdo -L chname,"$var",u -chcode,1,131 "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    fi

	elif [[ "$var" == "va" ]]; then
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",v -chcode,1,132 "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    else
	       cdo -L chname,"$var",v -chcode,1,132 "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    fi

	else
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",t "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       $CLEAN_ENV cdo gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	    else
	       cdo -L chname,"$var",t "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       cdo -L gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	    fi
	  
	fi



fi



if [[ "$in_model_level" == "False" ]]; then
   
	
        if [[ "$var" == "ps" ]]; then
            if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",lnsp "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       $CLEAN_ENV cdo gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	       $CLEAN_ENV cdo -v -f grb -copy "${workdir}temp_${var}_chname_SP.nc" "${workdir}temp_${var}_seldate.grib"
	       grib_set -s paramId="$paramID" "${workdir}temp_${var}_seldate.grib" "${workdir}temp_${var}_renamed_SP.grib"
	    else
	       cdo -L chname,"$var",lnsp "${workdir}temp_${var}_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       cdo -L gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	       cdo -L -v -f grb -copy "${workdir}temp_${var}_chname_SP.nc" "${workdir}temp_${var}_seldate.grib"
	       grib_set -s centre=98,table2Version=128,paramId="$paramID" "${workdir}temp_${var}_seldate.grib" "${workdir}temp_${var}_renamed_SP.grib"
	    fi
	    
	    rm -f "${workdir}temp_${var}_chname.nc"
	    rm -f "${workdir}temp_${var}_chname_SP.nc"
	    

	elif [[ "$var" == "ua" ]]; then
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",u -chcode,1,131 "${workdir}temp_${var}_vertint_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    else
	       cdo -L chname,"$var",u -chcode,1,131 "${workdir}temp_${var}_vertint_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    fi

	elif [[ "$var" == "va" ]]; then
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",v -chcode,1,132 "${workdir}temp_${var}_vertint_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    else
	       cdo -L chname,"$var",v -chcode,1,132 "${workdir}temp_${var}_vertint_seldate.nc" "${workdir}temp_${var}_chname.nc"
	    fi

	else
	    if [ "$in_HPC" == "false" ]; then
	       $CLEAN_ENV cdo chname,"$var",t "${workdir}temp_${var}_vertint_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       $CLEAN_ENV cdo gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	    else
	       cdo -L chname,"$var",t "${workdir}temp_${var}_vertint_seldate.nc" "${workdir}temp_${var}_chname.nc"
	       cdo -L gp2sp,type=cubic "${workdir}temp_${var}_chname.nc" "${workdir}temp_${var}_chname_SP.nc"
	    fi
	    rm -f "${workdir}temp_${var}_chname.nc"
	    
	fi
   
	
fi


rm -f "${workdir}temp_${var}_seldate.grib"



