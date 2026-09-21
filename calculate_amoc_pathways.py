"""
A Tool for Calculating AMOC Upwelling Pathways

Author: Jonathan A. Baker
Email:  jonathan.baker@metoffice.gov.uk

Description:
    This script implements a method for calculating the upwelling pathways of the AMOC. 
    For a detailed description of the methodology, please refer to our paper:

    Baker J.A., Bell, M.J., Jackson, L.C., Vallis, G.K., Watson, A.J., & Wood, R.A. (2025),
    Continued Atlantic overturning circulation even under climate extremes, Nature, 638, 
    https://doi.org/10.1038/s41586-024-08544-0.

    The code is archived on Zenodo: 
    DOI: https://doi.org/10.5281/zenodo.11116004

Citation:
    If you use this tool in your research, please cite the references above.

Usage:
    Args:
        moc_global   : xarray.dataset for global MOC streamfunction (z,y)
        moc_atlantic : xarray.dataset for Atlantic MOC streamfunction (z,y)
        moc_indopac  : xarray.dataset for Indo-Pacific MOC streamfunction (z,y)
        index_345    : Integer. Index for 34.5S latitude
        index_eq     : Integer. Index for the equator   

    Returns: 
    - Dictionary of AMOC upwelling pathways:
        AMOC_strength     : Maximum AMOC strength in North Atlantic
        Atlantic_Up       : AMOC's Atlantic upwelling pathway
        SouthernOcean_Up  : AMOC's Southern Ocean upwelling pathway
        IndoPac_ResidualUp: AMOC's Indo-Pacific residual upwelling pathway    

License:
    Creative Commons Attribution 4.0 International (CC BY 4.0)
"""

import os
import os.path as op

import numpy as np
import xarray as xr
import netCDF4 as nc

from terrafirma_analysis.circulation import geodef_CONSTANT
from terrafirma_analysis.io_core import _first_match
from terrafirma_analysis.io_core import create_dimensions_time, create_variables_1d_timeseries
from terrafirma_analysis.utils.conversions import time_coverage


def interpolate_streamfunctions(moc_data, index_lat, depth_interp):
    """
    Interpolates MOC data to a uniform depth grid, depth_interp.
    """
    return moc_data[:, index_lat].fillna(0).interp(depthw=depth_interp, method="linear")

def calculate_amoc_pathways(moc_global, moc_atlantic, moc_indopac, index_345, index_eq):
    # Interpolate data to 10m vertical grid spacing
    depth_interp = np.arange(moc_global.depthw[0], moc_global.depthw[-1], 10)
    streamfunc_atl_full = interpolate_streamfunctions(moc_atlantic, slice(None), depth_interp)
    streamfunc_atl_34S = interpolate_streamfunctions(moc_atlantic, index_345, depth_interp)
    streamfunc_global_34S = interpolate_streamfunctions(moc_global, index_345, depth_interp)
    streamfunc_indopac_34S = interpolate_streamfunctions(moc_indopac, index_345, depth_interp)

    # Depth index at 500 m 
    z_gyre = np.where(moc_atlantic.depthw > 500)[0][0] 
    z_gyre_interp = np.where(depth_interp > 500)[0][0]

    # Calculate maximum MOC strength at different latitudes
    AMOC_strength = np.nanmax(streamfunc_atl_full[z_gyre_interp:, index_eq:])  
    AMOC_34S = streamfunc_atl_34S[z_gyre_interp:].max()  
    AMOC_min_orig = np.nanmin(np.nanmax(streamfunc_atl_full[z_gyre_interp:, index_345:index_eq], axis=0))
    AMOC_min = AMOC_34S.copy()
    AMOC_min.values = AMOC_min_orig  
    MOC_34S_global_below_gyre = streamfunc_global_34S[z_gyre_interp:].max()

    # Calculate required depths of MOC
    z_AMOC_34S_max = (np.where(streamfunc_atl_34S[z_gyre_interp:] == streamfunc_atl_34S[z_gyre_interp:].max())[0][0]
        + z_gyre_interp
    )  
    z_south_atlantic_local_bottom = (
        np.where(streamfunc_atl_34S[z_AMOC_34S_max:] <= AMOC_min)[0][0] + z_AMOC_34S_max
    )  

    # Calculate components of the localised South Atlantic circulation
    south_atlantic_local_total = AMOC_34S - AMOC_min
    south_atlantic_local_indopacup = min(south_atlantic_local_total,
        (streamfunc_indopac_34S[z_south_atlantic_local_bottom].clip(max=0) 
        - streamfunc_indopac_34S[z_AMOC_34S_max].clip(max=0)
    ).clip(min=0))
    # Ensures south_atlantic_local_indopacup is zero if net flow is southward in Indo-Pacific over depth of localised South Atlantic circulation

    south_atlantic_local_windup = (south_atlantic_local_total - south_atlantic_local_indopacup).clip(min=0)  

    # Calculate Atlantic upwelling pathway
    Atlantic_Up = (AMOC_strength - AMOC_min).clip(min=0)

    # Calculate PMOC strength at depth of the maximum AMOC strength at 34.5S
    if (streamfunc_indopac_34S[z_AMOC_34S_max] > 0).any(): 
        PMOC_z_AMOC_34S_max = streamfunc_indopac_34S[z_AMOC_34S_max].max()  
    else:
        PMOC_z_AMOC_34S_max = Atlantic_Up * 0

    # Calculate Southern Ocean upwelling pathway, removing PMOC upwelling in Southern Ocean that cannot be connected to AMOC
    SouthernOcean_Up = (streamfunc_global_34S[:].max() - PMOC_z_AMOC_34S_max).clip(min=0)

    if south_atlantic_local_windup > 0: 
        SouthernOcean_Up = (SouthernOcean_Up - south_atlantic_local_windup).clip(min=0)
    SouthernOcean_Up = min(SouthernOcean_Up, AMOC_min)

    # Calculate Indo-Pacific residual upwelling pathway
    IndoPac_ResidualUp = AMOC_strength - Atlantic_Up - SouthernOcean_Up

    return {
        "AMOC_strength_Baker2025": AMOC_strength,
        "Atlantic_Up": Atlantic_Up.values,
        "SouthernOcean_Up": SouthernOcean_Up.values,
        "IndoPac_ResidualUp": IndoPac_ResidualUp.values
    }


