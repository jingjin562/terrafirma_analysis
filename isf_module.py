#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:22:19 2025

@author: jingjin

Only change vs. the original: opened file handles (yearly isf files and the
land-sea mask dataset) are now closed after reading. Numerical behaviour is
identical.
"""

import netCDF4 as nc
import numpy as np
import os
import os.path as op
import terrafirma_analysis
from terrafirma_analysis.io_core import open_isf_file, read_area, create_dimensions_time, create_variables_1d_timeseries
from terrafirma_analysis.utils.conversions import time_coverage
from terrafirma_analysis.utils.conversions import kg_per_m2_per_s_to_Gt_per_yr

_PKG_DIR = list(terrafirma_analysis.__path__)[0]
MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'Global_Ocean_sections_mask.nc')
ISF_MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'nemo_cavity_mask.nc')

def _read_isf(file_dir, suite_id, y, var_read, so_slice=False):
    ds = open_isf_file(file_dir, suite_id, y)
    try:
        if so_slice:
            return np.squeeze(ds.variables[var_read][:, :113, :], axis=0)
        return np.squeeze(ds.variables[var_read][:], axis=0)
    finally:
        ds.close()


def read_isf(suite_id, file_dir, var_read):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 113, 362])

    for y in year:
        var[y-year_start, ] = _read_isf(file_dir, suite_id, y, var_read, so_slice=True)

    return var

def read_SO_shelf_sectors_isf(suite_id, file_dir, var_read, region=None):
    
    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 113, 362])
    
    if region is None:
        print('No region is given, read the entire Southern Ocean shelf seas')
        return read_isf(suite_id, file_dir, var_read)    
    else:
        with nc.Dataset(ISF_MASK_PATH, 'r') as ds_mask:
            cavity_mask = ds_mask.variables[f'mask_{region}'][:113, :]
            var = read_isf(suite_id, file_dir, var_read)
            
            # apply the 2D mask to every year at once (broadcasts over axis 0)
            var = np.ma.masked_where(np.broadcast_to(cavity_mask == 0, var.shape), var)
        
        return var

def read_global_isf(suite_id, file_dir, var_read):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 332, 362])

    for y in year:
        var[y-year_start, ] = _read_isf(file_dir, suite_id, y, var_read)

    return var


def read_Arctic_Ocean_isf(suite_id, file_dir, var_read):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 332, 362])
    with nc.Dataset(MASK_PATH, 'r') as ds_mask:
        Arctic_Ocean = np.squeeze(ds_mask.variables['Arctic_Ocean'][:])

    for y in year:
        var_unmask = _read_isf(file_dir, suite_id, y, var_read)
        var[y-year_start, ] = np.ma.array(var_unmask, mask=Arctic_Ocean==0)

    return var


def prep_isf_var(suite_id, file_dir, var_read,
                 if_SO=True,
                 if_continental_shelf=False,
                 if_global=False,
                 if_Arctic_ocean=False):

    if if_SO or if_continental_shelf:
        print('the Antarctic ice shelf basal melt will be calculated')
        var = read_isf(suite_id, file_dir, var_read)

    if if_global:
        print('the global ice shelf basal melt will be calculated')
        var = read_global_isf(suite_id, file_dir, var_read)

    if if_Arctic_ocean:
        print('the Greenland ice shelf basal melt will be calculated')
        var = read_Arctic_Ocean_isf(suite_id, file_dir, var_read)

    return var


def nemo_isf_timeseries(suite_id, file_dir, var_read,
                        if_SO=True,
                        if_continental_shelf=False,
                        if_global=False,
                        if_Arctic_ocean=False):

    if if_SO or if_continental_shelf:
        if_SO_focus = True
    else:
        if_SO_focus = False

    area = read_area(if_SO_focus=if_SO_focus)

    isf = prep_isf_var(suite_id, file_dir, var_read,
                       if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                       if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)
    
    if var_read == 'sowflisf':
        timeseries = np.sum(kg_per_m2_per_s_to_Gt_per_yr(-isf, area), axis=(1,2))
    elif var_read == 'sohflisf':
        timeseries = np.sum(-isf*area, axis=(1,2))
    
    # --- bad data in cx209 ---
    if suite_id == 'cx209':
        timeseries[342] = np.nan
    
    return timeseries


def write_isf_timeseries(suite_id, file_dir, var_read, path_out, filename_out, varout_name, units,
                         if_SO=True,
                         if_continental_shelf=False,
                         if_global=False,
                         if_Arctic_ocean=False):

    timeseries = nemo_isf_timeseries(suite_id, file_dir, var_read,
                                     if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                                     if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries
    finally:
        ncfile.close()

    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')

