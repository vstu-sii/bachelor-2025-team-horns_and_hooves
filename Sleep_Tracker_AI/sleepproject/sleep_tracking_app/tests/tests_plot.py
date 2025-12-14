import unittest
from datetime import datetime

from sleep_tracking_app.sleep_statistic import (
    get_sleep_phases_pie_data,
    get_heart_rate_bell_curve_data,
    get_sleep_duration_trend,
    get_sleep_efficiency_trend,
)


class DummyStat:
    def __init__(self, sleep_phases=None):
        self.sleep_phases = sleep_phases or {}


class DummyHR:
    def __init__(self, time, bpm):
        self.time = time
        self.bpm = bpm


class DummyRecord:
    def __init__(self, hr_entries):
        self._hr = hr_entries

    @property
    def night_hr_entries(self):
        class Q:
            def __init__(self, arr):
                self._arr = arr

            def all(self):
                return self._arr

        return Q(self._hr)


class PlotDiagramTests(unittest.TestCase):
    def test_get_sleep_phases_pie_data_with_rem(self):
        stat = DummyStat({'deep': 30, 'light': 50, 'rem': 15, 'awake': 5})
        res = get_sleep_phases_pie_data(stat)
        # expect four slices
        self.assertEqual(len(res), 4)
        names = [p['name'] for p in res]
        self.assertIn('REM', names)

    def test_get_sleep_phases_pie_data_without_rem(self):
        stat = DummyStat({'deep': 40, 'light': 60, 'rem': 0, 'awake': 0})
        res = get_sleep_phases_pie_data(stat)
        self.assertEqual(len(res), 3)
        names = [p['name'] for p in res]
        self.assertNotIn('REM', names)

    def test_get_heart_rate_bell_curve_data_empty(self):
        self.assertEqual(get_heart_rate_bell_curve_data(None), {'date': [], 'bpm': []})

    def test_get_heart_rate_bell_curve_data_with_entries(self):
        entries = [DummyHR(datetime(2025, 11, 22, 23, 0), 60), DummyHR(datetime(2025, 11, 23, 0, 0), 62)]
        rec = DummyRecord(entries)
        res = get_heart_rate_bell_curve_data(rec)
        self.assertEqual(res['bpm'], [60, 62])
        self.assertEqual(res['date'][0], '23:00')

    def test_get_sleep_duration_trend_empty(self):
        self.assertEqual(get_sleep_duration_trend([]), {"dates": [], "sleep_duration": []})

    def test_get_sleep_duration_trend(self):
        class S:
            def __init__(self, dt, duration):
                self.sleep_date_time = dt
                self.duration = duration

        items = [S(datetime(2025, 11, 20), 420), S(datetime(2025, 11, 21), 480)]
        res = get_sleep_duration_trend(items)
        self.assertEqual(res['dates'], ['2025-11-20', '2025-11-21'])
        self.assertEqual(res['sleep_duration'], [420, 480])

    def test_get_sleep_efficiency_trend(self):
        class SS:
            def __init__(self, date, latency, eff, frag, cal):
                self.date = date
                self.latency_minutes = latency
                self.sleep_efficiency = eff
                self.sleep_fragmentation_index = frag
                self.sleep_calories_burned = cal

        from datetime import date
        items = [SS(date(2025, 11, 20), 10.1234, 95.5678, 0.5, 200.1234)]
        res = get_sleep_efficiency_trend(items)
        self.assertIn('dates', res)
        self.assertEqual(len(res['dates']), 1)
        self.assertAlmostEqual(res['latency_minutes'][0], round(10.1234, 2))


if __name__ == '__main__':
    unittest.main()
