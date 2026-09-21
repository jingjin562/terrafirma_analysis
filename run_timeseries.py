#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick start
-----------
    from run_timeseries import Config, run

    run(Config(
        suite_id="cz826",
        var_dir="sowflisf",
        var_read="sowflisf",
        task="isf",          # one of TASKS.keys()
        region="shelf",      # one of REGIONS.keys()
    ))

Batch several diagnostics in one go:

    cfg = Config(suite_id="cx209", region="shelf", var_dir="thetao+so",
                 var_read="so")
    run(cfg.but(task="nemo_3d",
                varname_out={'0': 'so_0_120m', '1': 'so_120_400m',
                             '2': 'so_400_850m', '3': 'so_below_850m',
                             '4': 'so_full_depth'},
                units_out="psu"))
    run(cfg.but(task="nemo_2d", var_read="sos", varname_out="sos", units_out="psu"))
"""

from dataclasses import dataclass, replace
from typing import Optional, Union

from terrafirma_analysis.nemo_3d import write_nemo_3d_timeseries, write_nemo_3d_hovemoller
from terrafirma_analysis.isf_module import write_isf_timeseries
from terrafirma_analysis.nemo_2d import write_nemo_2d_timeseries
from terrafirma_analysis.water_flux import (
    write_single_water_flux_timeseries,
    write_sea_ice_timeseries,
    write_total_FW_timeseries,
    write_all_FW_timeseries,
    write_GrIS_runoff_timeseries,
)
from terrafirma_analysis.calculate_amoc_pathways import write_amoc_pathways_timeseries
from terrafirma_analysis.circulation import (
    write_AMOC_strength_timeseries,
    write_lower_cell_strength_timeseries,
    write_SMOC_strength_timeseries,
    write_Drake_Passage_timeseries,
    write_SouthernOcean_baromsf,
)
# ---------------------------------------------------------------------------
# Region -> the four boolean flags the write_* functions still expect
# ---------------------------------------------------------------------------
REGIONS = {
    'SO':     dict(if_SO=True,  if_continental_shelf=False, if_global=False, if_Arctic_ocean=False),
    'shelf':  dict(if_SO=False, if_continental_shelf=True,  if_global=False, if_Arctic_ocean=False),
    'global': dict(if_SO=False, if_continental_shelf=False, if_global=True,  if_Arctic_ocean=False),
    'arctic': dict(if_SO=False, if_continental_shelf=False, if_global=False, if_Arctic_ocean=True),
}

# Output filename convention: <suite_id>_<var>_timeseries.nc
_FILENAME = {
    'shelf':  lambda s: f"test_{s}_shelfsea_timeseries.nc",
    'SO':     lambda s: f"{s}_timeseries.nc",
    'global': lambda s: f"{s}_global_timeseries.nc",
    'arctic': lambda s: f"{s}_Arctic_ocean_timeseries.nc",
}


@dataclass
class Config:
    suite_id: str
    task: str = ""
    region: str = "global"
    var_dir: str = ""
    var_read: str = ""
    varname_out: Optional[Union[str, dict]] = None
    units_out: str = ""
    path_out: str = "/home/jingjin/work/postpro/misc_data/"
    base_dir: str = "/home/jingjin/work/terrafirma"
    filename_out: Optional[str] = None   # auto-derived from region if left None
    # Ice-shelf (sowflisf / isf-T) files may live apart from the grid-T fields.
    # Set one of these for the FW tasks (total_*, all_FW) when that's the case;
    # otherwise the isf files are assumed to sit alongside the others.
    isf_dir: Optional[str] = None         # explicit full path, or
    isf_var_dir: Optional[str] = None     # a sub-dir under base_dir/<suite_id>/

    @property
    def file_dir(self) -> str:
        return f"{self.base_dir}/{self.suite_id}/{self.var_dir}/"

    @property
    def isf_dir_explicit(self) -> Optional[str]:
        """The isf directory *only* if one was given, else None.

        The FW writers fall back to file_dir, while the 3D readers fall back to
        their own archive path, so tasks that use the latter must pass None
        rather than a guessed directory when the user hasn't set one.
        """
        if self.isf_dir:
            return self.isf_dir
        if self.isf_var_dir:
            return f"{self.base_dir}/{self.suite_id}/{self.isf_var_dir}/"
        return None

    @property
    def isf_file_dir(self) -> str:
        """Directory holding the sowflisf (isf-T) files. Falls back to file_dir
        when the isf files are co-located with the grid-T fields."""
        return self.isf_dir_explicit or self.file_dir

    @property
    def flags(self) -> dict:
        return REGIONS[self.region]

    @property
    def out_name(self) -> str:
        return self.filename_out or _FILENAME[self.region](self.suite_id)

    @property
    def out_varname(self) -> str:
        """Variable name to store the result under.

        Falls back to a region-aware default (the original `shelfsea_<var>`
        convention) when varname_out is not given, so a minimal Config just works
        for the scalar-output tasks (nemo_2d, hovemoller, water_flux).
        """
        if self.varname_out is not None:
            return self.varname_out
        if not self.var_read:
            raise ValueError("var_read must be set to derive a default output "
                             "variable name (or pass varname_out explicitly)")
        return f"shelfsea_{self.var_read}" if self.region == 'shelf' else self.var_read

    def but(self, **changes) -> "Config":
        """Return a copy with some fields changed (handy for batching)."""
        return replace(self, **changes)

    def validate(self):
        if self.task not in TASKS:
            raise ValueError(
                f"unknown task {self.task!r}. Valid tasks: {sorted(TASKS)}")
        if self.region not in REGIONS:
            raise ValueError(
                f"unknown region {self.region!r}. Valid regions: {sorted(REGIONS)}")


# ---------------------------------------------------------------------------
# Task registry: task name -> function(cfg) that calls the right writer
# ---------------------------------------------------------------------------
def _nemo_3d(cfg):
    if not isinstance(cfg.varname_out, dict):
        raise ValueError(
            "task 'nemo_3d' needs varname_out as a dict of depth-band names, "
            "e.g. {'0': 'so_0_120m', '1': 'so_120_400m', '2': 'so_400_850m', "
            "'3': 'so_below_850m', '4': 'so_full_depth'}")
    write_nemo_3d_timeseries(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        cfg.varname_out, cfg.units_out, isf_dir=cfg.isf_dir_explicit, **cfg.flags)

def _hovemoller(cfg):
    write_nemo_3d_hovemoller(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        cfg.out_varname, cfg.units_out, isf_dir=cfg.isf_dir_explicit, **cfg.flags)

def _nemo_2d(cfg):
    write_nemo_2d_timeseries(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        cfg.out_varname, cfg.units_out, **cfg.flags)

def _isf(cfg):
    write_isf_timeseries(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        cfg.out_varname, cfg.units_out, **cfg.flags)
    
def _water_flux(cfg):
    write_single_water_flux_timeseries(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        cfg.out_varname, 'Gt/yr', **cfg.flags)

def _seaice(cfg):
    write_sea_ice_timeseries(
        cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name, **cfg.flags)

def _total_FW(kind):
    kinds = dict(total='if_total', atmos='if_atmos',
                 ocean='if_ocean', icesheet='if_icesheet')
    def _f(cfg):
        opts = {v: (k == kind) for k, v in kinds.items()}
        write_total_FW_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out,
                                  cfg.out_name, **opts,
                                  isf_dir=cfg.isf_file_dir, **cfg.flags)
    return _f

def _all_FW(cfg):
    # total / net_precip / ocean / icesheet from a single read of each field
    write_all_FW_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out,
                            cfg.out_name, isf_dir=cfg.isf_file_dir, **cfg.flags)

def _GrIS_runoff(cfg):
    # GrIS runoff uses the Greenland mask; it is not region-flagged.
    write_GrIS_runoff_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name)

def _AMOC_strength(cfg):
    write_AMOC_strength_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name)

def _lower_cell_strength(cfg):
    write_lower_cell_strength_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name)

def _SMOC_strength(cfg):
    write_SMOC_strength_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name)

def _DrakePassage_strength(cfg):
    write_Drake_Passage_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name)

def _SouthernOcean_baromsf(cfg):
    write_SouthernOcean_baromsf(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name)

def _amoc_pathways(cfg):
    # Baker et al. (2025) AMOC upwelling decomposition; basin-based, no region flags.
    write_amoc_pathways_timeseries(cfg.suite_id, cfg.file_dir, cfg.path_out, cfg.out_name,
                                   varout_name=cfg.varname_out
                                   if isinstance(cfg.varname_out, dict) else None)
    
TASKS = {
    'nemo_3d':        _nemo_3d,      # thetao, so, uo, vo, thkcello, ...
    'hovemoller':     _hovemoller,   # depth-vs-time of a 3D field
    'nemo_2d':        _nemo_2d,      # tos, sos, tob, sob, soicecov, hfds, ssh, ...
    'isf':            _isf,          # sowflisf / sohflisf basal melt
    'water_flux':     _water_flux,   # fsitherm, friver, ficeberg, pr, prsn, evs
    'seaice':         _seaice,       # fsitherm decomposed: net/melting/freezing
    'total_FW':       _total_FW('total'),
    'total_atmos':    _total_FW('atmos'),
    'total_ocean':    _total_FW('ocean'),
    'total_icesheet': _total_FW('icesheet'),
    'all_FW':         _all_FW,       # all four FW outputs from one read pass
    'GrIS_runoff':    _GrIS_runoff,  # GrIS surface melt
    'AMOC_strength':  _AMOC_strength,       # max streamfunction at 26.5 N (Atlantic)
    'lower_cell_strength': _lower_cell_strength,  # min streamfunction below 30 S
    'SMOC_strength':  _SMOC_strength,       # min streamfunction below 55 S
    'DrakePassage':   _DrakePassage_strength,
    'SO_baromsf':     _SouthernOcean_baromsf,
    'amoc_pathways':  _amoc_pathways,
}


def run(cfg: Config):
    """Validate a Config and dispatch to the matching writer."""
    cfg.validate()
    print(f"[{cfg.task}] suite={cfg.suite_id} region={cfg.region} "
          f"-> {cfg.path_out}{cfg.out_name}")
    return TASKS[cfg.task](cfg)
