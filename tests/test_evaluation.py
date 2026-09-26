import unittest
from unittest.mock import patch
from evaluation.latency import measure_latency


class LatencyTests(unittest.TestCase):
    def test_timings_are_measured(self):
        with patch("evaluation.latency.time.perf_counter", side_effect=[1., 1.2, 2., 2.4]):
            report = measure_latency(lambda: None, runs=2, audio_seconds=2)
        self.assertAlmostEqual(report["mean_seconds"], .3)
        self.assertAlmostEqual(report["mean_real_time_factor"], .15)
        self.assertNotIn("accuracy", report)
        self.assertNotIn("f1", report)

    def test_failures_not_counted_as_success(self):
        def fail():
            raise RuntimeError("private text")
        report = measure_latency(fail, runs=2)
        self.assertEqual(report["successful_runs"], 0)
        self.assertEqual(len(report["failures"]), 2)
        self.assertNotIn("mean_seconds", report)
        self.assertNotIn("private text", str(report))

    def test_bad_run_count(self):
        with self.assertRaises(ValueError):
            measure_latency(lambda: None, runs=0)
