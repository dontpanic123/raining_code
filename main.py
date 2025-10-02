import os, requests, datetime

API_KEY = os.getenv("OPENWEATHER_KEY")  # OpenWeather API Key
CITY = "Beijing"

# 请求天气
url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&lang=zh_cn&units=metric"
res = requests.get(url).json()


# Debug：把返回内容打印出来
print("API 返回结果:", res)

if "list" not in res:
    raise Exception(f"OpenWeather API 出错: {res}")
    
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


# 微信推送
server_key = os.getenv("SERVERCHAN_KEY")
if server_key:
    push_url = f"https://sctapi.ftqq.com/{server_key}.send"
    requests.post(push_url, data={"title": "带伞提醒", "desp": msg})



