"""Daily weather and AI fortune email. Importing this module has no side effects."""
import argparse
import datetime
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from daily_fortune import get_daily_fortune
from email_template import render_email, combine_emails

def get_solar_term(year, month, day):
    """计算二十四节气日期（使用近似算法）"""
    # 二十四节气对应的太阳黄经度数（每个节气相差15度）
    # 使用简化公式计算每个节气的日期
    # 基于1900年1月6日小寒的基准日期

    # 每个节气的大致日期范围（考虑年份差异，每年可能有1-2天偏差）
    # 格式: (月份, 最小日期, 最大日期)
    solar_term_dates = {
        "小寒": (1, 4, 6), "大寒": (1, 19, 21),
        "立春": (2, 3, 5), "雨水": (2, 18, 20),
        "惊蛰": (3, 5, 7), "春分": (3, 20, 22),
        "清明": (4, 4, 6), "谷雨": (4, 19, 21),
        "立夏": (5, 5, 7), "小满": (5, 20, 22),
        "芒种": (6, 5, 7), "夏至": (6, 21, 23),
        "小暑": (7, 6, 8), "大暑": (7, 22, 24),
        "立秋": (8, 7, 9), "处暑": (8, 22, 24),
        "白露": (9, 7, 9), "秋分": (9, 22, 24),
        "寒露": (10, 7, 9), "霜降": (10, 23, 25),
        "立冬": (11, 7, 9), "小雪": (11, 22, 24),
        "大雪": (12, 6, 8), "冬至": (12, 21, 23)
    }

    # 检查是否是某个节气
    for term, (term_month, start_day, end_day) in solar_term_dates.items():
        if month == term_month and start_day <= day <= end_day:
            return term
    return None

def calculate_easter(year):
    """计算复活节日期（使用算法）"""
    # 使用匿名格里高利历算法计算复活节
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(year, month, day)

def get_solar_term_info(date=None):
    """检查是否是二十四节气，并返回简单介绍"""
    if date is None:
        date = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
    elif isinstance(date, datetime.datetime):
        date = date.date()

    year = date.year
    month = date.month
    day = date.day

    solar_term = get_solar_term(year, month, day)
    if solar_term:
        solar_term_intros = {
            "立春": "立春是二十四节气之首，标志着春天的开始，万物复苏。",
            "雨水": "雨水节气，天气回暖，降雨增多，是春耕的好时节。",
            "惊蛰": "惊蛰时节，春雷始鸣，蛰伏的动物开始苏醒。",
            "春分": "春分日，昼夜平分，是春季的中分点，也是踏青的好时节。",
            "清明": "清明时节雨纷纷，是祭祖扫墓和踏青的节日。",
            "谷雨": "谷雨是春季最后一个节气，雨生百谷，是播种移苗的好时机。",
            "立夏": "立夏标志着夏季的开始，万物繁茂，气温逐渐升高。",
            "小满": "小满时节，麦类等夏熟作物籽粒开始饱满，但尚未成熟。",
            "芒种": "芒种是农忙时节，有芒的麦子快收，有芒的稻子可种。",
            "夏至": "夏至日，北半球白昼最长，标志着盛夏的到来。",
            "小暑": "小暑时节，天气开始炎热，但还未到最热的时候。",
            "大暑": "大暑是一年中最热的节气，要注意防暑降温。",
            "立秋": "立秋标志着秋季的开始，天气逐渐转凉。",
            "处暑": "处暑意味着炎热的夏天即将结束，天气开始转凉。",
            "白露": "白露时节，天气转凉，清晨的露水增多。",
            "秋分": "秋分日，昼夜平分，是秋季的中分点。",
            "寒露": "寒露时节，气温更低，露水更冷，即将凝结成霜。",
            "霜降": "霜降是秋季最后一个节气，天气渐冷，开始降霜。",
            "立冬": "立冬标志着冬季的开始，万物收藏，准备过冬。",
            "小雪": "小雪时节，天气寒冷，开始降雪，但雪量不大。",
            "大雪": "大雪时节，降雪量增多，天气更加寒冷。",
            "冬至": "冬至日，北半球白昼最短，标志着数九寒天的开始。",
            "小寒": "小寒时节，天气寒冷，但还未到最冷的时候。",
            "大寒": "大寒是一年中最冷的节气，也是冬季的最后一个节气。"
        }
        return f"{solar_term}节气 - {solar_term_intros.get(solar_term, '')}"
    return None

