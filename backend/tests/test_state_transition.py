"""Joint-slot invariants across policies, runtime models and session commit."""
import importlib.util
import unittest
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import numpy as np
from pydantic import ValidationError

from simulator.config import (BATTERY_MAX, COMPUTE_ENERGY_COST, LAYER_OUTPUT_DATA_SIZE,
                               LAYER_PROCESS_SECOND_COST_GPU, STATIC_ENERGY_COST, TRANSMIT_ISL_ENERGY_COST)
from simulator.core.actions import ComputeAction, SchedulingActions, TaskAction, TransferAction
from simulator.core.world_transition import execute_actions
from simulator.core.model import SimulationModel, StepContext
from simulator.core.session import SimulationSession
from simulator.core.staging import fork_environment
from simulator.core.time_step import step_context
from simulator.defaults import default_project
from simulator.entities.link_entity import LinkAction, LinkEntity
from simulator.entities.satellite_entity import SatelliteEntity
from simulator.schemas.base import XYZ
from simulator.schemas.task import Task
from simulator.services.network_service import LinkSnapshot
from simulator.services.project_service import detect_update


def project(duration_s=65, period_s=30):
    value = default_project()
    value.project_id = "transition_test"
    value.seed = 31
    value.constellation.number_of_planes = 2
    value.constellation.number_of_sat_per_planes = 3
    value.experiment.time_slot = period_s
    value.experiment.end_time = "2025-12-01T00:00:00+00:00"
    from simulator.core.initialisation import normalize_time
    value.experiment.end_time = (normalize_time(value.experiment.start_time) + timedelta(seconds=duration_s)).isoformat()
    return detect_update(value)


class IdlePolicy:
    def decide(self, state, context):
        return SchedulingActions()


