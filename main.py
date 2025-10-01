import os, requests, datetime

API_KEY = os.getenv("OPENWEATHER_KEY")
CITY = "Beijing"
url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&lang=zh_cn&units=metric"

res = requests.get(url).json()

# Debug：把返回内容打印出来
print("API 返回结果:", res)

if "list" not in res:
    raise Exception(f"OpenWeather API 出错: {res}")

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
else:
    msg = f"明天 {CITY} 天气正常，无需带伞 😎"

# 微信推送
server_key = os.getenv("SERVERCHAN_KEY")
if server_key:
    push_url = f"https://sctapi.ftqq.com/{server_key}.send"
    requests.post(push_url, data={"title": "带伞提醒", "desp": msg})
