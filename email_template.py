"""Email-safe table layout and matching plain text, with escaped dynamic content."""
from html import escape


def render_email(date, city, periods, rain, extreme, fortune, generated, festivals, preview=False):
    e = lambda value: escape(str(value), quote=True)
    label = "明日签" if generated else "明日寄语"
    note = ("示例文案 · 仅供预览" if preview else
            "AI 创作 · 宜忌仅作生活灵感" if generated else "日常寄语 · 非 AI 生成")
    tip = "明天有雨，记得带伞。" if rain else "出门前，留一点时间看看天空。"
    if extreme:
        tip = ("明天有雨，记得带伞；另有特殊天气，请留意预报。" if rain and
               any("type" in w for w in extreme) else
               "明天有雨，记得带伞。" if rain else "明天有特殊天气，请留意预报、安排出行。")
    rows, lines = [], []
    for name, p in periods.items():
        title = name.split("(")[0].strip()
        desc = p["main_desc"]
        temperature = f'{p["min_temp"]:.0f}–{p["max_temp"]:.0f}°'
        detail = f'体感 {p["avg_feels_like"]:.0f}° · 降水 {p["max_pop"]:.0%}'
        rows.append(f'''<tr><td style="padding:13px 0;border-bottom:1px solid #eeeae3;width:22%;font-size:14px;">{e(title)}</td>
<td style="padding:13px 4px;border-bottom:1px solid #eeeae3;font-size:14px;">{e(desc)}<br><span style="font-size:11px;color:#858078;">{e(detail)}</span></td>
<td align="right" style="padding:13px 0;border-bottom:1px solid #eeeae3;font-size:19px;white-space:nowrap;">{e(temperature)}</td></tr>''')
        lines.append(f"{name}：{desc}，{temperature}，{detail}")
    warnings = "；".join(f"{w['time']} {w['desc']}" for w in extreme)
    festival_text = " · ".join(f.split(" - ")[0] for f in festivals)
    f = {key: e(value) for key, value in fortune.items()}
    plain = f"{city} · {date:%Y年%m月%d日}\n{label} · {fortune['title']}\n{fortune['verse']}\n\n{fortune['interpretation']}\n宜：{fortune['good']}\n忌：{fortune['avoid']}\n\n明日天气\n" + "\n".join(lines) + f"\n{tip}\n{warnings}\n{festival_text}\n\n{note}\n"
    html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(label)}</title></head>
<body style="margin:0;padding:0;background-color:#f3f1ec;color:#383c36;font-family:Arial,'Microsoft YaHei',sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{e(fortune['verse'])} {e(tip)}</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#f3f1ec;"><tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="560" cellspacing="0" cellpadding="0" style="width:100%;max-width:560px;background-color:#fffdf8;border:1px solid #e5e0d6;border-radius:12px;">
<tr><td style="padding:30px 26px 22px;">
<p style="margin:0 0 8px;font-size:11px;letter-spacing:3px;color:#878574;">给明天的一封信</p>
<p style="margin:0;font-size:13px;color:#75766e;">{e(city)} &nbsp; / &nbsp; {date:%Y.%m.%d}</p>
</td></tr>
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
<p style="margin:0;padding-top:22px;border-top:1px solid #e5e0d6;font-size:12px;letter-spacing:2px;color:#797b70;">明日天气</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0">{''.join(rows)}</table>
<p style="margin:16px 0 0;font-size:13px;line-height:1.8;color:#5e7253;">{e(tip)}</p>
{f'<p style="margin:8px 0 0;font-size:12px;line-height:1.8;color:#96764f;">{e(warnings)}</p>' if warnings else ''}
{f'<p style="margin:12px 0 0;font-size:12px;color:#858078;">{e(festival_text)}</p>' if festival_text else ''}
</td></tr>
<tr><td align="center" style="padding:18px 20px;border-top:1px solid #eeeae3;font-size:10px;letter-spacing:1px;color:#96958c;">{e(note)}</td></tr>
</table></td></tr></table></body></html>'''
    return html, plain


def combine_emails(emails, failed=0):
    """Combine city cards into one valid HTML document and one plain text body."""
    import re
    bodies = [re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL).group(1)
              for html, _ in emails]
    notice = "部分城市天气暂不可用，以下为已获取的预报。" if failed else ""
    html = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>明日签与天气</title></head>'
            '<body style="margin:0;background-color:#f3f1ec;color:#383c36;'
            'font-family:Arial,Microsoft YaHei,sans-serif;">'
            + (f'<p style="text-align:center;font-size:13px;">{notice}</p>' if notice else '')
            + ''.join(bodies) + '</body></html>')
    return html, (notice + "\n" if notice else "") + "\n\n".join(plain for _, plain in emails)
