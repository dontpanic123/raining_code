import os, requests, datetime, smtplib, hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

API_KEY = os.getenv("OPENWEATHER_KEY")  # OpenWeather API Key
CITY = os.getenv("CITY", "Sydney")  # 城市名称，默认悉尼

def get_geo_fact(city_name):
    """根据城市名称返回有趣的地理知识"""
    city_facts = {
        "Sydney": "悉尼歌剧院的设计灵感来自于切开的橘子瓣，而不是帆船。",
        "北京": "北京是全世界唯一既举办过夏季奥运会又举办过冬季奥运会的城市。",
        "Beijing": "北京是全世界唯一既举办过夏季奥运会又举办过冬季奥运会的城市。",
        "上海": "上海的黄浦江实际上是一条河，而非真正的江。",
        "Shanghai": "上海的黄浦江实际上是一条河，而非真正的江。",
        "深圳": "深圳在40年前还是一个小渔村，现在已成为拥有1700万人口的超大城市。",
        "Shenzhen": "深圳在40年前还是一个小渔村，现在已成为拥有1700万人口的超大城市。",
        "广州": "广州是海上丝绸之路的起点之一，有2000多年的对外贸易历史。",
        "Guangzhou": "广州是海上丝绸之路的起点之一，有2000多年的对外贸易历史。",
        "杭州": "西湖的苏堤和白堤分别是以两位著名诗人苏东坡和白居易的名字命名的。",
        "Hangzhou": "西湖的苏堤和白堤分别是以两位著名诗人苏东坡和白居易的名字命名的。",
        "成都": "成都是大熊猫的故乡，也是全世界唯一一个在城市中心设立大熊猫繁育基地的城市。",
        "Chengdu": "成都是大熊猫的故乡，也是全世界唯一一个在城市中心设立大熊猫繁育基地的城市。",
        "纽约": "纽约的中央公园占地341公顷，比摩纳哥公国还大。",
        "New York": "纽约的中央公园占地341公顷，比摩纳哥公国还大。",
        "伦敦": "伦敦的地铁系统是世界上最古老的地铁系统，1863年就开始运营了。",
        "London": "伦敦的地铁系统是世界上最古老的地铁系统，1863年就开始运营了。",
        "东京": "东京是世界上人口最密集的大都市区，但同时也是犯罪率最低的城市之一。",
        "Tokyo": "东京是世界上人口最密集的大都市区，但同时也是犯罪率最低的城市之一。",
        "巴黎": "埃菲尔铁塔在建造时曾经被很多艺术家和知识分子反对，认为它破坏了巴黎的美景。",
        "Paris": "埃菲尔铁塔在建造时曾经被很多艺术家和知识分子反对，认为它破坏了巴黎的美景。",
        "柏林": "柏林拥有比威尼斯更多的桥梁，约有1700座。",
        "Berlin": "柏林拥有比威尼斯更多的桥梁，约有1700座。",
        "墨尔本": "墨尔本连续多年被评为全球最宜居城市，有'澳大利亚的文化之都'之称。",
        "Melbourne": "墨尔本连续多年被评为全球最宜居城市，有'澳大利亚的文化之都'之称。",
    }
    
    # 通用地理知识（如果找不到对应城市）
    general_facts = [
        "地球上有约200个国家，但只有23个国家的国界线是完全笔直的。",
        "世界上最长的山脉不是在地面上，而是在海底——大西洋中脊全长约16000公里。",
        "地球上最干燥的地方不是撒哈拉沙漠，而是南极洲的麦克默多干谷，那里已经有200万年没有下雨了。",
        "澳大利亚是世界上唯一一个国土覆盖整个大陆的国家。",
        "如果你把地球上的所有冰都融化，海平面会上升约70米。",
        "地球自转速度正在减慢，每天的时长每100年增加约1.7毫秒。",
    ]
    
    # 尝试匹配城市名（不区分大小写）
    city_key = None
    for key in city_facts.keys():
        if city_name.lower() in key.lower() or key.lower() in city_name.lower():
            city_key = key
            break
    
    if city_key:
        return city_facts[city_key]
    else:
        # 随机返回一个通用地理知识（使用城市名的hash来确保同一城市总是返回相同的知识）
        city_hash = int(hashlib.md5(city_name.encode()).hexdigest(), 16)
        return general_facts[city_hash % len(general_facts)]

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
    msg_parts.append(f"{tomorrow.strftime('%Y年%m月%d日')} {CITY} 天气预报")
    msg_parts.append("")
    
    # 异常天气预警（突出显示）
    if extreme_weather:
        msg_parts.append("【降雨预警】")
        for ew in extreme_weather:
            if "rain_volume" in ew:
                rain_info = f" 降雨量{ew['rain_volume']:.1f}mm" if ew['rain_volume'] > 0 else ""
                msg_parts.append(f"{ew['time']}: {ew['desc']} 降水概率{int(ew['pop']*100)}%{rain_info}")
            else:
                msg_parts.append(f"{ew['time']}: {ew['desc']}")
        msg_parts.append("")
    
    # 各时段预报（简洁格式）
    for period_name, period_info in period_weather.items():
        # 时间段标题（去掉括号）
        period_title = period_name.split("(")[0].strip()
        msg_parts.append(f"{period_title}")
        
        # 关键信息：天气、温度、降水
        weather_line = f"天气: {period_info['main_desc']}"
        temp_line = f"温度: {period_info['min_temp']:.0f}~{period_info['max_temp']:.0f}°C (体感{period_info['avg_feels_like']:.0f}°C)"
        
        if period_info["max_pop"] > 0:
            rain_line = f"降水概率: {int(period_info['max_pop']*100)}%"
            if period_info["max_rain"] > 0:
                rain_line += f" 降雨量: {period_info['max_rain']:.1f}mm"
            msg_parts.append(f"{weather_line} | {temp_line} | {rain_line}")
        else:
            msg_parts.append(f"{weather_line} | {temp_line}")
        
        msg_parts.append("")
    
    # 简短提示
    if rain_expected:
        msg_parts.append("提示: 明天有降雨，请带伞")
    elif extreme_weather:
        msg_parts.append("提示: 明天有极端天气，请注意安全")
    
    # 添加有趣的地理知识
    msg_parts.append("")
    msg_parts.append("【地理小知识】")
    geo_fact = get_geo_fact(CITY)
    msg_parts.append(geo_fact)
    
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



