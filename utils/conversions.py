#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 13:17:13 2025

@author: jingjin
"""

import numpy as np

def time_coverage(suite_id):
    year_start = {
        'cx209': 1850,
        'cz826': 1850,
        'cw988': 1850,
        'cw989': 1850,
        'cw990': 1850,
        'dn026': 2007,
        'cy838': 1944,
        'cz375': 1992,
        'cz376': 2044,
        'cz377': 2082,
        'cs495': 1950,
        }
    
    year_end = {
        'cx209': 2237,
        'cz826': 2210,
        'cw988': 2197,
        'cw989': 2175,
        'cw990': 2202,
        'dn026': 2219,
        'cy838': 2489,
        'cz375': 2451,
        'cz376': 2573,
        'cz377': 2589,
        'cs495': 2278,
        }
    
    return year_start[suite_id], year_end[suite_id]+1

def mmolC_per_day_to_Gt_per_yr(mmolC_per_day):
    return mmolC_per_day * 1e-3 * 12.011 * 360 * 1e-15

def kg_per_m2_per_s_to_Gt_per_yr(kg_per_m2_per_s, area):
    s2yr = 360 * 24 * 3600
    kg2Gt = 1e-12
    return kg_per_m2_per_s * area * s2yr * kg2Gt

def degree_C_to_K(degree_C):
    return degree_C+273.15