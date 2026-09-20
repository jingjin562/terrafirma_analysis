#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 11:16:50 2026

@author: jingjin
"""

geodef_for_circulation = {
    'AMOC':         228,                 # lat 26.5 N
    'lower_cell':   139,                 # lat 30 S
    'SMOC':         105,                 # lat 55 S
    'DrakePassage': (219, 79, 107),      # lon, lat1, lat2
}


# ----- Dictionary of x and y at bottom left and top right describing isf cavity region -------
# ----- May be multiple boxes if a isf cavity has irregular shape ------
# ---- e.g. ''amery'  : {'box1': [[x of bottom left, x of top right], [y of bottom left, y of top right]], 
#                        'box2': [[x of bottom left, x of top right], [y of bottom left, y of top right]],
#                        'box3': .... }, ----

isf_cavity = {
    'amery'             : {'box1': [[350, 362], [60, 80]], 'box2':[[0, 4], [60, 77]],},
    'amundsen_sea'      : {'box1': [[140, 189], [40, 61]], 'box2':[[133, 140], [40, 48]], 'box3': [[128, 133],[43, 48]],},
    'bellingshausen_sea': {'box1': [[189, 221], [58, 95]],},  
    'larsen'            : {'box1': [[222, 240], [60, 95]],},  
    'ross'              : {'box1': [[70, 133], [0, 44]], 'box2':[[133, 150], [0, 40]],},  
    'filchner_ronne'    : {'box1': [[195, 280], [0, 45]], 'box2':[[195, 245], [45, 59]],},
    'wilkes'            : {'box1': [[250, 350], [45, 90]],},
    'dronning_maud'     : {'box1': [[4, 110], [45, 90]],},
    'east_antarctica'   : {'box1': [[4, 110], [45, 90]], 'box2': [[250, 350], [45, 90]], 'box3': [[350, 362], [60, 80]], 'box4':[[0, 4], [60, 77]],}, # Dronning Maud + Amery + Wilkes
    'west_antarctica'   : {'box1': [[140, 189], [40, 61]], 'box2':[[133, 140], [40, 48]], 'box3': [[128, 133],[43, 48]], 'box4': [[189, 221], [58, 95]],}, 
    }

# Dictionary of x and y describing key waypoints for transect paths.
# ---- e.g. 'amery': [[x grid points], [y grid points]] ----
transect_SO = {
    'pine_island':[[173, 176, 178, 181, 183, 184, 186], [80, 68, 60, 56, 54, 52, 50]],
    'ross' :[[122, 123, 125, 127, 134], [55, 51, 45, 41, 35]],
    'filchner_ronne':[[260, 258, 256, 253, 250, 247, 248], [60, 57, 53, 50, 46, 42, 38]],
    'amery':[[359, 359], [84, 70]],
}

# ---- definition of AIS continental shelfsea
slope_isobathy = 1200 #--- m
shelfsea_lat = -58    # --- N

# Dictionary of lon-lat points bounding given region. Will be used to "cut" the continental shelf mask (build_shelf_mask in utils.py) either north-south or east-west depending on the value of region_edges_flag. The first point and its connected N/S (or E/W) neighbours will be included in the mask, but not the second. The direction of travel is west to east around the coastline.
region_edges = {
    'abbot'             : [[-103.2, -71.8] , [-83, -72]],
    'amery'             : [[60, -67.0]   , [79.5, -68]],
    'amundsen_sea'      : [[-157.5, -76.5] , [-102.48, -72.0]],
    'bellingshausen_sea': [[-102.48, -72.0], [-56.5, -61.72]],
    'cosgrove'          : [[-104.24, -73.846], [-102.91, -73.2]],
    'dotson_crosson'    : [[-114.7, -73.8] , [-107.5, -75.3]],
    'dotson_front'      : [[-112.5, -74.4] , [-110.5, -73.85]], # just shelf
    'pine_island'       : [[-102.6, -75.1] , [-101.5, -74.2]],
    'pine_island_bay'   : [[-104.0, -74.8] , [-103, -74.2]], # just shelf
    'dotson_cosgrove'   : [[-114.7, -73.8] , [-102.91, -73.2]],
    'dronning_maud'     : [[-23.42, -73.85] , [60, -67.0]],
    'wilkes'            : [[79.5, -68] , [169.5, -71]],
    'east_antarctica'   : [[-23.42, -73.85]    , [169.5 , -71]], # Dronning Maud + Amery + Wilkes
    'filchner_ronne'    : [[-57, -71.5]    , [-23.42, -73.85]],
    'getz'              : [[-135, -74.5]   , [-114.7, -73.8]],
    'larsen'            : [[-56.5, -61.72]   , [-57, -71.5]],
    'ross'              : [[169.5, -71]    , [-157.5, -76.5]],
    'thwaites'          : [[-107.5, -75.3] , [-103.6, -74.5]],
    'west_antarctica'   : [[-157.5, -76.5] , [-56.5, -61.72]], # Amundsen and Bellingshausen
}

region_edges_flag = {
    'abbot'             : ['NS', 'NS'],
    'amery'             : ['NS', 'NS'],
    'amundsen_sea'      : ['NS', 'NS'],
    'bellingshausen_sea': ['NS', 'NS'],
    'cosgrove'          : ['EW', 'EW'],
    'dotson_crosson'    : ['NS', 'NS'],
    'dotson_front'      : ['EW', 'EW'],
    'dotson_cosgrove'   : ['NS', 'EW'],
    'dronning_maud'     : ['NS', 'NS'],
    'wilkes'            : ['NS', 'NS'],
    'east_antarctica'   : ['NS', 'NS'],
    'filchner_ronne'    : ['EW', 'NS'],
    'getz'              : ['NS', 'NS'],
    'larsen'            : ['NS', 'EW'],
    'pine_island'       : ['NS', 'EW'], 
    'pine_island_bay'   : ['NS', 'EW'],
    'ross'              : ['NS', 'NS'],
    'thwaites'          : ['NS', 'EW'],
    'west_antarctica'   : ['NS', 'NS'],
}

# Names of each region
region_names = {
    'all'               : 'Antarctic',
    'abbot'             : 'Abbot Ice Shelf',
    'amery'             : 'Amery',
    'amundsen_sea'      : 'Amundsen Sea',
    'amundsen_west_shelf_break': 'Western Amundsen Sea shelf break',
    'bellingshausen_sea': 'Bellingshausen Sea',
    'brunt'             : 'Brunt and Riiser-Larsen Ice Shelves',
    'cosgrove'          : 'Cosgrove Ice Shelf',
    'dotson_crosson'    : 'Dotson-Crosson Ice Shelf',
    'dotson_front'      : 'front of Dotson',
    'dronning_maud'     : 'Dronning Maud Land',
    'wilkes'            : 'Wilkes Land',
    'east_antarctica'   : 'East Antarctica',
    'filchner_ronne'    : 'Filchner-Ronne',
    'getz'              : 'Getz Ice Shelf',
    'larsen'            : 'Larsen',
    'pine_island'       : 'Pine Island Ice Shelf',
    'pine_island_bay'   : 'Pine Island Bay',
    'ross'              : 'Ross',
    'thwaites'          : 'Thwaites Ice Shelf',
    'west_antarctica'   : 'West Antarctica',
    'filchner_trough'   : 'Filchner Trough',
    'ronne_depression'  : 'Ronne Depression',
    'LAB_trough'        : 'Little America Basin Trough',
    'drygalski_trough'  : 'Drygalski Trough',
    'dotson_cosgrove'   : 'Dotson to Cosgrove',
    'weddell_gyre'      : 'Weddell Gyre',
    'ross_gyre'         : 'Ross Gyre',
}