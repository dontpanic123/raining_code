import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from daily_knowledge import get_daily_knowledge, load_library
from daily_fortune import fallback_fortune
from email_template import render_email


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        self.start = dt.date(2026, 11, 13)

    def test_100_days_are_complete_unique_and_stable(self):
        library = load_library()
        self.assertEqual(len(library['entries']), 100)
        ids = set()
        for i in range(100):
            day = self.start + dt.timedelta(days=i)
            item = get_daily_knowledge(day)
            self.assertEqual(item['status'], 'ready')
            self.assertEqual(item['index'], i + 1)
            self.assertEqual(item, get_daily_knowledge(day))
            self.assertEqual(item['item'], library['entries'][i])
            ids.add(item['item']['id'])
        self.assertEqual(len(ids), 100)

    def test_no_wrap_before_start_or_after_exhaustion(self):
        self.assertEqual(get_daily_knowledge(self.start - dt.timedelta(days=1))['status'], 'pending')
        self.assertEqual(get_daily_knowledge(self.start + dt.timedelta(days=100))['status'], 'exhausted')
        self.assertIsNone(get_daily_knowledge('2027-02-21')['item'])

    def test_berlin_midnight_and_dst_ignore_forecast_city(self):
        # In winter Berlin midnight is 23:00 UTC on the previous calendar day.
        before = dt.datetime(2026, 11, 13, 22, 59, tzinfo=dt.timezone.utc)
        after = before + dt.timedelta(minutes=1)
        self.assertEqual(get_daily_knowledge(now=before)['index'], 1)
        self.assertEqual(get_daily_knowledge(now=after)['index'], 2)
        os.environ['KNOWLEDGE_START_DATE'] = '2027-03-27'
        before = dt.datetime(2027, 3, 28, 21, 59, tzinfo=dt.timezone.utc)
        after = before + dt.timedelta(minutes=1)
        self.assertEqual(get_daily_knowledge(now=before)['index'], 2)
        self.assertEqual(get_daily_knowledge(now=after)['index'], 3)

    def test_start_date_and_timezone_overrides(self):
        os.environ.update(KNOWLEDGE_START_DATE='2026-12-01', KNOWLEDGE_TIMEZONE='Asia/Shanghai')
        now = dt.datetime(2026, 11, 30, 16, tzinfo=dt.timezone.utc)
        self.assertEqual(get_daily_knowledge(now=now)['index'], 1)
        self.assertEqual(get_daily_knowledge(now=now)['timezone'], 'Asia/Shanghai')
        os.environ['KNOWLEDGE_START_DATE'] = 'invalid'
        self.assertEqual(get_daily_knowledge(now=now)['status'], 'unavailable')
        os.environ.update(KNOWLEDGE_START_DATE='2026-12-01', KNOWLEDGE_TIMEZONE='Invalid/Zone')
        self.assertEqual(get_daily_knowledge(now=now)['status'], 'unavailable')

    def test_bad_library_falls_back_and_rejects_unsafe_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'knowledge.json'
            with patch('daily_knowledge.KNOWLEDGE_LIBRARY', path):
                self.assertEqual(get_daily_knowledge(self.start)['status'], 'unavailable')
                path.write_text('broken', encoding='utf-8')
                self.assertEqual(get_daily_knowledge(self.start)['status'], 'unavailable')
            library = load_library()
            library['entries'][0]['url'] = 'javascript:alert(1)'
            path.write_text(json.dumps(library), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_library(path)
            library = load_library()
            library['entries'][1] = library['entries'][0]
            path.write_text(json.dumps(library), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_library(path)

    def test_distinct_topics_can_share_a_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'knowledge.json'
            library = load_library()
            library['entries'][1]['url'] = library['entries'][0]['url']
            path.write_text(json.dumps(library), encoding='utf-8')
            self.assertEqual(len(load_library(path)['entries']), 100)

    def test_chemistry_library_coverage_and_distinct_concepts(self):
        entries = load_library()['entries']
        expected = {'多孔碳': 20, '吸附原理': 15, '铯与碱金属': 10,
                    '固碳与CO₂化学': 15, '催化原理': 15, '有机反应机制': 10,
                    '周期表与无机化学': 10, '表征与机制证据': 5}
        from collections import Counter
        self.assertEqual(dict(Counter(x['category'] for x in entries)), expected)
        self.assertEqual(len({x['title'] for x in entries}), 100)
        self.assertEqual(len({x['what'] for x in entries}), 100)
        for entry in entries:
            self.assertTrue(entry['id'].startswith('chemistry-'))
            self.assertEqual(len(entry['highlights']), 2)
            self.assertTrue(entry['source_title'])
            self.assertTrue(entry['source_scope'])

    def test_html_plain_match_escape_and_separate_weather_date(self):
        knowledge = get_daily_knowledge(self.start)
        knowledge['item']['title'] = '<script>test</script>'
        html, plain = render_email(self.start + dt.timedelta(days=1), 'Berlin', {}, False, [],
                                   fallback_fortune(), False, [], knowledge=knowledge)
        self.assertIn('&lt;script&gt;test&lt;/script&gt;', html)
        self.assertNotIn('<script>', html)
        for field in ('what', 'why', 'when', 'access', 'url'):
            self.assertIn(knowledge['item'][field], plain)
        for point in knowledge['item']['highlights']:
            self.assertIn(point, plain)
        self.assertIn('2026-11-13', html)
        self.assertIn('2026年11月14日', html)
        self.assertEqual(html.count('每日化学小知识'), 1)
        self.assertLess(html.index('核心概念'), html.index('<h1'))
        self.assertTrue(plain.startswith('每日化学小知识'))
        self.assertLess(plain.index('核心概念'), plain.index('明日寄语'))
        self.assertNotIn('本地预编于', html)
        self.assertNotIn('本地预编于', plain)
        exhausted = get_daily_knowledge('2027-02-21')
        html, plain = render_email(self.start, 'Berlin', {}, False, [], fallback_fortune(), False,
                                   [], knowledge=exhausted)
        self.assertIn('等待补充', html)
        self.assertIn('等待补充', plain)

    @patch('main.fetch_weather', return_value={})
    @patch('main.prepare_weather', return_value=(dt.date(2026, 11, 14), {}, False, []))
    @patch('main.get_daily_fortune', return_value=(fallback_fortune(), False))
    @patch('main.send_email')
    def test_main_includes_one_discovery_for_all_cities_without_network_generation(self, send, fortune, weather, fetch):
        os.environ.update(CITY='Cambridge,Berlin', SENDER_EMAIL='sender@example.com',
                          SENDER_PASSWORD='test', RECIPIENT_EMAIL='receiver@example.com')
        with patch('sys.argv', ['main.py', '--knowledge-date', '2026-11-14']):
            main.main()
        send.assert_called_once()
        html, plain = send.call_args.args[1:3]
        self.assertEqual(html.count('每日化学小知识'), 1)
        self.assertEqual(plain.count('每日化学小知识'), 1)
        self.assertIn('Langmuir方程', html)
        self.assertIn('第 2/100 天', plain)

    def test_preview_offline_contains_selected_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'preview.html'
            with patch('sys.argv', ['main.py', '--preview', str(path), '--knowledge-date', '2027-02-20']), \
                    patch('main.fetch_weather') as fetch, patch('main.send_email') as send:
                main.main()
            self.assertIn('碳骨架并不在所有电位与气氛下稳定', path.read_text())
            fetch.assert_not_called()
            send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
