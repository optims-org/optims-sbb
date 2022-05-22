import logging
import os

import numpy as np
import pandas as pd

from .exporter.matsim_plans import write_matsim_plans
from .plots.activity_profile import plot_activity_profile
from .plots.schedule import plot_schedule
from .plots.timing_distribution import plot_timing_distribution_for_act_type
from .plots.timing_duration_heatmap import plot_heatmap_for_act_type
from ..config.config_container import ConfigContainer
from ..solution import Solution
from ..utils.constants import DAWN_NAME, DUSK_NAME, HOME_NAME


class OutputWriter:
    def __init__(self, config: ConfigContainer, solution: Solution):
        """
            This class writes several key statistics based on the model solution. Per default, all statistics are
            generated.
            Several statistics are available: computational times, activity profiles, heat maps or timing histograms.

            Parameters:
                config: ConfigContainer
                solution: Solution
        """

        self.solution = solution
        self.solver_times = solution.get_solver_times()
        self.solution_df = solution.get_full_result_df()
        self.output_folder = config.output_folder.resolve()
        self.rel_act_types = [a for a in self.solution_df['act_type'].unique() if a not in [DAWN_NAME, DUSK_NAME]]

        self._create_output_folder()

    def _create_output_folder(self):
        logging.info(f'writing outputs to {self.output_folder}.')
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        pass

    def write_statistics(self):
        self._write_solver_times()
        self._write_realized_activity_sets()
        self._create_activity_timing_histogram(timing_type='start_time')
        self._create_activity_timing_histogram(timing_type='end_time')
        self._create_activity_timing_histogram(timing_type='duration')
        self._plot_timing_duration_heatmap()
        self._create_activity_profile()
        self._plot_random_schedules()
        self._write_matsim_plans()
        logging.info('finished writing output statistics.')

    def _write_matsim_plans(self):
        write_matsim_plans(os.path.join(self.output_folder, f'plans.xml.gz'), self.solution)

    def _plot_random_schedules(self):
        person_ids = [*self.solution_df.index.unique()]
        person_ids = np.random.choice(person_ids, min(len(person_ids), 10), replace=False)
        for i in person_ids:
            plot_schedule(self.solution_df.loc[i], self.output_folder)

    def _plot_timing_duration_heatmap(self):
        df = self.solution_df.copy()
        df.loc[((df['act_type'] == DAWN_NAME) | (df['act_type'] == DUSK_NAME)), 'act_type'] = HOME_NAME
        df['duration_class'] = 0.5 * (df['realized_duration'] / 0.5).apply(np.floor)
        df['start_time_class'] = 1.0 * (df['realized_timing'] / 1).apply(np.floor)
        df['pf'] = 1
        for act_type in self.rel_act_types:
            plot_heatmap_for_act_type(df, self.output_folder, act_type,
                                      max_dur=df[df['act_type'] == act_type]['realized_duration'].max())

    def _create_activity_timing_histogram(self, timing_type: str = 'start_time'):
        df = self.solution_df.copy()
        df = df[df['act_type'] != DAWN_NAME]
        df.loc[df['act_type'] == DUSK_NAME, 'act_type'] = HOME_NAME
        if timing_type == 'start_time':
            df[f'{timing_type}_class'] = 0.5 * (df['realized_timing'] / 0.5).apply(np.floor)
            max_x = 26.5
        elif timing_type == 'end_time':
            df[f'{timing_type}_class'] = 0.5 * ((df['realized_timing'] + df['realized_duration']) / 0.5).apply(np.floor)
            max_x = 26.5
        elif timing_type == 'duration':
            df[f'{timing_type}_class'] = 0.5 * (df['realized_duration'] / 0.5).apply(np.floor)
            max_x = df['realized_duration'].max() + 0.5
        else:
            raise KeyError(f'{timing_type} is not valid.')
        df = df.groupby(['act_type', f'{timing_type}_class']).agg({'realized_timing': 'count'}).unstack(level=0)
        df = df.reindex(index=np.arange(start=0, stop=max_x, step=0.5)).fillna(0).droplevel(level=0, axis=1)
        df['all'] = df.sum(axis=1)
        df.to_csv(os.path.join(self.output_folder, f'activity_{timing_type}_histogram.csv'), sep=";")

        for col in df.columns:
            plot_timing_distribution_for_act_type(df, self.output_folder, timing_type=timing_type, act_type=col,
                                                  max_timing=max_x)

    def _create_activity_profile(self):
        df = self.solution_df.copy()
        df['start_time_minutes'] = 60 * df['realized_timing']
        df['end_time_minutes'] = 60 * (df['realized_timing'] + df['realized_duration'])
        df['act_index'] = 0
        df.loc[df['act_type'] == DAWN_NAME, 'act_index'] = 1
        df.loc[((df['act_type'] == DAWN_NAME) | (df['act_type'] == DUSK_NAME)), 'act_type'] = HOME_NAME
        act_to_ind_dict = {self.rel_act_types[i]: i for i in range(len(self.rel_act_types))}
        df['act_number'] = df['act_type'].map(act_to_ind_dict).fillna(0).astype(int)

        plot_activity_profile(df, self.output_folder, self.rel_act_types)

    def _write_realized_activity_sets(self):
        self.solution_df.to_csv(os.path.join(self.output_folder, r'realized_activity_sets.csv'), sep=";")

    def _write_solver_times(self):
        df = pd.DataFrame(self.solver_times, columns=['number_of_activities', 'solving time'])
        df['observations'] = 1
        df = df.groupby('number_of_activities').agg({'solving time': 'mean', 'observations': 'count'})
        df.to_csv(os.path.join(self.output_folder, r'solving_time.csv'), sep=";")
        # todo add plot
