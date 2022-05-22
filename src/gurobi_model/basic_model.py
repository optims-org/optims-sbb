from src.config.config_container import ConfigContainer
from src.parameter.activity_param_container import ActivityParam
from src.scenario.container.activity_sets import ActivitySet
from src.utils.constants import DAWN_NAME, DUSK_NAME

from gurobipy import GRB
import gurobipy as gp


class BasicModel:
    def __init__(self, config: ConfigContainer, activity_scoring: ActivityParam, activity_set: ActivitySet):
        """
            This class is responsible to formulate the basic structure of the model including the core decision
            variables and constraints. It is a copy of the model introduced by Pougala et al. (2021)

            Parameters:
                config: ConfigContainer
                activity_scoring: ActivityParam
                activity_set: ActivitySet
        """

        self.config = config
        self.activity_scoring = activity_scoring
        self.act_set = activity_set
        self.act_labels = activity_set.get_labels()

    def add_decision_variables(self, m):
        # decision variables with travel time not being modelled as actual decision
        w, z, x, d, tt = self._add_decision_variables(m)

        # basic constraints according to mathematical formulation
        self._add_basic_constraints(m, w, z, x, d, tt)

        return w, z, x, d, tt

    def _add_decision_variables(self, m):
        """
            Adds all basic decision variables to the model.

            Parameters:
                m: Empty optimization model.

            Returns:
                w: Decision whether activity should take place.
                z: Decision about activity sequence.
                x: Start time decision for each activity.
                d: Duration decision for each activity.
                tt: Travel time decision between two activities.
        """

        inf = GRB.INFINITY
        # w -> indicator of activity choice
        w = {a: m.addVar(vtype=GRB.BINARY, name=f'w_{a}') for a in self.act_labels}
        # z -> activity sequence
        z = {(a, b): m.addVar(vtype=GRB.BINARY, name=f'z_{a}_{b}') for a in self.act_labels for b in self.act_labels}
        # x -> activity start times
        x = {a: m.addVar(lb=-inf, ub=inf, vtype=GRB.CONTINUOUS, name=f'x_{a}') for a in self.act_labels}
        # d -> activity durations
        d = {a: m.addVar(vtype=GRB.CONTINUOUS, name=f'd_{a}', lb=-inf, ub=inf) for a in self.act_labels}
        # tt -> travel times between activities
        tt = {a: m.addVar(vtype=GRB.CONTINUOUS, name=f'tt_{a}', lb=-inf, ub=inf) for a in self.act_labels}

        return w, z, x, d, tt

    def _add_basic_constraints(self, m, w, z, x, d, tt):
        """
            Adds all basic constraints to the model to make schedules fully consistent in time and space.

            Parameters:
                m: Model containing the decision variables.
                w: Decision whether activity should take place.
                z: Decision about activity sequence.
                x: Start time decision for each activity.
                d: Duration decision for each activity.
                tt: Travel time decision between two activities.

            Returns:
                Model updated with basic constraints.
        """

        max_time = max([tp.period[1] for tp in self.config.time_periods])
        # sum of durations all durations and travel times must equal day time budget
        m.addConstr(gp.quicksum(d[a] + tt[a] for a in self.act_labels) == max_time)

        for act in self.act_set.activities:
            a = act.label
            m.addConstr(z[a, DAWN_NAME] == 0)  # no activity takes place before dawn
            m.addConstr(z[DUSK_NAME, a] == 0)  # no activity takes place after dusk
            m.addConstr(z[a, a] == 0)  # same activity
            # sequence constraints, either a is before b or b is before a
            for b in [b for b in self.act_labels if b != a]:
                m.addConstr(z[a, b] + z[b, a] <= 1)

            m.addConstr(w[a] * self.config.model_settings.min_act_duration <= d[a])  # minimal duration constraint
            params_for_activity = self.activity_scoring.param[(act.act_type, act.scoring_group)]
            m.addConstr(x[a] >= params_for_activity.feasible_start)  # start times within feasible window constraint
            m.addConstr(x[a] + d[a] <= params_for_activity.feasible_end)  # end times within feasible window constraint

            for b in self.act_labels:
                m.addConstr(x[a] + d[a] + tt[a] - x[b] >= (z[a, b] - 1) * max_time)  # inferior times constraint
                m.addConstr(x[a] + d[a] + tt[a] - x[b] <= (1 - z[a, b]) * max_time)  # superior times constraint

            if a == DAWN_NAME:
                m.addConstr(x[a] == 0)  # start time of dawn is always midnight
            else:
                # predecessor constraints, only one activity towards a
                m.addConstr(gp.quicksum(z[b, a] for b in self.act_labels if b != a) == w[a])

            if a == DUSK_NAME:
                m.addConstr(x[a] + d[a] == max_time)  # end time of dusk is always midnight (or some hours past)
            else:
                # successor constraints, only one activity from a away
                m.addConstr(gp.quicksum(z[a, b] for b in self.act_labels if b != a) == w[a])
