import gzip
import io

from matsim import writers

from src.solution import Solution
from src.utils.constants import DUSK_NAME


def write_matsim_plans(output_filename, solution: Solution):
    with gzip.open(output_filename, 'wb+') as f_write:
        with io.BufferedWriter(f_write, buffer_size=2 * 1_024 ** 3) as buffered_writer:
            writer = writers.PopulationWriter(buffered_writer)
            writer.start_population()

            for person, container in solution.output_container.items():
                writer.start_person(person_id=person.name)
                writer.start_plan(selected=True)
                for activity in container.realized_activity_set.get_sorted_activity_list():
                    if isinstance(activity.locations, list):
                        # todo this should be resolved in the creation of the realized activity set
                        loc = activity.locations[0]
                    else:
                        loc = activity.locations
                    # todo integrate location reader which loads coordinates
                    writer.add_activity(type=activity.act_type, x=loc.x_coord, y=loc.y_coord,
                                        start_time=int(activity.realized_timing * 3600),
                                        end_time=int(3600 * (activity.realized_timing + activity.realized_duration)))
                    if activity.act_type != DUSK_NAME:
                        writer.add_leg(mode=activity.mode, travel_time=int(3600 * activity.travel_time))
                writer.end_plan()
                writer.end_person()
            writer.end_population()
