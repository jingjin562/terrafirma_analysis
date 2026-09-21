#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_dn026.py  --  batch post-processing job for suite cz826 (shelf-sea diagnostics).

Uses the engine in run_timeseries.py. Edit the base Config and the run(...) calls
below, then:  python run_cz826.py
(To run the same set for another suite, copy this file and change suite_id.)
"""
import sys
sys.path.append('/home/users/jingj/python_script/')
sys.path.append('/home/users/jingj/')
from terrafirma_analysis.run_timeseries import Config, run


def main():
    cfg = Config(suite_id="dn026", suite_prefix="u-", region="shelf")
    run(cfg.but(var_read='sohflisf', varname_out='ice_latent_heat', units_out="W", task="isf"))
    
    """
    # --- 3D salinity / temperature, depth-band means ---

    run(cfg.but( var_read='so',
                task="nemo_3d",
                varname_out={'0': 'so_0_120m', '1': 'so_120_400m',
                             '2': 'so_400_850m', '3': 'so_below_850m',
                             '4': 'so_full_depth'},
                units_out="psu"))

    run(cfg.but(var_read='thetao',
                task="nemo_3d",
                varname_out={'0': 'thetao_0_120m', '1': 'thetao_120_400m',
                             '2': 'thetao_400_850m', '3': 'thetao_below_850m',
                             '4': 'thetao_full_depth'},
                units_out="degree_C"))

    # --- single water-flux fields ---
    run(cfg.but(var_read='fsitherm', task="water_flux"))
    run(cfg.but(var_read='friver', task="water_flux"))
    run(cfg.but(var_read='ficeberg', task="water_flux"))
    run(cfg.but(var_read='pr', task="water_flux"))
    run(cfg.but(var_read='prsn', task="water_flux"))
    run(cfg.but(var_read='evs', task="water_flux"))
    
    # --- AIS basal mass loss ---
    run(cfg.but(var_read='sowflisf', varname_out='basal_mass_loss', units_out="Gt/yr", task="isf"))
    run(cfg.but(var_read='sohflisf', varname_out='ice_latent_heat', units_out="W", task="isf"))
    
    # --- 2D surface / bottom fields ---
    run(cfg.but(var_read='tos', units_out="degree_C", task="nemo_2d"))
    run(cfg.but(var_read='tob', units_out="degree_C", task="nemo_2d"))
    run(cfg.but(var_read='sob', units_out="psu", task="nemo_2d"))
    run(cfg.but(var_read='soicecov', units_out="m2", task="nemo_2d"))
    run(cfg.but(var_read='hfds', units_out="W", task="nemo_2d"))
    run(cfg.but(var_read='mlotstmax', units_out="m", task="nemo_2d"))
    
    # --- freshwater budget (all four components from one read pass) ---
    run(cfg.but(task="all_FW"))

    # --- circulation strength ----
    run(cfg.but(task="SMOC_strength"))
    run(cfg.but(task="lower_cell_strength"))
    run(cfg.but(task="DrakePassage"))
      
    # --- depth-vs-time hovmoller (both variables into one file) ---
    
    hov = f"{cfg.suite_id}_shelfsea_hovemoller.nc"
    run(cfg.but(filename_out=hov, var_read='so', units_out='psu', task="hovemoller"))
    run(cfg.but(filename_out=hov, var_read='thetao', units_out='degree_C', task="hovemoller"))
    """
    
if __name__ == "__main__":
    main()
