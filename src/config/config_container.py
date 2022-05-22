from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.scenario.container.travel_components import TimePeriod, Mode


@dataclass(frozen=True)
class InputPaths:
    persons_file: Path
    activity_parameter: Path
    activity_sets: Path
    travel_parameter: Path
    travel_components: Path

    def __str__(self):
        return f"activity sets: {self.activity_sets}; activity parameter: {self.activity_parameter}; " \
               f"travel components: {self.travel_components}; travel parameter: {self.travel_parameter}"


@dataclass(frozen=True)
class SolverSettings:
    solver_name: str = 'SCIP'
    big_m: int = 1_000
    time_limit: float = 5.0
    mip_gap: float = 0.0


@dataclass(frozen=True)
class ModelSettings:
    act_sequence_restrictions: str
    mode_choice_restrictions: str
    min_act_duration: float = 0.2


@dataclass(frozen=True)
class ConfigContainer:
    input_paths: InputPaths
    output_folder: Path
    time_periods: List[TimePeriod]
    modes: List[Mode]
    cores: int
    solver_settings: SolverSettings
    model_settings: ModelSettings

    def __str__(self) -> str:
        return f'\n \t - input paths: {self.input_paths}' \
               f'\n \t - solver settings: {self.solver_settings}' \
               f'\n \t - model settings: {self.model_settings}' \
               f'\n \t - time periods: {self.time_periods}' \
               f'\n \t - modes: {self.modes}' \
               f'\n \t - cores: {self.cores}'
