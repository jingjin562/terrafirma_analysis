#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 28 11:30:52 2026

@author: jingjin

Adapted from Kaitlin Naughten's nemo_python tool
(https://github.com/knaughten/nemo_python)
"""
import numpy as np
import xarray as xr

# Given a mask (numpy array, 1='land', 0='ocean') and point0 (j,i) on the "mainland", remove any disconnected "islands" from the mask and return.
def remove_disconnected (mask, point0):

    if not mask[point0]:
        raise Exception('point0 is not on the mainland')

    connected = np.zeros(mask.shape)
    connected[point0] = 1
    ny = mask.shape[0]
    nx = mask.shape[1]

    queue = [point0]
    while len(queue) > 0:
        (j,i) = queue.pop(0)
        neighbours = []
        if j > 0:
            neighbours.append((j-1,i))
        if j < ny-1:
            neighbours.append((j+1,i))
        if i > 0:
            neighbours.append((j,i-1))
        if i < nx-1:
            neighbours.append((j,i+1))
        for point in neighbours:
            if connected[point]:
                continue
            if mask[point]:
                connected[point] = True
                queue.append(point)

    return connected

# Choose the right latitude and longitude name for the given dataset (sometimes it's stamped with the grid)
def latlon_name (ds):

    if 'nav_lat' in ds or 'nav_lat' in ds.coords:
        return 'nav_lon', 'nav_lat'
    elif 'nav_lat_grid_T' in ds or 'nav_lat_grid_T' in ds.coords:
        return 'nav_lon_grid_T', 'nav_lat_grid_T'
    elif 'nav_lat_grid_V' in ds or 'nav_lat_grid_V' in ds.coords:
        return 'nav_lon_grid_V', 'nav_lat_grid_V'
    elif 'nav_lat_grid_U' in ds or 'nav_lat_grid_U' in ds.coords:
        return 'nav_lon_grid_U', 'nav_lat_grid_U'
    elif 'lat' in ds or 'lat' in ds.coords:
        return 'lon', 'lat'
    elif 'latitude' in ds or 'latitude' in ds.coords:
        return 'longitude', 'latitude'
    elif 'TLAT' in ds or 'TLAT' in ds.coords:
        return 'TLON', 'TLAT'
    else:
        raise Exception('No valid lat or lon coordinate')

def xy_name (ds):

    if 'y' in ds.dims:
        return 'x', 'y'
    elif 'y_grid_T' in ds.dims:
        return 'x_grid_T', 'y_grid_T'
    elif 'y_grid_V' in ds.dims:
        return 'x_grid_V', 'y_grid_V'
    elif 'y_grid_U' in ds.dims:
        return 'x_grid_U', 'y_grid_U'
    elif 'ny' in ds.dims:
        return 'nx', 'ny'
    elif 'latitude' in ds.dims:
        return 'longitude', 'latitude'
    elif 'lat' in ds.dims:
        return 'lon', 'lat'        
    else:
        raise Exception('No valid x or y coordinate')

# Find the (y,x) coordinates of the closest model point to the given (lon, lat) coordinates. Pass an xarray Dataset containing nav_lon, nav_lat, and a target point (lon0, lat0).
def closest_point (ds, target):

    lon_name, lat_name = latlon_name(ds)
    lon = ds[lon_name].squeeze()
    lat = ds[lat_name].squeeze()
    [lon0, lat0] = target
    # Calculate distance of every model point to the target
    dist = np.sqrt((lon-lon0)**2 + (lat-lat0)**2)
    # Find the indices of the minimum distance
    x_name, y_name = xy_name(ds)
    point0 = dist.argmin(dim=(y_name, x_name))
    return (int(point0[y_name].data), int(point0[x_name].data))

def create_transect(transect_x, transect_y):
    # ----------------------------- ------------------------------------
    #           Define the coordinates of the irregular transect
    # -------------------------------------------------------------------------- 
    # --- transect_x, transect_y are grid points, not lat&lon.
    
    # ---- inner function
    def arange_ignore_sign(x1, x2):
        if x1<x2:
            X_arange = np.arange(x1, x2+1, 1)
        elif x1>x2:
            X_arange = np.arange(x1, x2-1, -1)

        return X_arange
    
    def nearest_interp1d(X_linspace, X_arange):
        from scipy.interpolate import interp1d
        # interpolate step-size spaced 1d array onto linspace array
        
        # Find the index of the nearest line point for each grid point
        nearest_interp = interp1d(X_arange, X_arange, kind='nearest', fill_value="extrapolate")
        # Interpolated values
        X_interp = nearest_interp(X_linspace)

        return X_interp

    def interp_transect(X_linspace, X_arange, Y_linspace, Y_arange):
        X_interp = nearest_interp1d(X_linspace, X_arange)
        Y_interp = nearest_interp1d(Y_linspace, Y_arange)
        return X_interp, Y_interp
    
    X_interp = []
    Y_interp = []
    
    for t_num in range(0, np.size(transect_x)-1, 1):
    
        x1 = transect_x[t_num]
        y1 = transect_y[t_num]
        
        x2 = transect_x[t_num+1]
        y2 = transect_y[t_num+1]
        
        nspace = np.max([np.abs(x1-x2), np.abs(y1-y2)])+1
        
        if x1==x2 or y1==y2:
            if x1==x2:
                X_interp = np.append(X_interp, np.full_like(arange_ignore_sign(y1, y2), x1)[:-1])
                Y_interp = np.append(Y_interp, arange_ignore_sign(y1, y2)[:-1])            
                X_linspace = X_interp
                Y_linspace = np.linspace(y1, y2, nspace)
                
            if y1==y2:
                Y_interp = np.append(Y_interp, np.full_like(arange_ignore_sign(x1, x2), y1)[:-1])
                X_interp = np.append(X_interp, arange_ignore_sign(x1, x2)[:-1])            
                X_linspace = np.linspace(x1, x2, nspace)
                Y_linspace = Y_interp
        else:
            X_linspace = np.linspace(x1, x2, nspace)
            Y_linspace = np.linspace(y1, y2, nspace)
            
            X_arange = arange_ignore_sign(x1, x2)
            Y_arange = arange_ignore_sign(y1, y2)
            
            X_interp_tmp, Y_interp_tmp = interp_transect(X_linspace, X_arange, Y_linspace, Y_arange)
            X_interp = np.append(X_interp, X_interp_tmp[:-1])
            Y_interp = np.append(Y_interp, Y_interp_tmp[:-1])

    return X_interp.astype(int), Y_interp.astype(int)


    