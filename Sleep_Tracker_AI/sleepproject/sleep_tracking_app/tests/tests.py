from datetime import datetime, timedelta
import importlib
import unittest
from datetime import date

import numpy as np

from sleep_tracking_app.sleep_statistic import (
    calculate_calories_burned,
    evaluate_bedtime,
    evaluate_wake_time,
    chronotype_assessment,
    calculate_cycle_count,
    time_to_minutes,
    sleep_regularity,
    calculate_sleep_statistics_metrics,
    avg_sleep_duration,
)


from django.test import RequestFactory, TestCase as DjangoTestCase
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from sleep_tracking_app.views import home, register, custom_logout, profile, sleep_chronotype, sleep_fragmentation
from sleep_tracking_app.models import UserData


class DummySegments:
    def __init__(self, segs):
        # segs: list of dicts with keys 'start_time','end_time','state'
        self._segs = segs

    def order_by(self, *args, **kwargs):
        return self

    def values_list(self, *args, **kwargs):
        class VList:
            def __init__(self, vals):
                self._vals = vals

            def first(self):
                return self._vals[0] if self._vals else None

        vals = [s['start_time'] for s in self._segs]
        return VList(vals)

    def __iter__(self):
        return iter(self._segs)

    def __len__(self):
        return len(self._segs)

    def __getitem__(self, idx):
        return self._segs[idx]


class DummyRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CalculateSleepStatisticTests(unittest.TestCase):
    def test_calculate_calories_burned(self):
        # age in months (30 years = 360 months)
        res = calculate_calories_burned(gender=1, weight=70.0, height=175, age=np.float64(360), sleep_duration=480)
        # compute expected manually: BMR = 10*70 + 6.25*175 - 5*(360/12) + 5 = 1648.75
        # calories = (bmr * (480/60))/24 = bmr*(8/24) = bmr/3 = 549.583...
        self.assertAlmostEqual(res, round(1648.75 / 3, 1))

    def test_evaluate_bedtime_and_wake_time(self):
        dt1 = datetime(2025, 11, 22, 22, 0)
        dt2 = datetime(2025, 11, 22, 22, 30)
        r = DummyRecord(device_bedtime=dt1, bedtime=dt2, device_wake_up_time=datetime(2025, 11, 23, 6, 0), wake_up_time=datetime(2025, 11, 23, 5, 50))
        self.assertEqual(evaluate_bedtime(r), dt1)
        self.assertEqual(evaluate_wake_time(r), datetime(2025, 11, 23, 6, 0))

    def test_time_to_minutes(self):
        t = datetime(2025, 11, 22, 23, 30)
        # default ref_hour=20 -> ref_minutes=1200; total_minutes=1410; normalized=210
        self.assertEqual(time_to_minutes(t), 210)

    def test_sleep_regularity(self):
        r1 = DummyRecord(bedtime=datetime(2025, 11, 21, 22, 0), wake_up_time=datetime(2025, 11, 22, 6, 0))
        r2 = DummyRecord(bedtime=datetime(2025, 11, 22, 23, 0), wake_up_time=datetime(2025, 11, 23, 7, 0))
        res = sleep_regularity([r1, r2])
        # bedtimes normalized -> [120, 180] -> std = 30.0
        self.assertAlmostEqual(res['bedtime_std'], 30.0)
        self.assertAlmostEqual(res['wake_time_std'], 30.0)

    def test_avg_sleep_duration(self):
        class Item:
            def __init__(self, duration):
                self.duration = duration

        items = [Item(480), Item(420)]
        self.assertEqual(avg_sleep_duration(items), round(np.mean([480, 420]) / 60, 2))

    def test_calculate_cycle_count(self):
        # Build segments that form one complete cycle: Light+Deep+REM total >=90 then Awake
        now = datetime(2025, 11, 22, 22, 0)
        segs = [
            {'start_time': now, 'end_time': now + timedelta(minutes=30), 'state': 2},
            {'start_time': now + timedelta(minutes=30), 'end_time': now + timedelta(minutes=90), 'state': 3},
            {'start_time': now + timedelta(minutes=90), 'end_time': now + timedelta(minutes=110), 'state': 4},
            {'start_time': now + timedelta(minutes=110), 'end_time': now + timedelta(minutes=115), 'state': 5},
        ]
        record = DummyRecord(segments=DummySegments(segs))
        self.assertEqual(calculate_cycle_count(record), 1)

    def test_calculate_sleep_statistics_metrics(self):
        # Create a fake sleep_data with required attributes
        device_bedtime = datetime(2025, 11, 22, 22, 0)
        bedtime = datetime(2025, 11, 22, 22, 30)
        device_wake = datetime(2025, 11, 23, 6, 0)
        wake_time = datetime(2025, 11, 23, 5, 50)

        # segment start_time a bit after device_bedtime
        segs = [{'start_time': device_bedtime + timedelta(minutes=10), 'end_time': device_bedtime + timedelta(minutes=490), 'state': 2}]

        sleep_data = DummyRecord(
            device_bedtime=device_bedtime,
            bedtime=bedtime,
            device_wake_up_time=device_wake,
            wake_up_time=wake_time,
            segments=DummySegments(segs),
            sleep_deep_duration=180,
            sleep_light_duration=270,
            sleep_rem_duration=30,
            sleep_awake_duration=0,
            duration=480,
            awake_count=1,
        )

        metrics = calculate_sleep_statistics_metrics(sleep_data=sleep_data, age=np.float64(360), gender=1, weight=70.0, height=175)

        # latency should be 10 minutes
        self.assertAlmostEqual(metrics['latency_minutes'], 10)
        # efficiency = duration / time_in_bed *100 => 480/480*100 = 100
        self.assertAlmostEqual(metrics['sleep_efficiency'], 100)
        # phases percentages
        self.assertAlmostEqual(metrics['sleep_phases']['deep'], 180 / 480 * 100)
        self.assertAlmostEqual(metrics['sleep_phases']['light'], 270 / 480 * 100)
        self.assertAlmostEqual(metrics['sleep_phases']['rem'], 30 / 480 * 100)
        # fragmentation index
        self.assertAlmostEqual(metrics['sleep_fragmentation_index'], 1 / (480 / 60))
        # calories burned should be calculated consistently
        expected_cal = calculate_calories_burned(gender=1, weight=70.0, height=175, age=np.float64(360), sleep_duration=480)
        self.assertAlmostEqual(metrics['sleep_calories_burned'], expected_cal)

    def test_chronotype_assessment_with_mocked_interpret(self):
        # Monkeypatch interpret_chronotype inside module to return a dict with known key
        mod = importlib.import_module('sleep_tracking_app.sleep_statistic.calculate_sleep_statistic')

        def fake_interpret(msf_time, name, language):
            return {'skylark': 'early'}

        mod.interpret_chronotype = fake_interpret

        # Create one free-day record (weekend)
        free_bedtime = datetime(2025, 11, 22, 23, 0)  # 22 Nov 2025 is Saturday
        rec = DummyRecord(device_bedtime=free_bedtime, bedtime=free_bedtime, duration=480, wake_up_time=free_bedtime + timedelta(minutes=480))
        res = chronotype_assessment([rec])
        # Should have added 'img' -> 'skylark.png'
        self.assertEqual(res.get('img'), 'skylark.png')


