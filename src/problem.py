from .config.config_container import ConfigContainer
from .output.output_container import OutputContainer
from .parameter.activity_param_container import ActivityParam
from .scenario.container.activity_sets import ActivitySet
from .scenario.container.persons import Person
from .scenario.container.travel_components import TravelDict


class OptimizationProblem:
    def __init__(self, config: ConfigContainer, person: Person, activity_scoring: ActivityParam,
                 activity_set: ActivitySet, travel_dict: TravelDict):
        """
            This abstract class contains the general structure of an optimization model as needed in this context.
            An optimization model solves one scheduling problem for one person based on a given activity set and given
            travel components.

            Parameters:
                config: ConfigContainer
                person: Person
                activity_scoring: ActivityParam
                activity_set: ActivitySet
                travel_dict: TravelDict
        """

        self.config = config
        self.person = person
        self.activity_param = activity_scoring
        self.act_set = activity_set
        self.travel_dict = travel_dict

    def formulate_problem(self):
        """
            This method has the task of formulating the optimization model by adding the constraints and
            decisions variables.
            It returns the full model with all the constraints and decision variables.
        """

        raise NotImplementedError()

    def solve_problem(self, model):
        """
            This method has the task of calling the solve method of the model. It returns a solved model including
            a solution for every decision variable.
        """

        raise NotImplementedError()

    def update_activity_set(self, model) -> OutputContainer:
        """
            This method updates the activity set with the outcomes of the model. Basically, it brings the results
            of all decision variables back to the activity set.
        """

        raise NotImplementedError()
