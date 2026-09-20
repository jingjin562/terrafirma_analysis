#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:22:19 2025

@author: jingjin

Additions vs. the original:
  * FW_components() / write_all_FW_timeseries() read each of the seven freshwater
    component fields ONCE and derive all of total / net_precip / ocean / icesheet
    from that single read. Producing the full breakdown the old way (four
    separate write_total_FW_timeseries calls) re-read the shared fields several
    times each. The existing per-mode functions are unchanged for when you only
    want one output.
  * Writers wrap their netCDF handle in try/finally so the file is closed even
    if writing raises. (The 2D/isf readers this module calls now also close
    their handles -- see nemo_2d.py / isf_module.py.)
"""

import netCDF4 as nc
import numpy as np
import os
import os.path as op
from terrafirma_analysis.io_core import read_area, create_dimensions_time, create_variables_1d_timeseries
from terrafirma_analysis.nemo_2d import read_SO_nemo_2d, read_global_nemo_2d, read_Arctic_Ocean_nemo_2d, read_Greenland_nemo_2d, prep_var
from terrafirma_analysis.isf_module import prep_isf_var
from terrafirma_analysis.utils.conversions import kg_per_m2_per_s_to_Gt_per_yr


def _if_SO_focus(if_SO, if_continental_shelf):
    return bool(if_SO or if_continental_shelf)


def single_water_flux_timeseries(suite_id, file_dir, var_read,
                                 if_SO=True,
                                 if_continental_shelf=False,
                                 if_global=False,
                                 if_Arctic_ocean=False):

    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))

    var = prep_var(suite_id, file_dir, var_read,
                   if_SO=if_SO,
                   if_continental_shelf=if_continental_shelf,
                   if_global=if_global,
                   if_Arctic_ocean=if_Arctic_ocean)

    timeseries = np.sum(kg_per_m2_per_s_to_Gt_per_yr(var, area), axis=(1,2))

    return timeseries


def write_single_water_flux_timeseries(suite_id, file_dir, var_read, path_out,
                                       filename_out, varout_name, units,
                                       if_SO=True,
                                       if_continental_shelf=False,
                                       if_global=False,
                                       if_Arctic_ocean=False):

    timeseries = single_water_flux_timeseries(suite_id, file_dir, var_read,
                                              if_SO=if_SO,
                                              if_continental_shelf=if_continental_shelf,
                                              if_global=if_global,
                                              if_Arctic_ocean=if_Arctic_ocean)

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        print('units is overwritten to Gt/yr')
        units = 'Gt/yr'
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries
    finally:
        ncfile.close()

    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')


def net_precip_timeseries(suite_id, file_dir,
                          if_SO=True,
                          if_continental_shelf=False,
                          if_global=False,
                          if_Arctic_ocean=False):

    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))

    pr = prep_var(suite_id, file_dir, 'pr', if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                  if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)
    prsn = prep_var(suite_id, file_dir, 'prsn', if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                  if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)
    evs = prep_var(suite_id, file_dir, 'evs', if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                  if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)

    var = pr+prsn-evs
    timeseries = np.sum(kg_per_m2_per_s_to_Gt_per_yr(var, area), axis=(1,2))

    return timeseries


def write_net_precip_timeseries(suite_id, file_dir, path_out,
                                filename_out, varout_name, units,
                                if_SO=True,
                                if_continental_shelf=False,
                                if_global=False,
                                if_Arctic_ocean=False):

    timeseries = net_precip_timeseries(suite_id, file_dir,
                                       if_SO=if_SO,
                                       if_continental_shelf=if_continental_shelf,
                                       if_global=if_global,
                                       if_Arctic_ocean=if_Arctic_ocean)

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        print('units is overwritten to Gt/yr')
        units = 'Gt/yr'
        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries
    finally:
        ncfile.close()

    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')


def fsitherm_timeseries(suite_id, file_dir,
                        if_SO=True,
                        if_continental_shelf=False,
                        if_global=False,
                        if_Arctic_ocean=False):
    print('global timeseries of fsitherm melting/freezing has not been implemented')

    timeseries = {}

    print('The variable to read is overwritten to fsitherm.')

    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))

    fsitherm = prep_var(suite_id, file_dir, 'fsitherm', if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                  if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)
    seaice_melting = np.where(fsitherm>0, fsitherm, 0)
    seaice_freezing = np.where(fsitherm<0, fsitherm, 0)

    net = np.sum(kg_per_m2_per_s_to_Gt_per_yr(fsitherm, area), axis=(1,2))
    melting = np.sum(kg_per_m2_per_s_to_Gt_per_yr(seaice_melting, area), axis=(1,2))
    freezing = np.sum(kg_per_m2_per_s_to_Gt_per_yr(seaice_freezing, area), axis=(1,2))

    timeseries = {
        'fsitherm_net': net,
        'fsitherm_melting': melting,
        'fsitherm_freezing': freezing,
        }
    return timeseries


def write_sea_ice_timeseries(suite_id, file_dir, path_out, filename_out,
                             if_SO=True,
                             if_continental_shelf=False,
                             if_global=False,
                             if_Arctic_ocean=False):

    timeseries = fsitherm_timeseries(suite_id, file_dir,
                                     if_SO=if_SO,
                                     if_continental_shelf=if_continental_shelf,
                                     if_global=if_global,
                                     if_Arctic_ocean=if_Arctic_ocean)

    varout_name = ['fsitherm_net', 'fsitherm_melting', 'fsitherm_freezing']
    print('units is overwritten to Gt/yr')
    units = 'Gt/yr'

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        for var_current in varout_name:
            data_var = create_variables_1d_timeseries(ncfile, var_current)
            data_var.units = units
            data_var[:] = timeseries[var_current]
    finally:
        ncfile.close()

    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')


# ---------------------------------------------------------------------------
# Freshwater flux composition
# ---------------------------------------------------------------------------
def _read_FW_fields(suite_id, file_dir, flags, isf_dir):
    """Read each freshwater component field exactly once.

    The six grid-T fields all come from the same grid-T file, so they share
    file_dir. sowflisf comes from the isf-T stream, which may live in a
    different directory (isf_dir).
    """
    def rd(v):
        return prep_var(suite_id, file_dir, v, **flags)
    return {
        'pr':       rd('pr'),
        'prsn':     rd('prsn'),
        'evs':      rd('evs'),
        'fsitherm': rd('fsitherm'),
        'ficeberg': rd('ficeberg'),
        'friver':   rd('friver'),
        'sowflisf': prep_isf_var(suite_id, isf_dir, 'sowflisf', **flags),
    }


def FW_components(suite_id, file_dir,
                  if_SO=True,
                  if_continental_shelf=False,
                  if_global=False,
                  if_Arctic_ocean=False,
                  isf_dir=None):
    """Return all freshwater-flux decompositions from a single read of each field.

    isf_dir : directory holding the sowflisf (isf-T) files. Defaults to file_dir
    when the isf files sit alongside the grid-T fields; set it when they don't.

    Definitions (identical to the original total_FW_timeseries modes):
        net_precip               = pr + prsn - evs
        total_icesheet_FW        = friver + ficeberg - sowflisf
        total_seaice_icesheet_FW = fsitherm + total_icesheet_FW
        total_FW                 = net_precip + total_seaice_icesheet_FW
    """
    isf_dir = isf_dir or file_dir
    flags = dict(if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                 if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)

    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))
    f = _read_FW_fields(suite_id, file_dir, flags, isf_dir)

    atmos    = f['pr'] + f['prsn'] - f['evs']
    icesheet = f['friver'] + f['ficeberg'] - f['sowflisf']
    ocean    = f['fsitherm'] + icesheet
    total    = atmos + ocean

    def integ(v):
        return np.sum(kg_per_m2_per_s_to_Gt_per_yr(v, area), axis=(1, 2))

    return {
        'total_FW':                 integ(total),
        'net_precip':               integ(atmos),
        'total_seaice_icesheet_FW': integ(ocean),
        'total_icesheet_FW':        integ(icesheet),
    }


def write_all_FW_timeseries(suite_id, file_dir, path_out, filename_out,
                            if_SO=True,
                            if_continental_shelf=False,
                            if_global=False,
                            if_Arctic_ocean=False,
                            isf_dir=None):
    """Write total / net_precip / ocean / icesheet FW from one field-read pass."""
    timeseries = FW_components(suite_id, file_dir,
                               if_SO=if_SO,
                               if_continental_shelf=if_continental_shelf,
                               if_global=if_global,
                               if_Arctic_ocean=if_Arctic_ocean,
                               isf_dir=isf_dir)

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)
        for name, series in timeseries.items():
            data_var = create_variables_1d_timeseries(ncfile, name)
            data_var.units = 'Gt/yr'
            data_var[:] = series
    finally:
        ncfile.close()

    return print(f'{fi_out} is created. \n {list(timeseries)} are saved.')


def total_FW_timeseries(suite_id, file_dir,
                        if_total=True, if_atmos=False, if_ocean=False, if_icesheet=False,
                        if_SO=True,
                        if_continental_shelf=False,
                        if_global=False,
                        if_Arctic_ocean=False,
                        isf_dir=None):

    isf_dir = isf_dir or file_dir
    area = read_area(if_SO_focus=_if_SO_focus(if_SO, if_continental_shelf))
    flags = dict(if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                 if_global=if_global, if_Arctic_ocean=if_Arctic_ocean)

    def rd(v):
        return prep_var(suite_id, file_dir, v, **flags)

    def rd_isf():
        return prep_isf_var(suite_id, isf_dir, 'sowflisf', **flags)

    if if_total:
        var = rd('fsitherm') + rd('friver') + rd('ficeberg') - rd_isf() + rd('pr') + rd('prsn') - rd('evs')
    elif if_atmos:
        var = rd('pr') + rd('prsn') - rd('evs')
    elif if_ocean:
        var = rd('fsitherm') + rd('friver') + rd('ficeberg') - rd_isf()
    elif if_icesheet:
        var = rd('friver') + rd('ficeberg') - rd_isf()

    timeseries = np.sum(kg_per_m2_per_s_to_Gt_per_yr(var, area), axis=(1,2))

    return timeseries


def write_total_FW_timeseries(suite_id, file_dir, path_out, filename_out,
                              if_total=True, if_atmos=False, if_ocean=False, if_icesheet=False,
                              if_SO=True,
                              if_continental_shelf=False,
                              if_global=False,
                              if_Arctic_ocean=False,
                              isf_dir=None):

    timeseries = total_FW_timeseries(suite_id, file_dir,
                                     if_total=if_total,
                                     if_atmos=if_atmos,
                                     if_ocean=if_ocean,
                                     if_icesheet=if_icesheet,
                                     if_SO=if_SO,
                                     if_continental_shelf=if_continental_shelf,
                                     if_global=if_global,
                                     if_Arctic_ocean=if_Arctic_ocean,
                                     isf_dir=isf_dir)

    if if_total:
        varout_name = 'total_FW'
    elif if_atmos:
        varout_name = 'net_precip'
    if if_ocean:
        varout_name = 'total_seaice_icesheet_FW'
    if if_icesheet:
        varout_name = 'total_icesheet_FW'

    print('units is overwritten to Gt/yr')
    units = 'Gt/yr'

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


def GrIS_runoff(suite_id, file_dir):
    GrIS_runoff = read_Greenland_nemo_2d(suite_id, file_dir, 'friver')
    area = read_area(if_SO_focus=False)
    timeseries = np.sum(kg_per_m2_per_s_to_Gt_per_yr(GrIS_runoff, area), axis=(1,2))
    return timeseries


def write_GrIS_runoff_timeseries(suite_id, file_dir, path_out, filename_out):
    timeseries = GrIS_runoff(suite_id, file_dir)

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)

        print('varout_name is overwritten to GrIS_runoff')
        print('units is overwritten to Gt/yr')

        varout_name = 'GrIS_runoff'
        units = 'Gt/yr'

        data_var = create_variables_1d_timeseries(ncfile, varout_name)
        data_var.units = units
        data_var[:] = timeseries
    finally:
        ncfile.close()

    return print(f'{os.path.join(path_out, filename_out)} is created. \n {varout_name} is saved.')
