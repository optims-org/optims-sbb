from dataclasses import dataclass, field
from typing import List, Union

from .locations import Location
from ...utils.constants import HOME_NAME, DAWN_NAME, DUSK_NAME


@dataclass(order=True)
class Activity:
    __slots__ = ['label', 'act_type', 'tour_type', 'locations', 'desired_timing', 'desired_duration',
                 'realized_timing', 'realized_duration', 'travel_time', 'is_primary', 'is_subtour', 'tour_no',
                 '__dict__']
    sort_index: int = field(init=False, repr=False)
    label: str
    scoring_group: str
    act_type: str
    tour_type: str
    locations: Union[str, Location, List[Location]]
    location_group: str
    desired_timing: Union[float, List[float]]
    desired_duration: Union[float, List[float]]
    realized_timing: float
    realized_duration: float
    travel_time: float
    is_primary: bool
    is_subtour: bool
    tour_no: int
    participation: int = 1
    mode: str = ''

    def __post_init__(self):
        self.sort_index = self.realized_timing

    def get_attribute_by_str(self, attribute: str):
        mapping = {
            'tour_type': self.tour_type,
            'is_primary': self.is_primary
        }
        return mapping[attribute]

    def __str__(self) -> str:
        return f'{self.label}'


@dataclass
class ActivitySet:
    __slots__ = ['activities']
    activities: List[Activity]

    def get_size(self) -> int:
        return len(self.activities)

    def get_labels(self) -> List[str]:
        return [a.label for a in self.activities]

    def get_activity_by_index(self, i: int) -> Activity:
        return self.activities[i]

    def get_label_to_act(self):
        return {a.label: a for a in self.activities}

    def get_label_to_type(self):
        return {a.label: a.act_type for a in self.activities}

    def get_acts_wo_home(self):
        return [a for a in self.activities if a.act_type not in [HOME_NAME, DAWN_NAME, DUSK_NAME]]

    def get_labels_wo_home(self):
        return [a.label for a in self.get_acts_wo_home()]

    def get_labels_wo_dusk(self):
        return [a.label for a in self.activities if a.act_type != DUSK_NAME]

    def get_sorted_activity_list(self) -> List[Activity]:
        return sorted(self.activities)

    def get_tour_numbers(self) -> List[int]:
        return [*range(1, len(self.activities) - len(self.get_acts_wo_home()))]

    def get_number_of_tours(self) -> int:
        return len(self.get_tour_numbers())

    def get_number_of_primary_tours(self) -> int:
        return len(set([a.tour_no for a in self.activities if a.is_primary]))

    def get_number_of_activities_for_type(self, act_type: str) -> int:
        return len([a for a in self.activities if a.act_type == act_type])
