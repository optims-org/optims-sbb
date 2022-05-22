import logging
from typing import Dict, List, Tuple

import pandas as pd

from src.output.output_container import OutputContainer
from src.scenario.container.activity_sets import Activity
from src.scenario.container.persons import Person


class Solution:
    def __init__(self):
        """
            The solution class contains all the relevant outputs of the optimization model. For each person, it
            stores the realized activities as well as additional optional outputs.
        """

        self.output_container: Dict[Person, OutputContainer] = {}

    def add_person(self, person: Person, output: OutputContainer):
        if self.output_container.get(person):
            logging.info(f'person with id {person.name} already has an output container. will be overwritten.')
        self.output_container[person] = output

    def get_person(self, person: Person) -> OutputContainer:
        return self.output_container[person]

    def get_full_result_df(self) -> pd.DataFrame:
        realized_act_sets = self._get_realized_activity_sets()
        df = pd.DataFrame(realized_act_sets, columns=['label', 'act_type', 'tour_type', 'tour_no', 'is_primary',
                                                      'is_subtour', 'realized_timing', 'realized_duration',
                                                      'travel_time', 'locations', 'mode'])
        df['person_id'] = [o.person.name for o in self.output_container.values()
                           for _ in o.realized_activity_set.activities]
        df = df.set_index('person_id')
        return df

    def _get_realized_activity_sets(self) -> List[Activity]:
        return [a for o in self.output_container.values() for a in o.realized_activity_set.get_sorted_activity_list()]

    def get_solver_times(self) -> List[Tuple[int, float]]:
        return [(o.realized_activity_set.get_size(), o.solver_time) for o in self.output_container.values()]
