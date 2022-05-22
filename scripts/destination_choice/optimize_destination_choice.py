import logging
from pathlib import Path

from src.config.config_loader import load_config
from src.output.output_writer import OutputWriter
from src.scenario.scenario import create_scenario
from src.simulator import Simulator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

CONFIG_FILE = Path(__file__).parent.parent.parent / 'assets' / 'destination_choice' / 'config.yml'


def run_destination_choice():
    """
        This scripts runs an example of an optimization model for one person with a choice set of 10 considered
        locations per activity. The activity set was developed for the master thesis of Nicolas Salvadé.
        It is available under ./assets/destination_choice/.
    """

    # 1: load model configuration
    config = load_config(config_file=CONFIG_FILE)
    # 2: load and prepare all the required input data
    scenario = create_scenario(config=config)
    # 3: run the optimization model
    solution = Simulator(config=config, scenario=scenario).run()
    # 4: write the output statistics
    OutputWriter(config=config, solution=solution).write_statistics()


if __name__ == '__main__':
    run_destination_choice()
