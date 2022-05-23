from pathlib import Path
from typing import Dict

from src.parameter.activity_param_container import ActivityParam as ActParam
from src.parameter.activity_param_container import ActivityParamContainer as ActParamContainer
from src.utils.data_loader import data_loader


def load_activity_params(param_file: Path) -> Dict[str, ActParam]:
    """
        This function reads the activity parameter from a file and stores them in a dictionary. One set
        of activity parameter for each homogeneous scoring group.

        Parameters:
            param_file: file containing the activity parameters

        Returns:
            person_group_params: activity parameter for a specific person group
    """

    param_raw = data_loader(file_path=param_file)

    person_group_params = {}
    for person_group, activity_types in param_raw.items():
        act_params = {}
        for act_type, activity_groups in activity_types.items():
            if not activity_groups:
                activity_groups = {'': {}}
            for gr, pa in activity_groups.items():
                assert pa.get('penalty_early', 0) <= 0
                assert pa.get('penalty_late', 0) <= 0
                assert pa.get('penalty_short', 0) <= 0
                assert pa.get('penalty_long', 0) <= 0
                assert pa.get('feasible_start', 0) < pa.get('feasible_end', 99999)
                act_params[(act_type, gr)] = ActParamContainer(feasible_start=pa.get('feasible_start', 0),
                                                               feasible_end=pa.get('feasible_end', 99999),
                                                               constant=pa.get('constant', 0),
                                                               des_timing_mean=pa.get('desired_timing_mean', 0),
                                                               des_timing_std=pa.get('desired_timing_std', 0),
                                                               pen_early=pa.get('penalty_early', 0),
                                                               pen_late=pa.get('penalty_late', 0),
                                                               des_duration_mean=pa.get('desired_duration_mean', 0),
                                                               des_duration_std=pa.get('desired_duration_std', 0),
                                                               pen_short=pa.get('penalty_short', 0),
                                                               pen_long=pa.get('penalty_long', 0))
        person_group_params[person_group] = ActParam(param=act_params)
    return person_group_params
