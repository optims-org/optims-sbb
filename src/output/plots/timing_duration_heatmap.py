import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def plot_heatmap_for_act_type(schedule_df: pd.DataFrame, output_folder, act_type: str = None, max_dur: float = 10.0,
                              min_timing: float = 5.0, max_timing: float = 23.0, save_fig=True):
    if act_type:
        mask = ((schedule_df['realized_timing'] > min_timing) & (schedule_df['realized_timing'] < max_timing) &
                (schedule_df['realized_duration'] <= max_dur) & (schedule_df['act_type'] == act_type))
    else:
        act_type = 'all'
        mask = ((schedule_df['realized_timing'] > min_timing) & (schedule_df['realized_timing'] < max_timing) &
                (schedule_df['realized_duration'] <= max_dur))
    table = pd.pivot_table(schedule_df[mask], index='duration_class', columns='start_time_class', aggfunc='count')['pf']
    # reindex duration (rows)
    table = table.reindex(np.arange(start=0.0, stop=max_dur + 0.5, step=0.5)).fillna(0)
    # reindex timing (columns)
    table = table.reindex(np.arange(start=min_timing, stop=max_timing + 1, step=1.0), axis=1).fillna(0)
    plt.figure(num=None, figsize=(7, 4), dpi=120, facecolor='w', edgecolor='k')
    ax = sns.heatmap(table, cmap="Greys", linewidths=.1)
    ax.invert_yaxis()
    plt.title(f'{act_type} activities')
    plt.xlabel('start time [h]')
    plt.ylabel('duration [h]')
    if save_fig:
        plt.savefig(os.path.join(output_folder, f"timing_duration_heatmap_{act_type}.pdf"), bbox_inches='tight')
