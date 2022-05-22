import logging

from ortools.linear_solver import pywraplp
from ortools.linear_solver.pywraplp import Solver_CreateSolver, Solver

from src.config.config_container import ConfigContainer
from src.ortools_model.activity_penalties import ActivityPenalties
from src.ortools_model.activity_sequence import ActivitySequence
from src.ortools_model.basic_model import BasicModel
from src.ortools_model.travel_decisions import TravelDecisions
from src.output.output_container import OutputContainer
from src.parameter.activity_param_container import ActivityParam
from src.problem import OptimizationProblem
from src.scenario.container.activity_sets import Activity, ActivitySet
from src.scenario.container.persons import Person
from src.scenario.container.travel_components import TravelDict
from src.utils.constants import DUSK_NAME


class OptimizationCore(OptimizationProblem):
    def __init__(self, config: ConfigContainer, person: Person, activity_scoring: ActivityParam,
                 activity_set: ActivitySet, travel_dict: TravelDict):
        """
            This class contains a formulation which is able to solve the activity-based schedule generation problem for
            one individual person. The original basic optimization framework was proposed by Pougala et al. (2021).
            Swiss Federal Railways (SBB) changed the Python interface to OR-tools in order to run the optimization with
            multiple open source solvers. Also, SBB extended the optimization framework with optional activity sequence
            constraints, as well as with location choice and mode choice options.

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
        self.act_labels = activity_set.get_labels()
        self.travel_dict = travel_dict

    def formulate_problem(self):
        """
            Adds all variables and constraints to the optimization model based on the defined activity set of
            a person, a travel time matrix as well as activity and travel utility parameters.

            Returns:
                m: Full optimization model with all variables and constraints.
        """

        # get empty model object
        m = Solver_CreateSolver(self.config.solver_settings.solver_name)

        # decision variables with travel time not being modelled as actual decision
        w, z, x, d, tt = BasicModel(self.config, self.activity_param, self.act_set).add_decision_variables(m)

        # this class adds optional activity sequence restrictions (e.g. fixing the number of home activities)
        w_tour, w_subtour = ActivitySequence(self.act_set).add_restrictions(m, w, z)

        # this class makes all the travel decisions (mode choice) including location choice and calculates the
        # corresponding travel times and travel utilities for each trip
        travel_cost = TravelDecisions(self.config, self.act_set, self.travel_dict).add_variables(m, x, z, tt, w_tour,
                                                                                                 w_subtour)

        # returns utility penalties for shifting away from desired start times and durations
        pen_timing, pen_dur = ActivityPenalties(self.config, self.activity_param, self.act_set).get_penalties(m, x, d)

        # add the basic objective (maximize utility)
        self._add_objective(m, w, d, pen_timing, pen_dur, travel_cost)

        logging.info(f'optimization model consists of {m.NumVariables()} variables and {m.NumConstraints()} '
                     f'constraints.')
        return m

    def _add_objective(self, m: Solver, w, d, x_penalty, d_penalty, travel_cost):
        """
            Adds the objective to maximize utility of the schedule to the model.

            Parameters:
                m: Model containing the decision variables and constraints.
                w: Decision whether activity should take place.
                d: Duration decision for each activity.
                x_penalty: Penalty for being late or early for each activity.
                d_penalty: Penalty for too long or too short activity durations.
                travel_cost: Cost of travel (usually negative utility).

            Returns:
                Model updated with objective to maximize.
        """

        # aux terms for utility calculation in objective
        inf = m.infinity()
        big_m = self.config.solver_settings.big_m
        obj_aux = {a: m.NumVar(name=f'obj_aux_{a}', lb=-inf, ub=inf) for a in self.act_labels}

        for act in self.act_set.activities:
            a = act.label
            params_for_activity = self.activity_param.param[(act.act_type, act.scoring_group)]
            # aux term is 0 if activity does not take place (w=0)
            m.Add(obj_aux[a] >= -big_m * w[a])
            m.Add(obj_aux[a] <= big_m * w[a])
            # aux term is exactly total utility for the activity if activity does take place (w=1)
            m.Add(obj_aux[a] <= params_for_activity.constant  # constant depending on activity type
                  + d[a] * 0  # reward for doing something
                  + x_penalty.get(a, 0) + d_penalty.get(a, 0)  # penalties for shifting away from desired timings
                  + travel_cost[a]  # travel cost (usually negative utility)
                  + big_m * (1 - w[a]))
            m.Add(obj_aux[a] >= params_for_activity.constant + d[a] * 0
                  + x_penalty.get(a, 0) + d_penalty.get(a, 0)
                  + travel_cost[a]
                  - big_m * (1 - w[a]))

        # we maximize the sum of the utility over all activities which take place
        objective = m.Sum(obj_aux[a] for a in self.act_labels)
        m.Maximize(objective)

    def solve_problem(self, m: Solver):
        """
            Solves a fully defined model (m needs to include all variables and constraints as well as the objective).

            Parameters:
                m: Model containing the decision variables and constraints as well as the objective.

            Returns:
                Solved model with a result for all decision variables.
        """

        solver_settings = self.config.solver_settings
        solver_time_limit = solver_settings.time_limit  # time limit in minutes
        m.SetTimeLimit(int(solver_time_limit * 60 * 1000))

        parameters = pywraplp.MPSolverParameters()
        if solver_settings.mip_gap != 0:
            logging.info(f'setting mip gap to {solver_settings.mip_gap}')
            parameters.SetDoubleParam(pywraplp.MPSolverParameters.RELATIVE_MIP_GAP, solver_settings.mip_gap)

        m.Solve(parameters)
        return m

    def update_activity_set(self, m: Solver) -> OutputContainer:
        """
            This method has the task of translating the model solution into a realized activity set.

            Parameters:
                m: Solved optimization problem.

            Returns:
                An output container that includes all relevant information for a post-processing.
        """

        realized_activity_set = []
        for a in self.act_set.activities:
            participation = m.LookupVariable(f"w_{a}").solution_value()
            timing = m.LookupVariable(f"x_{a}").solution_value()
            duration = m.LookupVariable(f"d_{a}").solution_value()
            is_subtour = m.LookupVariable(f"w_subtour_{a}").solution_value()
            try:
                location = [l for l in a.locations if m.LookupVariable(f"loc_choice_{a}_{l}").solution_value() == 1][0]
                mode = [mo for mo in self.config.modes
                        if m.LookupVariable(f"mode_ch_{a}_{mo}").solution_value() == 1][0].__str__()
            except:
                location = a.locations
                mode = a.mode
            if a.act_type == DUSK_NAME:
                tour_no = -1
                travel_time = 0
            else:
                tour_no = [no for no in self.act_set.get_tour_numbers()
                           if m.LookupVariable(f"w_tour_{a}_{no}").solution_value() == 1][0]
                travel_time = m.LookupVariable(f"tt_{a}").solution_value()

            if participation == 1:
                realized_activity_set.append(Activity(label=a.label, participation=participation, tour_type=a.tour_type,
                                                      tour_no=tour_no, is_subtour=is_subtour,
                                                      locations=location, location_group='',
                                                      mode=mode, realized_timing=timing,
                                                      realized_duration=duration,
                                                      scoring_group=a.scoring_group, is_primary=a.is_primary,
                                                      act_type=a.act_type, desired_timing=a.desired_timing,
                                                      desired_duration=a.desired_duration, travel_time=travel_time))

        travel_cost_dict = {a.label: m.LookupVariable(f"travel_cost_{a}").solution_value()
                            for a in realized_activity_set}
        objective_dict = {a.label: m.LookupVariable(f"obj_aux_{a}").solution_value() for a in realized_activity_set}

        return OutputContainer(person=self.person, realized_activity_set=ActivitySet(activities=realized_activity_set),
                               travel_cost_dict=travel_cost_dict, objective_dict=objective_dict)
