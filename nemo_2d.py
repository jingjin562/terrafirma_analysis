#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:22:19 2025

@author: jingjin

Only change vs. the original: every opened file handle (yearly, monthly, medusa,
and the land-sea mask datasets) is now closed after reading. The previous version
leaked one handle per year per variable, which can exhaust the OS descriptor
limit on long runs. All numerical behaviour is identical.
"""

import netCDF4 as nc
import numpy as np
import os
import os.path as op
import terrafirma_analysis
from terrafirma_analysis.io_core import create_dimensions_time, create_variables_1d_timeseries
from terrafirma_analysis.io_core import open_nemo_file, open_medusa_file, read_area
from terrafirma_analysis.utils.conversions import time_coverage
from terrafirma_analysis.shelfsea import AIS_continental_shelf, shelfsea_masking
from terrafirma_analysis.utils.mask import sea_surface_masking

_PKG_DIR = list(terrafirma_analysis.__path__)[0]
MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'Global_Ocean_sections_mask.nc')
GrIS_MASK = os.path.join(_PKG_DIR, 'utils', 'masks', 'GrIS_mask.nc')
SO_SHELF_SECTORS_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'nemo_shelf_mask.nc')

def _if_SO_focus(if_SO, if_continental_shelf):
    return bool(if_SO or if_continental_shelf)

def _read2d(open_fn, file_dir, suite_id, y, var_read, so_slice=False):
    """Open one file, read one 2D field, and always close the handle."""
    ds = open_fn(file_dir, suite_id, y)
    try:
        if so_slice:
            return np.squeeze(ds.variables[var_read][:, :113, :], axis=0)
        return np.squeeze(ds.variables[var_read][:], axis=0)
    finally:
        ds.close()


def read_SO_nemo_2d(suite_id, file_dir, var_read, if_continental_shelf=False):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 113, 362])

    if if_continental_shelf:
        shelfsea = AIS_continental_shelf(suite_id)

    for y in year:
        var[y-year_start, ] = _read2d(open_nemo_file, file_dir, suite_id, y, var_read, so_slice=True)

        if if_continental_shelf:
            var[y-year_start, ] = shelfsea_masking(suite_id, var[y-year_start, ], shelfsea)

    return var

def read_SO_shelf_sectors_2d(suite_id, file_dir, var_read, region=None):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 113, 362])
    
    if region is None:
        print('No region is given, read the entire Southern Ocean shelf seas')
        return read_SO_nemo_2d(suite_id, file_dir, var_read, if_continental_shelf=True)
    
    else:
        with nc.Dataset(SO_SHELF_SECTORS_PATH, 'r') as ds_mask:
            shelf_sector_mask = ds_mask.variables[f'mask_{region}'][:113, :]
        
        for y in year:
            var[y-year_start, ] = _read2d(open_nemo_file, file_dir, suite_id, y, var_read, so_slice=True)
            
        # apply the 2D mask to every year at once (broadcasts over axis 0)
        var = np.ma.masked_where(np.broadcast_to(shelf_sector_mask == 0, var.shape), var)
        
        return var

def read_global_nemo_2d(suite_id, file_dir, var_read):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 332, 362])

    for y in year:
        var[y-year_start, ] = _read2d(open_nemo_file, file_dir, suite_id, y, var_read)

    return var


def read_Arctic_Ocean_nemo_2d(suite_id, file_dir, var_read):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)

    var = np.empty([len(year), 332, 362])
    with nc.Dataset(MASK_PATH, 'r') as ds_mask:
        Arctic_Ocean = np.squeeze(ds_mask.variables['Arctic_Ocean'][:])

    for y in year:
        var[y-year_start, ] = _read2d(open_nemo_file, file_dir, suite_id, y, var_read)

    # apply the 2D mask to every year at once (broadcasts over axis 0)
    var = np.ma.masked_where(np.broadcast_to(Arctic_Ocean == 0, var.shape), var)

    return var


def read_Greenland_nemo_2d(suite_id, file_dir, var_read):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)

    var = np.empty([len(year), 332, 362])
    with nc.Dataset(GrIS_MASK, 'r') as ds_mask:
        GrIS = np.squeeze(ds_mask.variables['GrIS_mask'][:])

    for y in year:
        var[y-year_start, ] = _read2d(open_nemo_file, file_dir, suite_id, y, var_read)

    # apply the 2D mask to every year at once (broadcasts over axis 0)
    var = np.ma.masked_where(np.broadcast_to(GrIS == 0, var.shape), var)

    return var


def read_monthly_nemo_2d(suite_id, file_dir, var_read, if_continental_shelf=False):
    from glob import glob
    monthly_nemo_list = sorted(glob(f"{file_dir}/nemo_{suite_id}o_1m_*.nc"))

    var = np.empty([len(monthly_nemo_list), 113, 362])
    if if_continental_shelf:
        shelfsea = AIS_continental_shelf(suite_id)

    for f in range(0, len(monthly_nemo_list), 1):
        with nc.Dataset(monthly_nemo_list[f], 'r') as ds:
            var[f, ] = np.squeeze(ds.variables[var_read][:, :113, :], axis=0)

        if if_continental_shelf:
            var[f, ] = shelfsea_masking(suite_id, var[f, ], shelfsea)

    return var


def read_medusa_2d(suite_id, file_dir, var_read, if_continental_shelf=False):

    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 113, 362])

    if if_continental_shelf:
        shelfsea = AIS_continental_shelf(suite_id)

    for y in year:
        var[y-year_start, ] = _read2d(open_medusa_file, file_dir, suite_id, y, var_read, so_slice=True)

        if if_continental_shelf:
            var[y-year_start, ] = shelfsea_masking(suite_id, var[y-year_start, ], shelfsea)

    return var


def prep_var(suite_id, file_dir, var_read,
             if_SO=True,
             if_continental_shelf=False,
             if_global=False,
             if_Arctic_ocean=False):

    if if_SO:
        if if_continental_shelf:
            print('the Southern Ocean continental shelf seas will be calculated')
            var = read_SO_nemo_2d(suite_id, file_dir, var_read, if_continental_shelf=if_continental_shelf)
        else:
            print('the Southern Ocean will be calculated')
            var = read_SO_nemo_2d(suite_id, file_dir, var_read, if_continental_shelf=if_continental_shelf)
    else:
        if if_continental_shelf:
            print('if_SO is overwritten to True, the Southern Ocean continental shelf seas will be calculated')
            var = read_SO_nemo_2d(suite_id, file_dir, var_read, if_continental_shelf=if_continental_shelf)

    if if_global:
        print('the global ocean will be calculated')
        var = read_global_nemo_2d(suite_id, file_dir, var_read)

    if if_Arctic_ocean:
        print('the Arctic Ocean will be calculated')
        var = read_Arctic_Ocean_nemo_2d(suite_id, file_dir, var_read)

    return var


def nemo_seaice_like_timeseries(suite_id, file_dir, var_read,
                                if_SO=True,
                                if_continental_shelf=False,
                                if_global=False,
                                if_Arctic_ocean=False):

    # ---- suitable for sea surface variables like soicecov, sithick, which have uniformed sign values (all positive/negative)
    var_unmask = prep_var(suite_id, file_dir, var_read,
                          if_SO=if_SO,
                          if_continental_shelf=if_continental_shelf,
                          if_global=if_global,
                          if_Arctic_ocean=if_Arctic_ocean)
    
    var = sea_surface_masking(var_unmask, if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))
    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))
    
    if var_read in ['soicecov']:
        timeseries = np.ma.sum(np.ma.array(var*area, mask=np.isnan(var)), axis=(1,2))
        print('sea ice concentration is converted to sea ice area (m2)')
    else:
        timeseries = np.ma.mean(np.ma.array(var, mask=np.isnan(var)), axis=(1,2))

    return timeseries


def nemo_surface_heat_flux_like_timeseries(suite_id, file_dir, var_read,
                                           if_SO=True,
                                           if_continental_shelf=False,
                                           if_global=False,
                                           if_Arctic_ocean=False):

    # ---- suitable for sea surface variables like CO2 flux, heat flux (hfds), which have two-sign values (positive and negative)
    from terrafirma_analysis.io_core import read_area

    if var_read in ['hfds']:
        var_unmask = prep_var(suite_id, file_dir, var_read,
                              if_SO=if_SO,
                              if_continental_shelf=if_continental_shelf,
                              if_global=if_global,
                              if_Arctic_ocean=if_Arctic_ocean)

    elif var_read in ['CO2FLUX']:
        var_unmask = read_medusa_2d(suite_id, file_dir, var_read, if_continental_shelf)

    var = sea_surface_masking(var_unmask, if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))
    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))

    timeseries = np.nansum(var*area, axis=(1,2))

    if var_read in ['CO2FLUX']:
        from terrafirma_analysis.utils.conversions import mmolC_per_day_to_Gt_per_yr
        timeseries = mmolC_per_day_to_Gt_per_yr(timeseries)

    return timeseries


def nemo_2d_timeseries(suite_id, file_dir, var_read,
                       if_SO=True,
                       if_continental_shelf=False,
                       if_global=False,
                       if_Arctic_ocean=False):

    var = prep_var(suite_id, file_dir, var_read,
                   if_SO=if_SO,
                   if_continental_shelf=if_continental_shelf,
                   if_global=if_global,
                   if_Arctic_ocean=if_Arctic_ocean)

    timeseries = np.ma.mean(np.ma.array(var, mask=var==0), axis=(1,2))

    return timeseries


def write_nemo_2d_timeseries(suite_id, file_dir, var_read, path_out,
                             filename_out, varout_name, units,
                             if_SO=True,
                             if_continental_shelf=False,
                             if_global=False,
                             if_Arctic_ocean=False):

    if var_read in ['soicecov', 'sithick']:
        timeseries = nemo_seaice_like_timeseries(suite_id, file_dir, var_read,
                                                 if_SO=if_SO,
                                                 if_continental_shelf=if_continental_shelf,
                                                 if_global=if_global,
                                                 if_Arctic_ocean=if_Arctic_ocean)
        if var_read in ['soicecov']:
            print('sea ice concentration is overwritten to sea ice area')
            units = 'm2'
            if if_continental_shelf:
                varout_name = 'shelfsea_siarea'
            else:
                varout_name = 'siarea'

    elif var_read in ['hfds', 'CO2FLUX']:
        timeseries = nemo_surface_heat_flux_like_timeseries(suite_id, file_dir, var_read,
                                                            if_SO=if_SO,
                                                            if_continental_shelf=if_continental_shelf,
                                                            if_global=if_global,
                                                            if_Arctic_ocean=if_Arctic_ocean)
        if var_read == 'hfds':
            print('units_out is overwritten to "W"')
            units = 'W'
    else:
        timeseries = nemo_2d_timeseries(suite_id, file_dir, var_read,
                                        if_SO=if_SO,
                                        if_continental_shelf=if_continental_shelf,
                                        if_global=if_global,
                                        if_Arctic_ocean=if_Arctic_ocean)

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

