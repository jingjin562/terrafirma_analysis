#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 11:21:40 2026

@author: jingjin
"""
import netCDF4 as nc
import numpy as np
import os
import os.path as op
import terrafirma_analysis
from terrafirma_analysis.io_core import create_dimensions_time, create_variables_1d_timeseries
from terrafirma_analysis.nemo_diaptr import *
from terrafirma_analysis.io_core import create_dimensions_3d, create_variables_3d

_GEODEF = {
    'AMOC_265N':    228,                 # lat 26.5 N
    'AMOC_345S':    134,                 # lat 34.5 S
    'lower_cell':   139,                 # lat 30 S
    'SMOC':         105,                 # lat 55 S
    'Equator':      186,                 # lat 0
    'DrakePassage': (219, 79, 107),      # lon, lat1, lat2
}

def geodef_CONSTANT(geodef):
    try:
        return _GEODEF[geodef]
    except KeyError:
        raise ValueError(
            f"unknown geodef {geodef!r}; "
            f"expected one of {list(_GEODEF)}"
        )

def AMOC_strength_timeseries(suite_id, file_dir):
    # --- The maxium streamfunction at 26.5 N
    print('AMOC strength is being calculating')
    AMOC = read_AMOC_mean(suite_id, file_dir) + read_AMOC_eddy(suite_id, file_dir)
    AMOC_lat = geodef_CONSTANT('AMOC') # --- 26.5 N
    AMOC_strength = np.max(AMOC[:,:, AMOC_lat], axis=1)
    return AMOC_strength

def lower_cell_strength_timeseries(suite_id, file_dir):
    # --- The minimum streamfunction below 30 S
    print('lower cell MOC strength is being calculating')
    MOC = read_global_MOC_mean(suite_id, file_dir) + read_global_MOC_eddy(suite_id, file_dir)
    GMOC_lower_lat = geodef_CONSTANT('lower_cell') # --- 30 S
    lower_cell_strength = np.min(MOC[:, :, :GMOC_lower_lat], axis=(1,2))
    return lower_cell_strength

def SMOC_strength_timeseries(suite_id, file_dir):
    # --- The minimum streamfunction below 55 S
    print('Southern Ocean MOC strength is being calculating')
    MOC = read_global_MOC_mean(suite_id, file_dir) + read_global_MOC_eddy(suite_id, file_dir)
    SO_lat = geodef_CONSTANT('SMOC') # --- 55 S
    SMOC_strength = np.min(MOC[:, :, :SO_lat], axis=(1,2))
    return SMOC_strength

def DrakePassage_timeseries(suite_id, file_dir):
    from terrafirma_analysis.nemoU_3d import prep_var
    # --- integrated umo along 68W from land to land and from surface to bottom
    
    print('Drake Passage transport is being calculating')
    DrakePassage_LON, DrakePassage_LAT1, DrakePassage_LAT2 = geodef_CONSTANT('DrakePassage')
    
    var_read = 'umo'
    print('var_read is overwritten to "umo"')
    print('if_global is overwritten to True')
    umo = prep_var(suite_id, file_dir, var_read, 
                   if_SO=False,
                   if_continental_shelf=False,
                   if_global=True,
                   if_Arctic_ocean=False)[:, :, DrakePassage_LAT1:DrakePassage_LAT2, DrakePassage_LON]
    umo = np.ma.array(umo, mask=umo==0)
    rho = 1026 # --- kg/m3
    return np.abs(-np.ma.sum(umo, axis=(1,2))/rho/1e6) # --- convert mass transport to volume transport in units of Sv

def SouthernOcean_baromsf(suite_id, file_dir):
    from terrafirma_analysis.nemoU_3d import prep_var
    
    # umo: zonal mass transport kg/s
    print('Southern Ocean barotropic streamfunction is being calculating')
    var_read = 'umo'
    print('var_read is overwritten to "umo"')
    print('if_SO is overwritten to True')
    umo = prep_var(suite_id, file_dir, var_read, 
                   if_SO=True,
                   if_continental_shelf=False,
                   if_global=False,
                   if_Arctic_ocean=False)
    
    umo = np.ma.array(umo, mask=umo==0)
    rho = 1026 # --- kg/m3
    psi = (-np.ma.cumsum(np.ma.sum(umo, axis=1), axis=1))/rho/1e6 # --- sum along depth-axis, and then cumsum along lat-axis
                                                                  # --- convert mass transport to volume transport in units of Sv
    
    return np.where(psi.mask, np.nan, psi) # --- mask land cells as zeros

def write_AMOC_strength_timeseries(suite_id, file_dir, path_out, filename_out):
    timeseries = AMOC_strength_timeseries(suite_id, file_dir)
    
    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        varout_name = 'AMOC_strength'
        units = 'Sv'
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries

    finally:
        ncfile.close()
    
    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')
    
def write_lower_cell_strength_timeseries(suite_id, file_dir, path_out, filename_out):
    timeseries = lower_cell_strength_timeseries(suite_id, file_dir)
    
    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        varout_name = 'lower_cell_strength'
        units = 'Sv'
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries

    finally:
        ncfile.close()
    
    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')

def write_SMOC_strength_timeseries(suite_id, file_dir, path_out, filename_out):
    timeseries = SMOC_strength_timeseries(suite_id, file_dir)
    
    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        varout_name = 'SMOC_strength'
        units = 'Sv'
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries

    finally:
        ncfile.close()
    
    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')


def write_Drake_Passage_timeseries(suite_id, file_dir, path_out, filename_out):
    timeseries = DrakePassage_timeseries(suite_id, file_dir)
    
    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        varout_name = 'DrakePassage_transport'
        units = 'Sv'
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries

    finally:
        ncfile.close()
    
    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')

def write_SouthernOcean_baromsf(suite_id, file_dir, path_out, filename_out):
    var2d = SouthernOcean_baromsf(suite_id, file_dir)
    [dim_t, dim_y, dim_x] = var2d.shape
    
    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_3d(ncfile, dim_y, dim_x)

        varout_name = 'SouthernOcean_baromsf'
        units = 'Sv'
        data_var = create_variables_3d(ncfile, varout_name)
        data_var.units = units
        data_var[:] = var2d

    finally:
        ncfile.close()
    
    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')