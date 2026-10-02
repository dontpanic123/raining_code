import datetime as dt
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
import main
from daily_fortune import fallback_fortune, get_daily_fortune
from email_template import render_email


class DailyMailTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {"FORTUNE_CACHE_DIR": self.tmp.name}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.date = dt.date(2026, 10, 3)

    @patch('daily_fortune.requests.post')
    def test_missing_key_never_calls_api(self, post):
        self.assertFalse(get_daily_fortune(self.date, 'Sydney', [])[1])
        post.assert_not_called()

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
        self.assertIn('非 AI 生成', html)
        self.assertIn('明日寄语', plain)

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
        self.assertEqual(fortune.call_count, 2)
        send.assert_called_once()
        html = send.call_args.args[1]
        self.assertEqual(html.count('<html'), 1)
        self.assertEqual(html.count('<body'), 1)
        self.assertIn('Sydney', html)
        self.assertIn('Berlin', html)

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
