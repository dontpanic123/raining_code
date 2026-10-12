import datetime as dt
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
import main
from daily_fortune import FORTUNE_LIBRARY, PROMPT, fallback_fortune, get_daily_fortune, validate_fortune
from email_template import render_email, travel_advice


class DailyMailTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"FORTUNE_CACHE_DIR": self.tmp.name,
                                      "FORTUNE_SOURCE": "ai"}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.date = dt.date(2026, 10, 3)

    @patch('daily_fortune.requests.post')
    def test_missing_key_never_calls_api(self, post):
        self.assertFalse(get_daily_fortune(self.date, 'Sydney', [])[1])
        post.assert_not_called()

    @patch('daily_fortune.requests.post')
    def test_default_uses_prepared_content_even_with_api_key_and_cache(self, post):
        os.environ.pop('FORTUNE_SOURCE')
        os.environ['OPENAI_API_KEY'] = 'test-key'
        date = dt.date(2026, 10, 8)
        cache_key = hashlib.sha256(f'{date}|Sydney|gpt-4o-mini|{PROMPT}'.encode()).hexdigest()
        (Path(self.tmp.name) / f'{cache_key}.json').write_text(
            json.dumps(fallback_fortune()), encoding='utf-8')
        for offset in range(3):
            day = date + dt.timedelta(days=offset)
            self.assertEqual(get_daily_fortune(day, 'Sydney', []), (fallback_fortune(day), False))
        post.assert_not_called()

    def test_prepared_year_is_complete_and_distinct(self):
        entries = json.loads(FORTUNE_LIBRARY.read_text(encoding='utf-8'))
        start = dt.date(2026, 10, 8)
        expected = {(start + dt.timedelta(days=i)).isoformat() for i in range(365)}
        self.assertEqual(set(entries), expected)
        self.assertEqual(len({item['verse'] for item in entries.values()}), 365)
        for date, content in entries.items():
            self.assertEqual(validate_fortune(content), content)
            self.assertEqual(fallback_fortune(dt.date.fromisoformat(date)), content)

    @patch('daily_fortune.requests.post')
    def test_prepared_content_used_without_key_and_on_http_failure(self, post):
        date = dt.date(2026, 10, 8)
        expected = (fallback_fortune(date), False)
        self.assertEqual(get_daily_fortune(date, 'Sydney', []), expected)
        self.assertNotEqual(expected[0], fallback_fortune(date + dt.timedelta(days=1)))
        post.assert_not_called()
        os.environ['OPENAI_API_KEY'] = 'test-key'
        response = requests.Response()
        response.status_code = 429
        post.return_value.raise_for_status.side_effect = requests.HTTPError(response=response)
        self.assertEqual(get_daily_fortune(date, 'Berlin', []), expected)

    def test_library_rotates_outside_range_and_survives_missing_file(self):
        start = dt.date(2026, 10, 8)
        self.assertEqual(fallback_fortune(start + dt.timedelta(days=365)), fallback_fortune(start))
        validate_fortune(fallback_fortune(start - dt.timedelta(days=1)))
        with patch('daily_fortune.FORTUNE_LIBRARY', new=Path(self.tmp.name) / 'missing.json'):
            self.assertEqual(fallback_fortune(start), fallback_fortune())

    @patch('daily_fortune.requests.post')
    def test_success_cached_across_calls(self, post):
        os.environ['OPENAI_API_KEY'] = 'test-key'
        post.return_value.json.return_value = {'choices': [{'finish_reason': 'stop',
            'message': {'content': json.dumps(fallback_fortune())}}]}
        first = get_daily_fortune(self.date, 'Sydney', [])
        self.assertTrue(first[1])
        self.assertEqual(first, get_daily_fortune(self.date, 'Sydney', [{'changed': True}]))
        self.assertEqual(post.call_count, 1)
        get_daily_fortune(self.date + dt.timedelta(days=1), 'Sydney', [])
        self.assertEqual(post.call_count, 2)

    @patch('daily_fortune.requests.post')
    def test_api_failures_fall_back(self, post):
        os.environ['OPENAI_API_KEY'] = 'test-key'
        post.side_effect = requests.Timeout()
        self.assertFalse(get_daily_fortune(self.date, 'Sydney', [])[1])
        post.side_effect = None
        for choice in [
            {'finish_reason': 'stop', 'message': {'content': '{}'}},
            {'finish_reason': 'length', 'message': {'content': '{}'}},
            {'finish_reason': 'stop', 'message': {'refusal': 'no'}},
            {'finish_reason': 'stop', 'message': {'content': 'not json'}},
            {'finish_reason': 'stop', 'message': {'content': json.dumps({**fallback_fortune(), 'title': 'a' * 100})}},
        ]:
            post.return_value.json.return_value = {'choices': [choice]}
            self.assertFalse(get_daily_fortune(self.date, 'Sydney', [])[1])

    def test_html_escapes_ai_and_city(self):
        fortune = {**fallback_fortune(), 'verse': '<script>alert(1)</script>'}
        html, plain = render_email(self.date, '<Berlin>', {}, False, [], fortune, False, [])
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&lt;Berlin&gt;', html)
        self.assertIn('预备文案', html)
        self.assertIn('明日寄语', plain)

    def test_travel_advice_uses_rain_times_and_temperature(self):
        def period(desc, low, high, pop, kind='Clouds'):
            return dict(main_desc=desc, min_temp=low, max_temp=high,
                        avg_feels_like=low, max_pop=pop, main_weather=kind)
        periods = {'早上 (07:00-10:00)': period('多云', 12, 14, .1),
                   '中午 (10:00-15:00)': period('小雨', 21, 23, .8, 'Rain')}
        advice = travel_advice(periods, True, [])
        self.assertIn('温差较大', advice)
        self.assertIn('中午可能有雨', advice)
        self.assertNotIn('早上可能有雨', advice)
        snow = travel_advice({'晚上': period('大雪', -3, 0, .9, 'Snow')}, False,
                             [{'time': '18:00', 'desc': '大雪', 'type': '极端天气'}])
        self.assertIn('保暖', snow)
        self.assertIn('特殊天气', snow)
        self.assertNotIn('带伞', snow)
        self.assertIn('数据不足', travel_advice({}, False, []))
        self.assertIn('雷雨', travel_advice({'中午': period('雷雨', 20, 24, .9)}, True, []))

    def test_city_date_and_dst(self):
        os.environ['CITY_TIMEZONE'] = 'Australia/Sydney'
        # UTC Oct 2 afternoon is already Oct 3 in Sydney. Tomorrow is Oct 4,
        # when DST begins; 20:00 UTC Oct 3 is 07:00 local Oct 4.
        item = {'dt': int(dt.datetime(2026, 10, 3, 20, tzinfo=dt.timezone.utc).timestamp()),
                'weather': [{'description': '小雨', 'main': 'Rain'}],
                'main': {'temp': 15, 'feels_like': 14, 'humidity': 80},
                'wind': {'speed': 3}, 'pop': .8, 'rain': {'3h': 1}}
        date, periods, rain, _ = main.prepare_weather({'list': [item]},
            dt.datetime(2026, 10, 2, 15, tzinfo=dt.timezone.utc))
        self.assertEqual(date, dt.date(2026, 10, 4))
        self.assertIn('早上 (07:00-10:00)', periods)
        self.assertTrue(rain)

    def test_evening_forecast_targets_tomorrow_and_marks_abnormal_weather(self):
        now = dt.datetime(2026, 10, 12, 17, tzinfo=dt.timezone.utc)
        def sample(day, hour, kind, desc, temp=15, wind=3, rain=0):
            return dict(dt=int(dt.datetime(2026, 10, day, hour, tzinfo=dt.timezone.utc).timestamp()),
                        weather=[dict(main=kind, description=desc)],
                        main=dict(temp=temp, feels_like=temp, humidity=80),
                        wind=dict(speed=wind), pop=.8, rain={'3h': rain})
        samples = [sample(12, 18, 'Thunderstorm', '今天雷雨'),
                   sample(13, 6, 'Rain', '小雨'),
                   sample(13, 9, 'Thunderstorm', '雷雨'),
                   sample(13, 12, 'Clouds', '多云', wind=12),
                   sample(13, 15, 'Rain', '大雨', rain=12),
                   sample(13, 18, 'Snow', '雪', temp=-1),
                   sample(14, 6, 'Thunderstorm', '后天雷雨')]
        for zone in ('Europe/London', 'Europe/Berlin'):
            date, periods, rain, events = main.prepare_weather({'list': samples}, now, zone)
            self.assertEqual(date, dt.date(2026, 10, 13))
            self.assertTrue(rain)
            alerts = [event for event in events if 'type' in event]
            self.assertEqual(len(alerts), 4)
            self.assertFalse(any('小雨' in event['desc'] for event in alerts))
            self.assertFalse(any('今天' in event['desc'] or '后天' in event['desc'] for event in events))
            html, plain = render_email(date, 'Cambridge', periods, rain, events,
                                       fallback_fortune(), False, [])
            self.assertLess(html.index('明日异常天气'), html.index('<h1'))
            self.assertLess(plain.index('明日异常天气'), plain.index('明日寄语'))
            self.assertIn('风力较强', html)
            self.assertIn('降雨量较大', html)
            self.assertEqual(html.count('明日异常天气'), 1)
        html, plain = render_email(self.date, 'Berlin', {}, False, [], fallback_fortune(), False, [])
        self.assertNotIn('明日异常天气', html)
        self.assertNotIn('明日异常天气', plain)

    def test_empty_forecast_is_failure(self):
        with self.assertRaises(ValueError):
            main.prepare_weather({'city': {'timezone': 0}, 'list': []})

    @patch('main.smtplib.SMTP')
    def test_multipart_and_recipient_isolation(self, smtp):
        os.environ.update(SENDER_EMAIL='sender@example.com', SENDER_PASSWORD='test')
        main.send_email('主题', '<html>签语</html>', '签语', ['a@example.com', 'b@example.com'])
        calls = smtp.return_value.__enter__.return_value.send_message.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].args[0]['To'], 'a@example.com')
        self.assertEqual(calls[1].args[0]['To'], 'b@example.com')
        self.assertEqual(calls[0].args[0].get_content_type(), 'multipart/alternative')

    @patch('main.smtplib.SMTP')
    def test_send_failure_reported_and_other_recipient_attempted(self, smtp):
        os.environ.update(SENDER_EMAIL='sender@example.com', SENDER_PASSWORD='test')
        send = smtp.return_value.__enter__.return_value.send_message
        send.side_effect = [main.smtplib.SMTPException(), None]
        with self.assertRaises(RuntimeError):
            main.send_email('主题', '<html></html>', '签语', ['a@example.com', 'b@example.com'])
        self.assertEqual(send.call_count, 2)

    @patch('main.send_email')
    @patch('main.get_daily_fortune', return_value=(fallback_fortune(), True))
    @patch('main.prepare_weather')
    @patch('main.fetch_weather')
    def test_multiple_cities_share_one_email(self, fetch, prepare, fortune, send):
        os.environ.update(CITY='Sydney,Berlin', CITY_TIMEZONE='Australia/Sydney,Europe/Berlin',
                          SENDER_EMAIL='sender@example.com', SENDER_PASSWORD='test',
                          RECIPIENT_EMAIL='a@example.com')
        prepare.return_value = (self.date, {}, False, [])
        with patch('sys.argv', ['main.py']):
            main.main()
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(prepare.call_args_list[1].kwargs['timezone_name'], 'Europe/Berlin')
        self.assertEqual(fortune.call_count, 1)
        send.assert_called_once()
        html = send.call_args.args[1]
        self.assertEqual(html.count('<html'), 1)
        self.assertEqual(html.count('<body'), 1)
        self.assertIn('Sydney', html)
        self.assertIn('Berlin', html)
        self.assertEqual(html.count(fallback_fortune()['verse']), 1)
        self.assertEqual(send.call_args.args[2].count(fallback_fortune()['verse']), 1)

    def test_shared_layout_preserves_dates_missing_periods_and_alerts(self):
        period = {"main_desc": "小雨", "min_temp": 12, "max_temp": 15,
                  "avg_feels_like": 11, "max_pop": .8}
        forecasts = [dict(date=self.date, city='<Sydney>',
                          periods={'早上 (07:00-10:00)': period}, rain=True,
                          extreme=[], festivals=['节日 - 介绍']),
                     dict(date=self.date + dt.timedelta(days=1), city='Berlin',
                          periods={}, rain=False,
                          extreme=[{'time': '18:00', 'desc': '大雪', 'type': '极端天气'}],
                          festivals=['节日 - 介绍'])]
        html, plain = render_email(**forecasts[0], fortune=fallback_fortune(),
                                   generated=False, forecasts=forecasts, failed=1)
        self.assertIn('&lt;Sydney&gt;', html)
        self.assertNotIn('<Sydney>', html)
        self.assertIn('10月03日', html)
        self.assertIn('10月04日', html)
        self.assertIn('暂无数据', html)
        self.assertIn('Berlin 18:00 大雪', html)
        self.assertIn('部分城市天气暂不可用', plain)
        self.assertEqual(html.count('记得带伞'), 1)
        self.assertEqual(plain.count('记得带伞'), 1)
        self.assertEqual(html.count(fallback_fortune()['verse']), 1)
        self.assertIn('出行准备', html)
        self.assertIn('出行准备', plain)
        self.assertIn('早上可能有雨', plain)
        self.assertIn('scope="col"', html)
        self.assertIn('时间按各城市当地时间', html)

    @patch('main.send_email')
    @patch('main.get_daily_fortune', return_value=(fallback_fortune(), False))
    @patch('main.prepare_weather')
    @patch('main.fetch_weather', side_effect=[ValueError(), {}])
    def test_one_city_failure_still_sends_other_city(self, fetch, prepare, fortune, send):
        os.environ.update(CITY='Sydney,Berlin', SENDER_EMAIL='sender@example.com',
                          SENDER_PASSWORD='test', RECIPIENT_EMAIL='a@example.com')
        prepare.return_value = (self.date, {}, False, [])
        with patch('sys.argv', ['main.py']), self.assertRaises(RuntimeError):
            main.main()
        send.assert_called_once()
        self.assertIn('部分城市天气暂不可用', send.call_args.args[1])
        self.assertIn('Berlin', send.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
