from dataclasses import dataclass
from typing import Dict, List

from src.parameter.activity_param_container import ActivityParam
from .activity_sets import ActivitySet
from .persons import Person
from .travel_components import TravelDict


@dataclass(frozen=True)
class ScenarioContainer:
    persons: List[Person]
    activity_sets: Dict[Person, ActivitySet]
    travel_components: Dict[Person, TravelDict]
    activity_parameter: Dict[str, ActivityParam]

    def get_persons(self) -> List[Person]:
        return self.persons

    def get_activity_set_for_person(self, person: Person) -> ActivitySet:
        activity_set = self.activity_sets.get(person, None)
        if activity_set:
            return activity_set
        else:
            raise KeyError(f'person with id {person.name} has no activity set.')

    def get_travel_dict_for_person(self, person: Person) -> TravelDict:
        travel_components = self.travel_components.get(person, None)
        if travel_components:
            return travel_components
        else:
            raise KeyError(f'person with id {person.name} has no travel components.')

    def get_act_param_for_person_group(self, person_group: str) -> ActivityParam:
        act_params = self.activity_parameter.get(person_group, None)
        if act_params:
            return act_params
        else:
            raise KeyError(f'person group {person_group} has no activity parameter.')
