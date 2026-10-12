"""Email-safe table layout and matching plain text, with escaped dynamic content."""
from html import escape


def travel_advice(periods, rain, extreme):
    """Summarize forecast signals; thresholds are simple clothing heuristics."""
    parts = []
    if periods:
        low = min(p["min_temp"] for p in periods.values())
        high = max(p["max_temp"] for p in periods.values())
        feels = min(p["avg_feels_like"] for p in periods.values())
        if high - low >= 8:
            parts.append("预报时段温差较大，建议分层穿衣")
        elif feels <= 10:
            parts.append("体感偏冷，出门注意保暖")
        elif feels <= 16:
            parts.append("部分时段偏凉，可带一件薄外套")
        elif high >= 30:
            parts.append("部分时段较热，户外注意遮阳、补水")
    rainy_periods = []
    for name, p in periods.items():
        desc = p["main_desc"]
        snowy = p.get("main_weather") == "Snow" or "雪" in desc
        if "雨" in desc or p.get("main_weather") in {"Rain", "Drizzle", "Thunderstorm"}:
            rainy_periods.append(name.split("(")[0].strip())
        elif p["max_pop"] >= .6 and not snowy:
            rainy_periods.append(name.split("(")[0].strip())
    if rainy_periods:
        parts.append("、".join(rainy_periods) + "可能有雨，记得带伞")
    elif rain:
        parts.append("明天有雨，记得带伞")
    thunder = any("雷" in p["main_desc"] or p.get("main_weather") == "Thunderstorm"
                  for p in periods.values()) or any("雷" in w["desc"] for w in extreme)
    if thunder:
        parts.append("可能有雷雨，出行前留意预报")
    elif any("type" in w for w in extreme):
        parts.append("有特殊天气，提前安排出行")
    if not parts:
        parts.append("出门前查看最新预报" if periods else "分时数据不足，出门前查看最新预报")
    return "；".join(parts) + "。"


