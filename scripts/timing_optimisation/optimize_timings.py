import logging
from pathlib import Path

from src.config.config_loader import load_config
from src.output.output_writer import OutputWriter
from src.scenario.scenario import create_scenario
from src.simulator import Simulator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

CONFIG_FILE = Path(__file__).parent.parent.parent / 'assets' / 'timing_optimisation' / 'config.yml'


def run_example():
    """
        This scripts runs a minimal example of an optimization model for one person. The person is only allowed to
        shift timings and durations, and neither modes nor the activity sequence. Inputs can be found under
        ./assets/timing_optimisation/.
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
    run_example()
