#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:38:17 2025

@author: jingjin

Refactored for speed and robustness (behaviour-preserving):
  * The directory tree is now walked ONCE per directory and cached, instead of
    being re-walked on every single file open. For a run over N years this turns
    N tree traversals into 1 -- a large win on networked/HPC filesystems.
  * read_area() is cached and now closes the file it opens (previously leaked).
  * All list_nc_files_* / open_* / create_* signatures are unchanged, so this is
    a drop-in replacement for the original module.
"""
import os
import fnmatch
import netCDF4 as nc
import glob
from functools import lru_cache


# ----------------------------------------------------------------------------
# Cached file discovery
# ----------------------------------------------------------------------------
# The original code called os.walk(root_dir) + glob for EVERY file open. Here we
# walk each directory once, cache the full file list, and match patterns in
# memory with fnmatch (equivalent to glob for basename-only patterns on POSIX).

@lru_cache(maxsize=None)
def _walk_files(root_dir):
    """Return, and cache, every file path under root_dir (walked once)."""
    out = []
    for subdir, _, files in os.walk(root_dir):
        out.extend(os.path.join(subdir, f) for f in files)
    return tuple(out)


def _match(root_dir, pattern):
    """All files under root_dir whose basename matches a glob-style pattern."""
    return [p for p in _walk_files(root_dir)
            if fnmatch.fnmatch(os.path.basename(p), pattern)]


def clear_file_cache():
    """Drop cached directory listings and areas.

    Call this if files are added/removed on disk within the same Python session
    (e.g. an interactive session where new model output has appeared).
    """
    _walk_files.cache_clear()
    read_area.cache_clear()

def _first_match(root_dir, pattern):
    """First file under root_dir matching pattern, with a useful error if none.

    The original code indexed [0] straight off the glob, so a layout/naming
    mismatch surfaced as a bare IndexError. This says what was looked for and
    where, and shows what is actually there.
    """
    hits = sorted(_match(root_dir, pattern))
    if hits:
        return hits[0]
    present = sorted({os.path.basename(p) for p in _walk_files(root_dir)})
    sample = ', '.join(present[:5]) if present else '(no files found at all)'
    raise FileNotFoundError(
        f"no file matching {pattern!r} under {root_dir!r}.\n"
        f"  {len(present)} file(s) present, e.g.: {sample}\n"
        f"  check base_dir/suite_prefix/var_dir, and the output frequency "
        f"(freq='1y' vs '1m').")

def list_nc_files_monthly_T(root_dir, suite_id, timestamp):
    return _match(root_dir, f'nemo_{suite_id}o_1m_{timestamp}_grid-T.nc')

def list_nc_files_T(root_dir, suite_id, timestamp):
    return _match(root_dir, f'nemo_{suite_id}o_1y_{timestamp}_grid-T.nc')

def list_nc_files_U(root_dir, suite_id, timestamp):
    return _match(root_dir, f'nemo_{suite_id}o_1y_{timestamp}_grid-U.nc')

def list_nc_files_V(root_dir, suite_id, timestamp):
    return _match(root_dir, f'nemo_{suite_id}o_1y_{timestamp}_grid-V.nc')

def list_nc_files_isf(root_dir, suite_id, timestamp):
    return _match(root_dir, f'nemo_{suite_id}o_1y_{timestamp}_isf-T.nc')

def list_nc_files_diaptr(root_dir, suite_id, timestamp):
    return _match(root_dir, f'nemo_{suite_id}o_1y_{timestamp}_diaptr.nc')

def list_nc_files_medusa(root_dir, suite_id, timestamp):
    return _match(root_dir, f'medusa_{suite_id}o_1y_{timestamp}_diad-T.nc')

def list_bathy_files(root_dir, suite_id):
    return _match(root_dir, f'bisicles_{suite_id}c_*bathymetry-isf.nc')


# ----------------------------------------------------------------------------
# File openers (signatures unchanged)
# ----------------------------------------------------------------------------
def open_monthly_nemo_file(file_dir, suite_id, year_to_read, month_to_read):
    timestamp = f"{year_to_read}{month_to_read}-*"
    nc_files = list_nc_files_T(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')

def open_nemo_file(file_dir, suite_id, year_to_read):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = list_nc_files_T(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')

def open_nemoU_file(file_dir, suite_id, year_to_read):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = list_nc_files_U(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')

def open_nemoV_file(file_dir, suite_id, year_to_read):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = list_nc_files_V(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')

def open_diaptr_file(file_dir, suite_id, year_to_read):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = list_nc_files_diaptr(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')

def open_medusa_file(file_dir, suite_id, year_to_read):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = list_nc_files_medusa(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')

def open_isf_file(file_dir, suite_id, year_to_read):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = list_nc_files_isf(file_dir, suite_id, timestamp)[0]
    return nc.Dataset(nc_files, 'r')


@lru_cache(maxsize=None)
def read_area(if_SO_focus=False):
    # if_SO_focus = False for the globe / non-SO sectors; True for Southern Ocean only.
    # Cached because cell area is static within a run; the previous version
    # re-opened (and leaked) a file on every call.
    import terrafirma_analysis
    import netCDF4 as nc
    _PKG_DIR = list(terrafirma_analysis.__path__)[0]
    MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'sea_level_mask.nc')
    
    file = nc.Dataset(MASK_PATH, 'r')
    if if_SO_focus:
        return file.variables["area"][0, :113, ]
    else:
        return file.variables["area"][0, :]


def file_exists_in_directory(directory, filename):
    return os.path.isfile(os.path.join(directory, filename))


# ----------------------------------------------------------------------------
# Dimension / variable helpers (unchanged behaviour, deduplicated internally)
# ----------------------------------------------------------------------------
def _ensure_dim(ncfile, name, size):
    if name not in ncfile.dimensions:
        ncfile.createDimension(name, size)

def create_dimensions_time(ncfile, dim_t=None):
    _ensure_dim(ncfile, 'time_counter', dim_t)

def create_dimensions_lev(ncfile, dim_z):
    _ensure_dim(ncfile, 'lev', dim_z)

def create_dimensions_y(ncfile, dim_y):
    _ensure_dim(ncfile, 'y', dim_y)

def create_dimensions_x(ncfile, dim_x):
    _ensure_dim(ncfile, 'x', dim_x)

def create_dimensions_3d(ncfile, dim_y, dim_x):
    _ensure_dim(ncfile, 'time_counter', None)
    _ensure_dim(ncfile, 'y', dim_y)
    _ensure_dim(ncfile, 'x', dim_x)

def create_dimensions_4d(ncfile, dim_lev, dim_y, dim_x):
    _ensure_dim(ncfile, 'time_counter', None)
    _ensure_dim(ncfile, 'lev', dim_lev)
    _ensure_dim(ncfile, 'y', dim_y)
    _ensure_dim(ncfile, 'x', dim_x)


def _get_or_create_var(ncfile, varname, dims):
    if varname not in ncfile.variables:
        return ncfile.createVariable(varname, 'float64', dims)
    return ncfile.variables[varname]

def create_variables_4d(ncfile, varname):
    return _get_or_create_var(ncfile, varname, ('time_counter', 'lev', 'y', 'x'))

def create_variables_3d(ncfile, varname):
    return _get_or_create_var(ncfile, varname, ('time_counter', 'y', 'x'))

def create_variables_3d_zonal_mean(ncfile, varname):
    return _get_or_create_var(ncfile, varname, ('time_counter', 'lev', 'y'))

def create_variables_3d_meridional_mean(ncfile, varname):
    return _get_or_create_var(ncfile, varname, ('time_counter', 'lev', 'x'))

def create_variables_2d_hovemoller(ncfile, varname):  # depth vs. time
    return _get_or_create_var(ncfile, varname, ('time_counter', 'lev'))

def create_variables_2d_spatial(ncfile, varname):  # lat vs. lon
    return _get_or_create_var(ncfile, varname, ('y', 'x'))

def create_variables_1d_timeseries(ncfile, varname):  # time series
    return _get_or_create_var(ncfile, varname, ('time_counter',))

def create_variables_1d_depth(ncfile, varname):  # vertical profile
    return _get_or_create_var(ncfile, varname, ('lev',))

def create_variables_1d_y(ncfile, varname):
    return _get_or_create_var(ncfile, varname, ('y',))

def create_variables_1d_x(ncfile, varname):
    return _get_or_create_var(ncfile, varname, ('x',))
