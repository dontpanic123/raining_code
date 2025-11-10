import os, requests, datetime, smtplib, hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

API_KEY = os.getenv("OPENWEATHER_KEY")  # OpenWeather API Key
CITY = os.getenv("CITY", "Sydney")  # 城市名称，默认悉尼

def get_geo_fact(date=None):
    """根据日期返回有趣的地理知识（每天不同，所有城市看到相同的知识）"""
    city_facts_list = {
        "Sydney": [
            "悉尼歌剧院的设计灵感来自于切开的橘子瓣，而不是帆船。",
            "悉尼拥有超过100个海滩，是世界上拥有最多海滩的城市之一。",
            "悉尼海港大桥的钢铁用量可以建造1万辆汽车。",
        ],
        "北京": [
            "北京是全世界唯一既举办过夏季奥运会又举办过冬季奥运会的城市。",
            "北京紫禁城有9999间半的房间，因为古代皇帝认为天上有一万间房。",
            "北京的中轴线长达7.8公里，是世界上现存最长的城市中轴线。",
        ],
        "Beijing": [
            "北京是全世界唯一既举办过夏季奥运会又举办过冬季奥运会的城市。",
            "北京紫禁城有9999间半的房间，因为古代皇帝认为天上有一万间房。",
            "北京的中轴线长达7.8公里，是世界上现存最长的城市中轴线。",
        ],
        "上海": [
            "上海的黄浦江实际上是一条河，而非真正的江。",
            "上海拥有世界上最高的酒店——上海中心J酒店，高度632米。",
            "上海地铁网络是世界上里程最长的地铁系统之一，总长超过800公里。",
        ],
        "Shanghai": [
            "上海的黄浦江实际上是一条河，而非真正的江。",
            "上海拥有世界上最高的酒店——上海中心J酒店，高度632米。",
            "上海地铁网络是世界上里程最长的地铁系统之一，总长超过800公里。",
        ],
        "深圳": [
            "深圳在40年前还是一个小渔村，现在已成为拥有1700万人口的超大城市。",
            "深圳是中国第一个经济特区，被誉为'中国硅谷'。",
            "深圳拥有超过200座摩天大楼，密度居世界前列。",
        ],
        "Shenzhen": [
            "深圳在40年前还是一个小渔村，现在已成为拥有1700万人口的超大城市。",
            "深圳是中国第一个经济特区，被誉为'中国硅谷'。",
            "深圳拥有超过200座摩天大楼，密度居世界前列。",
        ],
        "广州": [
            "广州是海上丝绸之路的起点之一，有2000多年的对外贸易历史。",
            "广州的早茶文化被联合国教科文组织列为非物质文化遗产。",
            "广州塔（小蛮腰）高600米，是世界上最高的电视塔之一。",
        ],
        "Guangzhou": [
            "广州是海上丝绸之路的起点之一，有2000多年的对外贸易历史。",
            "广州的早茶文化被联合国教科文组织列为非物质文化遗产。",
            "广州塔（小蛮腰）高600米，是世界上最高的电视塔之一。",
        ],
        "杭州": [
            "西湖的苏堤和白堤分别是以两位著名诗人苏东坡和白居易的名字命名的。",
            "杭州被誉为'人间天堂'，马可波罗曾称赞它为世界上最美丽华贵的城市。",
            "杭州龙井茶是中国十大名茶之首，已有1200多年历史。",
        ],
        "Hangzhou": [
            "西湖的苏堤和白堤分别是以两位著名诗人苏东坡和白居易的名字命名的。",
            "杭州被誉为'人间天堂'，马可波罗曾称赞它为世界上最美丽华贵的城市。",
            "杭州龙井茶是中国十大名茶之首，已有1200多年历史。",
        ],
        "成都": [
            "成都是大熊猫的故乡，也是全世界唯一一个在城市中心设立大熊猫繁育基地的城市。",
            "成都拥有超过2300年的建城史，是中国历史文化名城之一。",
            "成都的川菜是中国四大菜系之一，'吃在中国，味在四川'。",
        ],
        "Chengdu": [
            "成都是大熊猫的故乡，也是全世界唯一一个在城市中心设立大熊猫繁育基地的城市。",
            "成都拥有超过2300年的建城史，是中国历史文化名城之一。",
            "成都的川菜是中国四大菜系之一，'吃在中国，味在四川'。",
        ],
        "纽约": [
            "纽约的中央公园占地341公顷，比摩纳哥公国还大。",
            "纽约每年接待超过6000万游客，是世界上游客最多的城市之一。",
            "纽约的帝国大厦在1931年建成时是世界第一高楼，这一记录保持了40年。",
        ],
        "New York": [
            "纽约的中央公园占地341公顷，比摩纳哥公国还大。",
            "纽约每年接待超过6000万游客，是世界上游客最多的城市之一。",
            "纽约的帝国大厦在1931年建成时是世界第一高楼，这一记录保持了40年。",
        ],
        "伦敦": [
            "伦敦的地铁系统是世界上最古老的地铁系统，1863年就开始运营了。",
            "伦敦有170多种语言在使用，是世界上语言最多样化的城市。",
            "伦敦的大本钟实际上是指钟楼，钟本身叫'大本钟'（Big Ben），但人们常用这个名字指代整个钟楼。",
        ],
        "London": [
            "伦敦的地铁系统是世界上最古老的地铁系统，1863年就开始运营了。",
            "伦敦有170多种语言在使用，是世界上语言最多样化的城市。",
            "伦敦的大本钟实际上是指钟楼，钟本身叫'大本钟'（Big Ben），但人们常用这个名字指代整个钟楼。",
        ],
        "东京": [
            "东京是世界上人口最密集的大都市区，但同时也是犯罪率最低的城市之一。",
            "东京拥有世界上最复杂的地铁系统，超过280个车站。",
            "东京的银座是世界上最昂贵的地段之一，每平方米售价可达数十万美元。",
        ],
        "Tokyo": [
            "东京是世界上人口最密集的大都市区，但同时也是犯罪率最低的城市之一。",
            "东京拥有世界上最复杂的地铁系统，超过280个车站。",
            "东京的银座是世界上最昂贵的地段之一，每平方米售价可达数十万美元。",
        ],
        "巴黎": [
            "埃菲尔铁塔在建造时曾经被很多艺术家和知识分子反对，认为它破坏了巴黎的美景。",
            "巴黎的地下墓穴有超过600万具骸骨，总长度超过300公里。",
            "巴黎卢浮宫是世界上参观人数最多的博物馆，每年接待超过1000万游客。",
        ],
        "Paris": [
            "埃菲尔铁塔在建造时曾经被很多艺术家和知识分子反对，认为它破坏了巴黎的美景。",
            "巴黎的地下墓穴有超过600万具骸骨，总长度超过300公里。",
            "巴黎卢浮宫是世界上参观人数最多的博物馆，每年接待超过1000万游客。",
        ],
        "柏林": [
            "柏林拥有比威尼斯更多的桥梁，约有1700座。",
            "柏林墙倒塌时留下的碎片被作为纪念品出售，至今仍在流通。",
            "柏林是欧洲最大的城市之一，面积约892平方公里。",
        ],
        "Berlin": [
            "柏林拥有比威尼斯更多的桥梁，约有1700座。",
            "柏林墙倒塌时留下的碎片被作为纪念品出售，至今仍在流通。",
            "柏林是欧洲最大的城市之一，面积约892平方公里。",
        ],
        "墨尔本": [
            "墨尔本连续多年被评为全球最宜居城市，有'澳大利亚的文化之都'之称。",
            "墨尔本有世界上最多的电车轨道系统，总长超过250公里。",
            "墨尔本的咖啡文化非常发达，据说每100米就有一家咖啡馆。",
        ],
        "Melbourne": [
            "墨尔本连续多年被评为全球最宜居城市，有'澳大利亚的文化之都'之称。",
            "墨尔本有世界上最多的电车轨道系统，总长超过250公里。",
            "墨尔本的咖啡文化非常发达，据说每100米就有一家咖啡馆。",
        ],
    }
    
    # 通用地理知识（如果找不到对应城市）
    general_facts = [
        "地球上有约200个国家，但只有23个国家的国界线是完全笔直的。",
        "世界上最长的山脉不是在地面上，而是在海底——大西洋中脊全长约16000公里。",
        "地球上最干燥的地方不是撒哈拉沙漠，而是南极洲的麦克默多干谷，那里已经有200万年没有下雨了。",
        "澳大利亚是世界上唯一一个国土覆盖整个大陆的国家。",
        "如果你把地球上的所有冰都融化，海平面会上升约70米。",
        "地球自转速度正在减慢，每天的时长每100年增加约1.7毫秒。",
        "太平洋的面积比地球上所有陆地面积加起来还要大。",
        "珠穆朗玛峰每年都在长高，大约每年增长4毫米。",
        "死海的海拔是负424米，是地球上最低的陆地表面。",
        "地球上约有71%的表面被水覆盖，但淡水资源只占全球水量的约2.5%。",
    ]
    
    # 合并所有知识到一个列表中（每天轮换显示，不区分城市）
    all_facts = []
    
    # 添加所有城市的知识（去重）
    unique_city_facts = set()
    for city_key, facts_list in city_facts_list.items():
        for fact in facts_list:
            unique_city_facts.add(fact)
    
    # 添加城市知识和通用知识
    all_facts.extend(unique_city_facts)
    all_facts.extend(general_facts)
    
    # 确定选择的索引（纯粹基于日期，不依赖城市名）
    if date:
        # 使用日期的年月日来计算索引
        date_str = date.strftime("%Y%m%d") if hasattr(date, 'strftime') else str(date)
        selection_hash = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    else:
        # 如果没有提供日期，使用当前日期
        today = datetime.date.today()
        date_str = today.strftime("%Y%m%d")
        selection_hash = int(hashlib.md5(date_str.encode()).hexdigest(), 16)
    
    # 基于日期选择知识（所有城市在同一天看到相同的知识）
    return all_facts[selection_hash % len(all_facts)]

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

