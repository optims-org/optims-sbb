import logging
from pathlib import Path
from typing import Dict, List

from ..container.locations import Location
from ..container.persons import Person
from ..container.travel_components import Mode, TimePeriod, TravelIndicator, ODTuple, TravelDict
from ...utils.data_loader import data_loader


def load_travel_data(travel_components_file: Path, persons_list: List[Person]) -> Dict[Person, TravelDict]:
    travel_components_raw = data_loader(file_path=travel_components_file)
    travel_components = {}
    for person in persons_list:
        modes_raw = travel_components_raw[person.name]
        modes = {}
        for mode_raw, travel_indicators_raw in modes_raw.items():
            travel_indicators = {}
            for travel_indicator_raw, time_periods_raw in travel_indicators_raw.items():
                time_periods = {}
                for time_period_raw, ods_raw in time_periods_raw.items():
                    od_tuples = {}
                    for origin, destinations in ods_raw.items():
                        for destination, value in destinations.items():
                            od_tuple = ODTuple(origin=Location(name=origin),
                                               destination=Location(name=destination))
                            od_tuples[od_tuple.__str__()] = value
                    time_periods[TimePeriod(name=time_period_raw).__str__()] = od_tuples
                travel_indicators[TravelIndicator(name=travel_indicator_raw).__str__()] = time_periods
            modes[Mode(name=mode_raw).__str__()] = travel_indicators
        travel_components[person] = TravelDict(travel_dict=modes)
    logging.info(f'loaded all travel components.')
    return travel_components
