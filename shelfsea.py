#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:18:25 2025

@author: jingjin

Changes vs. the original (mask values and masking logic are unchanged):
  * list_bathy_files is imported from terrafirma_analysis.io_core, where it
    actually lives; the original imported it from a `terrafirma_files_read`
    module that is not part of the package.
  * The bathymetry file read is cached (_read_bathy). The file is static per
    suite, so a batch of shelf diagnostics now reads it once instead of once per
    reader call. Only the raw fields are cached; the shelf mask is re-derived on
    every call, so callers still get a fresh array they are free to modify.
  * The silent suite_id fallback now prints, in the same style as the rest of
    the package, so it is visible when a suite has no bathymetry of its own.
"""

import numpy as np
import netCDF4 as nc
from functools import lru_cache

from terrafirma_analysis.io_core import list_bathy_files
import plotting_functions as pf

# Suites that have their own bathymetry-isf output. Anything else falls back to
# cx209 (see the note in AIS_continental_shelf).
_SUITES_WITH_BATHY = ('cx209', 'cz826')

BATHY_PATH = '/gws/ssde/j25b/terrafirma/jjin/cavity_analysis/overshoot/{suite_id}/icesheet/bathymetry-isf'

def clear_bathy_cache():
    """Drop the cached bathymetry (call if the underlying files change)."""
    _read_bathy.cache_clear()


@lru_cache(maxsize=None)
def _read_bathy(suite_id, if_global):
    """Read Bathymetry_isf / isf_draft once per (suite, extent).

    The returned arrays are cached and must not be modified in place; callers
    derive new arrays from them via np.where.
    """
    path = BATHY_PATH.format(suite_id=suite_id)
    bathy_file = list_bathy_files(path, suite_id)[0]

    with nc.Dataset(bathy_file, 'r') as ds:
        if if_global:
            bathy_isf = ds.variables['Bathymetry_isf'][:]
            isf_draft = ds.variables['isf_draft'][:]
        else:
            bathy_isf = ds.variables['Bathymetry_isf'][:113, ]
            isf_draft = ds.variables['isf_draft'][:113, ]
    return bathy_isf, isf_draft


def AIS_continental_shelf(suite_id, slope_isobathy=1200, if_global=False,
                          if_return_bathy=False):
    if suite_id not in _SUITES_WITH_BATHY:
        print(f'no bathymetry-isf output for {suite_id}; '
              f'the cx209 bathymetry is used instead')
        suite_id = 'cx209'

    bathy_isf, isf_draft = _read_bathy(suite_id, if_global)

    bathy_openocean = np.where(isf_draft != 0, 0, bathy_isf)
    shelfsea = np.where(bathy_openocean > slope_isobathy, 0, bathy_openocean)
    shelfsea[97:, ] = 0

    if if_return_bathy:
        return {
            'bathy_isf': bathy_isf.copy(),   # copies: the cached arrays are shared
            'isf_draft': isf_draft.copy(),
            'shelfsea': shelfsea,
        }
    else:
        return shelfsea


def shelfsea_masking(suite_id, var, shelfsea_mask=None, if_global=False):
    if shelfsea_mask is None:
        shelfsea_mask = AIS_continental_shelf(suite_id, if_global=if_global)

    dim = len(np.shape(var))
    if dim == 2:
        return np.where(shelfsea_mask == 0, 0, var)
    elif dim == 3:
        return np.where(pf.boost_dimension(shelfsea_mask, np.shape(var)) == 0, 0, var)
    else:
        raise ValueError("Input variable must be 2D or 3D only")
