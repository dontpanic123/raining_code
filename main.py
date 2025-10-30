import os, requests, datetime, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

API_KEY = os.getenv("OPENWEATHER_KEY")  # OpenWeather API Key
CITY = "Sydney"

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

# 发送天气邮件
recipient_email = os.getenv("RECIPIENT_EMAIL")  # 接收者邮箱
if recipient_email:
    send_email("带伞提醒", msg, recipient_email)
else:
    print("未设置接收者邮箱，跳过邮件发送")