# ---------------------------------------------------------------------------
# TerraFirma wrapper: reading the diaptr streamfunctions and building timeseries.
# (Not part of the tool above)
# ---------------------------------------------------------------------------

# Basins used by the pathway decomposition, and the mean + eddy pair for each.
BASINS = ('glo', 'atl', 'ipc')

# The four quantities returned by calculate_amoc_pathways, in output order.
PATHWAY_KEYS = ('AMOC_strength_Baker2025', 'Atlantic_Up', 'SouthernOcean_Up', 'IndoPac_ResidualUp')


def residual_msf(mean, eddy):
    return mean + eddy


def read_var_as_xarray(file_dir, suite_id, varname, year_to_read, freq='1y'):
    """Read a single diaptr variable for one year (kept for direct use)."""
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_diaptr.nc')
    with xr.open_dataset(nc_files) as ds:
        return ds[varname][0, :, :, 0].load()


def read_diaptr_year(file_dir, suite_id, year_to_read, freq='1y'):
    """Read every streamfunction needed for one year from a single file open.

    All six fields (mean + eddy for each of the three basins) live in the same
    diaptr file, so opening it once per year rather than once per field cuts the
    opens by 6x over a long run. The handle is closed either way.
    """
    timestamp = f"{year_to_read}1201-{year_to_read+1}1201"
    nc_files = _first_match(file_dir, f'nemo_{suite_id}o_{freq}_{timestamp}_diaptr.nc')
    with xr.open_dataset(nc_files) as ds:
        return {basin: residual_msf(ds[f'zomsf{basin}'][0, :, :, 0].load(),
                                    ds[f'zomsfeiv{basin}'][0, :, :, 0].load())
                for basin in BASINS}


def amoc_pathways_variables(file_dir, suite_id, year_to_read, freq='1y'):
    """The four AMOC upwelling pathways for a single year."""
    moc = read_diaptr_year(file_dir, suite_id, year_to_read, freq=freq)
    return calculate_amoc_pathways(moc['glo'], moc['atl'], moc['ipc'],
                                   geodef_CONSTANT('AMOC_345S'),
                                   geodef_CONSTANT('Equator'))


def _as_scalar(value, key, year):
    """One value per year; fail loudly rather than silently mis-shaping output."""
    arr = np.asarray(value)
    if arr.size != 1:
        raise ValueError(
            f"{key!r} for year {year} has shape {arr.shape}, but "
            f"amoc_pathways_timeseries expects a single value per year. "
            f"If these are profiles, write them with create_variables_2d_hovemoller "
            f"instead of create_variables_1d_timeseries.")
    return arr.reshape(-1)[0]


def amoc_pathways_timeseries(suite_id, file_dir, year=None, freq='1y'):
    """Timeseries of each AMOC upwelling pathway over the suite's year range.

    Returns a dict of 1D arrays keyed by PATHWAY_KEYS, one value per year.
    """
    print('AMOC upwelling pathways are being calculating')

    if year is None:
        year_start, year_end = time_coverage(suite_id)
        year = np.arange(year_start, year_end, 1)
    else:
        year = np.asarray(year)

    timeseries = {key: np.empty(len(year)) for key in PATHWAY_KEYS}

    for i, y in enumerate(year):
        pathways = amoc_pathways_variables(file_dir, suite_id, int(y), freq=freq)
        for key in PATHWAY_KEYS:
            timeseries[key][i] = _as_scalar(pathways[key], key, y)

    return timeseries


def write_amoc_pathways_timeseries(suite_id, file_dir, path_out, filename_out,
                                   varout_name=None, units='Sv',
                                   year=None, freq='1y'):
    """Write all four pathway timeseries into one file.

    varout_name : optional {pathway_key: output_variable_name} to rename outputs;
                  any key left out keeps its PATHWAY_KEYS name.
    """
    timeseries = amoc_pathways_timeseries(suite_id, file_dir, year=year, freq=freq)

    varout_name = varout_name or {}
    written = []

    fi_out = op.join(path_out, filename_out)
    ncfile = nc.Dataset(fi_out, 'a', 'NETCDF4')
    try:
        create_dimensions_time(ncfile, dim_t=None)
        for key in PATHWAY_KEYS:
            name = varout_name.get(key, key)
            data_var = create_variables_1d_timeseries(ncfile, name)
            data_var.units = units
            data_var[:] = timeseries[key]
            written.append(name)
    finally:
        ncfile.close()

    return print(f'{os.path.join(path_out, filename_out)} is created. \n {written} are saved.')
