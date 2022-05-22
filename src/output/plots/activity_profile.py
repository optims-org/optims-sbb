import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .colors import get_color_for_act_type, get_activity_hierarchy


def plot_activity_profile(schedule_df: pd.DataFrame, output_folder, act_types: List[str], save_fig=True):
    act_types_plus_travel = act_types + ['travel']
    max_t = int(27 * 60 / 5)
    max_acts = len(act_types_plus_travel)

    act_array = np.zeros((max_acts, max_t), dtype=int)
    array_info = schedule_df[['act_index', 'start_time_minutes', 'end_time_minutes', 'act_number']].values

    for i in range(array_info.shape[0]):
        row = array_info[i]

        if row[0] == 1:
            from_t_ind = 0
        else:
            from_t_ind = int(row[1] / 5)

            # process travel episode
            last_row = array_info[i - 1]
            last_act_end_time = int(last_row[2] / 5)
            act_array[max_acts - 1][last_act_end_time:from_t_ind] += 1

        if i == array_info.shape[0] - 1:
            to_t_ind = max_t
        elif array_info[i + 1][0] == 1:
            to_t_ind = max_t
        else:
            to_t_ind = int(row[2] / 5)

        act_array[int(row[3])][from_t_ind:to_t_ind] += 1

    df_act_stacked = pd.DataFrame(act_array.T, columns=act_types_plus_travel)
    df_act_stacked.index = df_act_stacked.index * 5 / 60
    df_act_stacked = df_act_stacked.div(df_act_stacked.sum(axis=1), axis=0)

    plot_hierarchy = ([t for t in get_activity_hierarchy() if t in act_types_plus_travel] +
                      [t for t in act_types_plus_travel if t not in get_activity_hierarchy()])
    colors = [get_color_for_act_type(t) for t in plot_hierarchy]
    plt.figure(num=None, figsize=(7, 4), dpi=120, facecolor='w', edgecolor='k')
    plt.stackplot(df_act_stacked.index, df_act_stacked[plot_hierarchy].values.T, colors=colors, labels=plot_hierarchy)
    plt.legend()
    plt.title(f'Activity profiles')
    plt.xlabel('time of day [h]')
    plt.xlim((2, 26))
    plt.ylabel('activity frequency []')
    if save_fig:
        plt.savefig(os.path.join(output_folder, f'activity_profile.pdf'), bbox_inches='tight')
