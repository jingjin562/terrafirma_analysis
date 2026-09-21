#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:38:17 2025

@author: jingjin

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
def _walk_files_cached(root_dir):
    """Return, and cache, every file path under root_dir (walked once)."""
    out = []
    for subdir, _, files in os.walk(root_dir):
        out.extend(os.path.join(subdir, f) for f in files)
    return tuple(out)


def _walk_files(root_dir):
    """Every file under root_dir, cached, keyed on the *normalised* path.

    Without normalising, '/a/b', '/a/b/' and '/a//b//' are three different cache
    keys for one directory, so the tree would be walked three times. Repeated
    slashes are harmless to the OS but not to an lru_cache.
    """
    return _walk_files_cached(os.path.normpath(root_dir))


# keep cache introspection/clearing available on the public name
_walk_files.cache_info = _walk_files_cached.cache_info
_walk_files.cache_clear = _walk_files_cached.cache_clear


def _match(root_dir, pattern):
    """All files under root_dir whose basename matches a glob-style pattern."""
    return [p for p in _walk_files(root_dir)
            if fnmatch.fnmatch(os.path.basename(p), pattern)]


def clear_file_cache():
    """Drop cached directory listings and areas.

    Call this if files are added/removed on disk within the same Python session
    (e.g. an interactive session where new model output has appeared).
    """
    _walk_files_cached.cache_clear()
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
    return list_nc_files_T(root_dir, suite_id, timestamp, freq='1m')

def list_nc_files_T(root_dir, suite_id, timestamp, freq='1y'):
    return _match(root_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_grid-T.nc')

def list_nc_files_U(root_dir, suite_id, timestamp, freq='1y'):
    return _match(root_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_grid-U.nc')

def list_nc_files_V(root_dir, suite_id, timestamp, freq='1y'):
    return _match(root_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_grid-V.nc')

def list_nc_files_isf(root_dir, suite_id, timestamp, freq='1y'):
    return _match(root_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_isf-T.nc')

def list_nc_files_diaptr(root_dir, suite_id, timestamp, freq='1y'):
    return _match(root_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_diaptr.nc')

def list_nc_files_medusa(root_dir, suite_id, timestamp, freq='1y'):
    return _match(root_dir, f'medusa_{suite_id}o_{freq}_{timestamp}_diad-T.nc')

def list_bathy_files(root_dir, suite_id):
    return _match(root_dir, f'bisicles_{suite_id}c_*bathymetry-isf.nc')


# ----------------------------------------------------------------------------
# File openers (signatures unchanged)
# ----------------------------------------------------------------------------
def open_monthly_nemo_file(file_dir, suite_id, year_to_read, month_to_read):
    # NOTE: the original called the 1y lister here, so it could never match a
    # monthly file. It now uses the 1m pattern.
    timestamp = f"{year_to_read}{month_to_read}-*"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_1m_{timestamp}_grid-T.nc')
    return nc.Dataset(nc_files, 'r')

def open_nemo_file(file_dir, suite_id, year_to_read, freq='1y'):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_grid-T.nc')
    return nc.Dataset(nc_files, 'r')

def open_nemoU_file(file_dir, suite_id, year_to_read, freq='1y'):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_grid-U.nc')
    return nc.Dataset(nc_files, 'r')

def open_nemoV_file(file_dir, suite_id, year_to_read, freq='1y'):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_grid-V.nc')
    return nc.Dataset(nc_files, 'r')

def open_diaptr_file(file_dir, suite_id, year_to_read, freq='1y'):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_diaptr.nc')
    return nc.Dataset(nc_files, 'r')

def open_medusa_file(file_dir, suite_id, year_to_read, freq='1y'):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'medusa_{suite_id}o_{freq}_{timestamp}_diad-T.nc')
    return nc.Dataset(nc_files, 'r')

def open_isf_file(file_dir, suite_id, year_to_read, freq='1y'):
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_isf-T.nc')
    return nc.Dataset(nc_files, 'r')


@lru_cache(maxsize=None)
def read_area(if_SO_focus=False):
    # Cell area is static across suites, so read it once from the packaged mask
    # file instead of re-opening (and leaking) model output on every call.
    # if_SO_focus=True returns the Southern-Ocean subset (first 113 rows).
    import terrafirma_analysis
    pkg_dir = list(terrafirma_analysis.__path__)[0]
    mask_path = os.path.join(pkg_dir, 'utils', 'masks', 'sea_level_mask.nc')
    ds = nc.Dataset(mask_path, 'r')
    try:
        return ds.variables["area"][0, :113, ] if if_SO_focus else ds.variables["area"][0, :]
    finally:
        ds.close()


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