def get_chinese_festival_info(date=None):
    """检查是否是中国节日，并返回简单介绍"""
    if date is None:
        date = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
    elif isinstance(date, datetime.datetime):
        date = date.date()

    month = date.month
    day = date.day
    month_day = (month, day)

    chinese_festivals = {
        (1, 1): ("元旦", "元旦是新年的第一天，标志着新一年的开始。"),
        (2, 14): ("情人节", "情人节是表达爱意的日子，也是浪漫的节日。"),
        (3, 8): ("国际妇女节", "国际妇女节是庆祝女性成就和争取平等权利的节日。"),
        (3, 12): ("植树节", "植树节是倡导植树造林、保护环境的节日。"),
        (4, 1): ("愚人节", "愚人节是西方的传统节日，人们可以互相开玩笑。"),
        (5, 1): ("劳动节", "劳动节是全世界劳动人民共同拥有的节日，庆祝劳动者的贡献。"),
        (5, 4): ("青年节", "五四青年节是纪念1919年五四运动的节日。"),
        (6, 1): ("儿童节", "国际儿童节是保障儿童权益、庆祝儿童成长的节日。"),
        (7, 1): ("建党节", "中国共产党建党节，纪念中国共产党的成立。"),
        (8, 1): ("建军节", "中国人民解放军建军节，纪念人民军队的建立。"),
        (9, 10): ("教师节", "教师节是感谢教师为教育事业做出贡献的节日。"),
        (10, 1): ("国庆节", "中华人民共和国国庆节，庆祝新中国的成立。"),
        (12, 25): ("圣诞节", "圣诞节是西方传统节日，庆祝耶稣基督的诞生。"),
    }

    if month_day in chinese_festivals:
        name, intro = chinese_festivals[month_day]
        return f"中国节日：{name} - {intro}"
    return None

def get_german_festival_info(date=None):
    """检查是否是德国节日，并返回简单介绍"""
    if date is None:
        date = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
    elif isinstance(date, datetime.datetime):
        date = date.date()

    year = date.year
    month = date.month
    day = date.day
    month_day = (month, day)

    easter = calculate_easter(year)
    german_festivals = {
        (1, 1): ("新年", "Neujahr - 德国的新年，是公共假日。"),
        (1, 6): ("主显节", "Heilige Drei Könige - 在巴伐利亚等州是公共假日。"),
        (5, 1): ("劳动节", "Tag der Arbeit - 德国的劳动节，是公共假日。"),
        (10, 3): ("德国统一日", "Tag der Deutschen Einheit - 庆祝1990年东西德统一，是公共假日。"),
        (11, 1): ("万圣节", "Allerheiligen - 在天主教州是公共假日。"),
        (12, 25): ("圣诞节", "Weihnachten - 德国最重要的节日之一，是公共假日。"),
        (12, 26): ("节礼日", "Zweiter Weihnachtsfeiertag - 圣诞节的第二天，是公共假日。"),
    }

    # 基于复活节的德国节日
    easter_friday = easter - datetime.timedelta(days=2)  # 耶稣受难日
    easter_monday = easter + datetime.timedelta(days=1)  # 复活节星期一
    ascension = easter + datetime.timedelta(days=39)  # 耶稣升天节
    whit_monday = easter + datetime.timedelta(days=50)  # 圣灵降临节星期一
    corpus_christi = easter + datetime.timedelta(days=60)  # 基督圣体节

    if date == easter_friday:
        return "德国节日：耶稣受难日（Karfreitag） - 这是复活节前的星期五，是公共假日。"
    elif date == easter:
        return "德国节日：复活节（Ostern） - 这是基督教最重要的节日之一，是公共假日。"
    elif date == easter_monday:
        return "德国节日：复活节星期一（Ostermontag） - 这是复活节的第二天，是公共假日。"
    elif date == ascension:
        return "德国节日：耶稣升天节（Christi Himmelfahrt） - 复活节后第40天，是公共假日。"
    elif date == whit_monday:
        return "德国节日：圣灵降临节星期一（Pfingstmontag） - 复活节后第50天，是公共假日。"
    elif date == corpus_christi:
        return "德国节日：基督圣体节（Fronleichnam） - 在天主教州是公共假日。"
    elif month_day in german_festivals:
        name, intro = german_festivals[month_day]
        return f"德国节日：{name} - {intro}"
    return None