def render_email(date, city, periods, rain, extreme, fortune, generated, festivals, preview=False, forecasts=None, failed=0):
    e = lambda value: escape(str(value), quote=True)
    label = "明日签" if generated else "明日寄语"
    note = ("示例文案 · 仅供预览" if preview else
            "AI 创作 · 宜忌仅作生活灵感" if generated else "预备文案 · 宜忌仅作生活灵感")
    forecasts = forecasts or [dict(date=date, city=city, periods=periods,
                                   rain=rain, extreme=extreme, festivals=festivals)]
    city = " · ".join(item["city"] for item in forecasts)
    multiple_dates = len({item["date"] for item in forecasts}) > 1
    rows, lines = [], []
    headers = '<th scope="col" style="padding:12px 4px;text-align:left;font-size:12px;color:#858078;">当地时段</th>'
    for item in forecasts:
        heading = item["city"]
        if multiple_dates:
            heading += f' · {item["date"]:%m月%d日}'
        headers += f'<th scope="col" style="padding:12px 4px;text-align:left;font-size:13px;">{e(heading)}</th>'
    rows.append(f'<tr>{headers}</tr>')
    names = dict.fromkeys(name for item in forecasts for name in item["periods"])
    for name in names:
        title = name.split("(")[0].strip()
        hours = name.split("(", 1)[1].rstrip(")") if "(" in name else ""
        cells = [f'<th scope="row" style="padding:13px 4px;border-bottom:1px solid #eeeae3;text-align:left;font-size:13px;font-weight:normal;">{e(title)}<br><span style="font-size:10px;color:#858078;">{e(hours)}</span></th>']
        entries = []
        for item in forecasts:
            p = item["periods"].get(name)
            if p is None:
                content = '暂无数据'
                entries.append(f'{item["city"]}：暂无数据')
            else:
                temperature = f'{p["min_temp"]:.0f}–{p["max_temp"]:.0f}°'
                detail = f'体感 {p["avg_feels_like"]:.0f}° · 降水 {p["max_pop"]:.0%}'
                content = f'{e(p["main_desc"])}<br><span style="font-size:18px;line-height:1.8;">{e(temperature)}</span><br><span style="font-size:11px;color:#858078;">{e(detail)}</span>'
                entries.append(f'{item["city"]}：{p["main_desc"]}，{temperature}，{detail}')
            cells.append(f'<td style="padding:13px 4px;border-bottom:1px solid #eeeae3;vertical-align:top;font-size:13px;">{content}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
        lines.append(name + "\n" + "\n".join(entries))
    advice = [(item["city"], travel_advice(item["periods"], item["rain"], item["extreme"]))
              for item in forecasts]
    advice_html = ''.join(
        f'<p style="margin:10px 0;font-size:13px;line-height:1.8;color:#5e7253;"><strong>{e(name)}</strong> · {e(text)}</p>'
        for name, text in advice)
    advice_plain = "\n".join(f"{name}：{text}" for name, text in advice)
    warnings = "；".join(f"{item['city']} {w['time']} {w['desc']}"
                         for item in forecasts for w in item["extreme"] if "type" in w)
    alert_html = (f'<tr><td style="padding:0 26px 22px;">'
                  f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#fff0e7;border:1px solid #df9b76;border-radius:8px;">'
                  f'<tr><td style="padding:16px;color:#963f24;">'
                  f'<p style="margin:0 0 8px;font-size:16px;font-weight:bold;">明日异常天气 · 请留意</p>'
                  f'<p style="margin:0;font-size:13px;line-height:1.8;">{e(warnings)}</p>'
                  f'<p style="margin:8px 0 0;font-size:11px;">时间为各城市当地时间；基于预报的生活提醒，出行前请查看最新预报。</p>'
                  f'</td></tr></table></td></tr>' if warnings else '')
    alert_plain = f"明日异常天气 · 请留意\n{warnings}\n时间为各城市当地时间；出行前请查看最新预报。\n\n" if warnings else ""
    festival_groups = {}
    for item in forecasts:
        for festival in item["festivals"]:
            key = (item["date"], festival.split(" - ")[0])
            festival_groups.setdefault(key, []).append(item["city"])
    festival_text = " · ".join(
        (f"{day:%m月%d日}（{'、'.join(cities)}） " if multiple_dates else "") + name
        for (day, name), cities in festival_groups.items())
    notice = "部分城市天气暂不可用，以下为已获取的预报。" if failed else ""
    date_text = ("；".join(f'{item["city"]} {item["date"]:%Y年%m月%d日}' for item in forecasts)
                 if multiple_dates else f"{date:%Y年%m月%d日}")
    f = {key: e(value) for key, value in fortune.items()}
    plain = f"{city} · {date_text}\n{alert_plain}{label} · {fortune['title']}\n{fortune['verse']}\n\n{fortune['interpretation']}\n宜：{fortune['good']}\n忌：{fortune['avoid']}\n\n出行准备\n{advice_plain}\n\n明日天气\n" + "\n".join(lines) + f"\n{notice}\n{festival_text}\n\n{note}\n"
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(label)}</title></head>
<body style="margin:0;padding:0;background-color:#f3f1ec;color:#383c36;font-family:Arial,'Microsoft YaHei',sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{e(city)} · 明日天气与生活寄语</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f3f1ec;"><tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="560" cellspacing="0" cellpadding="0" style="width:100%;max-width:560px;background-color:#fffdf8;border:1px solid #e5e0d6;border-radius:12px;">
<tr><td style="padding:30px 26px 22px;">
<p style="margin:0 0 8px;font-size:11px;letter-spacing:3px;color:#878574;">给明天的一封信</p>
<p style="margin:0;font-size:13px;color:#75766e;">{e(city)} &nbsp; / &nbsp; {e(date_text)}</p>
</td></tr>
{alert_html}
<tr><td style="padding:0 26px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#edf0e7;border:1px solid #dce2d2;border-radius:8px;">
<tr><td align="center" style="padding:30px 20px;">
<p style="margin:0 0 17px;font-size:11px;letter-spacing:4px;color:#78806b;">{e(label)} &nbsp; · &nbsp; 一日一念</p>
<h1 style="margin:0 0 18px;font-family:Georgia,'Songti SC',SimSun,serif;font-size:28px;font-weight:normal;letter-spacing:5px;color:#3e513f;">{f['title']}</h1>
<p style="margin:0;font-size:16px;line-height:1.9;color:#4f5e4b;">{f['verse']}</p>
</td></tr></table>
</td></tr>
<tr><td style="padding:22px 26px 26px;">
<p style="margin:0 0 18px;font-size:14px;line-height:1.9;color:#6f7066;">{f['interpretation']}</p>
<p style="margin:0 0 9px;font-size:13px;line-height:1.7;"><span style="color:#687e59;">宜</span> &nbsp; {f['good']}</p>
<p style="margin:0;font-size:13px;line-height:1.7;"><span style="color:#a48a70;">忌</span> &nbsp; {f['avoid']}</p>
</td></tr>
<tr><td style="padding:0 26px 26px;">
<p style="margin:0;padding-top:22px;border-top:1px solid #e5e0d6;font-size:12px;letter-spacing:2px;color:#797b70;">出行准备</p>
{advice_html}
<p style="margin:20px 0 0;font-size:12px;letter-spacing:2px;color:#797b70;">明日天气</p>
<p style="margin:8px 0;font-size:11px;color:#858078;">时间按各城市当地时间</p>
{f'<p style="font-size:13px;color:#96764f;">{e(notice)}</p>' if notice else ''}
<table width="100%" cellspacing="0" cellpadding="0" style="table-layout:fixed;">{''.join(rows)}</table>
{f'<p style="margin:12px 0 0;font-size:12px;color:#858078;">{e(festival_text)}</p>' if festival_text else ''}
</td></tr>
<tr><td align="center" style="padding:18px 20px;border-top:1px solid #eeeae3;font-size:10px;letter-spacing:1px;color:#96958c;">{e(note)}</td></tr>
</table></td></tr></table></body></html>'''
    return html, plain
