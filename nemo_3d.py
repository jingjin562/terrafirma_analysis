#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nemo_3d.py -- T-grid front-end.

Thin wrapper over nemo_grid_3d (grid='T'). All the shared logic now lives in
that module; this file only fixes the grid and the historical default flags so
that existing imports and call sites keep working unchanged.
"""
import terrafirma_analysis.nemo_grid_3d as _c
from terrafirma_analysis.nemo_grid_3d import DEPTH_BANDS  # noqa: F401 (re-export)


def read_SO_nemo_3d(suite_id, file_dir, var_read, year=None, depth=None,
                    if_continental_shelf=False, slope_isobathy=1200, if_mask_isf=True,
                    isf_dir=None):
    return _c.read_SO(suite_id, file_dir, var_read, grid='T', year=year, depth=depth,
                      if_continental_shelf=if_continental_shelf,
                      slope_isobathy=slope_isobathy, if_mask_isf=if_mask_isf,
                      isf_dir=isf_dir)


def read_global_nemo_3d(suite_id, file_dir, var_read, year=None, depth=None,
                        if_mask_isf=False, isf_dir=None):
    return _c.read_global(suite_id, file_dir, var_read, grid='T', year=year, depth=depth,
                          if_mask_isf=if_mask_isf, isf_dir=isf_dir)


def read_Arctic_Ocean_nemo_3d(suite_id, file_dir, var_read, year=None, depth=None):
    return _c.read_Arctic(suite_id, file_dir, var_read, grid='T', year=year, depth=depth)


def prep_var(suite_id, file_dir, var_read,
             if_SO=True, if_continental_shelf=False,
             if_global=False, if_Arctic_ocean=False, isf_dir=None):
    return _c.prep_var(suite_id, file_dir, var_read, grid='T',
                       if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                       if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                       isf_dir=isf_dir)


def nemo_3d_timeseries(suite_id, file_dir, var_read,
                       if_SO=True, if_continental_shelf=False,
                       if_global=False, if_Arctic_ocean=False, isf_dir=None):
    return _c.timeseries_3d(suite_id, file_dir, var_read, grid='T',
                            if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                            if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                            isf_dir=isf_dir)


def nemo_3d_hovemoller(suite_id, file_dir, var_read,
                       if_SO=True, if_continental_shelf=False,
                       if_global=False, if_Arctic_ocean=False, isf_dir=None):
    return _c.hovemoller_3d(suite_id, file_dir, var_read, grid='T',
                            if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                            if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                            isf_dir=isf_dir)


def write_nemo_3d_timeseries(suite_id, file_dir, var_read, path_out, filename_out,
                             varout_name, units,
                             if_SO=True, if_continental_shelf=False,
                             if_global=False, if_Arctic_ocean=False, isf_dir=None):
    return _c.write_timeseries_3d(suite_id, file_dir, var_read, path_out, filename_out,
                                  varout_name, units, grid='T',
                                  if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                                  if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                                  isf_dir=isf_dir)


def write_nemo_3d_hovemoller(suite_id, file_dir, var_read, path_out, filename_out,
                             varout_name, units,
                             if_SO=True, if_continental_shelf=False,
                             if_global=False, if_Arctic_ocean=False, isf_dir=None):
    return _c.write_hovemoller_3d(suite_id, file_dir, var_read, path_out, filename_out,
                                  varout_name, units, grid='T',
                                  if_SO=if_SO, if_continental_shelf=if_continental_shelf,
                                  if_global=if_global, if_Arctic_ocean=if_Arctic_ocean,
                                  isf_dir=isf_dir)


def main():
    suite_id = ''
    file_dir = f'/home/jingjin/work/terrafirma/{suite_id}/thetao+so/'
    var_read = 'so'
    path_out = "/home/jingjin/work/postpro/misc_data/"
    filename_out = f"{suite_id}_test_timeseries.nc"
    varout_name = {
        '0': 'shelfsea_salinity_0_120m',
        '1': 'shelfsea_salinity_120_400m',
        '2': 'shelfsea_salinity_400_850m',
        '3': 'shelfsea_salinity_below_850m',
        '4': 'shelfsea_salinity_full_depth',
    }
    write_nemo_3d_timeseries(suite_id, file_dir, var_read, path_out, filename_out,
                             varout_name, 'psu', if_continental_shelf=True)


if __name__ == "__main__":
    main()
