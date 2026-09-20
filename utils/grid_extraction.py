#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 10:45:31 2026

@author: jingjin
"""

import numpy as np
import xarray as xr
import netCDF4 as nc
import os
from terrafirma_analysis.utils.helpers import create_transect
from terrafirma_analysis.io_core import list_nc_files_T
from terrafirma_analysis.utils.constants import transect_SO

def extract_transect_var_TS(var, transect_x, transect_y):
    # --- var is preferred an xarray.DataArray
    X1_interp, Y1_interp = create_transect(transect_x, transect_y)
    if len(Y1_interp) != len(X1_interp):
        raise ValueError("Index arrays Y1_interp and X1_interp must have the same length.")
        return
    else:
        if isinstance(var, xr.DataArray):
            xi = xr.DataArray(X1_interp, dims="l")
            yi = xr.DataArray(Y1_interp, dims="l")
            var_transect = var.isel(x=xi, y=yi)   # -> dims (..., transect)
            return var_transect
        return var[..., Y1_interp, X1_interp]    # ndarray / MaskedArray: point-wise

def create_transect_file(ds, transect_x, transect_y,
                         out_file,
                         nemo_mesh=xr.open_dataset('/home/jingjin/mesh_mask/nemo_bv804c_21001201_mesh_mask.nc')):
    
    def geom(da):
        # 1-D geometry along l: squeeze the singleton mesh 't', drop nav_lat/lon
        return (extract_transect_var_TS(da, transect_x, transect_y)
                .squeeze(drop=True).reset_coords(drop=True))

    def field(da):
        # data along (time_counter, deptht, l): keep time_counter, drop nav_lat/lon
        out = extract_transect_var_TS(da, transect_x, transect_y).reset_coords(drop=True)
        if 'time_counter' not in out.dims:
            out = out.expand_dims('time_counter')     # length-1 record -> appendable
        return out

    e1t = geom(nemo_mesh.e1t)
    e2t = geom(nemo_mesh.e2t)
    seg = np.sqrt(e1t**2 + e2t**2) / 1000.0
    dl = seg.isel(l=slice(None, None, -1)).cumsum('l').isel(l=slice(None, None, -1))
    dl = dl-dl[-1]

    ds_out = xr.Dataset(
        data_vars={'bathy_transect': geom(nemo_mesh.bathy),
                   'thetao':         field(ds['thetao']),
                   'so':             field(ds['so'])},
        coords={'depth':    ('deptht', ds.deptht.values),
                'distance': ('l',      dl.data)},
    )

    # keep the real time axis so its 360-day calendar + units survive the round-trip
    if 'time_counter' in ds.variables:
        ds_out = ds_out.assign_coords(time_counter=ds['time_counter'])
        ds_out['time_counter'].encoding.update(ds['time_counter'].encoding)

    ds_out.to_netcdf(out_file, unlimited_dims=['time_counter'])
    return ds_out



    
def update_transect_file(ds, transect_x, transect_y, out_file,
                         data_vars=('thetao', 'so'),
                         nemo_mesh=xr.open_dataset('/home/jingjin/mesh_mask/nemo_bv804c_21001201_mesh_mask.nc')):
    
    def _extract_field(da, transect_x, transect_y):
        #One data field along (time_counter, deptht, l), time axis guaranteed present.
        out = extract_transect_var_TS(da, transect_x, transect_y).reset_coords(drop=True)
        if 'time_counter' not in out.dims:
            out = out.expand_dims('time_counter')      # single-slice input -> length-1 record
        return out

    # first year: nothing to append to -> build the file (geometry + first slice)
    if not os.path.isfile(out_file):
        return create_transect_file(ds, transect_x, transect_y, out_file, nemo_mesh)
    
    fields = {v: _extract_field(ds[v], transect_x, transect_y) for v in data_vars}
    nnew = next(iter(fields.values())).sizes['time_counter']
    
    ncfile = nc.Dataset(out_file, 'a', decode_times=False)
    try:
        n = ncfile.dimensions['time_counter'].size           # current length
        for v, da in fields.items():
            ncfile.variables[v][n:n + nnew, ] = da.values    # unlimited dim auto-extends
            
        if 'time_counter' in ncfile.variables and 'time_counter' in ds.variables:
            tvar = ncfile.variables['time_counter']
            tvar[n:n + nnew] = np.atleast_1d(ds['time_counter'].values)   # raw numbers, no calenda
    
    finally:
        ncfile.close()
        
def _opener(year, suite_id,
            dir = '/gws/ssde/j25b/ocean_ice/jjin/archer2/u-dn026'):
    
    fopen = list_nc_files_T(dir, suite_id, f"{year}1201-{year+1}1201")[0]
    return xr.open_dataset(fopen)

def main():
    suite_id = 'cz826'
    path_read = f'/home/jingjin/work/terrafirma/{suite_id}/thetao+so'
    years = np.arange(1850, 2210+1, 1)
    
    for region in ['amundsen_sea', 'ross', 'filchner_ronne', 'amery']:
        try:
            out_file = f'/home/jingjin/work/postpro/misc_data/transect_files/{suite_id}_{region}_transect.nc'
            transect_x, transect_y = transect_SO[region]
    
            for y in years:
                ds = _opener(y, suite_id, dir=path_read)                                   # your single-slice reader
                update_transect_file(ds, transect_x, transect_y, out_file)
        finally:
            print(f'{os.path.join(out_file)} is created.')
  
if __name__ == "__main__":
    main()
    