class StateTransitionTests(unittest.TestCase):
    def session(self, algorithm="phoenix", **kwargs):
        session = SimulationSession(project(**kwargs), algorithm)
        self.addCleanup(session.close)
        return session

    def test_models_have_a_shared_transition_contract_and_detached_task_snapshot(self):
        session = self.session()
        environment = session.environment
        entities = [*environment.sat, *environment.gs, *environment.roi,
                    environment.eth, environment.sun, environment.net, *environment.task_manager.tasks]
        self.assertTrue(all(isinstance(entity, SimulationModel) for entity in entities))
        task = environment.task_manager.tasks[0]
        state = task.snapshot()
        task.transition(TaskAction("age", elapsed_slots=1), step_context(environment))
        self.assertEqual(state.t_end + 1, task.t_end)
        with self.assertRaises(ValidationError):
            state.t_end = 10

    def test_failure_after_physics_keeps_old_world_clock_rng_and_policy_state(self):
        session = self.session("mhspo")
        original = session.environment
        state = session.snapshot().serialize()
        rng_state = deepcopy(original.task_manager.rng.bit_generator.state)
        queues = deepcopy(session.policy.QF)
        transition = SatelliteEntity.transition
        calls = []

        def fail_during_transition(entity, action, context):
            result = transition(entity, action, context)
            calls.append(entity.id)
            if len(calls) == 2:
                raise RuntimeError("injected execution failure")
            return result

        with patch.object(SatelliteEntity, "transition", fail_during_transition):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                session.step()
        self.assertIs(original, session.environment)
        self.assertEqual(state, session.snapshot().serialize())
        self.assertEqual(rng_state, original.task_manager.rng.bit_generator.state)
        self.assertEqual(queues, session.policy.QF)
        fresh = self.session("mhspo")
        self.assertEqual(fresh.step().serialize(), session.step().serialize())

    def test_snapshot_validation_failure_does_not_commit(self):
        session = self.session()
        original = session.environment
        with patch.object(session, "collect_snapshot", side_effect=ValueError("invalid state")):
            with self.assertRaisesRegex(ValueError, "invalid state"):
                session.step()
        self.assertIs(original, session.environment)
        self.assertEqual(0, session.snapshot().frame_counter)

    def test_task_age_advances_once_even_when_policy_visits_tasks_twice(self):
        session = self.session("mhspo")
        for task in session.environment.task_manager.tasks:
            task.t_start = task.t_end = 0
        session.step()
        self.assertTrue(all(task.t_end == 1 for task in session.environment.task_manager.tasks))

    def test_custom_policy_only_reads_old_state_and_commit_advances_exactly_once(self):
        session = SimulationSession(project(), "phoenix", policy=IdlePolicy())
        self.addCleanup(session.close)
        original = session.environment
        prior = session.snapshot()
        result = session.step()
        self.assertEqual(0, original.frame_counter)
        self.assertEqual(1, result.frame_counter)
        self.assertEqual(prior.time, original.time_recorder.isoformat())
        self.assertNotEqual(prior.time, result.time)
        self.assertEqual(0, original.sat[0].cost_percent)
        for before, after in zip(prior.tasks, result.tasks):
            self.assertEqual(before.t_end + int(before.t_start == 0), after.t_end)

    def test_fork_shares_geometry_inputs_but_isolates_runtime_and_randomness(self):
        original = self.session().environment
        candidate = fork_environment(original)
        self.assertIs(original.sat[0].time_series, candidate.sat[0].time_series)
        candidate.task_manager.tasks[0].t_end += 10
        candidate.sat[0].battery = 0
        rng_state = deepcopy(original.task_manager.rng.bit_generator.state)
        candidate.task_manager.rng.random()
        self.assertNotEqual(original.task_manager.tasks[0].t_end, candidate.task_manager.tasks[0].t_end)
        self.assertGreater(original.sat[0].battery, 0)
        self.assertEqual(rng_state, original.task_manager.rng.bit_generator.state)

    def test_link_budget_is_frozen_and_weighted(self):
        state = LinkSnapshot(type="ISL", src="a", dst="b", distance=1,
                             link_pos=[XYZ(x=0, y=0, z=0)], snr=1, rate=100)
        model = LinkEntity(state)
        context = StepContext(self.session().environment.t_start, 0.5, 0)
        model.transition(LinkAction(((1, 1), (2, 3))), context)
        self.assertEqual({1: 12.5, 2: 37.5}, model.allocated_bits)
        with self.assertRaises(ValueError):
            model.transition(LinkAction(((1, 1), (1, 1))), context)

    def transfer_environment(self):
        environment = self.session(period_s=0.5).environment
        src, dst = environment.sat[:2]
        environment.task_manager.tasks = [Task(id=i, plane_at=src.plane, order_at=src.order,
                                                t_start=0, t_end=0) for i in (1, 2)]
        environment.net._all_links = [LinkSnapshot(type="ISL", src=src.id, dst=dst.id,
            distance=1, link_pos=[src.pos, dst.pos], snr=1, rate=100)]
        return environment, src, dst

    def test_completing_one_transfer_cannot_expand_another_share_or_depend_on_iteration_order(self):
        environment, src, dst = self.transfer_environment()
        environment.task_manager.tasks[0].data_sent = LAYER_OUTPUT_DATA_SIZE[0] - 1
        reverse = fork_environment(environment)
        actions = tuple(TransferAction(i, src.id, dst.id, "isl") for i in (1, 2))
        execute_actions(environment, SchedulingActions(transfer=actions), step_context(environment))
        execute_actions(reverse, SchedulingActions(transfer=actions[::-1]), step_context(reverse))
        self.assertEqual(25, environment.task_manager.tasks[1].data_sent)
        self.assertEqual([t.snapshot() for t in environment.task_manager.tasks],
                         [t.snapshot() for t in reverse.task_manager.tasks])
        self.assertEqual(1, len(environment.trans_reqs))

    def test_opposite_directions_share_the_same_physical_budget(self):
        environment, src, dst = self.transfer_environment()
        task = environment.task_manager.tasks[1]
        task.plane_at, task.order_at = dst.plane, dst.order
        actions = SchedulingActions(transfer=(TransferAction(1, src.id, dst.id, "isl"),
                                               TransferAction(2, dst.id, src.id, "isl")))
        execute_actions(environment, actions, step_context(environment))
        self.assertEqual(50, sum(t.data_sent for t in environment.task_manager.tasks))

    def test_compute_and_transmit_charge_static_and_dynamic_energy_once(self):
        environment, src, dst = self.transfer_environment()
        actions = SchedulingActions(compute=(ComputeAction(1, src.id),),
            transfer=(TransferAction(2, src.id, dst.id, "isl"),))
        context = step_context(environment)
        execute_actions(environment, actions, context)
        expected = (STATIC_ENERGY_COST + COMPUTE_ENERGY_COST + TRANSMIT_ISL_ENERGY_COST) * context.dt_s
        self.assertAlmostEqual(expected / BATTERY_MAX * 100, environment.sat[0].cost_percent)
        self.assertTrue(environment.sat[0].is_processing)
        self.assertTrue(environment.sat[0].is_communicating_isl)

    def test_each_algorithm_clips_final_slot_and_uses_actual_timestamp_geometry(self):
        for algorithm in ("geometry", "l2d2", "phoenix", "mhspo", "ophanim"):
            with self.subTest(algorithm=algorithm):
                session = self.session(algorithm, duration_s=1.3, period_s=1)
                last_time = session.environment.time_recorder
                while not session.is_completed:
                    session.step()
                    self.assertGreater(session.environment.time_recorder, last_time)
                    last_time = session.environment.time_recorder
                self.assertEqual(session.environment.t_end, last_time)
                self.assertEqual(session.snapshot(), session.step())
        session = self.session()
        old_position = session.snapshot().satellites[0].pos
        new_position = session.step().satellites[0].pos
        self.assertNotEqual(old_position, new_position)
        from simulator.models.satellite_model import SatelliteModel
        config = session.environment.input.satellites[0]
        model = SatelliteModel(tle1text=config.tle1, tle2text=config.tle2)
        from simulator.models.realtime_ephemeris import TS
        expected = model.motion.at(TS.utc(session.environment.time_recorder)).position.m
        np.testing.assert_allclose(expected, [new_position.x, new_position.y, new_position.z], atol=1e-5)

    def test_partial_slot_computation_uses_elapsed_seconds(self):
        environment = self.session().environment
        task = Task(id=1, plane_at=0, order_at=0, t_start=0, t_end=0)
        task.transition(TaskAction("compute", nominal_slot_s=0.5), StepContext(environment.t_start, 0.2, 0))
        self.assertAlmostEqual(0.2 / LAYER_PROCESS_SECOND_COST_GPU[0], task.workload_percent)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "optional ML dependencies unavailable")
    def test_ppo_collects_all_actions_before_any_physical_state_changes(self):
        from simulator.core.simulation import Simulation
        from simulator.policies.discrete_scheduler import DiscreteScheduler
        from simulator.policies.view import PlanningView
        from simulator.env.core.observation import observation_shapes, validate_observation
        simulator = Simulation(project(period_s=0.5))
        self.addCleanup(simulator.close)
        simulator.reset(seed=31)
        src, other = simulator.sat[:2]
        simulator.task_manager.tasks = [Task(id=i, plane_at=node.plane, order_at=node.order,
                                                t_start=0, t_end=0) for i, node in enumerate((src, other))]
        scheduler = DiscreteScheduler()
        scheduler.begin(PlanningView.from_simulator(simulator))
        initial_tasks = [task.snapshot() for task in simulator.task_manager.tasks]
        initial_energy = [node.battery for node in simulator.sat]
        scheduler.submit(5)
        self.assertEqual(0, simulator.frame_counter)
        self.assertEqual(initial_tasks, [t.snapshot() for t in simulator.task_manager.tasks])
        self.assertEqual(initial_energy, [node.battery for node in simulator.sat])
        scheduler.submit(5)
        self.assertEqual(0, simulator.frame_counter)
        simulator.step(scheduler.actions())
        self.assertEqual(1, simulator.frame_counter)
        self.assertTrue(all(t.workload_done > 0 for t in simulator.task_manager.tasks))
        validate_observation(scheduler.observation(), observation_shapes(o=3, p=2))


if __name__ == "__main__":
    unittest.main()
