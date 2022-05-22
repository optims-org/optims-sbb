import logging
from pathlib import Path
from typing import List

from src.config.config_container import ConfigContainer, SolverSettings, ModelSettings, InputPaths
from src.scenario.container.travel_components import TimePeriod, Mode
from src.utils.data_loader import data_loader


def load_config(config_file: Path) -> ConfigContainer:
    """
        This function fills the configuration container by reading a given file.
        A minimal configuration file must contain:
            input_paths:
                persons: str
                activity_sets: str
                activity_parameter: str
                travel_components: str
            output_folder: str
            time_periods:
                all_day:
                    period_start: int
                    period_end: int
            modes:
                car:
                    home_bound: bool

        Parameters:
            config_file: path to configuration file

        Returns:
            config: ConfigContainer
    """

    config_raw = data_loader(file_path=config_file)

    # number of cores used to run the simulation. default is 1.
    cores = config_raw.get('cores', 1)
    # output folder to which the statistics will be written. default is output
    output_folder = Path(config_raw.get('output_folder', None))
    if not output_folder:
        raise KeyError('output_folder must be part of the configuration file.')

    input_paths = _create_input_paths(config_raw)  # paths to all the required scenario inputs
    solver_settings = _create_solver_settings(config_raw)  # solver-specific settings
    model_settings = _create_model_settings(config_raw)  # model-specific settings
    modes = _create_modes(config_raw)  # mode configurations
    time_periods = _create_time_periods(config_raw)  # time period configurations

    config = ConfigContainer(input_paths=input_paths, solver_settings=solver_settings, model_settings=model_settings,
                             modes=modes, time_periods=time_periods, cores=cores, output_folder=output_folder)
    logging.info(f'imported model config: {config}')
    return config


def _create_input_paths(config_raw) -> InputPaths:
    input_paths = config_raw.get('input_paths', None)
    if input_paths:
        persons = input_paths.get('persons', None)
        activity_sets = input_paths.get('activity_sets', None)
        activity_parameter = input_paths.get('activity_parameter', None)
        travel_components = input_paths.get('travel_components', None)
        # todo: travel parameter are not yet included in the model
        travel_parameter = input_paths.get('travel_parameter', None)
        assert persons and activity_sets and activity_sets and activity_parameter and travel_components, \
            'all required input paths must be specified!'
    else:
        raise KeyError('input_paths must be part of the configuration file.')
    return InputPaths(persons_file=Path(persons),
                      activity_sets=Path(activity_sets), activity_parameter=Path(activity_parameter),
                      travel_components=Path(travel_components), travel_parameter=travel_parameter)


def _create_time_periods(config_raw) -> List[TimePeriod]:
    time_periods_raw = config_raw.get('time_periods', None)
    if time_periods_raw:
        time_periods = [TimePeriod(name=tp, period=(attr['period_start'], attr['period_end']))
                        for tp, attr in time_periods_raw.items()]
    else:
        raise KeyError('at least one time period with a start and end time must be defined.')
    return time_periods


def _create_modes(config_raw) -> List[Mode]:
    modes_raw = config_raw.get('modes', None)
    if modes_raw:
        modes = [Mode(name=m, home_bound=attr['home_bound']) for m, attr in modes_raw.items()]
    else:
        raise KeyError('at least one mode must be defined.')
    return modes


def _create_solver_settings(config_raw) -> SolverSettings:
    solver_settings_raw = config_raw.get('solver_settings', None)
    if not solver_settings_raw:
        solver_settings_raw = {}
    solver_name = solver_settings_raw.get('solver_name', 'SCIP').lower()  # default solver is SCIP
    big_m = solver_settings_raw.get('big_m', 1000)
    time_limit = solver_settings_raw.get('time_limit', 5.0)  # time limit to solve one schedule
    mip_gap = solver_settings_raw.get('mip_gap', 0.0)
    return SolverSettings(solver_name=solver_name, big_m=big_m, time_limit=time_limit, mip_gap=mip_gap)


def _create_model_settings(config_raw) -> ModelSettings:
    model_settings_raw = config_raw.get('model_settings', None)
    if not model_settings_raw:
        model_settings_raw = {}
    mode_choice_restrictions = model_settings_raw.get('mode_choice_restrictions', None)
    act_sequence_restrictions = model_settings_raw.get('act_sequence_restrictions', None)
    min_act_duration = model_settings_raw.get('min_act_duration', 0.2)
    return ModelSettings(act_sequence_restrictions=act_sequence_restrictions,
                         mode_choice_restrictions=mode_choice_restrictions, min_act_duration=min_act_duration)