def get_australian_festival_info(date=None):
    """检查是否是澳大利亚节日，并返回简单介绍"""
    if date is None:
        date = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
    elif isinstance(date, datetime.datetime):
        date = date.date()

    month = date.month
    day = date.day
    month_day = (month, day)

    australian_festivals = {
        (1, 1): ("新年", "New Year's Day - 澳大利亚的新年，是公共假日。"),
        (1, 26): ("澳大利亚日", "Australia Day - 庆祝1788年第一批欧洲移民抵达澳大利亚，是公共假日。"),
        (3, 8): ("国际妇女节", "International Women's Day - 庆祝女性成就的节日。"),
        (4, 25): ("澳新军团日", "ANZAC Day - 纪念第一次世界大战中澳新军团的牺牲，是公共假日。"),
        (5, 1): ("劳动节", "Labour Day - 在部分州是公共假日。"),
        (6, 8): ("女王生日", "Queen's Birthday - 在部分州是公共假日（日期可能因州而异）。"),
        (10, 1): ("劳动节", "Labour Day - 在部分州是公共假日。"),
        (12, 25): ("圣诞节", "Christmas Day - 澳大利亚的圣诞节，是公共假日。"),
        (12, 26): ("节礼日", "Boxing Day - 圣诞节的第二天，是公共假日。"),
    }

    if month_day in australian_festivals:
        name, intro = australian_festivals[month_day]
        return f"澳大利亚节日：{name} - {intro}"
    return None

def prepare_weather(res, now=None, timezone_name=None):
    if timezone_name is None:
        timezone_name = os.getenv("CITY_TIMEZONE")
    tz = (ZoneInfo(timezone_name) if timezone_name else
          datetime.timezone(datetime.timedelta(seconds=res["city"]["timezone"])))
    now = now or datetime.datetime.now(datetime.timezone.utc)
    tomorrow = now.astimezone(tz).date() + datetime.timedelta(days=1)
    # 按时间段分组：早上7-10点，中午10-15点，下午15-18点，晚上18-23点
    time_periods = {
        "早上 (07:00-10:00)": (7, 10),
        "中午 (10:00-15:00)": (10, 15),
        "下午 (15:00-18:00)": (15, 18),
        "晚上 (18:00-23:00)": (18, 23)
    }

    # 收集明天的天气数据
    tomorrow_data = []
    rain_expected = False
    extreme_weather = []

    for item in res["list"]:
        dt = datetime.datetime.fromtimestamp(item["dt"], tz)
        if dt.date() == tomorrow:
            desc = item["weather"][0]["description"]
            main_weather = item["weather"][0]["main"]
            icon = item["weather"][0].get("icon", "01d")  # 天气图标代码
            temp = item["main"]["temp"]
            feels_like = item["main"]["feels_like"]
            humidity = item["main"]["humidity"]
            wind_speed = item["wind"]["speed"]
            pop = item.get("pop", 0)  # 降水概率
            rain_volume = item.get("rain", {}).get("3h", 0)  # 3小时降雨量

            weather_info = {
                "time": dt,
                "hour": dt.hour,
                "desc": desc,
                "main": main_weather,
                "icon": icon,  # 添加图标代码
                "temp": temp,
                "feels_like": feels_like,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "pop": pop,
                "rain_volume": rain_volume
            }
            tomorrow_data.append(weather_info)

            # 检测异常天气
            if main_weather in ["Rain", "Thunderstorm", "Drizzle"] or "雨" in desc:
                rain_expected = True
                extreme_weather.append({
                    "time": dt.strftime("%H:%M"),
                    "desc": desc,
                    "pop": pop,
                    "rain_volume": rain_volume
                })
            elif main_weather in ["Snow", "Squall", "Extreme"] or "雪" in desc:
                extreme_weather.append({
                    "time": dt.strftime("%H:%M"),
                    "desc": desc,
                    "type": "极端天气"
                })

    # 按时间段分组整理天气信息
    period_weather = {}
    for period_name, (start_hour, end_hour) in time_periods.items():
        period_data = [w for w in tomorrow_data if start_hour <= w["hour"] < end_hour]
        if period_data:
            # 计算该时间段的平均温度和主要天气
            avg_temp = sum(w["temp"] for w in period_data) / len(period_data)
            max_temp = max(w["temp"] for w in period_data)
            min_temp = min(w["temp"] for w in period_data)
            avg_feels_like = sum(w["feels_like"] for w in period_data) / len(period_data)
            max_pop = max(w["pop"] for w in period_data)
            max_rain = max(w["rain_volume"] for w in period_data)

            # 找到主要天气状况（降雨概率最高的时段）
            main_weather_item = max(period_data, key=lambda x: x["pop"])

            period_weather[period_name] = {
                "data": period_data,
                "avg_temp": avg_temp,
                "max_temp": max_temp,
                "min_temp": min_temp,
                "avg_feels_like": avg_feels_like,
                "max_pop": max_pop,
                "max_rain": max_rain,
                "main_desc": main_weather_item["desc"],
                "main_weather": main_weather_item["main"],
                "icon": main_weather_item.get("icon", "01d")  # 添加图标代码
            }

    if not tomorrow_data:
        raise ValueError("天气接口没有目标城市明日的数据")
    return tomorrow, period_weather, rain_expected, extreme_weather


