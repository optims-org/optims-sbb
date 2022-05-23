from typing import Dict, List

import numpy as np

from src.utils.constants import DAWN_NAME, HOME_NAME
from src.parameter.activity_param_container import ActivityParam
from src.scenario.container.activity_sets import ActivitySet
from src.scenario.container.persons import Person


def assign_desired_timings(persons: List[Person], activity_sets: Dict[Person, ActivitySet],
                           activity_parameter: Dict[str, ActivityParam]):
    """
         This function assigns the desired timings and durations to each activity based on the parameter
         as given for each scoring group. Returns an updated activity set for each person.

         Parameters:
             persons: list of all persons in the scenario
             activity_sets: dictionary containing an activity set for each person
             activity_parameter: dictionary containing
    """

    rand = np.random.RandomState(seed=20211220)
    for person in persons:
        person_group = person.activity_scoring_group
        activity_param = activity_parameter[person_group]
        activity_set = activity_sets[person]
        primary_act_types = []
        for a in activity_set.activities:
            act_param = activity_param.param[(a.act_type, a.scoring_group)]
            st = rand.normal(act_param.des_timing_mean, act_param.des_timing_std)
            if isinstance(st, (np.ndarray, np.generic)):
                st = rand.choice(st)
            a.desired_timing = [st if st >= 0 else 0]

            if a.act_type == DAWN_NAME:
                act_param = activity_param.param[(f'{HOME_NAME}_budget', 'all')]
            elif a.is_primary and a.act_type not in primary_act_types:
                act_param = activity_param.param[(f'{a.act_type}_budget', 'all')]
                primary_act_types.append(a.act_type)
            dur = rand.normal(act_param.des_duration_mean, act_param.des_duration_std)
            if isinstance(dur, (np.ndarray, np.generic)):
                dur = rand.choice(dur)
            a.desired_duration = [dur if dur >= 0 else 0]
