import logging
from pathlib import Path
from typing import Dict, List

from ..container.activity_sets import Activity, ActivitySet
from ..container.locations import Location
from ..container.persons import Person
from ...utils.data_loader import data_loader


def load_activity_sets(activity_sets_file: Path, persons_list: List[Person]) -> Dict[Person, ActivitySet]:
    activity_sets_raw = data_loader(file_path=activity_sets_file)
    activity_sets = {}
    for person in persons_list:
        activity_set_raw = activity_sets_raw[person.name]
        activities = []
        for label_raw, act_raw in activity_set_raw.items():
            locations_raw = act_raw['locations'] if isinstance(act_raw['locations'], list) else [act_raw['locations']]
            locations = [Location(name=l) for l in locations_raw]
            desired_timing = act_raw.get('desired_timing', -1)
            desired_timing = desired_timing if isinstance(desired_timing, List) else [desired_timing]
            desired_duration = act_raw.get('desired_duration', -1)
            desired_duration = desired_duration if isinstance(desired_duration, List) else [desired_duration]
            activities.append(Activity(label=label_raw, act_type=act_raw['activity_type'],
                                       scoring_group=act_raw.get('scoring_group', ''),
                                       participation=act_raw.get('participation', 1),
                                       is_primary=act_raw.get('is_primary', False),
                                       tour_type=act_raw.get('tour_type', 'secondary'),
                                       tour_no=act_raw.get('tour_no', -1),
                                       locations=locations, location_group=act_raw.get('location_group', None),
                                       is_subtour=act_raw.get('is_subtour', False),
                                       desired_timing=desired_timing, desired_duration=desired_duration,
                                       realized_timing=-1, realized_duration=-1, travel_time=-1))
        activity_sets[person] = ActivitySet(activities=activities)
    logging.info(f'loaded {len(activity_sets)} activity sets.')
    return activity_sets