def fetch_weather(city):
    key = os.getenv("OPENWEATHER_KEY")
    if not key:
        raise ValueError("请配置 OPENWEATHER_KEY")
    response = requests.get("https://api.openweathermap.org/data/2.5/forecast",
                            params={"q": city, "appid": key, "lang": "zh_cn", "units": "metric"},
                            timeout=(10, 30))
    if response.status_code != 200:
        raise ValueError(f"天气接口请求失败（HTTP {response.status_code}）")
    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("list"), list):
        raise ValueError("天气接口返回格式无效")
    return data


def send_email(subject, html, plain, recipients):
    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_PASSWORD")
    if not sender or not password or not recipients:
        raise ValueError("请配置 SENDER_EMAIL、SENDER_PASSWORD 和 RECIPIENT_EMAIL")
    failures = 0
    with smtplib.SMTP(os.getenv("SMTP_SERVER") or "smtp.gmail.com",
                      int(os.getenv("SMTP_PORT") or "587"), timeout=30) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(sender, password)
        for recipient in recipients:
            message = EmailMessage()
            message["From"] = sender
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(plain)
            message.add_alternative(html, subtype="html")
            try:
                server.send_message(message)
            except (smtplib.SMTPException, OSError):
                failures += 1
                logging.error("一封邮件发送失败。")
    if failures:
        raise RuntimeError(f"{failures} 封邮件发送失败")
    logging.info("已成功发送 %d 封邮件。", len(recipients))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", metavar="PATH", help="离线生成示例HTML，不调用API或发送邮件")
    args = parser.parse_args()
    city = os.getenv("CITY") or "Sydney"
    if args.preview:
        date = datetime.date(2026, 10, 3)
        periods = {name: {"main_desc": desc, "min_temp": low, "max_temp": high,
                          "avg_feels_like": low, "max_pop": pop}
                   for name, desc, low, high, pop in [
                       ("早上 (07:00-10:00)", "多云", 14, 16, .1),
                       ("中午 (10:00-15:00)", "小雨", 16, 18, .8),
                       ("下午 (15:00-18:00)", "小雨", 15, 17, .7),
                       ("晚上 (18:00-23:00)", "多云", 13, 15, .2)]}
        fortune = {"title": "云过天青", "verse": "等一朵云走过，也给心事一点晴空。",
                   "interpretation": "不必把一天安排得太满，留一点空白，接住生活的小惊喜。",
                   "good": "给惦记的人一句问候", "avoid": "为了赶路忘记看风景"}
        html, _ = render_email(date, city, periods, True, [], fortune, True, [], preview=True)
        Path(args.preview).write_text(html, encoding="utf-8")
        logging.info("示例预览已保存：%s", args.preview)
        return
    recipients = [v.strip() for v in (os.getenv("RECIPIENT_EMAIL") or "").split(",") if v.strip()]
    if not recipients or not os.getenv("SENDER_EMAIL") or not os.getenv("SENDER_PASSWORD"):
        raise ValueError("请先配置发件邮箱、密码和收件人")
    cities = list(dict.fromkeys(c.strip() for c in city.split(",") if c.strip())) or ["Sydney"]
    zones = [z.strip() for z in (os.getenv("CITY_TIMEZONE") or "").split(",")]
    if any(zones) and len(zones) != len(cities):
        raise ValueError("CITY_TIMEZONE 必须与 CITY 的城市数量及顺序一致")
    emails, failed = [], 0
    for index, city_name in enumerate(cities):
        try:
            date, periods, rain, extreme = prepare_weather(
                fetch_weather(city_name), timezone_name=zones[index] if any(zones) else "")
        except (requests.RequestException, ValueError, KeyError):
            logging.error("一个城市的天气获取失败，继续处理其余城市。")
            failed += 1
            continue
        summary = [{"period": name, "weather": p["main_desc"], "min_c": p["min_temp"],
                    "max_c": p["max_temp"], "rain_probability": p["max_pop"]}
                   for name, p in periods.items()]
        fortune, generated = get_daily_fortune(date, city_name, summary)
        festivals = [info for fn in (get_solar_term_info, get_chinese_festival_info,
                                     get_german_festival_info, get_australian_festival_info)
                     if (info := fn(date))]
        emails.append(render_email(date, city_name, periods, rain, extreme, fortune, generated, festivals))
    if not emails:
        raise ValueError("没有可发送的城市天气")
    html, plain = combine_emails(emails, failed)
    send_email("明日签与天气 | " + " · ".join(cities), html, plain, recipients)
    if failed:
        raise RuntimeError("已发送部分城市预报，但有城市天气获取失败")



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        main()
    except Exception as error:
        # Avoid logging request URLs, authentication data or recipient addresses.
        logging.error("运行失败（%s），请检查配置与服务状态。", type(error).__name__)
        raise SystemExit(1)
