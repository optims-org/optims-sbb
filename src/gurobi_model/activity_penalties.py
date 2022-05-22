from src.config.config_container import ConfigContainer
from src.parameter.activity_param_container import ActivityParam
from src.scenario.container.activity_sets import ActivitySet
from src.utils.constants import HOME_NAME, DAWN_NAME, DUSK_NAME

from gurobipy import GRB
import gurobipy as gp


class ActivityPenalties:
    def __init__(self, config: ConfigContainer, activity_scoring: ActivityParam, activity_set: ActivitySet):
        """
            This class adds the utility penalties to the model for shifting away from the desired start time and
            desired duration for each activity.

            Parameters:
                config: ConfigContainer
                activity_scoring: ActivityParam
                activity_set: ActivitySet
        """

        self.config = config
        self.act_param = activity_scoring.param
        self.activities = activity_set.activities

    def get_penalties(self, m, x, d):
        """
            This method returns the penalties for shifting away from the desired start time and desired duration for
            each activity. If multiple desired start times or durations are given, it finds the minimal penalty
            considering all start times and durations.

            Parameters:
                m: Optimization model with basic variables and constraints.
                x: Start time decision for each activity.
                d: Duration decision for each activity.

            Returns:
                x_penalty: Penalty for not starting at the desired start time.
                d_penalty: Penalty for performing an activity either too long or too short.
        """

        # get penalty variable for being early or late
        x_penalty = self._get_start_time_penalties(m, x)
        assert x_penalty is not None, 'Start time penalty variable should always contain a value.'

        # get penalty variable for performing short or long
        d_penalty = self._get_duration_penalties(m, d)
        assert d_penalty is not None, 'Duration penalty variable should always contain a value.'

        return x_penalty, d_penalty

    def _get_start_time_penalties(self, m, x):
        inf = GRB.INFINITY
        # penalty variable, which will be minimized (and by minimizing the penalty, it maximizes utility)
        x_penalty = {a.label: m.addVar(vtype=GRB.CONTINUOUS, name=f'start_pen_min_{a}', lb=-inf, ub=inf) for a in
                     self.activities}
        # aux terms for "max" between deviation and 0 (no minus values)
        ea_max = {(a.label, i): m.addVar(vtype=GRB.CONTINUOUS, name=f'eamax_{a}_{i}', lb=-inf, ub=inf)
                  for a in self.activities for i in range(len(a.desired_timing))}
        la_max = {(a.label, i): m.addVar(vtype=GRB.CONTINUOUS, name=f'lamax_{a}_{i}', lb=-inf, ub=inf)
                  for a in self.activities for i in range(len(a.desired_timing))}
        # binary auxiliary variable to see which start time was chosen in the case multiple start times are given
        w_x = {(a.label, i): m.addVar(vtype=GRB.BINARY, name=f'start_choice_{a}_{i}')
               for a in self.activities if len(a.desired_timing) > 1 for i in range(len(a.desired_timing))}

        for act in self.activities:
            a = act.label
            des_start_times = act.desired_timing
            act_params = self.act_param[(act.act_type, act.scoring_group)]

            if len(des_start_times) > 1:
                m.addConstr(gp.quicksum(
                    w_x[a, i] for i in range(len(des_start_times))) == 1)  # only one start time per activity

            for i, des_start_time in enumerate(des_start_times):
                m.addConstr(ea_max[a, i] >= des_start_time - x[a])
                m.addConstr(ea_max[a, i] >= 0)  # avoid negative values
                m.addConstr(la_max[a, i] >= x[a] - des_start_time)
                m.addConstr(la_max[a, i] >= 0)  # avoid negative values
                # minimize the penalty for being early or late
                if len(des_start_times) > 1:
                    m.addConstr(
                        x_penalty[a] >= (act_params.pen_early * ea_max[a, i] + act_params.pen_late * la_max[a, i]))
                    m.addConstr(
                        x_penalty[a] <= (act_params.pen_early * ea_max[a, i] + act_params.pen_late * la_max[a, i]
                                         + self.config.solver_settings.big_m * (1 - w_x[a, i])))
                else:
                    m.addConstr(
                        x_penalty[a] == (act_params.pen_early * ea_max[a, i] + act_params.pen_late * la_max[a, i]))
        return x_penalty

    def _get_duration_penalties(self, m, d):
        inf = GRB.INFINITY
        home_act_labels = [a.label for a in self.activities if a.act_type in [DAWN_NAME, DUSK_NAME, HOME_NAME]]

        # we do only score the total duration of home and primary activities
        rel_acts = [a for a in self.activities if ((a.act_type not in [HOME_NAME, DUSK_NAME]) and not a.is_primary)]
        primary_act_labels = []
        for prim_type in set(a.act_type for a in self.activities if a.is_primary):
            act = next(a for a in self.activities if a.act_type == prim_type)
            rel_acts.append(act)
            primary_act_labels.append(act.label)

        # penalty variable, which will be minimized (and by minimizing the penalty, it maximizes utility)
        d_penalty = {a.label: m.addVar(vtype=GRB.CONTINUOUS, name=f'dur_pen_min_{a}', lb=-inf, ub=inf) for a in
                     rel_acts}
        # aux terms for "max" between deviation and 0 (no minus values)
        sd_max = {(a.label, i): m.addVar(vtype=GRB.CONTINUOUS, name=f'sdmax_{a}_{i}', lb=-inf, ub=inf)
                  for a in rel_acts for i in range(len(a.desired_duration))}
        ld_max = {(a.label, i): m.addVar(vtype=GRB.CONTINUOUS, name=f'ldmax_{a}_{i}', lb=-inf, ub=inf)
                  for a in rel_acts for i in range(len(a.desired_duration))}
        # binary auxiliary variable to see which duration was chosen in the case multiple durations are given
        w_d = {(a.label, i): m.addVar(vtype=GRB.BINARY, name=f"dur_choice_{a}_{i}")
               for a in rel_acts if len(a.desired_duration) > 1 for i in range(len(a.desired_duration))}

        for act in rel_acts:
            a = act.label
            des_durations = act.desired_duration
            act_params = self.act_param[(act.act_type, act.scoring_group)]

            if len(des_durations) > 1:
                m.addConstr(
                    gp.quicksum(w_d[a, i] for i in range(len(des_durations))) == 1)  # only one start time per activity

            for i, des_dur in enumerate(des_durations):
                if a in primary_act_labels:
                    act_params = self.act_param[(f'{act.act_type}_budget', 'all')]
                    des_dur_tot = sum(
                        sum(b.desired_duration) for b in self.activities if b.act_type == act.act_type)
                    m.addConstr(sd_max[a, i] >= (des_dur_tot
                                                 - gp.quicksum(
                                d[b.label] for b in self.activities if b.act_type == act.act_type)))
                    m.addConstr(ld_max[a, i] >= (
                            gp.quicksum(d[b.label] for b in self.activities if b.act_type == act.act_type)
                            - des_dur_tot))
                elif a == DAWN_NAME:
                    act_params = self.act_param[(f'{HOME_NAME}_budget', 'all')]
                    m.addConstr(sd_max[a, i] >= des_dur - gp.quicksum(d[b] for b in home_act_labels))
                    m.addConstr(ld_max[a, i] >= gp.quicksum(d[b] for b in home_act_labels) - des_dur)
                else:
                    m.addConstr(sd_max[a, i] >= des_dur - d[a])
                    m.addConstr(ld_max[a, i] >= d[a] - des_dur)
                m.addConstr(sd_max[a, i] >= 0)  # avoid negative values
                m.addConstr(ld_max[a, i] >= 0)  # avoid negative values

                # minimize the penalty for performing short or long
                if len(des_durations) > 1:
                    m.addConstr(d_penalty[a] >= (act_params.pen_short * sd_max[a, i]
                                                 + act_params.pen_long * ld_max[a, i]))
                    m.addConstr(d_penalty[a] <= (act_params.pen_short * sd_max[a, i]
                                                 + act_params.pen_long * ld_max[a, i]
                                                 + self.config.solver_settings.big_m * (1 - w_d[a, i])))
                    
                else:
                    m.addConstr(d_penalty[a] == (act_params.pen_short * sd_max[a, i] + act_params.pen_long * ld_max[a, i]))

        return d_penalty
