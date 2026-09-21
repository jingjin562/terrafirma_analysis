#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  5 13:16:37 2025

@author: jingjin
"""

import numpy as np  # numerical library
import matplotlib.colors as mcolors

def get_cmap(name, is_set_bad=True):
    import matplotlib
    cmap = matplotlib.colormaps.get_cmap(name)
    if is_set_bad:
        cmap.set_bad([0.7, 0.7, 0.7] ,1)
    return cmap

def line_colors(colorname):
    linecmaps = {'blue': '#1f77b4',
                 'light blue': '#aec7e8',
                 'orange': '#ff7f0e',
                 'light orange': '#ffbb78',
                 'green': '#2ca02c',
                 'light green': '#98df8a',
                 'red': '#d62728',
                 'light red': '#ff9896',
                 'purple': '#9467bd',
                 'light purple': '#c5b0d5',
                 'brown': '#8c564b',
                 'light brown': '#c49c94',
                 'magenta': '#e377c2',
                 'light magenta': '#f7b6d2',
                 'grey': '#7f7f7f',
                 'light grey': '#c7c7c7',
                 'yellow': '#bcbd22',
                 'light yellow': '#dbdb8d',
                 'cyan': '#17becf',
                 'light cyan': '#9edae5'
                }    
    return linecmaps[colorname]

def uneven_cmap(original_cmap, reduced_ratio, is_set_bad=True):
    # Retrieve the original colormap
    
    # Convert the colormap to an array of RGBA values
    num_colors = 256  # Number of colors in the colormap
    colors = original_cmap(np.linspace(0, 1, num_colors))
    
    if reduced_ratio < 0:
        reduced_ratio = np.abs(reduced_ratio)
    
    if reduced_ratio > 1:        
        # Define the slicing indices (example: slice every 6th color from 1 to 118 and all colors from 138 to end)
        slice1 = slice(1, 128, round(reduced_ratio))  # 1 to 118, step 6
        slice2 = slice(129, None)  # 138 to end
    else:
        slice1 = slice(1, 128)
        slice2 = slice(129, num_colors, round(1/reduced_ratio))
    
    # Slice and concatenate
    modified_colors = np.vstack([colors[slice1], colors[slice2]])
    
    uneven_map = mcolors.LinearSegmentedColormap.from_list('custom_colormap', modified_colors)
    
    if is_set_bad:
        uneven_map.set_bad([0.7, 0.7, 0.7] ,1)
        
    # Create a new colormap
    return uneven_map

def set_bad_cmap(cmap):
    cmap.set_bad([0.7, 0.7, 0.7] ,1)
    return cmap