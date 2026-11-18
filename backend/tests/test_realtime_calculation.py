"""On-demand geometry and future predictions preserve the original sampling semantics."""
import unittest
from datetime import timedelta
from unittest.mock import patch

import numpy as np
from skyfield.api import load

from simulator.config import EPHEMERIS
from simulator.core.initialisation import build_static_objects, load_input_metadata, normalize_time
from simulator.defaults import default_project
from simulator.models.realtime_ephemeris import SatelliteSamples
from simulator.models.sampled_data import SampleSeries
from simulator.services.project_service import detect_update


class RealtimeCalculationTests(unittest.TestCase):
    def project(self):
        project = default_project()
        project.constellation.number_of_planes = 1
        project.constellation.number_of_sat_per_planes = 1
        project.experiment.end_time = (normalize_time(project.experiment.start_time) + timedelta(days=365)).isoformat()
        return detect_update(project)

    def objects(self):
        project = self.project()
        metadata = load_input_metadata(project, 7200)
        return build_static_objects(project, metadata["period"], metadata["max_period_numbers"], metadata["datetime_list"])

    def test_construction_does_not_calculate_future_trajectories(self):
        with patch.object(SatelliteSamples, "_calculate", side_effect=AssertionError("eager trajectory")):
            objects = self.objects()
        self.assertIsInstance(objects["sat_datas"][0]["space_xyz"], SampleSeries)
        self.assertGreater(len(objects["sat_datas"][0]["time"]), 500_000)

    def test_future_sunlight_only_computes_requested_window(self):
        objects = self.objects()
        satellite = objects["sat"][0]
        samples = satellite.time_series["is_sunlit"].sample.__self__
        start, delta, step = 100, 40, 3
        timeline = samples.timeline
        times = load.timescale().utc([timeline[index] for index in range(start, start + delta, step)])
        expected = samples.satellite.motion.at(times).is_sunlit(EPHEMERIS).mean()
        with patch.object(SatelliteSamples, "_calculate", side_effect=AssertionError("unneeded future geometry")):
            self.assertEqual(float(expected), satellite.sunlit_ratio(start, delta, step))
        self.assertEqual(14, len(samples.sunlight.samples))
        self.assertEqual(0, len(samples.states.samples))

    def test_cached_states_remain_bounded_and_match_direct_orbit(self):
        objects = self.objects()
        data = objects["sat_datas"][0]
        samples = data["is_sunlit"].sample.__self__
        for index in range(10):
            actual = data["space_xyz"][index]
            expected = samples.satellite.motion.at(samples.ephemeris.time_at(index)).position.m
            np.testing.assert_allclose(actual, expected, atol=1e-6)
        self.assertLessEqual(len(samples.states.samples), 2)
        self.assertLessEqual(len(samples.positions.samples), 4)

    def test_sunlight_request_larger_than_cache_preserves_all_values(self):
        objects = self.objects()
        series = objects["sat_datas"][0]["is_sunlit"]
        samples = series.sample.__self__
        series[2000:2050]
        result = series[:2100]
        self.assertEqual(2100, len(result))
        self.assertLessEqual(len(samples.sunlight.samples), 2048)
        self.assertEqual(result[2010], series[2010])
