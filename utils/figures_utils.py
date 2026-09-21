#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 14:25:21 2025

@author: jingjin
"""
import matplotlib.pyplot as plt  # plotting library

def variable_limits(cbar_tick):
    vmin = cbar_tick[0]
    vmax = cbar_tick[-1]
    return vmin, vmax

def save_figure(path_to_save_figure):
    return plt.savefig(path_to_save_figure, dpi=300)

def make_colorbar(cshading, cbar_tick, cbar_ticklabel, cbar_label, 
                  fig_current = None, ax_current=None):
    
    if fig_current is None:
        fig_current = plt.gcf()
    
    if ax_current is None:
        ax_current = plt.gca()
    
    cax = fig_current.add_axes([ax_current.get_position().x1+0.01,
                        ax_current.get_position().y0,
                        0.015,
                        ax_current.get_position().height])
    vmin, vmax = cshading.get_clim()
    
    cbar = fig_current.colorbar(cshading, ax=ax_current, cax=cax, orientation='vertical', extend='both') # --- This is for 2x1 figure
    cbar.set_ticks(cbar_tick)
    cbar.set_ticklabels(cbar_ticklabel)
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label(cbar_label, fontsize=8) 
    
    cbar.mappable.set_clim(vmin=vmin, vmax=vmax)
    
# If a figure name is defined, save the figure to that file. Otherwise, display the figure on screen.
def finished_plot (fig, fig_name=None, dpi=None, print_out=True):

    if fig_name is not None:
        if print_out: print(('Saving ' + fig_name))
        fig.savefig(fig_name, dpi=dpi)
    else:
        fig.show()