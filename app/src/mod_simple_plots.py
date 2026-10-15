#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 13:56:45 2025

@author: sandorma
"""

import matplotlib.pyplot as plt
import numpy as np

from cartopy.util import add_cyclic_point
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogLocator, ScalarFormatter



def wind_vertical_plot(arr,c_levs=32,varname='wind',save_plot=""):
    
    
    lat_name = None
    lev_name = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr.coords:
            lat_name = possible_lat
            break


    for possible_lev in ['lev', 'plev','level','hybrid']:
        if possible_lev in arr.coords:
            lev_name = possible_lev
            break

    if lat_name is None or lev_name is None:
        raise ValueError("Could not find valid latitude or level coordinates in DataArray.")

    
    plt.figure(figsize=(8, 6))
    vmax = np.nanmax(arr.values)
    vmin = np.nanmin(arr.values)
    if np.abs(vmin)<np.abs(vmax):
        levs = np.linspace(vmax*-1,vmax,c_levs)
    else:
        levs = np.linspace(vmin,vmin*-1,c_levs)
    
    cf = plt.contourf(arr[lat_name], arr[lev_name], arr, levels=levs, cmap='coolwarm')
    plt.gca().invert_yaxis()  # flip vertical axis
    
    plt.colorbar(cf, label="u wind (m/s)")
    plt.xlabel("Latitude")
    plt.ylabel("vertical level")
    plt.title(f"{varname} vs Latitude and Level")
    plt.tight_layout()
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    plt.show()


def general_vertical_plot(arr,c_levs=32,varname='n/a',save_plot=""):

    plt.figure(figsize=(8, 6))
    vmax = np.nanmax(arr.values)
    vmin = np.nanmin(arr.values)
    levs = np.linspace(vmin,vmax,c_levs)
    
    # Dynamically detect latitude and longitude keys
    lat_name = None
    lev_name = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr.coords:
            lat_name = possible_lat
            break


    for possible_lev in ['lev', 'plev','level','hybrid']:
        if possible_lev in arr.coords:
            lev_name = possible_lev
            break

    if lat_name is None or lev_name is None:
        raise ValueError("Could not find valid latitude or level coordinates in DataArray.")


    
    cf = plt.contourf(arr[lat_name], arr[lev_name], arr, levels=levs, cmap='coolwarm')
    plt.gca().invert_yaxis()  # flip vertical axis
    
    plt.colorbar(cf, label=f"{varname}")
    plt.xlabel("Latitude")
    plt.ylabel("vertical level")
    plt.title(f"{varname} vs Latitude and Level")
    plt.tight_layout()
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    plt.show()


def general_surface_plot(arr,c_levs=32,varname='n/a',save_plot=""):

    # Dynamically detect latitude and longitude keys
    lat_name = None
    lon_name = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr.coords:
            lat_name = possible_lat
            break

    for possible_lon in ['longitude', 'lon']:
        if possible_lon in arr.coords:
            lon_name = possible_lon
            break

    if lat_name is None or lon_name is None:
        raise ValueError("Could not find valid latitude or longitude coordinates in DataArray.")


    plt.figure(figsize=(8, 6))
    vmax = np.nanmax(arr.values)
    vmin = np.nanmin(arr.values)
    c_levs=32
    levs = np.linspace(vmin,vmax,c_levs)
    cf = plt.contourf(arr[lon_name], arr[lat_name], arr, levels=levs, cmap='coolwarm')
    plt.colorbar(cf, label=f"{varname}")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.tight_layout()
    
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    plt.show()

def cartopy_surface_plot(arr,c_levs=32,varname='n/a',unit='n/a',save_plot="",ylog=False):
    
    # Dynamically detect latitude and longitude keys
    lat_name = None
    lon_name = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr.coords:
            lat_name = possible_lat
            break

    for possible_lon in ['longitude', 'lon']:
        if possible_lon in arr.coords:
            lon_name = possible_lon
            break

    if lat_name is None or lon_name is None:
        raise ValueError("Could not find valid latitude or longitude coordinates in DataArray.")
        
    
    
    lon = arr[lon_name].values.astype(np.float64)
    # Replace with a perfectly uniform linspace
    lon_uniform = np.linspace(lon.min(), lon.max(), lon.size)

    data, lon = add_cyclic_point(arr.values, coord=lon_uniform)    
    #data, lon = add_cyclic_point(arr.values, coord=arr[lon_name].values)

    vmin = np.nanmin(data)
    vmax = np.nanmax(data)
    
    if ylog:
        levs=np.logspace(np.log10(vmin), np.log10(vmax), c_levs)
    else:
        levs = np.linspace(vmin, vmax, c_levs)
    
    # Create figure with PlateCarree projection
    fig = plt.figure(figsize=(10, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()  # Or set_extent([...]) to zoom
    
    # Filled contour plot
    if ylog:
        cf = ax.contourf(lon, arr[lat_name], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree(), norm=LogNorm(vmin=vmin, vmax=vmax))
    else:
        cf = ax.contourf(lon, arr[lat_name], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree())
        
    # Add features
    ax.coastlines()
    #ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.gridlines(draw_labels=True)
    
    # Add colorbar and labels
    cb = plt.colorbar(cf, orientation='horizontal', pad=0.05, aspect=50, label=f"{unit}")
    plt.title(f"{varname}")
    plt.tight_layout()
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    plt.show()


def cartopy_surface_plot_no_cycpoint(arr,c_levs=32,varname='n/a',unit='n/a',save_plot="",ylog=False):
    
    # Dynamically detect latitude and longitude keys
    lat_name = None
    lon_name = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr.coords:
            lat_name = possible_lat
            break

    for possible_lon in ['longitude', 'lon']:
        if possible_lon in arr.coords:
            lon_name = possible_lon
            break

    if lat_name is None or lon_name is None:
        raise ValueError("Could not find valid latitude or longitude coordinates in DataArray.")
        
    
    lon = arr[lon_name].values
    
    data = arr.values
    
    vmin = np.nanmin(data)
    vmax = np.nanmax(data)
    
    
    if ylog:
        if vmin <= 0:
            vmin = np.nanmin(data[data > 0])  # smallest positive value in data
        levs=np.logspace(np.log10(vmin), np.log10(vmax), c_levs)
    else:
        levs = np.linspace(vmin, vmax, c_levs)
    
    # Create figure with PlateCarree projection
    
    plt.close("all")
    
    fig = plt.figure(figsize=(10, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()  # Or set_extent([...]) to zoom
    
    # Filled contour plot
    if ylog:
        cf = ax.contourf(lon, arr[lat_name], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree(), norm=LogNorm(vmin=vmin, vmax=vmax))
    else:
        cf = ax.contourf(lon, arr[lat_name], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree())
    
    # Add features
    ax.coastlines()
    #ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.gridlines(draw_labels=True)
    
    # Add colorbar and labels
    
    cb = fig.colorbar(cf, ax=ax, orientation="horizontal",
                      pad=0.05, aspect=50, extend="both")

    cb.set_label(unit)

    if ylog:
        # manually force tick positions and labels
        ticks = np.logspace(np.log10(vmin), np.log10(vmax), 6)
        cb.set_ticks(ticks)
        cb.ax.set_xticklabels([f"{t:.1e}" for t in ticks])
        cb.ax.xaxis.set_major_formatter(ScalarFormatter())
        cb.ax.xaxis.get_major_formatter().set_scientific(False)

    plt.title(varname)
    plt.tight_layout()

    
    
    plt.title(f"{varname}")
    plt.tight_layout()
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    plt.show()


def compare_general_vertical(arr1,arr2,varname='var1',dset_name1='dset1',dset_name2='dset2',unit="",c_levs=32,save_plot=""):
    
    
    lat_name1 = None
    lev_name1 = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr1.coords:
            lat_name1 = possible_lat
            break


    for possible_lev in ['lev', 'plev','level', 'hybrid']:
        if possible_lev in arr1.coords:
            lev_name1 = possible_lev
            break

    if lat_name1 is None or lev_name1 is None:
        raise ValueError("Could not find valid latitude or level coordinates in DataArray.")
        
        
    lat_name2 = None
    lev_name2 = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr2.coords:
            lat_name2 = possible_lat
            break


    for possible_lev in ['lev', 'plev','level','hybrid']:
        if possible_lev in arr2.coords:
            lev_name2 = possible_lev
            break

    if lat_name2 is None or lev_name2 is None:
        raise ValueError("Could not find valid latitude or level coordinates in DataArray.")

    fig,ax = plt.subplots(1,2,figsize=(11, 6))
    #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)
    
    vmax = np.nanmax(arr1.values)
    vmin = np.nanmin(arr1.values)
    levs = np.linspace(vmin,vmax,c_levs)
    cf = ax[0].contourf(arr1[lat_name1], arr1[lev_name1][::-1], arr1.values[::-1, :], levels=levs, cmap='coolwarm', save_plot="")
    cb = plt.colorbar(cf, orientation='horizontal', ticks=levs)
    cb.set_label(label=unit)
    cb.ax.set_xticklabels(["{:.1E}".format(i) for i in levs])
    cb.ax.tick_params(rotation=45)
    ax[0].invert_yaxis()
    
    for label in cb.ax.xaxis.get_ticklabels()[1::2]:
            label.set_visible(False)
    
    ax[0].set_xlabel("Latitude")
    ax[0].set_ylabel("vertical level")
    ax[0].set_title(f"{varname} in {dset_name1}")
    
    vmax = np.nanmax(arr2.values)
    vmin = np.nanmin(arr2.values)
    if vmin!=vmax:
    	vmax = np.nanmax(arr2.values)
    	vmin = np.nanmin(arr2.values)
    	levs = np.linspace(vmin,vmax,c_levs)
    
    
    cf = ax[1].contourf(arr2[lat_name2], arr2[lev_name2][::-1], arr2.values[::-1, :], levels=levs, cmap='coolwarm')
    cb = plt.colorbar(cf, orientation='horizontal', ticks=levs)
    cb.set_label(label=unit)
    cb.ax.set_xticklabels(["{:.1E}".format(i) for i in levs])
    cb.ax.tick_params(rotation=45)
    ax[1].invert_yaxis()
    
    for label in cb.ax.xaxis.get_ticklabels()[1::2]:
            label.set_visible(False)
    
    ax[1].set_xlabel("Latitude")
    ax[1].set_ylabel("vertical level")
    ax[1].set_title(f"{varname} in {dset_name2}")
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    
    nan_count = np.isnan(np.array(arr1)).sum()
    print(f"Number of NaNs of {dset_name1}: {nan_count}/{np.array(arr1).size}")
    nan_count = np.isnan(np.array(arr2)).sum()
    print(f"Number of NaNs of {dset_name2}: {nan_count}/{np.array(arr2).size}")
    
    
    plt.show() 



def compare_wind_vertical(arr1,arr2,varname='var1',dset_name1='dset1',dset_name2='dset2',c_levs=32,save_plot=""):
    
    lat_name1 = None
    lev_name1 = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr1.coords:
            lat_name1 = possible_lat
            break


    for possible_lev in ['lev', 'plev','level', 'hybrid']:
        if possible_lev in arr1.coords:
            lev_name1 = possible_lev
            break

    if lat_name1 is None or lev_name1 is None:
        raise ValueError("Could not find valid latitude or level coordinates in DataArray.")
    
    lat_name2 = None
    lev_name2 = None

    for possible_lat in ['latitude', 'lat']:
        if possible_lat in arr2.coords:
            lat_name2 = possible_lat
            break


    for possible_lev in ['lev', 'plev','level','hybrid']:
        if possible_lev in arr2.coords:
            lev_name2 = possible_lev
            break

    if lat_name2 is None or lev_name2 is None:
        raise ValueError("Could not find valid latitude or level coordinates in DataArray.")


    fig,ax = plt.subplots(1,2,figsize=(11, 6))
    #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)
    
    vmax = np.nanmax(arr1.values)
    vmin = np.nanmin(arr2.values)
    if np.abs(vmin)<np.abs(vmax):
        levs = np.linspace(vmax*-1,vmax,c_levs)
    else:
        levs = np.linspace(vmin,vmin*-1,c_levs)
    cf = ax[0].contourf(arr1[lat_name1], arr1[lev_name1][::-1], arr1.values[::-1, :], levels=levs, cmap='coolwarm')
    cb = plt.colorbar(cf, orientation='horizontal', ticks=levs)
    cb.set_label(label="m/s")
    cb.ax.set_xticklabels(["{:.1f}".format(i) for i in levs])
    cb.ax.tick_params(rotation=45)
    ax[0].invert_yaxis()
    
    for label in cb.ax.xaxis.get_ticklabels()[1::2]:
            label.set_visible(False)
    
    ax[0].set_xlabel("Latitude")
    ax[0].set_ylabel("vertical level")
    ax[0].set_title(f"{varname} in {dset_name1}")
    
    
    vmax = np.nanmax(arr2.values)
    vmin = np.nanmin(arr2.values)
    cf = ax[1].contourf(arr2[lat_name2], arr2[lev_name2][::-1], arr2.values[::-1, :], levels=levs, cmap='coolwarm')
    cb = plt.colorbar(cf, orientation='horizontal', ticks=levs)
    cb.set_label(label="m/s")
    cb.ax.set_xticklabels(["{:.1f}".format(i) for i in levs])
    cb.ax.tick_params(rotation=45)
    ax[1].invert_yaxis()
    
    for label in cb.ax.xaxis.get_ticklabels()[1::2]:
            label.set_visible(False)
    
    ax[1].set_xlabel("Latitude")
    ax[1].set_ylabel("vertical level")
    ax[1].set_title(f"{varname} in {dset_name2}")
    
    
    # Save figure if path is provided
    if save_plot.strip() != "":
        plt.savefig(save_plot, bbox_inches='tight')
    
    nan_count = np.isnan(arr1).sum()
    print(f"Number of NaNs of {dset_name1}: {nan_count}")
    nan_count = np.isnan(arr2).sum()
    print(f"Number of NaNs of {dset_name2}: {nan_count}")
    
    
    plt.show() 




def compare_cartopy_surface(arr1,arr2,varname='var1',dset_name1='dset1',dset_name2='dset2',c_levs=32,TCO=False,save_plot=""):
    
    if TCO==False:
    
        lat_name1 = None
        lon_name1 = None

        for possible_lat in ['latitude', 'lat']:
            if possible_lat in arr1.coords:
                lat_name1 = possible_lat
                break


        for possible_lon in ['longitude', 'lon']:
            if possible_lon in arr1.coords:
                lon_name1 = possible_lon
                break

        if lat_name1 is None or lon_name1 is None:
            raise ValueError("Could not find valid latitude or level coordinates in DataArray.")
            
        
        lat_name2 = None
        lon_name2 = None

        for possible_lat in ['latitude', 'lat']:
            if possible_lat in arr2.coords:
                lat_name2 = possible_lat
                break


        for possible_lon in ['longitude', 'lon']:
            if possible_lon in arr2.coords:
                lon_name2 = possible_lon
                break

        if lat_name2 is None or lon_name2 is None:
            raise ValueError("Could not find valid latitude or level coordinates in DataArray.")
        

        fig, ax = plt.subplots(1, 2, figsize=(11, 6), subplot_kw={'projection': ccrs.PlateCarree()})

        #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)
        
        lon = arr1[lon_name1].values.astype(np.float64)
        
        data = arr1.values
        
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        levs = np.linspace(vmin, vmax, c_levs)
        

        
        
        # Filled contour plot
        cf = ax[0].contourf(lon, arr1[lat_name1], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree())
        
        # Add features
        ax[0].coastlines()
        #ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax[0].gridlines(draw_labels=True)
        ax[0].set_title(f"{varname} in {dset_name1}")
        
        # Add colorbar and labels
        cb = plt.colorbar(cf, orientation='horizontal', pad=0.05, aspect=50)
        
        
        
        lon = arr2[lon_name2].values.astype(np.float64)
        
        data = arr2.values
        
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        levs = np.linspace(vmin, vmax, c_levs)
        
        
        

        
        # Filled contour plot
        cf = ax[1].contourf(lon, arr2[lat_name2], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree())
        
        # Add features
        ax[1].coastlines()
        #ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax[1].gridlines(draw_labels=True)
        ax[1].set_title(f"{varname} in {dset_name2}")
        
        # Add colorbar and labels
        cb = plt.colorbar(cf, orientation='horizontal', pad=0.05, aspect=50)
        
        
        plt.tight_layout()
        
        # Save figure if path is provided
        if save_plot.strip() != "":
            plt.savefig(save_plot, bbox_inches='tight')
        
        plt.show()
    else:

        def tco319_coordinates(yvals, reduced_points):
            lats = []
            lons = []

            for lat, nlon in zip(yvals, reduced_points):
                lon = np.arange(nlon) * 360.0 / nlon

                lats.extend(np.full(nlon, lat))
                lons.extend(lon)

            return np.asarray(lats), np.asarray(lons)

        lat_name1 = None
        lon_name1 = None

        for possible_lat in ['latitude', 'lat']:
            if possible_lat in arr1.coords:
                lat_name1 = possible_lat
                break


        for possible_lon in ['longitude', 'lon']:
            if possible_lon in arr1.coords:
                lon_name1 = possible_lon
                break

        if lat_name1 is None or lon_name1 is None:
            raise ValueError("Could not find valid latitude or level coordinates in DataArray.")
            
        
        

        fig, ax = plt.subplots(1, 2, figsize=(11, 6), subplot_kw={'projection': ccrs.PlateCarree()})

        #plt.subplots_adjust(left=0.2,right=0.5,bottom=0.4,top=0.5)
        
        lon = arr1[lon_name1].values.astype(np.float64)
        
        data = arr1.values
        
        vmin = np.nanmin(data)
        vmax = np.nanmax(data)
        levs = np.linspace(vmin, vmax, c_levs)
        

        
        
        # Filled contour plot
        cf = ax[0].contourf(lon, arr1[lat_name1], data, levels=levs, cmap='coolwarm', transform=ccrs.PlateCarree())
        
        # Add features
        ax[0].coastlines()
        #ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax[0].gridlines(draw_labels=True)
        ax[0].set_title(f"{varname} in {dset_name1}")
        
        # Add colorbar and labels
        cb = plt.colorbar(cf, orientation='horizontal', pad=0.05, aspect=50)
        
        
        
        if "rgrid" in arr2.dims:
            # TCO/reduced Gaussian grid
            lat, lon = tco319_coordinates(yvals, reduced_points)

            data = arr.values

            cf = ax[1].scatter(
                lon,
                lat,
                c=data,
                s=1,
                cmap="coolwarm",
                transform=ccrs.PlateCarree()
            )
        
            # Add features
            ax[1].coastlines()
            #ax.add_feature(cfeature.BORDERS, linewidth=0.5)
            ax[1].gridlines(draw_labels=True)
            ax[1].set_title(f"{varname} in {dset_name2}")
            
            # Add colorbar and labels
            cb = plt.colorbar(cf, orientation='horizontal', pad=0.05, aspect=50)
            
            
            plt.tight_layout()
            
            # Save figure if path is provided
            if save_plot.strip() != "":
                plt.savefig(save_plot, bbox_inches='tight')
            
            plt.show()
        
