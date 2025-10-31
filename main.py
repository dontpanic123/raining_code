import os, requests, datetime, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

API_KEY = os.getenv("OPENWEATHER_KEY")  # OpenWeather API Key
CITY = os.getenv("CITY", "Sydney")  # 城市名称，默认悉尼

# 请求天气
url = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&lang=zh_cn&units=metric"
res = requests.get(url).json()


# Debug：把返回内容打印出来
print("API 返回结果:", res)

if "list" not in res:
    raise Exception(f"OpenWeather API 出错: {res}")
    
tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date()

# 按时间段分组：早上7-10点，中午10-15点，下午15-18点，晚上18-23点
time_periods = {
    "早上 (07:00-10:00)": (7, 10),
    "中午 (10:00-15:00)": (10, 15),
    "下午 (15:00-18:00)": (15, 18),
    "晚上 (18:00-23:00)": (18, 23)
}

if "list" not in res:
    msg = f"天气接口错误: {res}"
else:
    # 收集明天的天气数据
    tomorrow_data = []
    rain_expected = False
    extreme_weather = []
    
    for item in res["list"]:
        dt = datetime.datetime.fromtimestamp(item["dt"])
        if dt.date() == tomorrow:
            desc = item["weather"][0]["description"]
            main_weather = item["weather"][0]["main"]
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
                "main_weather": main_weather_item["main"]
            }
    
    # 构造格式化的邮件内容
    msg_parts = []
    msg_parts.append(f"📅 明天 {tomorrow.strftime('%Y年%m月%d日')} {CITY} 天气预报")
    msg_parts.append("=" * 50)
    msg_parts.append("")
    
    # 异常天气预警
    if extreme_weather:
        msg_parts.append("⚠️ 【异常天气预警】")
        for ew in extreme_weather:
            if "rain_volume" in ew:
                rain_info = f" | 降雨量: {ew['rain_volume']}mm" if ew['rain_volume'] > 0 else ""
                msg_parts.append(f"  ☔ {ew['time']} - {ew['desc']} (降水概率: {int(ew['pop']*100)}%){rain_info}")
            else:
                msg_parts.append(f"  ⚠️ {ew['time']} - {ew['desc']}")
        msg_parts.append("")
    
    # 各时段详细预报
    msg_parts.append("📊 分时段预报：")
    msg_parts.append("")
    
    for period_name, period_info in period_weather.items():
        msg_parts.append(f"【{period_name}】")
        
        # 天气描述和温度
        weather_emoji = {
            "Rain": "☔",
            "Thunderstorm": "⛈️",
            "Drizzle": "🌦️",
            "Snow": "❄️",
            "Clear": "☀️",
            "Clouds": "☁️",
            "Mist": "🌫️",
            "Fog": "🌫️"
        }
        emoji = weather_emoji.get(period_info["main_weather"], "🌤️")
        
        msg_parts.append(f"  {emoji} {period_info['main_desc']}")
        msg_parts.append(f"  🌡️ 温度: {period_info['min_temp']:.1f}°C ~ {period_info['max_temp']:.1f}°C")
        msg_parts.append(f"  🌡️ 体感: {period_info['avg_feels_like']:.1f}°C")
        
        # 降雨信息（如果有）
        if period_info["max_pop"] > 0:
            msg_parts.append(f"  ☔ 降水概率: {int(period_info['max_pop']*100)}%")
            if period_info["max_rain"] > 0:
                msg_parts.append(f"  💧 降雨量: {period_info['max_rain']:.1f}mm")
        
        # 详细时段数据
        msg_parts.append("  详细:")
        for w in period_info["data"]:
            wind_info = f"🌬️{w['wind_speed']:.1f}m/s" if w['wind_speed'] > 5 else ""
            pop_info = f"☔{int(w['pop']*100)}%" if w['pop'] > 0 else ""
            msg_parts.append(f"    {w['time'].strftime('%H:%M')}: {w['temp']:.1f}°C 💧{w['humidity']}% {wind_info} {pop_info}".strip())
        
        msg_parts.append("")
    
    # 总结和建议
    msg_parts.append("=" * 50)
    if rain_expected:
        msg_parts.append("☔ 【温馨提示】明天有降雨，请记得带伞！")
    elif extreme_weather:
        msg_parts.append("⚠️ 【温馨提示】明天有极端天气，请注意安全！")
    else:
        msg_parts.append("😎 【温馨提示】明天天气良好，适合出行！")
    
    msg = "\n".join(msg_parts)


# 邮箱推送
def send_email(subject, body, to_email):
    """发送邮件"""
    # 邮箱配置
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # SMTP服务器
    smtp_port = int(os.getenv("SMTP_PORT", "587"))  # SMTP端口
    sender_email = os.getenv("SENDER_EMAIL")  # 发送者邮箱
    sender_password = os.getenv("SENDER_PASSWORD")  # 发送者密码或应用密码
    
    if not all([sender_email, sender_password, to_email]):
        print("邮箱配置不完整，跳过邮件发送")
        return
    
    try:
        # 创建邮件对象
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject
        
        # 添加邮件正文
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # 连接SMTP服务器并发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # 启用TLS加密
            server.login(sender_email, sender_password)
            server.send_message(message)
            print(f"邮件已成功发送到 {to_email}")
            
    except Exception as e:
        print(f"邮件发送失败: {e}")

# 发送天气邮件（支持多个收件人，用逗号分隔）
recipient_emails_str = os.getenv("RECIPIENT_EMAIL", "")  # 接收者邮箱，支持多个，用逗号分隔
if recipient_emails_str:
    # 分割邮箱地址，去除空白字符
    recipient_emails = [email.strip() for email in recipient_emails_str.split(",") if email.strip()]
    
    if recipient_emails:
        print(f"📧 准备发送邮件到 {len(recipient_emails)} 个收件人: {', '.join(recipient_emails)}")
        for email in recipient_emails:
            send_email("带伞提醒", msg, email)
        print(f"✅ 已向所有收件人发送邮件")
    else:
        print("❌ 未检测到有效的收件人邮箱")
else:
    print("❌ 未设置接收者邮箱，跳过邮件发送")
    print("   请设置环境变量: export RECIPIENT_EMAIL='email1@example.com,email2@example.com'")
    print("   或在 GitHub Secrets 中设置 RECIPIENT_EMAIL（支持多个邮箱，用逗号分隔）")



