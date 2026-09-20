#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 10:43:38 2026

@author: jingjin
"""

import netCDF4 as nc
import numpy as np
import os
import os.path as op
import terrafirma_analysis
from terrafirma_analysis.io_core import create_dimensions_time, create_variables_1d_timeseries
from terrafirma_analysis.io_core import open_diaptr_file
from terrafirma_analysis.utils.conversions import time_coverage


def read_nemo_diaptr(suite_id, file_dir, var_read):
    
    year_start, year_end = time_coverage(suite_id)
    year = np.arange(year_start, year_end, 1)
    var = np.empty([len(year), 75, 332, 1])
    
    for y in year:
        ds = open_diaptr_file(file_dir, suite_id, y)
        try:
            var[y-year_start, ] = ds.variables[var_read][:]
        finally:
            ds.close()
    return np.squeeze(var)

def read_global_MOC_mean(suite_id, file_dir):
    print("var_read is overwritten to 'zomsfglo'")
    MOC_mean = read_nemo_diaptr(suite_id, file_dir, 'zomsfglo')
    return MOC_mean

def read_global_MOC_eddy(suite_id, file_dir):
    print("var_read is overwritten to 'zomsfeivglo'")
    MOC_eddy = read_nemo_diaptr(suite_id, file_dir, 'zomsfeivglo')
    return MOC_eddy

def read_AMOC_mean(suite_id, file_dir):
    print("var_read is overwritten to 'zomsfatl'")
    AMOC_mean = read_nemo_diaptr(suite_id, file_dir, 'zomsfatl')
    return AMOC_mean

def read_AMOC_eddy(suite_id, file_dir):
    print("var_read is overwritten to 'zomsfeivatl'")
    AMOC_eddy = read_nemo_diaptr(suite_id, file_dir, 'zomsfeivatl')
    return AMOC_eddy


    