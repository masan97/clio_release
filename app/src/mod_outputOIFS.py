#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 11:50:54 2025

@author: sandorma
"""

import metview as mv
import os



def update_ICMSH(origfile,temp_t,temp_vor,temp_div,temp_ps,outfile):
    # Read original GRIB file
    '''
    input params
    
    origfile :   full paths for ICMSH file
    
    temp_t   : temperature grib file for the udate
    
    temp_vor : vorticity grib file for the update
    
    temp_div : divergence grib file for the update
    
    temp_ps  : log surface pressure grib file
    
    outfile  : full path for the modified ICMSH file
    
    
    '''
    
    if not os.path.exists(origfile):
        raise FileNotFoundError(f"Input file not found: {origfile}")
    
    for name in [temp_t,temp_vor,temp_div,temp_ps]:
        if not os.path.exists(name):
            raise FileNotFoundError(f"Input file not found: {name}")
    
    orig = mv.read(origfile)
    
    # Read update GRIB files (assumes only 1 field each)
    lnsp_new = mv.read(temp_ps)
    t_new = mv.read(temp_t)
    vor_new = mv.read(temp_vor)
    div_new = mv.read(temp_div)
    
    # Initialize updated list
    
    
    updated = []

    for i in range(int(mv.count(orig))):
        f = orig[i]
        shortname = mv.grib_get_string(f, "shortName")
    
        if shortname == "lnsp":
            new_f = find_matching_field_lnsp(f, lnsp_new)
        elif shortname == "t":
            new_f = find_matching_field(f, t_new)
        elif shortname == "vo":
            new_f = find_matching_field(f, vor_new)
        elif shortname == "d":
            new_f = find_matching_field(f, div_new)
        else:
            new_f = None
    
        if new_f is not None:
            f = new_f  # field with original metadata + new data
    
        updated.append(f)
        
    mv.write(outfile, updated)



def update_ICMGG(origfile,outfile,f_sst,f_ci,f_stl1="",f_stl2="",f_stl3="",f_stl4="",
                 f_istl1="",f_istl2="",f_istl3="",f_istl4="",
                 f_swvl1="",f_swvl2="",f_swvl3="",f_swvl4="",
                 f_sd="",f_tsn="",f_asn="", f_rsn="", f_skt="",
                 f_lmlt="", f_lmld="", f_lblt="", f_ltlt="", f_lshf="", f_lict="", f_licd="",
                 f_char="", f_src="", f_lailv="", f_laihv="", f_al=""):
    # Read original GRIB file
    '''
    input params
    
    origfile : full paths for ICMSH file
    
    outfile  : full path for the modified ICMSH file
    
    f_sst    : grib file with SST field
        
    f_ci     : grib file with sea ice content field
    
    f_stl..  : soil temperature grib files in different levels
    
    f_istl.. : ice temperature grib files in different levels
    
    f_swvl.. : soil moisture grib files in different levels
    
    f_sd     : snow depth grib file
    
    f_tsn     : temperature of snow grib file
    
    f_asn     : snow albedo grib file
    
    f_rsn     : snow density file
    
    f_skt    : skin temperature
    
    f_lmlt   : lake mix-layer temperature
    
    f_lmld   : lake mix-layer depth
    
    f_lblt   : lake bottom temperature
    
    f_ltlt   : lake total layer temperature
    
    f_lshf   : lake shape factor
    
    f_lict   : lake ice surface temperature
    
    f_licd   : lake ice total depth
    
    f_src =  : skin reservoir content
    
    f_char   : Charnock
    
    f_lailv  : leaf-eare index, low vegetation
    
    f_laihv  : leaf-area index, high vegetation
    
    f_al     : albedo
    
    '''
    
    orig = mv.read(origfile)
    
    sst_new = mv.read(f_sst)
    ci_new = mv.read(f_ci)
    
    var_list = []
    
    # Read update GRIB files (assumes only 1 field each)
    if f_stl1.strip() != "":
        stl1_new = mv.read(f_stl1)
        var_list.append("stl1")
    if f_stl2.strip() != "":
        stl2_new = mv.read(f_stl2)
        var_list.append("stl2")
    if f_stl3.strip() != "":
        stl3_new = mv.read(f_stl3)
        var_list.append("stl3")
    if f_stl4.strip() != "":
        stl4_new = mv.read(f_stl4)
        var_list.append("stl4")
    if f_istl1.strip() != "":
        istl1_new = mv.read(f_istl1)
        var_list.append("istl1")
    if f_istl2.strip() != "":
        istl2_new = mv.read(f_istl2)
        var_list.append("istl2")
    if f_istl3.strip() != "":
        istl3_new = mv.read(f_istl3)
        var_list.append("istl3")
    if f_istl4.strip() != "":
        istl4_new = mv.read(f_istl4)
        var_list.append("istl4")
    if f_swvl1.strip() != "":
        swvl1_new = mv.read(f_swvl1)
        var_list.append("swvl1")
    if f_swvl2.strip() != "":
        swvl2_new = mv.read(f_swvl2)
        var_list.append("swvl2")
    if f_swvl3.strip() != "":
        swvl3_new = mv.read(f_swvl3)
        var_list.append("swvl3")
    if f_swvl4.strip() != "":
        swvl4_new = mv.read(f_swvl4)
        var_list.append("swvl4")
    if f_sd.strip() != "":
        sd_new = mv.read(f_sd)
        var_list.append("sd")
    if f_tsn.strip() != "":
        tsn_new = mv.read(f_tsn)
        var_list.append("tsn")
    if f_asn.strip() != "":
        asn_new = mv.read(f_asn)
        var_list.append("asn")
    if f_rsn.strip() != "":
        rsn_new = mv.read(f_rsn)
        var_list.append("rsn")
    if f_skt.strip() != "":
        skt_new = mv.read(f_skt)
        var_list.append("skt")
    if f_lmlt.strip() != "":
        lmlt_new = mv.read(f_lmlt)
        var_list.append("lmlt")
    if f_lmld.strip() != "":
        lmld_new = mv.read(f_lmld)
        var_list.append("lmld")
    if f_lblt.strip() != "":
        lblt_new = mv.read(f_lblt)
        var_list.append("lblt")
    if f_ltlt.strip() != "":
        ltlt_new = mv.read(f_ltlt)
        var_list.append("ltlt")
    if f_lshf.strip() != "":
        lshf_new = mv.read(f_lshf)
        var_list.append("lshf")
    if f_lict.strip() != "":
        lict_new = mv.read(f_lict)
        var_list.append("lict")
    if f_licd.strip() != "":
        licd_new = mv.read(f_licd)
        var_list.append("licd")
    if f_char.strip() != "":
        chnk_new = mv.read(f_char)
        var_list.append("chnk")
    if f_src.strip() != "":
        src_new = mv.read(f_src)
        var_list.append("src")
    if f_lailv.strip() != "":
        lailv_new = mv.read(f_lailv)
        var_list.append("lai_lv")
    if f_laihv.strip() != "":
        laihv_new = mv.read(f_laihv)
        var_list.append("lai_hv")
    if f_al.strip() != "":
        al_new = mv.read(f_al)
        var_list.append("al")
    
    
    updated = []

    for i in range(int(mv.count(orig))):
        f = orig[i]
        shortname = mv.grib_get_string(f, "shortName")
        
    
        if shortname == "sst":
            new_f = find_matching_field(f, sst_new)
        elif shortname == "ci":
            new_f = find_matching_field(f, ci_new)
        elif shortname == "stl1" and "stl1" in var_list:
            new_f = find_matching_surface_field(f, stl1_new)
        elif shortname == "stl2" and "stl2" in var_list:
            new_f = find_matching_surface_field(f, stl2_new)
        elif shortname == "stl3" and "stl3" in var_list:
            new_f = find_matching_surface_field(f, stl3_new)
        elif shortname == "stl4" and "stl4" in var_list:
            new_f = find_matching_surface_field(f, stl4_new)
        elif shortname == "istl1" and "istl1" in var_list:
            new_f = find_matching_surface_field(f, istl1_new)
        elif shortname == "istl2" and "istl2" in var_list:
            new_f = find_matching_surface_field(f, istl2_new)
        elif shortname == "istl3" and "istl3" in var_list:
            new_f = find_matching_surface_field(f, istl3_new)
        elif shortname == "istl4" and "istl4" in var_list:
            new_f = find_matching_surface_field(f, istl4_new)
        elif shortname == "swvl1" and "swvl1" in var_list:
            new_f = find_matching_surface_field(f, swvl1_new)
        elif shortname == "swvl2" and "swvl2" in var_list:
            new_f = find_matching_surface_field(f, swvl2_new)
        elif shortname == "swvl3" and "swvl3" in var_list:
            new_f = find_matching_surface_field(f, swvl3_new)
        elif shortname == "swvl4" and "swvl4" in var_list:
            new_f = find_matching_surface_field(f, swvl4_new)
        elif shortname == "sd" and "sd" in var_list:
            new_f = find_matching_field_snow(f, sd_new)
        elif shortname == "tsn" and "tsn" in var_list:
            new_f = find_matching_field_snow(f, tsn_new)
        elif shortname == "asn" and "asn" in var_list:
            new_f = find_matching_field_snow(f, asn_new)
        elif shortname == "rsn" and "rsn" in var_list:
            new_f = find_matching_field_snow(f, rsn_new)
        elif shortname == "skt" and "skt" in var_list:
            new_f = find_matching_surface_field(f, skt_new)
        elif shortname == "lmlt" and "lmlt" in var_list:
            new_f = find_matching_surface_field(f, lmlt_new)
        elif shortname == "lmld" and "lmld" in var_list:
            new_f = find_matching_surface_field(f, lmld_new)
        elif shortname == "lblt" and "lblt" in var_list:
            new_f = find_matching_surface_field(f, lblt_new)
        elif shortname == "ltlt" and "ltlt" in var_list:
            new_f = find_matching_surface_field(f, ltlt_new)
        elif shortname == "lshf" and "lshf" in var_list:
            new_f = find_matching_surface_field(f, lshf_new)
        elif shortname == "lict" and "lict" in var_list:
            new_f = find_matching_surface_field(f, lict_new)
        elif shortname == "licd" and "licd" in var_list:
            new_f = find_matching_surface_field(f, licd_new)
        elif shortname == "chnk" and "chnk" in var_list:
            new_f = find_matching_surface_field(f, chnk_new)
        elif shortname == "src" and "src" in var_list:
            new_f = find_matching_surface_field(f, src_new)
        elif shortname == "lai_lv" and "lai_lv" in var_list:
            new_f = find_matching_surface_field(f, lailv_new)
        elif shortname == "lai_hv" and "lai_hv" in var_list:
            new_f = find_matching_surface_field(f, laihv_new)
        elif shortname == "al" and "al" in var_list:
            new_f = find_matching_surface_field(f, al_new)
        else:
            new_f = None
    
        if new_f is not None:
            f = new_f  # field with original metadata + new data
    
        updated.append(f)
    
    
    mv.write(outfile, updated)




def update_ICMUA(origfile,temp_q,temp_clwc,temp_ciwc,temp_cc,temp_cswc,temp_crwc,outfile):
    # Read original GRIB file
    '''
    input params
    
    origfile :   full paths for ICMSH file
    
    temp_q   : specific humidity grib file for the udate
    
    temp_clwc : cloud liquid water content grib file for the update
    
    temp_ciwc : cloud ice water content grib file for the update
    
    temp_cc  : cloud cover grib file
    
    temp_cswc : cloud snow water content grib file for the update
    
    temp_crwc : cloud rain water content grib file for the update
    
    outfile  : full path for the modified ICMSH file
    
    
    '''
    
    if not os.path.exists(origfile):
        raise FileNotFoundError(f"Input file not found: {origfile}")
    
    for name in [temp_q,temp_clwc,temp_ciwc,temp_cc,temp_cswc,temp_crwc]:
        if not os.path.exists(name):
            raise FileNotFoundError(f"Input file not found: {name}")
    
    orig = mv.read(origfile)
    
    # Read update GRIB files (assumes only 1 field each)
    q_new = mv.read(temp_q)
    clwc_new = mv.read(temp_clwc)
    ciwc_new = mv.read(temp_ciwc)
    cc_new = mv.read(temp_cc)
    crwc_new = mv.read(temp_crwc)
    cswc_new = mv.read(temp_cswc)
    
    # Initialize updated list
    
    
    updated = []

    for i in range(int(mv.count(orig))):
        f = orig[i]
        shortname = mv.grib_get_string(f, "shortName")
    
        if shortname == "q":
            new_f = find_matching_field(f, q_new)
        elif shortname == "clwc":
            new_f = find_matching_field(f, clwc_new)
        elif shortname == "ciwc":
            new_f = find_matching_field(f, ciwc_new)
        elif shortname == "cc":
            new_f = find_matching_field(f, cc_new)
        elif shortname == "crwc":
            new_f = find_matching_field(f, crwc_new)
        elif shortname == "cswc":
            new_f = find_matching_field(f, cswc_new)
        else:
            new_f = None
    
        if new_f is not None:
            f = new_f  # field with original metadata + new data
    
        updated.append(f)
        
    mv.write(outfile, updated)



def update_ICMCL(origfile,temp_ci,temp_stl1,temp_al,temp_lai_lv,temp_lai_hv,outfile):
    # Read original GRIB file
    '''
    input params
    
    origfile :   full paths for ICMSH file
    
    temp_ci   : sea ice content grib file for the udate
    
    temp_stl1 : soil temperature level_1 grib file for the update
    
    temp_al : albedo grib file for the update
    
    temp_lai_lv : leaf-area index, low vegetation grib file for the update
    
    temp_lai_hv : leaf-area index, high vegetation grib file for the update
    
    outfile  : full path for the modified ICMSH file
    
    
    '''
    
    if not os.path.exists(origfile):
        raise FileNotFoundError(f"Input file not found: {origfile}")
    
    for name in [temp_ci,temp_stl1]:
        if not os.path.exists(name):
            raise FileNotFoundError(f"Input file not found: {name}")
    
    orig = mv.read(origfile)
    
    # Read update GRIB files (assumes only 1 field each)
    ci_new = mv.read(temp_ci)
    stl1_new = mv.read(temp_stl1)
    al_new = mv.read(temp_al)
    lai_lv_new = mv.read(temp_lai_lv)
    lai_hv_new = mv.read(temp_lai_hv)
    
    
    # Initialize updated list
    
    
    updated = []

    for i in range(int(mv.count(orig))):
        f = orig[i]
        shortname = mv.grib_get_string(f, "shortName")
    
        if shortname == "ci":
            new_f = find_matching_CL_field(f, ci_new)
        elif shortname == "stl1":
            new_f = find_matching_CL_field(f, stl1_new)
        elif shortname == "al":
            new_f = find_matching_CL_field(f, al_new)
        elif shortname == "lai_lv":
            new_f = find_matching_CL_field(f, lai_lv_new)
        elif shortname == "lai_hv":
            new_f = find_matching_CL_field(f, lai_hv_new)
        else:
            new_f = None
    
        if new_f is not None:
            f = new_f  # field with original metadata + new data
    
        updated.append(f)
        
    mv.write(outfile, updated)







def find_matching_field(original_field, candidate_fields):
    shortname = mv.grib_get_string(original_field, "shortName")
    level = mv.grib_get_long(original_field, "level")

    for f in candidate_fields:
        if (mv.grib_get_string(f, "shortName") == shortname and
            mv.grib_get_long(f, "level") == level):
            # Extract values from replacement field
            new_values = mv.values(f)
            # Copy values into original field (preserving metadata)
            return mv.set_values(original_field, new_values)
    return None




def find_matching_field_snow(original_field, candidate_fields):
    shortname = mv.grib_get_string(original_field, "shortName")
    level = mv.grib_get_long(original_field, "level")

    for f in candidate_fields:
        if mv.grib_get_string(f, "shortName") != shortname:
            continue
        
        if (mv.grib_get_string(f, "shortName") == shortname and
            level==1):
    
            # Extract values from replacement field
            new_values = mv.values(f)
            # Copy values into original field (preserving metadata)
            return mv.set_values(original_field, new_values)
        else:
            continue
        
    return None


def find_matching_surface_field(original_field, candidate_fields):
    shortname = mv.grib_get_string(original_field, "shortName")
   

    for f in candidate_fields:
        if mv.grib_get_string(f, "shortName") != shortname:
            continue

        
        if shortname in ["stl1","stl2","stl3","stl4",
                         "istl1","istl2","istl3","istl4",
                         "swvl1","swvl2","swvl3","swvl4",
                         "sd","tsn","asn","rsn",
                         "lblt","licd","lict","lmld",
                         "lmlt","lshf","ltlt"]:
            
            # assume candidate matches regardless of level metadata
            new_values = mv.values(f)
            return mv.set_values(original_field, new_values)

        # Otherwise fall back to strict level matching
        level_orig = mv.grib_get_long(original_field, "level")
        level_new  = mv.grib_get_long(f, "level")
        if level_orig == level_new:
            new_values = mv.values(f)
            return mv.set_values(original_field, new_values)

    return None


def find_matching_CL_field(original_field, candidate_fields):
    shortname = mv.grib_get_string(original_field, "shortName")
    level = mv.grib_get_long(original_field, "level")
    dataDate = mv.grib_get_long(original_field, "dataDate")
    dataTime = mv.grib_get_long(original_field, "dataTime")

    for f in candidate_fields:
        if (
            mv.grib_get_string(f, "shortName") == shortname
            and mv.grib_get_long(f, "level") == level
            and mv.grib_get_long(f, "dataDate") == dataDate
            and mv.grib_get_long(f, "dataTime") == dataTime
        ):
            
            # Copy values into original field (preserve metadata)
            return mv.set_values(original_field, mv.values(f))
    return None


def find_matching_field_lnsp(original_field, candidate_fields):
    shortname = mv.grib_get_string(original_field, "shortName")
    level = mv.grib_get_long(original_field, "level")

    for f in candidate_fields:
        if mv.grib_get_string(f, "shortName") == shortname:
            if shortname == "lnsp":
                # Don't enforce level/typeOfLevel for lnsp
                new_values = mv.values(f)
                return mv.set_values(original_field, new_values)
            elif mv.grib_get_long(f, "level") == level:
                new_values = mv.values(f)
                return mv.set_values(original_field, new_values)
    return None