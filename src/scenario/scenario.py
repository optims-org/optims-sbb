import logging

from src.scenario.container.persons import Person
from src.scenario.container.scenario import ScenarioContainer
from src.scenario.loader.activity_sets_loader import load_activity_sets
from src.scenario.loader.travel_components_loader import load_travel_data
from src.config.config_container import ConfigContainer
from src.parameter.activity_param_loader import load_activity_params
from src.utils.data_loader import data_loader


def create_scenario(config: ConfigContainer) -> ScenarioContainer:
    """
        This function reads all the input files as specified in the config and converts them into a scenario.
        All input file need to be in a consistent format, which will be checked when creating a scenario.

        Parameters:
            config: ConfigContainer

        Returns:
            scenario: ScenarioContainer
    """

    logging.info('creating scenario.')
    persons_list = [Person(name=p, activity_scoring_group=attr['activity_scoring'])
                    for p, attr in data_loader(config.input_paths.persons_file).items()]
    activity_parameter = load_activity_params(config.input_paths.activity_parameter)
    activity_sets = load_activity_sets(config.input_paths.activity_sets, persons_list)
    travel_components = load_travel_data(config.input_paths.travel_components, persons_list)
    # create a new scenario container
    scenario = ScenarioContainer(persons=persons_list,
                                 activity_sets=activity_sets, activity_parameter=activity_parameter,
                                 travel_components=travel_components)
    _check_consistency(scenario)
    logging.info('scenario is ready.')
    return scenario


def _check_consistency(scenario: ScenarioContainer):
    # todo implement several scenario consistency checks.
    # dawn/dusk in scenario?
    # are labels unique?
    # activity type in scoring?
    # travel components for each person?
    # travel times must be part of travel_components
    # are all modes defined
    # are all time periods defined
    pass
