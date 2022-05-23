import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.interpolate as interpol

from src.output.plots.colors import get_color_for_act_type


def plot_timing_distribution_for_act_type(schedule_df: pd.DataFrame, output_folder, timing_type: str,
                                          act_type: str, max_timing: float = 25.0, save_fig=True):
    x = np.linspace(1, max_timing, 500)
    y = interpol.make_interp_spline(schedule_df.index, schedule_df[act_type], k=2)(x)

    plt.figure(num=None, figsize=(7, 4), dpi=120, facecolor='w', edgecolor='k')
    plt.plot(x, y, label='optimization model', color=get_color_for_act_type(act_type), linestyle='-')
    timing_type_axis = timing_type.replace("_", " ")
    plt.title(f'{timing_type_axis.capitalize()} distribution {act_type} activities')
    plt.xlabel(f'activity {timing_type_axis} [h]')
    plt.ylabel(f'observations []')
    plt.ylim((0, schedule_df[act_type].max() + 10))
    plt.xlim((0, max_timing))
    if save_fig:
        plt.savefig(os.path.join(output_folder, f'activity_{timing_type}_distribution_{act_type}.pdf'),
                    bbox_inches='tight')
