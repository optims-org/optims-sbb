from dataclasses import dataclass
from typing import Dict, Tuple

from .locations import Location


@dataclass(frozen=True)
class Mode:
    name: str
    home_bound: bool = None

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class TimePeriod:
    name: str
    period: Tuple[float, float] = None

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class TravelIndicator:
    __slots__ = ['name']
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class ODTuple:
    __slots__ = ['origin', 'destination']
    origin: Location
    destination: Location

    def __str__(self):
        return f"({self.origin.name}, {self.destination.name})"


@dataclass
class TravelDict:
    __slots__ = ['travel_dict']
    travel_dict: Dict[str, Dict[str, Dict[str, Dict[str, float]]]]

    def get_value(self, mode: str, indicator: str, time_period: str, origin: Location, destination: Location):
        od_tuple_str = ODTuple(origin=origin, destination=destination).__str__()
        return self.travel_dict[mode][indicator][time_period][od_tuple_str]

    def get_mode_list(self):
        return [*self.travel_dict.keys()]
