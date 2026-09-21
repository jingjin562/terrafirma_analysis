#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 10:00:43 2026

@author: jingjin
"""

import netCDF4 as nc
import numpy as np
import os
import os.path as op
import terrafirma_analysis
from terrafirma_analysis.io_core import (
    open_nemo_file, open_nemoU_file, open_nemoV_file, open_isf_file,
    create_dimensions_time, create_dimensions_lev,
    create_variables_1d_timeseries, create_variables_2d_hovemoller,
    read_area
    )
from terrafirma_analysis.utils.conversions import time_coverage
from terrafirma_analysis.utils.mask import sea_surface_masking, mask_zeros
from terrafirma_analysis.nemo_2d import read_SO_shelf_sectors_2d
from terrafirma_analysis.isf_module import read_SO_shelf_sectors_isf
from terrafirma_analysis.nemo_grid_3d import read_SO_shelf_sectors
from terrafirma_analysis.utils.conversions import kg_per_m2_per_s_to_Gt_per_yr

_PKG_DIR = list(terrafirma_analysis.__path__)[0]
MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'nemo_shelf_mask.nc')
ISF_MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'nemo_cavity_mask.nc')

_DEFAULT_DEPTH = 75

# depth-band index ranges used for the layered timeseries (unchanged)
DEPTH_BANDS = {
    '0': np.arange(0, 25, 1),    # e.g. 0-120 m
    '1': np.arange(25, 38, 1),   #      120-400 m
    '2': np.arange(38, 44, 1),   #      400-850 m
    '3': np.arange(44, 75, 1),   #      below 850 m
    '4': np.arange(0, 75, 1),    #      full depth
}

# ---------------------------------------------------------------------------
# Derived quantities
# ---------------------------------------------------------------------------
def SO_sector_timeseries_3d(suite_id, file_dir, var_read, grid='T', region=None):
    var = read_SO_shelf_sectors(suite_id, file_dir, var_read, grid=grid, region=region)
    return {p: np.ma.mean(mask_zeros(var[:, idx, :, :]), axis=(1, 2, 3))
            for p, idx in DEPTH_BANDS.items()}

def SO_sector_hovemoller_3d(suite_id, file_dir, var_read, grid='T', region=None):
    var = read_SO_shelf_sectors(suite_id, file_dir, var_read, grid=grid, region=region)
    return np.ma.mean(mask_zeros(var), axis=(2, 3))

def SO_sector_timeseries_2d(suite_id, file_dir, var_read, region=None):
    var = read_SO_shelf_sectors_2d(suite_id, file_dir, var_read, region=region)
    return np.ma.mean(mask_zeros(var), axis=(1,2))

def SO_sector_water_flux_timeseries_2d(suite_id, file_dir, var_read, region=None):
    var = read_SO_shelf_sectors_2d(suite_id, file_dir, var_read, region=region)
    area = read_area(if_SO_focus=True)
    def integ(v):
        return np.sum(kg_per_m2_per_s_to_Gt_per_yr(v, area), axis=(1, 2))    
    return integ(var)

def SO_sector_areainteg_timeseries_2d(suite_id, file_dir, var_read, region=None):
    var = read_SO_shelf_sectors_2d(suite_id, file_dir, var_read, region=region)
    area = read_area(if_SO_focus=True)
    def integ(v):
        return np.sum(var*area, axis=(1, 2))   
    return integ(var)

def SO_sector_basal_mass_loss_timeseries_2d(suite_id, file_dir, var_read, region=None):
    var = read_SO_shelf_sectors_isf(suite_id, file_dir, var_read, region=region)
    area = read_area(if_SO_focus=True)
    def integ(v):
        return np.sum(kg_per_m2_per_s_to_Gt_per_yr(v, area), axis=(1, 2))    
    return integ(-var) 

# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
def write_SO_sector_timeseries_3d(suite_id, file_dir, var_read, path_out, filename_out,
                                  varout_name, units, grid='T', region=None):
    ts = SO_sector_timeseries_3d(suite_id, file_dir, var_read, grid=grid, region=region)
    ncfile = nc.Dataset(op.join(path_out, filename_out), 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)
        for p in DEPTH_BANDS:
            data_var = create_variables_1d_timeseries(ncfile, varout_name[p])
            data_var.units = units
            data_var[:] = ts[p]
    finally:
        ncfile.close()
    print(f'{op.join(path_out, filename_out)} is created. \n {len(varout_name)} variables are saved.')
    
def write_SO_sector_hovemoller_3d(suite_id, file_dir, var_read, path_out, filename_out,
                                  varout_name, units, grid='T', region=None):
    hov = SO_sector_hovemoller_3d(suite_id, file_dir, var_read, grid=grid, region=region)
    ncfile = nc.Dataset(op.join(path_out, filename_out), 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)
        create_dimensions_lev(ncfile, np.shape(hov)[1])
        data_var = create_variables_2d_hovemoller(ncfile, varout_name)
        data_var.units = units
        data_var[:] = hov
    finally:
        ncfile.close()
    print(f'{op.join(path_out, filename_out)} is created. \n A hovemoller variable {var_read} is saved.')

def write_SO_sector_timeseries_2d(suite_id, file_dir, var_read, path_out, filename_out,
                                  varout_name, units, region=None):
    
    if var_read in ['fsitherm', 'friver', 'ficeberg', 'pr', 'prsn', 'evs']:
        print('units_out is overwritten to "Gt/yr"')
        units = 'Gt/yr'
        ts = SO_sector_water_flux_timeseries_2d(suite_id, file_dir, var_read, region=region)
    elif var_read in ['sowflisf']:
        print('units_out is overwritten to "Gt/yr"')
        units = 'Gt/yr'
        ts = SO_sector_basal_mass_loss_timeseries_2d(suite_id, file_dir, var_read, region=region)
    elif var_read in ['soicecov']:
        print('sea ice concentration is overwritten to sea ice area')
        units = 'm2'
        ts = SO_sector_areainteg_timeseries_2d(suite_id, file_dir, var_read, region=region)        
    elif var_read in ['hfds']:
        print('units_out is overwritten to "W"')
        units = 'W'
        ts = SO_sector_areainteg_timeseries_2d(suite_id, file_dir, var_read, region=region)       
    else:
        ts = SO_sector_timeseries_2d(suite_id, file_dir, var_read, region=region)
        
    ncfile = nc.Dataset(op.join(path_out, filename_out), 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)       
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = ts
    finally:
        ncfile.close()
        
    print(f'{op.join(path_out, filename_out)} is created. \n {len(varout_name)} variables are saved.')