import os

import matplotlib.pyplot as plt
import numpy as np

from src.output.plots.colors import get_color_for_act_type
from src.utils.constants import DUSK_NAME


def plot_schedule(schedule_df, output_folder, save_fig=True):
    """
        Plots given realized activity set for one person.

        Parameters:
            schedule_df: dataframe containing the realized activity set
            output_folder: output folder
    """

    person_ids = schedule_df.index.unique()
    assert len(person_ids) == 1
    person_id = person_ids[0]
    max_time = max(schedule_df[['realized_timing', 'realized_duration']].sum(axis=1))
    plt.figure(figsize=[20, 3])
    y1 = [0, 0]
    y2 = [1, 1]
    plt.fill_between([0, max_time], y1, y2, color='silver')

    for idx, row in schedule_df.iterrows():
        end_time = row['realized_timing'] + row['realized_duration']
        # plot activity episode
        x = [row['realized_timing'], end_time]
        plt.fill_between(x, y1, y2, color=get_color_for_act_type(row['act_type']))
        plt.text(np.mean(x), 1.6, row['act_type'], horizontalalignment='center', verticalalignment='center',
                 rotation=-25, fontsize=10)

        # plot travel episode after activity participation
        if not row['act_type'] == DUSK_NAME:
            x = [end_time, end_time + row['travel_time']]
            plt.text(np.mean(x), 1.2, row['mode'], horizontalalignment='center', verticalalignment='center',
                     fontsize=8)
            plt.fill_between(x, y1, y2, color=get_color_for_act_type('travel'))

    plt.xticks(np.arange(0, max_time + 1))
    plt.yticks([])
    plt.xlim([0, max_time])
    plt.ylim([-0.2, 2])
    plt.xlabel('time of day [h]')
    if save_fig:
        plt.savefig(os.path.join(output_folder, f'schedule_{person_id}.pdf'), bbox_inches='tight')
