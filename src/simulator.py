import importlib
import logging
import time

import ray

from .config.config_container import ConfigContainer
from .output.output_container import OutputContainer
from .problem import OptimizationProblem
from .scenario.container.scenario import ScenarioContainer
from .solution import Solution

optimization_models = {'scip': 'src.ortools_model.optimization_core',
                       'gurobi': 'src.gurobi_model.optimization_core'}


class Simulator:
    def __init__(self, config: ConfigContainer, scenario: ScenarioContainer):
        """
            This class is responsible for running the optimization model based on a model configuration and a scenario.
            A parallel computing solution is provided to use multiple cores.

            Parameters:
                config: ConfigContainer
                scenario: ScenarioContainer

            Returns:
                solution: Solution
        """

        self.config = config
        self.scenario = scenario
        solver_name = config.solver_settings.solver_name
        try:
            self.opt_module = importlib.import_module(optimization_models[solver_name])
        except:
            raise ModuleNotFoundError(f'{solver_name} is not supported')

    def run(self) -> Solution:
        if self.config.cores > 1:
            return self._run_parallel()
        else:
            return self._run_sequential()

    def _run_sequential(self) -> Solution:
        solution = Solution()
        logging.info(f'simulating {len(self.scenario.get_persons())} schedules sequentially.')

        for i, person in enumerate(self.scenario.get_persons()):
            activity_set = self.scenario.get_activity_set_for_person(person)
            logging.info(f'solving problem for person {person.name} ({i + 1} of {len(self.scenario.get_persons())}) '
                         f'with {activity_set.get_size()} activities.')
            start_time = time.time()
            output = self._solve_problem(self.opt_module, self.config, person,
                                         self.scenario.get_act_param_for_person_group(person.activity_scoring_group),
                                         self.scenario.get_activity_set_for_person(person),
                                         self.scenario.get_travel_dict_for_person(person))
            solution.add_person(person, output)
            logging.info(f'solved problem in {round(time.time() - start_time, 3)} seconds.')
        return solution

    def _run_parallel(self) -> Solution:
        ray.shutdown()
        ray.init(num_cpus=self.config.cores, logging_level=logging.NOTSET)

        @ray.remote
        class ScheduleCounterActor(object):
            def __init__(self):
                self.counter = 0

            def inc(self):
                self.counter = self.counter + 1

            def get_counter(self):
                return self.counter

        @ray.remote
        def f(schedule_counter, pers, opt_module, conf, act_set, act_scoring, travel_dict) -> OutputContainer:
            schedule_counter.inc.remote()
            return self._solve_problem(opt_module, conf, pers, act_scoring, act_set, travel_dict)

        counter_actor = ScheduleCounterActor.remote()

        output_list = [f.remote(counter_actor, person, self.opt_module, self.config,
                                self.scenario.get_activity_set_for_person(person),
                                self.scenario.get_act_param_for_person_group(person.activity_scoring_group),
                                self.scenario.get_travel_dict_for_person(person))
                       for person in self.scenario.get_persons()]

        while ray.get(counter_actor.get_counter.remote()) < len(self.scenario.get_persons()):
            counter = ray.get(counter_actor.get_counter.remote())
            logging.info(f"solved {counter} of {len(self.scenario.get_persons())} schedules.")
            time.sleep(2 * 60)

        solution = Solution()
        output_list = ray.get(output_list)
        solution.output_container = {o.person: o for o in output_list}
        return solution

    @staticmethod
    def _solve_problem(opt_module, conf, pers, act_scoring, act_set, travel_dict) -> OutputContainer:
        start_time = time.time()
        model: OptimizationProblem = opt_module.OptimizationCore(config=conf, person=pers, activity_scoring=act_scoring,
                                                                 activity_set=act_set, travel_dict=travel_dict)
        problem = model.formulate_problem()
        solved_problem = model.solve_problem(problem)
        output = model.update_activity_set(solved_problem)
        output.solver_time = time.time() - start_time
        return output
