#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_{suite_id}_sectors.py  --  batch shelf-SECTOR diagnostics for suite cz826.

Uses the engine in run_sectors.py. Every variable is run for all 10 Antarctic
shelf sectors via run_all_regions, and everything lands in ONE consolidated
netCDF, with region-qualified variable names so nothing collides:
    test_cz826_shelfsea_sectors.nc
      ross_shelfsea_tos, amundsen_sea_shelfsea_tos, ...     (1D, time)
      ross_so_0_120m, ross_so_full_depth, ...               (1D, time)
      ross_so_hov, ross_thetao_hov, ...                     (2D, time x lev)

To run the same set for another suite, copy this file and change suite_id.
    python run_cz826_sectors.py
"""
import sys
sys.path.append('/home/users/jingj/python_script/')
sys.path.append('/home/users/jingj/')
from terrafirma_analysis.run_sectors import Config, run_all_regions


def main():
    cfg = Config(suite_id="dn026", suite_prefix="u-")
    
    # ---- basal mass loss ----
    run_all_regions(cfg.but(var_read="sowflisf", task="sector_2d", varname_out='massloss')) 
    
"""
    # --- 3D depth-band means (T-grid) ---
    run_all_regions(cfg.but(
        var_read="so", task="sector_3d",
        varname_out={'0': 'so_0_120m', '1': 'so_120_400m',
                     '2': 'so_400_850m', '3': 'so_below_850m',
                     '4': 'so_full_depth'},
        units_out="psu"))

    run_all_regions(cfg.but(
        var_read="thetao", task="sector_3d",
        varname_out={'0': 'thetao_0_120m', '1': 'thetao_120_400m',
                     '2': 'thetao_400_850m', '3': 'thetao_below_850m',
                     '4': 'thetao_full_depth'},
        units_out="degree_C"))
    
    # --- 2D surface / bottom fields (units passed straight through) ---
    for var, units in [
        ("tos",       "degree_C"),
        ("sos",       "psu"),
        ("tob",       "degree_C"),
        ("sob",       "psu"),
    ]:
        run_all_regions(cfg.but(var_read=var,
                                units_out=units, task="sector_2d"))

    # --- 2D water-flux fields (writer overrides units_out -> Gt/yr) ---
    for var in ['fsitherm', 'friver', 'ficeberg', 'pr', 'prsn', 'evs']:
        run_all_regions(cfg.but(var_read=var,
                                task="sector_2d"))
                                
    # --- freshwater budget (all four components from one read pass) ---
    run_all_regions(cfg.but(task="all_FW"))

    # --- 2D fields with special area-integrated handling in the writer ---
    run_all_regions(cfg.but(var_read="soicecov",
                            task="sector_2d"))            # writer -> units m2
    run_all_regions(cfg.but(var_read="hfds",
                            task="sector_2d"))            # writer -> units W

    # --- depth-vs-time hovmoller (T-grid); explicit *_hov names so these
    #     (time x lev) fields are unambiguous next to the surface fields ---
    hov_dir = f"{cfg.suite_id}_shelfsea_sectors_hovemoller.nc"
    run_all_regions(cfg.but(filename_out=hov_dir, var_read="so",
                            varname_out="so_hov", units_out="psu",
                            task="sector_hovemoller"))
    run_all_regions(cfg.but(filename_out=hov_dir, var_read="thetao",
                            varname_out="thetao_hov", units_out="degree_C",
                            task="sector_hovemoller"))
"""

if __name__ == "__main__":
    main()
