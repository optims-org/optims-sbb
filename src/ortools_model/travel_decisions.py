from collections import defaultdict

from ortools.linear_solver.pywraplp import Solver

from src.config.config_container import ConfigContainer
from src.scenario.container.activity_sets import ActivitySet
from src.scenario.container.travel_components import TravelDict


class TravelDecisions:
    def __init__(self, config: ConfigContainer, activity_set: ActivitySet, travel_dict: TravelDict):
        """
            This class is responsible to manage choice variables for mode, location and time of day choice if necessary.
            It sets the travel time between two activities equal to the value in the travel matrix which is given by
            an external input.

             Parameters:
                 config: ConfigContainer
                 activity_set: ActivitySet
                 travel_dict: TravelDict
        """

        self.config = config
        self.travel_dict = travel_dict

        self.modes = [m.name for m in config.modes if m.name in travel_dict.get_mode_list()]
        self.home_based_modes = [m.name for m in config.modes if
                                 (m.home_bound and (m.name in travel_dict.get_mode_list()))]

        self.time_periods = {tp.name: tp.period for tp in config.time_periods}

        self.act_set = activity_set
        self.tour_numbers = activity_set.get_tour_numbers()
        self.activities = activity_set.activities
        self.act_labels = activity_set.get_labels()
        self.act_label_to_type = activity_set.get_label_to_type()
        self.act_labels_wo_home = activity_set.get_labels_wo_home()
        self.act_labels_wo_dusk = activity_set.get_labels_wo_dusk()

    def add_variables(self, m: Solver, x, z, tt, w_tour, w_subtour):
        """
            This method introduces choice variables for mode, location and time of day choice if necessary. Based
            on those choices, it looks up the travel time from an external matrix. Also, it calculates the costs
            for travelling between two activities.

            Parameters:
                m: Optimization model with basic variables and constraints.
                x: Start time decision for each activity.
                z: Decision about activity sequence.
                tt: Travel time decision between two activities.
                w_tour: Variable which indicates the tour number in which the activity takes place. Necessary
                    for sub-tour based mode choice.
                w_subtour: Variable which indicates whether the activity takes place in a sub-tour.

            Returns:
                travel_cost: Cost for traveling between two activities a and b at a certain time using a certain mode.
        """

        # if we have either more than 1 mode, 1 time slot or multiple desired locations, we must introduce
        # a binary product which combines the choices in all these dimensions and will be multiplied with the
        # travel time matrix later.
        if len(self.modes) > 1 or len(self.time_periods) > 1 or any([len(a.locations) > 1 for a in self.activities]):
            # introducing the choice variables for location, mode and time slot decisions
            location_choice = self._add_location_choice_variable(m)
            time_slot_choice = self._add_time_slot_variable(m, x)
            mode_choice = self._add_mode_choice_variable(m)
            # mode choice can be restricted to subtour based mode choice
            if self.config.model_settings.mode_choice_restrictions == 'subtour_based':
                self._subtour_based_mode_choice_constraints(m, z, mode_choice, w_tour, w_subtour)
            # introducing the product to represent the combination between mode, time and location choice
            prod = self._add_location_mode_time_slot_product(m, z, mode_choice, location_choice, time_slot_choice)
            # adding travel time constraints and calculate travel costs
            self._add_mode_specific_travel_time_constraint(m, tt, prod)
        else:
            # if no choice variables are defined, one can simply look up the travel time without binary product
            self._add_simple_travel_time_constraint(m, tt, z)

        # introducing the linear travel cost calculation
        travel_utilities = {'p_travel': -1}  # todo: read the travel utility from a file
        travel_cost = self._add_travel_cost(m, tt, travel_utilities)

        return travel_cost

    def _add_mode_choice_variable(self, m):
        # mode choice variable
        mode_ch = {(a, mode): m.IntVar(name=f'mode_ch_{a}_{mode}', lb=0, ub=1)
                   for a in self.act_labels for mode in self.modes}

        # one mode per trip only
        for a in self.act_labels:
            m.Add(m.Sum(mode_ch[a, mode] for mode in self.modes) == 1)

        return mode_ch

    def _subtour_based_mode_choice_constraints(self, m, z, mode_ch, w_tour, w_subtour):
        # two primary activity variable which is one if two primary activities are present in a tour
        two_prim_acts_in_tour = {a: m.IntVar(name=f'two_prim_act_in_tour_{a}', lb=0, ub=1)
                                 for a in self.act_labels_wo_home}
        prim_acts_tour_no = [a.tour_no for a in self.activities if a.is_primary]
        two_prim_act_tours = {t: 1 for t in self.tour_numbers if prim_acts_tour_no.count(t) == 2}
        for a in self.act_set.get_acts_wo_home():
            m.Add(two_prim_acts_in_tour[a.label] == m.Sum((a.is_primary * two_prim_act_tours.get(t, 0) *
                                                           w_tour[a.label, t]) for t in self.tour_numbers))

        # if in the same tour, then we need to use the same mode from and to the activities
        for a in self.act_labels_wo_dusk:
            for b in self.act_labels_wo_home:
                for mode in self.modes:
                    # mode choice is tight if one primary activity is present and loose if two primary activities take
                    # place in the tour
                    m.Add(z[a, b] <= mode_ch[a, mode] - mode_ch[b, mode] + 1 + two_prim_acts_in_tour[b])
                    m.Add(z[a, b] <= mode_ch[b, mode] - mode_ch[a, mode] + 1 + two_prim_acts_in_tour[b])

        for a in self.act_labels:
            # for prim_acts in prim_act_per_tour_dict.values():
            for p in [p.label for p in self.activities if p.is_primary]:
                for q in [q.label for q in self.activities if (q.is_primary and (p != q.label))]:
                    for mode in self.modes:
                        # these constraints make sure that the same mode is used to the first primary activity
                        # and from the second primary activity away
                        m.Add(mode_ch[a, mode] >= mode_ch[p, mode] - 1 + z[a, q])
                        m.Add(mode_ch[a, mode] <= mode_ch[q, mode] + 1 - z[a, p])

        for a in self.act_labels:
            for mode in [m for m in self.home_based_modes]:
                for p in [p.label for p in self.activities if p.is_primary]:
                    # this constraint makes sure some modes (e.g. car) are not available within the subtour if the
                    # mode is not used to get to the primary activity
                    m.Add(mode_ch[p, mode] <= mode_ch[a, mode] + 1 - z[a, p] + w_subtour[a])

    def _add_location_choice_variable(self, m):
        # location choice variable
        loc_choice = {(a.label, l.name): m.IntVar(name=f"loc_choice_{a.label}_{l.name}", lb=0, ub=1)
                      for a in self.activities for l in a.locations}

        # location groups can be used to fix locations over multiple activities
        location_groups = defaultdict(list)

        # one location per activity only
        for a in self.activities:
            m.Add(m.Sum(loc_choice[a.label, l.name] for l in a.locations) == 1)
            if a.location_group:
                location_groups[a.location_group].append(a)

        for acts in location_groups.values():
            first_act = acts[0]
            for a in acts[1:]:
                for l in first_act.locations:
                    m.Add(loc_choice[first_act.label, l.name] - loc_choice[a.label, l.name] == 0)
        return loc_choice

    def _add_time_slot_variable(self, m, x):
        # time period choice variable
        time_slot_ch = {(a, time_slot): m.IntVar(name=f'time_slot_{a}_{time_slot}', lb=0, ub=1)
                        for a in self.act_labels for time_slot in self.time_periods.keys()}
        big_m = self.config.solver_settings.big_m

        for a in self.act_labels:
            # force one of the time_slot choice vars to be 1
            m.Add(m.Sum(time_slot_ch[a, time_slot] for time_slot in self.time_periods.keys()) == 1)

            for time_slot, interval in self.time_periods.items():
                # force time_slot_ch[a, i] = 0 when a's endtime is out of its bounds
                m.Add(x[a] >= interval[0] - big_m * (1 - time_slot_ch[a, time_slot]))
                m.Add(x[a] <= interval[1] + big_m * (1 - time_slot_ch[a, time_slot]))

        return time_slot_ch

    def _add_location_mode_time_slot_product(self, m, z, mode_ch, loc_ch, time_period_ch):
        # introduce product which represents the combination of all choice dimensions
        mode_loc_time_decision_prod = {
            (a.label, b.label, o.name, d.name, mode, time_slot):
                m.IntVar(name=f'mode_ch_loc_ch_product_{a}_{b}_{o}_{d}_{mode}_{time_slot}', lb=0, ub=1)
            for a in self.activities for b in self.activities
            for o in a.locations for d in b.locations
            for mode in self.modes for time_slot in self.time_periods.keys()}

        # product is only 1 for 1 combination of mode, location and time decision
        for _a in self.activities:
            a = _a.label
            for _b in self.activities:
                b = _b.label
                for _o in _a.locations:
                    o = _o.name
                    for _d in _b.locations:
                        d = _d.name
                        for mode in self.modes:
                            for tp in self.time_periods.keys():
                                m.Add(mode_loc_time_decision_prod[a, b, o, d, mode, tp] <= z[a, b])
                                m.Add(mode_loc_time_decision_prod[a, b, o, d, mode, tp] <= mode_ch[a, mode])
                                m.Add(mode_loc_time_decision_prod[a, b, o, d, mode, tp] <= loc_ch[a, o])
                                m.Add(mode_loc_time_decision_prod[a, b, o, d, mode, tp] <= loc_ch[b, d])
                                m.Add(mode_loc_time_decision_prod[a, b, o, d, mode, tp] <= time_period_ch[a, tp])
                                m.Add(mode_loc_time_decision_prod[a, b, o, d, mode, tp] >= z[a, b] +
                                      mode_ch[a, mode] + loc_ch[a, o] + loc_ch[b, d] + time_period_ch[a, tp] - 4)

        return mode_loc_time_decision_prod

    def _add_mode_specific_travel_time_constraint(self, m, tt, mode_loc_time_decision_prod):
        # travel time calculation. not an actual decision, more a look-up from an external matrix
        for a in self.activities:
            m.Add(tt[a.label] == m.Sum(self.travel_dict.get_value(m, 'travel_times', tp, o, d) *
                                       mode_loc_time_decision_prod[a.label, b.label, o.name, d.name, m, tp]
                                       for b in self.activities for o in a.locations for d in b.locations
                                       for m in self.modes for tp in self.time_periods.keys()))

    def _add_simple_travel_time_constraint(self, m, tt, z):
        # travel time for just one global mode. a and b have one desired location only.
        for a in self.activities:
            m.Add(tt[a.label] == m.Sum(z[a.label, b.label] * self.travel_dict.get_value(m, 'travel_times', tp, o, d)
                                       for b in self.activities for o in a.locations for d in b.locations
                                       for m in self.modes for tp in self.time_periods.keys()))

    def _add_travel_cost(self, m, tt, travel_utilities):
        inf = m.infinity()

        # linear cost for traveling between two activities a and b depending on the time spent traveling.
        travel_cost = {a: m.NumVar(name=f'travel_cost_{a}', lb=-inf, ub=inf) for a in self.act_labels}
        for a in self.act_labels:
            # travel cost is just a linear function which depends on a penalty term and the travel time variable
            # todo not only consider travel times, but also other relevant service indicators
            # todo use different travel utilities for different modes
            m.Add(travel_cost[a] == travel_utilities['p_travel'] * tt[a])

        return travel_cost
