#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 15:00:50 2025

@author: jingjin

tmask_level_1 is now cached. Previously every call to sea_surface_masking read
the full `tos` field across all years just to rebuild the (identical) wet mask,
so processing N surface variables meant reading `tos` N times. With the cache it
is read once per (suite, region) per Python session.

Note on time-varying domains: this keeps the original per-year wet mask, which
is correct if the ocean domain evolves (e.g. changing ice-shelf cavities). If
your land-sea mask is instead static across the run, you can cut the mask read
to a single year -- see the commented `_static` variant below.
"""
import numpy as np
from functools import lru_cache
from terrafirma_analysis.utils.constants import slope_isobathy, shelfsea_lat, isf_cavity, region_edges, region_edges_flag, region_names
from terrafirma_analysis.utils.helpers import *

def mask_zeros(var):
    return np.ma.array(var, mask=var == 0)


def mask_nans(var):
    return np.ma.array(var, mask=np.isnan(var))


def clear_mask_cache():
    """Drop cached masks (call if the underlying files change mid-session)."""
    tmask_level_1.cache_clear()


@lru_cache(maxsize=None)
def tmask_level_1(if_SO_focus=False):
    
    # if_global = False for the Southern Ocean only
    # if_global = True for the remaining of the ocean sectors and the globe
    import terrafirma_analysis
    import netCDF4 as nc
    import os
    _PKG_DIR = list(terrafirma_analysis.__path__)[0]
    MASK_PATH = os.path.join(_PKG_DIR, 'utils', 'masks', 'sea_level_mask.nc')
    
    file = nc.Dataset(MASK_PATH, 'r')
    if if_SO_focus:
        return file.variables["tmask_level_1"][0, :113, ]
    else:
        return file.variables["tmask_level_1"][0, :]

def sea_surface_masking(var_unmask, if_SO_focus=False):
    import numpy as np
    tmask = tmask_level_1(if_SO_focus=if_SO_focus)
    var = np.where(tmask!=0, var_unmask, np.nan)
    return var

# Select the continental shelf and ice shelf cavities. Pass it the path to an xarray Dataset which contains one of the following combinations:
# 1. nav_lon, nav_lat, bathy, tmaskutil (NEMO3.6 mesh_mask)
# 2. nav_lon, nav_lat, bathy_metry, bottom_level (NEMO4.2 domain_cfg)
# 3. nav_lon, nav_lat, thkcello/e3t, a 3D data variable with a zero-mask applied (current options are thetao or so) (NEMO output file)
# 4. lon, lat, bathymetry (Shenjie's climatology)
def build_shelf_mask (ds):
    
    time_dim = next((d for d in ('time_counter', 't') if d in ds.dims), None)

    if time_dim is not None:
        ds = ds.isel({time_dim: 0})
    
    bathy_openocean = xr.where(ds['isfdraft'] != 0, 0, ds['bathy'])
    shelfsea = xr.where(bathy_openocean > slope_isobathy, 0, bathy_openocean)
    shelfsea[114:, :] = 0
    shelfsea[97:, ] = 0
    shelfsea[90:95, 241:246] = 0
    shelfsea[79:82, 90:93] = 0
    mask=shelfsea.copy()
    
    return mask, ds

def build_cavity_mask (ds, region):
    time_dim = next((d for d in ('time_counter', 't') if d in ds.dims), None)

    if time_dim is not None:
        ds = ds.isel({time_dim: 0})
        
    mask = np.zeros_like(ds.isfdraft.values, dtype=int)
    boxes = isf_cavity[region]
    for (x0, x1), (y0, y1) in boxes.values():
            mask[y0:y1, x0:x1] = 1

    return mask


def region_shelf_mask(region, ds, return_name=False, lon_bounds=None):
    mask, ds = build_shelf_mask(ds)
    mask = mask.copy()
    x_name, y_name = xy_name(ds)
    
    if return_name:
        # Construct the title
        title = region_names[region]
    
    if region in region_edges:
        # Restrict to a specific region of the coast
        # Select one point each on western and eastern boundaries
        [coord_W, coord_E] = region_edges[region]
        point0_W = closest_point(ds, coord_W)
        [j_W, i_W] = point0_W
        point0_E = closest_point(ds, coord_E)
        [j_E, i_E] = point0_E

        # Make two cuts to disconnect the region
        # Inner function to cut the mask in the given direction: remove the given point and all of its connected neighbours to the N/S or E/W
        def cut_mask (point0, direction):
            if direction == 'NS':
                i = point0[1]
                # Travel north until disconnected
                for j in range(point0[0], ds.sizes[y_name]):
                    if mask[j,i] == 0:
                        break
                    mask[j,i] = 0
                # Travel south until disconnected
                for j in range(point0[0]-1, -1, -1):
                    if mask[j,i] == 0:
                        break
                    mask[j,i] = 0
            elif direction == 'EW':
                j = point0[0]
                # Travel east until disconnected
                for i in range(point0[1], ds.sizes[x_name]):
                    if mask[j,i] == 0:
                        break
                    mask[j,i] = 0
                # Travel west until disconnected
                for i in range(point0[1]-1, -1, -1):
                    if mask[j,i] == 0:
                        break
                    mask[j,i] = 0
        # Inner function to select one cell "west" of the given point - this might not actually be properly west if the cut is made in the east/west direction, in this case you have to choose one cell north or south depending on the direction of travel.
        def cell_to_west (point0, direction):
            (j,i) = point0
            if direction == 'NS':
                # Cell to the west
                return (j, i-1)
            elif direction == 'EW':
                if j_E > j_W:
                    # Travelling north: cell to the south
                    return (j-1, i)
                elif j_E < j_W:
                    # Travelling south: cell to the north
                    return (j+1, i)
                else:
                    raise Exception('Something is wrong with region_edges')
                    
        
        def dronning_maud_eORCA1(j_E, i_E, j_W, i_W):
            mask_region = np.zeros_like(mask.values)
            if i_E < i_W: # --- for east antarctica
                copy = mask.values.copy()
                copy[:, i_E:i_W] = 0
                copy[:j_W, :] = 0
                mask_region = np.where(copy!=0, 1, 0)
            else:
                mask_region[j_W:j_E, i_W:i_E] = np.where(mask.values[j_W:j_E, i_W:i_E]!=0, 1, 0)
            return mask_region
        
        [flag_W, flag_E] = region_edges_flag[region]
        # Western boundary is inclusive: cut at cell to "west"
        cut_mask(cell_to_west(point0_W, flag_W), flag_W)
        # Eastern boundary is exclusive: cut at that cell
        cut_mask(point0_E, flag_E)              

        if region in ['dronning_maud', 'east_antarctica']:
            mask_region = dronning_maud_eORCA1(j_E, i_E, j_W, i_W)
            mask.data = mask_region
            
        else:                        
            # Run remove_disconnected on western point to disconnect the rest of the continental shelf
            mask_region = remove_disconnected(mask, point0_W)
            # Check if it wraps around the periodic boundary
            if i_E < i_W:
                # Make a second region by running remove_disconnected on one cell "west" from eastern point
                mask_region2 = remove_disconnected(mask, cell_to_west(point0_E, flag_E))
                mask_region += mask_region2
                
            mask.data = mask_region
            if region == 'dotson_cosgrove':
                # Bear Ridge can interrupt this one
                (j,i) = point0_E
                for n in range(2):
                    if np.max(mask[j,:]) > 0:
                        # Need to make a second cut (sometimes even a third)
                        i = np.where(mask[j,:] > 0)[0][0]
                        cut_mask((j,i), flag_E)
                        mask_region = remove_disconnected(mask, point0_W)
                        mask.data = mask_region
    else:
        raise Exception('Undefined region '+region)
        
    if return_name:
        return mask, ds, title
    else:
        return mask, ds

# Function to create a NetCDF file that contains the region masks
# Inputs:
# nemo_mesh : string of nemo meshmask file 
# option    : mask type ('all', 'cavity', or 'shelf') # --- not in use
# out_file  : string of output file path
def create_regions_file(out_file,
                        nemo_mesh=xr.open_dataset('/home/jingjin/mesh_mask/nemo_bv804c_21001201_mesh_mask.nc')):

    ds = xr.Dataset(
        coords={'nav_lon':(["y","x"], nemo_mesh.nav_lon.values),
                'nav_lat':(["y","x"], nemo_mesh.nav_lat.values)})

    masks={}
    # later should be for name in region_names
    for name in ['amundsen_sea','bellingshausen_sea','larsen','filchner_ronne',
                 'ross', 'amery', 'wilkes', 'dronning_maud', 'west_antarctica', 'east_antarctica']:
        mask, _, region_name = region_shelf_mask(name, nemo_mesh, return_name=True)
        masks[name] = mask
        ds = ds.assign({f'mask_{name}':(["y","x"], masks[name].values)})

    ds.to_netcdf(out_file)

    return ds

def create_cavity_mask_file(out_file,
                            nemo_mesh=xr.open_dataset('/home/jingjin/mesh_mask/nemo_bv804c_21001201_mesh_mask.nc')):
    ds = xr.Dataset(
        coords={'nav_lon':(["y","x"], nemo_mesh.nav_lon.values),
                'nav_lat':(["y","x"], nemo_mesh.nav_lat.values)})
    
    try:
        for name in ['amundsen_sea','bellingshausen_sea','larsen','filchner_ronne',
                     'ross', 'amery', 'wilkes', 'dronning_maud', 'west_antarctica', 'east_antarctica']:

            ds = ds.assign({f'mask_{name}':(["y","x"], build_cavity_mask (nemo_mesh, name))})
            
        ds.to_netcdf(out_file)
    finally:
        nemo_mesh.close()
        
    return ds
    
#out_file = '/home/jingjin/work/postpro/terrafirma_analysis/utils/masks/nemo_cavity_mask.nc'
#ds_out = create_cavity_mask_file(out_file)