# 收集明天的天气数据
tomorrow_data = []
rain_expected = False
extreme_weather = []

for item in res["list"]:
    dt = datetime.datetime.fromtimestamp(item["dt"])
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

# 构造格式化的邮件内容（HTML格式，支持图片）
html_parts = []
html_parts.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { font-size: 18px; font-weight: bold; margin-bottom: 15px; }
        .warning { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 10px 0; }
        .period { margin: 15px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }
        .period-title { font-size: 16px; font-weight: bold; margin-bottom: 8px; }
        .weather-info { margin: 5px 0; }
        .tip { background-color: #d1ecf1; padding: 10px; border-left: 4px solid #0c5460; margin: 10px 0; }
        .fact { background-color: #e7f3ff; padding: 10px; border-left: 4px solid #0066cc; margin: 10px 0; font-style: italic; }
        .weather-icon { vertical-align: middle; margin-right: 5px; }
    </style>
</head>
<body>""")

html_parts.append(f'<div class="header">📅 {tomorrow.strftime("%Y年%m月%d日")} {CITY} 天气预报 🌤️</div>')

# 异常天气预警（突出显示）
if extreme_weather:
    html_parts.append('<div class="warning">⚠️ <strong>【降雨预警】</strong> 🌧️')
    for ew in extreme_weather:
        if "rain_volume" in ew:
            rain_info = f" 降雨量{ew['rain_volume']:.1f}mm" if ew['rain_volume'] > 0 else ""
            html_parts.append(f"<div>⏰ {ew['time']}: {ew['desc']} 降水概率{int(ew['pop']*100)}%{rain_info}</div>")
        else:
            html_parts.append(f"<div>⏰ {ew['time']}: {ew['desc']}</div>")
    html_parts.append('</div>')

# 各时段预报（简洁格式）
period_emojis = {
    "早上": "🌅",
    "中午": "☀️",
    "下午": "🌤️",
    "晚上": "🌙"
}

for period_name, period_info in period_weather.items():
    # 时间段标题（去掉括号）
    period_title = period_name.split("(")[0].strip()
    emoji = period_emojis.get(period_title, "📌")
    
    # 获取天气图标URL
    icon_code = period_info.get("icon", "01d")
    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    
    html_parts.append(f'<div class="period">')
    html_parts.append(f'<div class="period-title">{emoji} {period_title}</div>')
    
    # 根据天气类型选择emoji
    weather_emoji = "🌤️"  # 默认
    main_weather = period_info['main_weather']
    desc = period_info['main_desc']
    if main_weather in ["Rain", "Thunderstorm", "Drizzle"] or "雨" in desc:
        weather_emoji = "🌧️"
    elif main_weather in ["Snow"] or "雪" in desc:
        weather_emoji = "❄️"
    elif main_weather in ["Clear"] or "晴" in desc:
        weather_emoji = "☀️"
    elif main_weather in ["Clouds"] or "云" in desc:
        weather_emoji = "☁️"
    elif main_weather in ["Mist", "Fog", "Haze"] or "雾" in desc or "霾" in desc:
        weather_emoji = "🌫️"
    
    # 关键信息：天气、温度、降水（带图标）
    weather_line = f'<div class="weather-info">{weather_emoji} <img src="{icon_url}" alt="weather" class="weather-icon" style="width: 50px; height: 50px;"> 天气: {period_info["main_desc"]}</div>'
    temp_line = f'<div class="weather-info">🌡️ 温度: {period_info["min_temp"]:.0f}~{period_info["max_temp"]:.0f}°C (体感{period_info["avg_feels_like"]:.0f}°C)</div>'
    
    if period_info["max_pop"] > 0:
        rain_line = f'<div class="weather-info">☔ 降水概率: {int(period_info["max_pop"]*100)}%'
        if period_info["max_rain"] > 0:
            rain_line += f' 降雨量: {period_info["max_rain"]:.1f}mm'
        rain_line += '</div>'
        html_parts.append(weather_line)
        html_parts.append(temp_line)
        html_parts.append(rain_line)
    else:
        html_parts.append(weather_line)
        html_parts.append(temp_line)
    
    html_parts.append('</div>')

# 简短提示
if rain_expected:
    html_parts.append('<div class="tip">💡 <strong>提示:</strong> 明天有降雨，请带伞 ☂️</div>')
elif extreme_weather:
    html_parts.append('<div class="tip">💡 <strong>提示:</strong> 明天有极端天气，请注意安全 ⚠️</div>')

# 添加有趣的地理知识（基于日期，每天不同）
geo_fact = get_geo_fact(tomorrow)
html_parts.append(f'<div class="fact">🌍 {geo_fact}</div>')

html_parts.append("</body></html>")
html_msg = "\n".join(html_parts)

# 同时生成纯文本版本（作为备选）
msg_parts = []
msg_parts.append(f"📅 {tomorrow.strftime('%Y年%m月%d日')} {CITY} 天气预报 🌤️")
msg_parts.append("")

if extreme_weather:
    msg_parts.append("⚠️ 【降雨预警】🌧️")
    for ew in extreme_weather:
        if "rain_volume" in ew:
            rain_info = f" 降雨量{ew['rain_volume']:.1f}mm" if ew['rain_volume'] > 0 else ""
            msg_parts.append(f"⏰ {ew['time']}: {ew['desc']} 降水概率{int(ew['pop']*100)}%{rain_info}")
        else:
            msg_parts.append(f"⏰ {ew['time']}: {ew['desc']}")
    msg_parts.append("")

period_emojis = {
    "早上": "🌅",
    "中午": "☀️",
    "下午": "🌤️",
    "晚上": "🌙"
}

for period_name, period_info in period_weather.items():
    period_title = period_name.split("(")[0].strip()
    emoji = period_emojis.get(period_title, "📌")
    msg_parts.append(f"{emoji} {period_title}")
    
    weather_emoji = "🌤️"
    main_weather = period_info['main_weather']
    desc = period_info['main_desc']
    if main_weather in ["Rain", "Thunderstorm", "Drizzle"] or "雨" in desc:
        weather_emoji = "🌧️"
    elif main_weather in ["Snow"] or "雪" in desc:
        weather_emoji = "❄️"
    elif main_weather in ["Clear"] or "晴" in desc:
        weather_emoji = "☀️"
    elif main_weather in ["Clouds"] or "云" in desc:
        weather_emoji = "☁️"
    elif main_weather in ["Mist", "Fog", "Haze"] or "雾" in desc or "霾" in desc:
        weather_emoji = "🌫️"
    
    weather_line = f"{weather_emoji} 天气: {period_info['main_desc']}"
    temp_line = f"🌡️ 温度: {period_info['min_temp']:.0f}~{period_info['max_temp']:.0f}°C (体感{period_info['avg_feels_like']:.0f}°C)"
    
    if period_info["max_pop"] > 0:
        rain_line = f"☔ 降水概率: {int(period_info['max_pop']*100)}%"
        if period_info["max_rain"] > 0:
            rain_line += f" 降雨量: {period_info['max_rain']:.1f}mm"
        msg_parts.append(f"{weather_line} | {temp_line} | {rain_line}")
    else:
        msg_parts.append(f"{weather_line} | {temp_line}")
    
    msg_parts.append("")

if rain_expected:
    msg_parts.append("💡 提示: 明天有降雨，请带伞 ☂️")
elif extreme_weather:
    msg_parts.append("💡 提示: 明天有极端天气，请注意安全 ⚠️")

msg_parts.append("")
msg_parts.append(" ")
msg_parts.append(f"🌍 {geo_fact}")

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
        
        # 添加邮件正文（HTML格式，支持图片）
        # 如果body是HTML格式，则同时提供HTML和纯文本版本
        if isinstance(body, tuple):
            html_body, text_body = body
        else:
            # 检查body是否包含HTML标签
            if "<html>" in body or "<div" in body:
                # 从HTML中提取纯文本版本（简单处理）
                import re
                text_body = re.sub(r'<[^>]+>', '', body).replace('&nbsp;', ' ').strip()
                html_body = body
            else:
                html_body = None
                text_body = body
        
        if html_body:
            # 创建多部分消息，包含HTML和纯文本版本
            from email.mime.text import MIMEText
            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part1)
            message.attach(part2)
        else:
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
            send_email("今天小宝要带伞吗？", (html_msg, msg), email)
        print(f"✅ 已向所有收件人发送邮件")
    else:
        print("❌ 未检测到有效的收件人邮箱")
else:
    print("❌ 未设置接收者邮箱，跳过邮件发送")
    print("   请设置环境变量: export RECIPIENT_EMAIL='email1@example.com,email2@example.com'")
    print("   或在 GitHub Secrets 中设置 RECIPIENT_EMAIL（支持多个邮箱，用逗号分隔）")