if __name__ == '__main__':
    unittest.main()


class ViewsTests(DjangoTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # create a user and related UserData
        self.user = User.objects.create_user(username='viewuser', password='viewpass123', email='a@b.com', first_name='A', last_name='B')
        UserData.objects.create(user=self.user, date_of_birth=date.today() - timedelta(days=365 * 30), weight=70, gender=1, height=175, active=False)

    def _add_session(self, request):
        # SessionMiddleware requires a get_response callable in newer Django versions
        middleware = SessionMiddleware(get_response=lambda req: None)
        middleware.process_request(request)
        request.session.save()

    def test_home_redirects_when_anonymous(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        response = home(request)
        self.assertEqual(response.status_code, 302)

    def test_home_authenticated(self):
        request = self.factory.get('/')
        self._add_session(request)
        request.user = self.user
        response = home(request)
        self.assertEqual(response.status_code, 200)

    def test_profile_renders(self):
        request = self.factory.get('/profile')
        self._add_session(request)
        request.user = self.user
        response = profile(request)
        self.assertEqual(response.status_code, 200)

    def test_register_post_creates_user_and_userdata(self):
        # prepare valid registration + userdata form data
        dob = (date.today() - timedelta(days=6*365)).isoformat()
        data = {
            'username': 'newuser',
            'first_name': 'First',
            'last_name': 'Last',
            'email': 'new@user.test',
            'password1': 'strong-password-1',
            'password2': 'strong-password-1',
            'date_of_birth': dob,
            'weight': '68',
            'gender': '1',
            'height': '175',
            'active': ''
        }
        request = self.factory.post('/register', data)
        self._add_session(request)
        response = register(request)
        # successful registration should redirect
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(UserData.objects.filter(user__username='newuser').exists())

    def test_logout_redirects(self):
        request = self.factory.get('/logout')
        self._add_session(request)
        request.user = self.user
        response = custom_logout(request)
        self.assertEqual(response.status_code, 302)

    def test_simple_statics_render(self):
        # chronotype and fragmentation views are simple renders
        req1 = self.factory.get('/chronotype')
        self._add_session(req1)
        req1.user = self.user
        resp1 = sleep_chronotype(req1)
        self.assertEqual(resp1.status_code, 200)

        req2 = self.factory.get('/fragment')
        self._add_session(req2)
        req2.user = self.user
        resp2 = sleep_fragmentation(req2)
        self.assertEqual(resp2.status_code, 200)





