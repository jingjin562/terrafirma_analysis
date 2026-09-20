#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_cz826.py  --  batch post-processing job for suite cz826 (shelf-sea diagnostics).

Uses the engine in run_timeseries.py. Edit the base Config and the run(...) calls
below, then:  python run_cz826.py
(To run the same set for another suite, copy this file and change suite_id.)
"""
import sys
sys.path.append('/home/jingjin/work/postpro/')
sys.path.append('/home/jingjin/work/terrafirma/')
from terrafirma_analysis.run_timeseries import Config, run


def main():
    cfg = Config(suite_id="cx209", isf_var_dir='sowflisf', region="shelf")
    
    # --- 3D salinity / temperature, depth-band means ---
    
    run(cfg.but(var_dir="thetao+so",
                var_read='so',
                task="nemo_3d",
                varname_out={'0': 'shelfsea_so_0_120m', '1': 'shelfsea_so_120_400m',
                             '2': 'shelfsea_so_400_850m', '3': 'shelfsea_so_below_850m',
                             '4': 'shelfsea_so_full_depth'},
                units_out="psu"))

    run(cfg.but(var_dir="thetao+so",
                var_read='thetao',
                task="nemo_3d",
                varname_out={'0': 'shelfsea_thetao_0_120m', '1': 'shelfsea_thetao_120_400m',
                             '2': 'shelfsea_thetao_400_850m', '3': 'shelfsea_thetao_below_850m',
                             '4': 'shelfsea_thetao_full_depth'},
                units_out="degree_C"))
    
    # --- single water-flux fields ---
    run(cfg.but(var_dir="water_fluxes", var_read='fsitherm', task="water_flux"))
    run(cfg.but(var_dir="water_fluxes", var_read='friver', task="water_flux"))
    run(cfg.but(var_dir="water_fluxes", var_read='ficeberg', task="water_flux"))
    run(cfg.but(var_dir="water_fluxes", var_read='pr', task="water_flux"))
    run(cfg.but(var_dir="water_fluxes", var_read='prsn', task="water_flux"))
    run(cfg.but(var_dir="water_fluxes", var_read='evs', task="water_flux"))
    
    # --- AIS basal mass loss ---
    run(cfg.but(var_dir="sowflisf", var_read='sowflisf', task="isf"))
    
    # --- 2D surface / bottom fields ---
    run(cfg.but(var_dir="water_fluxes", var_read='tos', units_out="degree_C", task="nemo_2d"))
    run(cfg.but(var_dir="water_fluxes", var_read='sos', units_out="psu", task="nemo_2d"))
    run(cfg.but(var_dir="tob+sob", var_read='tob', units_out="degree_C", task="nemo_2d"))
    run(cfg.but(var_dir="tob+sob", var_read='sob', units_out="psu", task="nemo_2d"))
    run(cfg.but(var_dir="soicecov", var_read='soicecov', units_out="m2", task="nemo_2d"))
    run(cfg.but(var_dir="hfds", var_read='hfds', units_out="W", task="nemo_2d"))
    run(cfg.but(var_dir="mlotstmax", var_read='mlotstmax', units_out="m", task="nemo_2d"))
    
    # --- freshwater budget (all four components from one read pass) ---
    run(cfg.but(var_dir="water_fluxes", task="all_FW"))

    # --- depth-vs-time hovmoller (both variables into one file) ---
    hov = f"test_{cfg.suite_id}_shelfsea_hovemoller.nc"
    run(cfg.but(filename_out=hov, var_dir="thetao+so",
                var_read='so', units_out='psu', task="hovemoller"))
    run(cfg.but(filename_out=hov, var_dir="thetao+so",
                var_read='thetao', units_out='degree_C', task="hovemoller"))

    
if __name__ == "__main__":
    main()
