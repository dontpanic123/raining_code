"""Select one locally prepared discovery per Berlin calendar day, without network calls."""
import datetime as dt
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

KNOWLEDGE_LIBRARY = Path(__file__).resolve().parent / 'data/daily_knowledge_100.json'


def load_library(path=None):
    library = json.loads(Path(path or KNOWLEDGE_LIBRARY).read_text(encoding='utf-8'))
    if library['schema_version'] != 1:
        raise ValueError('Unsupported knowledge schema')
    dt.date.fromisoformat(library['start_date'])
    ZoneInfo(library['timezone'])
    entries = library['entries']
    if not isinstance(entries, list) or not entries:
        raise ValueError('Empty knowledge library')
    ids, titles = set(), set()
    for item in entries:
        for field in ('id', 'category', 'title', 'what', 'why', 'when', 'url', 'access'):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError('Invalid knowledge text')
        highlights = item['highlights']
        if (not isinstance(highlights, list) or not 1 <= len(highlights) <= 2
                or any(not isinstance(x, str) or not x.strip() for x in highlights)):
            raise ValueError('Invalid highlights')
        url = urlsplit(item['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Invalid source URL')
        if item['id'] in ids or item['title'] in titles:
            raise ValueError('Duplicate knowledge entry')
        ids.add(item['id'])
        titles.add(item['title'])
    return library


def get_daily_knowledge(day=None, now=None):
    """Stable date selection; never repeat at exhaustion or block weather mail on bad data."""
    try:
        library = load_library()
        zone = ZoneInfo(os.getenv('KNOWLEDGE_TIMEZONE') or library['timezone'])
        if day is None:
            instant = now if now is not None else dt.datetime.now(dt.timezone.utc)
            if instant.tzinfo is None:
                raise ValueError('now must be timezone aware')
            day = instant.astimezone(zone).date()
        if isinstance(day, str):
            day = dt.date.fromisoformat(day)
        start = dt.date.fromisoformat(os.getenv('KNOWLEDGE_START_DATE') or library['start_date'])
        index = (day - start).days
        total = len(library['entries'])
        result = dict(date=day.isoformat(), total=total, timezone=str(zone), item=None,
                      column_title=library.get('column_title', '每日化学小知识'))
        if index < 0:
            return dict(result, status='pending', message=f'内容将从 {start.isoformat()} 开始，每天介绍一条中高级化学知识。')
        if index >= total:
            logging.warning('每日化学小知识内容库已用完，请补充新内容。')
            return dict(result, status='exhausted', message=f'{total} 天内容已用完，等待补充新主题；不重复旧推荐。')
        item = library['entries'][index]
        logging.info('每日化学小知识：%s，第 %d/%d 条，%s。', day, index + 1, total, item['title'])
        return dict(result, status='ready', index=index + 1, item=item,
                    prepared_on=library['prepared_on'])
    except (OSError, ValueError, KeyError, TypeError):
        logging.warning('每日化学小知识暂不可用，请检查本地内容库和日期配置。')
        return dict(status='unavailable', item=None, column_title='每日化学小知识', message='今日知识内容暂不可用，天气与寄语照常提供。')
