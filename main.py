import requests
import datetime
import os
API_KEY = os.getenv("OPENWEATHER_KEY")
server_key = os.getenv("SERVERCHAN_KEY")


API_KEY = "你的openweather api key"  # 去 openweathermap.org 注册
CITY = "Beijing"  # 你要查询的城市

url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&lang=zh_cn&units=metric"
res = requests.get(url).json()

tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
rain_expected = False

for item in res["list"]:
    dt = datetime.datetime.fromtimestamp(item["dt"])
    if dt.date() == tomorrow:
        desc = item["weather"][0]["description"]
        if "雨" in desc:
            rain_expected = True
            break

if rain_expected:
    msg = f"明天 {CITY} 可能下雨，记得带伞 ☔"
    server_key = "你的server酱key"  # 待会放到 GitHub Secrets
    push_url = f"https://sctapi.ftqq.com/{server_key}.send"
    requests.post(push_url, data={"title": "带伞提醒", "desp": msg})
