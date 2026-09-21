#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_sectors.py  --  config-driven front-end for the Southern Ocean shelf-SECTOR
diagnostics in Antarctic_sectors.py.

Same shape as run_timeseries.py: you pick one `task` and one `region`, and the
underlying write_SO_sector_* functions run unchanged, so the scientific output
is identical -- only the way you *ask* for it changes.

The one deliberate difference from run_timeseries.py: here `region` is a shelf
SECTOR name that is passed straight through to the writers (which look up
mask_<region> in nemo_shelf_mask.nc), NOT a SO/shelf/global/arctic flag set.
region=None means the whole Antarctic continental shelf (no sector mask).

This module is the reusable engine (Config, REGIONS, TASKS, run, run_all_regions).
Put the actual batch for a given suite in its own job script that imports from
here -- see run_cz826_sectors.py.

Quick start
-----------
    from run_sectors import Config, run, run_all_regions

    # one sector, one field
    run(Config(suite_id="cz826", var_dir="water_fluxes",
               var_read="tos", units_out="degree_C",
               task="sector_2d", region="ross"))

    # one field, every sector -> all sectors into the one consolidated file,
    # as variables ross_shelfsea_tos, amundsen_sea_shelfsea_tos, ...
    run_all_regions(Config(suite_id="cz826", var_dir="water_fluxes",
                           var_read="tos", units_out="degree_C",
                           task="sector_2d"))
"""

from dataclasses import dataclass, replace
from typing import Optional, Union

from terrafirma_analysis.Antarctic_sectors import (
    write_SO_sector_timeseries_3d,
    write_SO_sector_hovemoller_3d,
    write_SO_sector_timeseries_2d,
)

# ---------------------------------------------------------------------------
# The Antarctic shelf sectors, exactly as stored (mask_<name>) in
# nemo_shelf_mask.nc. region=None (i.e. not in this list) = the whole shelf.
# ---------------------------------------------------------------------------
REGIONS = [
    'amundsen_sea', 'bellingshausen_sea', 'larsen', 'filchner_ronne',
    'ross', 'amery', 'wilkes', 'dronning_maud',
    'west_antarctica', 'east_antarctica',
]


def _qualify(region, name):
    """Region-qualify an output variable name.

    Every sector writes into the same consolidated file, so the sector has to
    live in the variable name (e.g. 'ross_shelfsea_tos') to avoid collisions.
    region=None (whole shelf) leaves the name unprefixed.
    """
    return f"{region}_{name}" if region else name


@dataclass
class Config:
    suite_id: str
    task: str = ""
    region: Optional[str] = None          # a REGIONS entry, or None = whole shelf
    grid: str = "T"                       # 'T' | 'U' | 'V' (3D reads only)
    var_dir: str = ""
    var_read: str = ""
    varname_out: Optional[Union[str, dict]] = None
    units_out: str = ""
    path_out: str = "/home/users/jingj/work/terrafirma_timeseries"
    base_dir: str = "/gws/ssde/j25b/ocean_ice/jjin/archer2"
    # Suite dir name is f"{suite_prefix}{suite_id}"; set suite_prefix="u-" for
    # the ARCHER2 single-tree layout (.../u-<suite>/<cycle>/nemo_...grid-T.nc).
    suite_prefix: str = ""
    filename_out: Optional[str] = None    # auto-derived from region/task if None

    @property
    def suite_dir(self) -> str:
        return f"{self.base_dir}/{self.suite_prefix}{self.suite_id}"

    @property
    def file_dir(self) -> str:
        # var_dir optional: empty -> single tree, the recursive file search picks
        # the right file out of the cycle dirs.
        return f"{self.suite_dir}/{self.var_dir}/" if self.var_dir else f"{self.suite_dir}/"

    @property
    def out_name(self) -> str:
        # One consolidated file per suite: every variable for every sector lands
        # here. Names are region-qualified in the task handlers so they don't
        # collide. Override with filename_out to split the output however you like.
        return self.filename_out or f"{self.suite_id}_shelfsea_sectors_timeseries.nc"

    @property
    def out_varname(self) -> str:
        """Scalar output variable name (sector_2d / sector_hovemoller tasks).

        Files are already per-sector, so the default keeps the original
        shelfsea_<var> convention and lets the sector live in the filename.
        sector_3d uses a varname_out dict instead and never hits this.
        """
        if self.varname_out is not None:
            return self.varname_out
        if not self.var_read:
            raise ValueError("var_read must be set to derive a default output "
                             "variable name (or pass varname_out explicitly)")
        return self.var_read

    def but(self, **changes) -> "Config":
        """Return a copy with some fields changed (handy for batching)."""
        return replace(self, **changes)

    def validate(self):
        if self.task not in TASKS:
            raise ValueError(
                f"unknown task {self.task!r}. Valid tasks: {sorted(TASKS)}")
        if self.region is not None and self.region not in REGIONS:
            raise ValueError(
                f"unknown region {self.region!r}. Valid sectors: {REGIONS} "
                f"(or None for the whole shelf)")


# ---------------------------------------------------------------------------
# Task registry: task name -> function(cfg) that calls the right writer
# ---------------------------------------------------------------------------
def _sector_3d(cfg):
    if not isinstance(cfg.varname_out, dict):
        raise ValueError(
            "task 'sector_3d' needs varname_out as a dict of depth-band names, "
            "e.g. {'0': 'so_0_120m', '1': 'so_120_400m', '2': 'so_400_850m', "
            "'3': 'so_below_850m', '4': 'so_full_depth'}")
    varout = {k: _qualify(cfg.region, v) for k, v in cfg.varname_out.items()}
    write_SO_sector_timeseries_3d(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        varout, cfg.units_out, grid=cfg.grid, region=cfg.region)


def _sector_hovemoller(cfg):
    write_SO_sector_hovemoller_3d(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        _qualify(cfg.region, cfg.out_varname), cfg.units_out, grid=cfg.grid, region=cfg.region)


def _sector_2d(cfg):
    write_SO_sector_timeseries_2d(
        cfg.suite_id, cfg.file_dir, cfg.var_read, cfg.path_out, cfg.out_name,
        _qualify(cfg.region, cfg.out_varname), cfg.units_out, region=cfg.region)


TASKS = {
    'sector_3d':         _sector_3d,          # depth-band means of a 3D field
    'sector_hovemoller': _sector_hovemoller,  # depth-vs-time of a 3D field
    'sector_2d':         _sector_2d,          # surface / flux 2D field
}


def run(cfg: Config):
    """Validate a Config and dispatch to the matching sector writer."""
    cfg.validate()
    print(f"[{cfg.task}] suite={cfg.suite_id} region={cfg.region or 'allshelf'} "
          f"grid={cfg.grid} -> {cfg.path_out}{cfg.out_name}")
    return TASKS[cfg.task](cfg)


def run_all_regions(cfg: Config, regions=None):
    """Run the same cfg for every sector (one output file per sector)."""
    return [run(cfg.but(region=r)) for r in (regions or REGIONS)]


# ---------------------------------------------------------------------------
# Minimal smoke example; real batches live in run_<suite>_sectors.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_all_regions(Config(
        suite_id="cz826",
        var_dir="water_fluxes",
        var_read="tos",
        units_out="degree_C",
        task="sector_2d",
    ))
