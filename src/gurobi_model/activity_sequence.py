import gurobipy as gp
from gurobipy import GRB

from src.scenario.container.activity_sets import ActivitySet
from src.utils.constants import HOME_NAME, DAWN_NAME, DUSK_NAME


class ActivitySequence:
    def __init__(self, activity_set: ActivitySet):
        """
            This class manages activity sequence restrictions in the optimization model.

            Parameters:
                activity_set: ActivitySet
        """

        self.activities = activity_set.activities
        self.tour_numbers = activity_set.get_tour_numbers()

    def add_restrictions(self, m, w, z):
        """
            This method adds activity sequence restrictions and the tour and subtour indicator variables
            to the optimization model.

            Parameters:
                m: Optimization model with basic variables and constraints.
                w: Decision whether activity should take place.
                z: Decision about activity sequence.

            Returns:
                w_tour: Variable which indicates the tour number in which the activity takes place.
                w_subtour: Variable which indicates whether the activity takes place in a sub-tour.
        """

        self._fix_activity_participation(m, w)
        self._restrict_sequence_of_home_and_primary_activities(m, z)

        w_tour = self._add_tour_indicator_variable(m, w, z)
        self._fix_number_of_primary_activities_per_tour(m, w_tour)
        self._fix_tour_types(m, w, w_tour)

        w_subtour = self._add_subtour_indicator(m, z)
        self._fix_subtour_activities(m, w_subtour)

        return w_tour, w_subtour

    def _fix_activity_participation(self, m, w):
        """
            This method gives the option to fix activity participation. If participation should be a free decision
            variable, please define participation=-1 in the activity set.
        """

        for a in self.activities:
            # if not specified in the activity set, participation is fixed to be 1 in this model
            m.addConstr(w[a.label] >= a.participation)  # enforce activities to take place if participation is fixed

    def _restrict_sequence_of_home_and_primary_activities(self, m, z):
        """
            Does not allow two home or primary activities after each other.
        """

        # we do not allow for multiple home activities to take place after each other.
        home_activity_labels = [a.label for a in self.activities if a.act_type in [HOME_NAME, DAWN_NAME, DUSK_NAME]]
        for a in home_activity_labels:
            for b in home_activity_labels:
                m.addConstr(z[a, b] <= 0)

        # we restrict the sequence of primary activities such that they can not take place after each other
        primary_activity_labels = [a.label for a in self.activities if a.is_primary]
        for a in primary_activity_labels:
            for b in primary_activity_labels:
                m.addConstr(z[a, b] <= 0)

    def _add_tour_indicator_variable(self, m, w, z):
        """
            This method introduces a variable containing an indicator of the tour number of each activity. Each
            activity must take place in exactly one tour, meaning between two home activities. The number of tours
            is defined by the number of home activities in the activity set.
        """

        act_labels_wo_dusk = [a.label for a in self.activities if a.act_type != DUSK_NAME]

        # w_tour is an indicator in which tour number the activity takes part
        w_tour = {(a, i): m.addVar(vtype=GRB.BINARY, name=f'w_tour_{a}_{i}')
                  for a in act_labels_wo_dusk for i in self.tour_numbers}

        for a in act_labels_wo_dusk:
            # one tour number per activity
            m.addConstr(gp.quicksum(w_tour[a, i] for i in self.tour_numbers) >= w[a])
            for b in [b.label for b in self.activities if b.act_type not in [HOME_NAME, DAWN_NAME, DUSK_NAME]]:
                for tour_no in self.tour_numbers:
                    # w_tour must be same for two activities a and b, if b is performed right after a
                    # since we exclude home activities from b, w_tour can change at each home activities
                    m.addConstr(z[a, b] <= w_tour[a, tour_no] - w_tour[b, tour_no] + 1)
                    m.addConstr(z[a, b] <= w_tour[b, tour_no] - w_tour[a, tour_no] + 1)

        return w_tour

    def _fix_number_of_primary_activities_per_tour(self, m, w_tour):
        """
            This method fixes the amount of primary activities per tour.
        """

        prim_acts_tour_no = [a.tour_no for a in self.activities if a.is_primary]
        for t in self.tour_numbers:
            # this constraint fixes the amount of primary activities for each tour as defined in the activity set
            m.addConstr(gp.quicksum(w_tour[a.label, t]
                                    for a in self.activities if a.is_primary) == prim_acts_tour_no.count(t))

    def _fix_tour_types(self, m, w, w_tour):
        """
            This method fixes the tour type as given in the activity set. Mainly, we differ between the tour types
            primary (includes min. one primary activity) and secondary (no primary activity present).
        """

        # primary activities must have a tour number which is defined in the activity set
        tour_dict = {act.tour_no: act.tour_type for act in [a for a in self.activities if a.is_primary]}
        # if the tour contains no primary activity, we define it to be a secondary tour
        for t in [t for t in self.tour_numbers if t not in tour_dict]:
            tour_dict[t] = 'secondary'

        for a in [a for a in self.activities if a.act_type not in [HOME_NAME, DAWN_NAME, DUSK_NAME]]:
            m.addConstr(gp.quicksum(w_tour[a.label, t]
                                    for t, t_type in tour_dict.items() if t_type == a.tour_type) >= w[a.label])

    def _add_subtour_indicator(self, m, z):
        """
            This method introduces an identifier for sub-tours. If more than one primary activity is performed within
            one tour, a sub-tour is present by definition. The first primary activity is always part of the sub-tour.
        """

        w_subtour = {a.label: m.addVar(vtype=GRB.BINARY, name=f'w_subtour_{a}') for a in self.activities}

        prim_acts_tour_no = [a.tour_no for a in self.activities if a.is_primary]
        two_prim_act_tours = [t for t in self.tour_numbers if prim_acts_tour_no.count(t) == 2]
        # the number of primary sub-tour activities must be exactly equal to the number of tours with two primary
        # activities.
        m.addConstr(len(two_prim_act_tours) == gp.quicksum(w_subtour[a.label] for a in self.activities if a.is_primary))

        for a in [a.label for a in self.activities]:
            for b in [b.label for b in self.activities if not b.is_primary]:
                # make sure that all the activities between two primary activities are part of the sub-tour as well.
                m.addConstr(z[a, b] <= w_subtour[a] - w_subtour[b] + 1)
                m.addConstr(z[a, b] <= w_subtour[b] - w_subtour[a] + 1)

        return w_subtour

    def _fix_subtour_activities(self, m, w_subtour):
        """
            This method fixes the sub-tour activities as specified in the activity set
        """

        for a in self.activities:
            if a.act_type in [HOME_NAME, DAWN_NAME, DUSK_NAME]:
                # home activities are per defintion not part of a subtour
                m.addConstr(w_subtour[a.label] == 0)
            elif a.is_subtour and not a.is_primary:
                m.addConstr(w_subtour[a.label] == 1)
            elif not a.is_subtour and not a.is_primary:
                m.addConstr(w_subtour[a.label] == 0)
