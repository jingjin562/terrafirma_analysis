#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nemoU_3d.py -- U-grid front-end (thin wrapper over nemo_grid_3d, grid='U').
Historical defaults preserved: prep_var defaults to the global ocean.
"""
import terrafirma_analysis.nemo_grid_3d as _c


def read_SO_nemoU_3d(suite_id, file_dir, var_read, year=None, depth=None,
                     if_continental_shelf=False, slope_isobathy=1200, if_mask_isf=True,
                     isf_dir=None):
    return _c.read_SO(suite_id, file_dir, var_read, grid='U', year=year, depth=depth,
                      if_continental_shelf=if_continental_shelf,
                      slope_isobathy=slope_isobathy, if_mask_isf=if_mask_isf,
                      isf_dir=isf_dir)


def read_global_nemoU_3d(suite_id, file_dir, var_read, year=None, depth=None):
    return _c.read_global(suite_id, file_dir, var_read, grid='U', year=year, depth=depth)


def read_Arctic_Ocean_nemoU_3d(suite_id, file_dir, var_read, year=None, depth=None):
    return _c.read_Arctic(suite_id, file_dir, var_read, grid='U', year=year, depth=depth)


def prep_var(suite_id, file_dir, var_read,
             if_SO=False, if_continental_shelf=False,
             if_global=True, if_Arctic_ocean=False, isf_dir=None):
    return _c.prep_var(suite_id, file_dir, var_read, grid='U',
                       if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                       if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                       isf_dir=isf_dir)
