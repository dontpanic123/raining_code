import os, requests, datetime

API_KEY = os.getenv("OPENWEATHER_KEY")  # OpenWeather API Key
CITY = "Beijing"

# 请求天气
url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&lang=zh_cn&units=metric"
res = requests.get(url).json()

tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date()
rain_expected = False
weather_details = []

if "list" not in res:
    msg = f"天气接口错误: {res}"
else:
    for item in res["list"]:
        dt = datetime.datetime.fromtimestamp(item["dt"])
        if dt.date() == tomorrow:
            desc = item["weather"][0]["description"]
            temp = item["main"]["temp"]
            feels_like = item["main"]["feels_like"]
            humidity = item["main"]["humidity"]
            wind_speed = item["wind"]["speed"]
            pop = item.get("pop", 0)  # 降水概率
            weather_details.append(f"{dt.strftime('%H:%M')}: {desc} 🌡{temp}°C (体感 {feels_like}°C) 💧湿度{humidity}% 🌬风速{wind_speed}m/s ☔降水概率{int(pop*100)}%")
            
            if "雨" in desc:
                rain_expected = True

    # 构造推送消息
    rain_note = "注意带伞 ☔" if rain_expected else "明天天气良好 😎"
    details = "\n".join(weather_details)
    msg = f"明天 {CITY} 天气预报:\n{details}\n\n{rain_note}"

# 企业微信群机器人推送
WEBHOOK = os.getenv("WECHAT_WEBHOOK")
data = {
    "msgtype": "text",
    "text": {
        "content": msg
    }
}
resp = requests.post(WEBHOOK, json=data)
print("推送结果:", resp.text)
