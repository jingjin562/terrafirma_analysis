#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nemo_grid_3d.py -- single shared implementation for reading 3D NEMO fields on
the T, U or V grid.

This replaces the three near-identical modules nemo_3d.py / nemoU_3d.py /
nemoV_3d.py, which differed only in which file opener they called and in a
couple of default flags. The grid is now a parameter ('T' | 'U' | 'V').

Changes vs. the originals (all otherwise behaviour-preserving):
  * File handles are closed after each read (they were previously leaked, one
    per year per variable, which risks exhausting the OS descriptor limit on
    long runs).
  * The Arctic reader now returns a properly masked array on ALL grids. In the
    old nemo_3d.py the T-grid Arctic mask was assigned into an np.empty array
    and silently dropped, so T-grid Arctic output came back unmasked. The U/V
    versions were already correct; this makes T consistent with them. If you
    were relying on the old (unmasked) T behaviour, note this change.

The thin modules nemo_3d.py / nemoU_3d.py / nemoV_3d.py now just re-export from
here with the right grid and default flags, so all existing imports keep working.
"""
import netCDF4 as nc
import numpy as np
import os
import os.path as op
import plotting_functions as pf
import terrafirma_analysis
from terrafirma_analysis.io_core import (
    open_nemo_file, open_nemoU_file, open_nemoV_file, open_isf_file,
    create_dimensions_time, create_dimensions_lev,
    create_variables_1d_timeseries, create_variables_2d_hovemoller,
)
from terrafirma_analysis.utils.conversions import time_coverage
from terrafirma_analysis.shelfsea import AIS_continental_shelf, shelfsea_masking
from terrafirma_analysis.utils.mask import mask_zeros

_PKG_DIR = list(terrafirma_analysis.__path__)[0]
MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'Global_Ocean_sections_mask.nc')
SO_SHELF_SECTORS_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'nemo_shelf_mask.nc')

_OPENERS = {'T': open_nemo_file, 'U': open_nemoU_file, 'V': open_nemoV_file}

_DEFAULT_DEPTH = 75

# depth-band index ranges used for the layered timeseries (unchanged)
DEPTH_BANDS = {
    '0': np.arange(0, 25, 1),    # e.g. 0-120 m
    '1': np.arange(25, 38, 1),   #      120-400 m
    '2': np.arange(38, 44, 1),   #      400-850 m
    '3': np.arange(44, 75, 1),   #      below 850 m
    '4': np.arange(0, 75, 1),    #      full depth
}


def _resolve_years(suite_id, year):
    if year is None:
        year_start, year_end = time_coverage(suite_id)
        return np.arange(year_start, year_end, 1), year_start
    return np.asarray(year), year[0]


def _resolve_isf_dir(suite_id, isf_dir=None):
    """Directory holding the isf-T (sowflisf) files used for the ice-shelf mask.

    The isf files are not always co-located with the grid-T/U/V files, so this is
    a separate parameter. It defaults to the archive path these readers have
    always used, leaving existing call sites unchanged.
    """
    return isf_dir or f'/home/users/jingj/ocean_ice/archer2/u-{suite_id}'


def _opener(grid):
    try:
        return _OPENERS[grid]
    except KeyError:
        raise ValueError(f"grid must be one of {sorted(_OPENERS)}, got {grid!r}")


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------
def read_SO(suite_id, file_dir, var_read, grid='T',
            year=None, depth=None,
            if_continental_shelf=False, slope_isobathy=1200,
            if_mask_isf=True, isf_dir=None):
    opener = _opener(grid)
    isf_dir = _resolve_isf_dir(suite_id, isf_dir)
    year, year_start = _resolve_years(suite_id, year)
    depth = _DEFAULT_DEPTH if depth is None else depth

    var = np.empty([len(year), depth, 113, 362])
    if if_continental_shelf:
        shelfsea = AIS_continental_shelf(suite_id, slope_isobathy=slope_isobathy)

    for y in year:
        ds = opener(file_dir, suite_id, y)
        try:
            var_unmask = np.squeeze(ds.variables[var_read][:, :depth, :113, :], axis=0)
        finally:
            ds.close()

        if if_mask_isf:
            fm = open_isf_file(isf_dir, suite_id, y)
            try:
                isf_mask = np.squeeze(fm.variables['sowflisf'][:, :113, :], axis=0)
            finally:
                fm.close()
            isf_mask_4d = pf.boost_dimension(isf_mask, np.shape(var_unmask))
            var[y - year_start, ] = np.where(isf_mask_4d == 0, var_unmask, 0)
        else:
            var[y - year_start, ] = var_unmask

        if if_continental_shelf:
            var[y - year_start, ] = shelfsea_masking(suite_id, var[y - year_start, ], shelfsea)

    return var

def read_SO_shelf_sectors(suite_id, file_dir, var_read, grid='T',
                          year=None, depth=None, region=None):
    
    if region is None:
        return read_SO(suite_id, file_dir, var_read, grid=grid,
                       year=year, depth=depth,
                       if_continental_shelf=True, slope_isobathy=1200,
                       if_mask_isf=True, isf_dir=None)
    else:
        opener = _opener(grid)
        year, year_start = _resolve_years(suite_id, year)
        depth = _DEFAULT_DEPTH if depth is None else depth
        var = np.empty([len(year), depth, 113, 362])
        
        with nc.Dataset(SO_SHELF_SECTORS_PATH, 'r') as ds_mask:
            shelf_sector_mask = ds_mask.variables[f'mask_{region}'][:113, :]
        
        for y in year:
            ds = opener(file_dir, suite_id, y)
            try:
                var[y-year_start, ] = np.squeeze(ds.variables[var_read][:, :depth, :113, :], axis=0)
            finally:
                ds.close()
                
        # apply the 2D mask to every year at once (broadcasts over axis 0)
        var = np.ma.masked_where(np.broadcast_to(shelf_sector_mask == 0, var.shape), var)
            
        return var
    

def read_global(suite_id, file_dir, var_read, grid='T', year=None, depth=None,
                if_mask_isf=False, isf_dir=None):
    opener = _opener(grid)
    isf_dir = _resolve_isf_dir(suite_id, isf_dir)
    year, year_start = _resolve_years(suite_id, year)
    depth = _DEFAULT_DEPTH if depth is None else depth

    var = np.empty([len(year), depth, 332, 362])
    for y in year:
        ds = opener(file_dir, suite_id, y)
        try:
            var_unmask = np.squeeze(ds.variables[var_read][:, :depth, ], axis=0)
        finally:
            ds.close()

        if if_mask_isf:
            fm = open_isf_file(isf_dir, suite_id, y)
            try:
                isf_mask = np.squeeze(fm.variables['sowflisf'][:], axis=0)
            finally:
                fm.close()
            isf_mask_4d = pf.boost_dimension(isf_mask, np.shape(var_unmask))
            var[y - year_start, ] = np.where(isf_mask_4d == 0, var_unmask, 0)
        else:
            var[y - year_start, ] = var_unmask
    return var


def read_Arctic(suite_id, file_dir, var_read, grid='T', year=None, depth=None):
    opener = _opener(grid)
    year, year_start = _resolve_years(suite_id, year)
    depth = _DEFAULT_DEPTH if depth is None else depth

    var = np.empty([len(year), depth, 332, 362])
    for y in year:
        ds = opener(file_dir, suite_id, y)
        try:
            var[y - year_start, ] = np.squeeze(ds.variables[var_read][:, :depth, ], axis=0)
        finally:
            ds.close()

    with nc.Dataset(MASK_PATH, 'r') as ds_mask:
        arctic = np.squeeze(ds_mask.variables['Arctic_Ocean'][:])  # (y, x)

    # broadcast the 2D mask over (time, depth) and mask out non-Arctic points
    return np.ma.masked_where(np.broadcast_to(arctic == 0, var.shape), var)


def prep_var(suite_id, file_dir, var_read, grid='T',
             if_SO=False, if_continental_shelf=False,
             if_global=True, if_Arctic_ocean=False, isf_dir=None):
    if if_SO or if_continental_shelf:
        if if_continental_shelf:
            print('the Southern Ocean continental shelf seas will be calculated')
        else:
            print('the Southern Ocean will be calculated')
        var = read_SO(suite_id, file_dir, var_read, grid=grid,
                      if_continental_shelf=if_continental_shelf, isf_dir=isf_dir)
    if if_global:
        print('the global ocean will be calculated')
        var = read_global(suite_id, file_dir, var_read, grid=grid, isf_dir=isf_dir)
    if if_Arctic_ocean:
        print('the Arctic Ocean will be calculated')
        var = read_Arctic(suite_id, file_dir, var_read, grid=grid)
    return var


# ---------------------------------------------------------------------------
# Derived quantities
# ---------------------------------------------------------------------------
def timeseries_3d(suite_id, file_dir, var_read, grid='T',
                  if_SO=True, if_continental_shelf=False,
                  if_global=False, if_Arctic_ocean=False, isf_dir=None):
    var = prep_var(suite_id, file_dir, var_read, grid=grid,
                   if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                   if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                   isf_dir=isf_dir)
    return {p: np.ma.mean(mask_zeros(var[:, idx, :, :]), axis=(1, 2, 3))
            for p, idx in DEPTH_BANDS.items()}


def hovemoller_3d(suite_id, file_dir, var_read, grid='T',
                  if_SO=True, if_continental_shelf=False,
                  if_global=False, if_Arctic_ocean=False, isf_dir=None):
    var = prep_var(suite_id, file_dir, var_read, grid=grid,
                   if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                   if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                   isf_dir=isf_dir)
    return np.ma.mean(mask_zeros(var), axis=(2, 3))


def global_moc(suite_id, file_dir, var_read, grid='V',
               if_SO=False, if_continental_shelf=False,
               if_global=True, if_Arctic_ocean=False, isf_dir=None):
    vmo = prep_var(suite_id, file_dir, var_read, grid=grid,
                   if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                   if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                   isf_dir=isf_dir)
    V = np.ma.sum(vmo, axis=3)
    MOC = np.ma.cumsum(V, axis=1)
    return MOC / 1026 / 1e6  # kg/s mass transport -> Sv


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
def write_timeseries_3d(suite_id, file_dir, var_read, path_out, filename_out,
                        varout_name, units, grid='T',
                        if_SO=True, if_continental_shelf=False,
                        if_global=False, if_Arctic_ocean=False, isf_dir=None):
    ts = timeseries_3d(suite_id, file_dir, var_read, grid=grid,
                       if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                       if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                       isf_dir=isf_dir)
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


def write_hovemoller_3d(suite_id, file_dir, var_read, path_out, filename_out,
                        varout_name, units, grid='T',
                        if_SO=True, if_continental_shelf=False,
                        if_global=False, if_Arctic_ocean=False, isf_dir=None):
    hov = hovemoller_3d(suite_id, file_dir, var_read, grid=grid,
                        if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                        if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                        isf_dir=isf_dir)
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
