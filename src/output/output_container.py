from dataclasses import dataclass
from typing import Dict

from ..scenario.container.activity_sets import ActivitySet
from ..scenario.container.persons import Person


@dataclass
class OutputContainer:
    person: Person
    realized_activity_set: ActivitySet
    travel_cost_dict: Dict[str, float]
    objective_dict: Dict[str, float]
    solver_time: float = 0
