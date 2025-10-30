#!/usr/bin/env python3
"""
邮箱推送测试脚本
用于测试天气提醒的邮箱发送功能
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_test_email():
    """发送测试邮件"""
    # 邮箱配置
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    
    # 检查配置
    if not all([sender_email, sender_password, recipient_email]):
        print("❌ 邮箱配置不完整！")
        print("请设置以下环境变量：")
        print("  SENDER_EMAIL=your_email@gmail.com")
        print("  SENDER_PASSWORD=your_app_password")
        print("  RECIPIENT_EMAIL=recipient@example.com,recipient2@example.com (支持多个，用逗号分隔)")
        print("  SMTP_SERVER=smtp.gmail.com (可选)")
        print("  SMTP_PORT=587 (可选)")
        return False
    
    # 解析多个收件人邮箱
    recipient_emails = [email.strip() for email in recipient_email.split(",") if email.strip()]
    if not recipient_emails:
        print("❌ 未检测到有效的收件人邮箱")
        return False
    
    # 测试邮件内容
    subject = "🌤️ 天气提醒测试邮件"
    body = """明天 Sydney 天气预报:
08:00: 小雨 🌡15°C (体感 13°C) 💧湿度85% 🌬风速3.2m/s ☔降水概率80%
12:00: 多云 🌡18°C (体感 16°C) 💧湿度70% 🌬风速2.8m/s ☔降水概率30%
16:00: 晴 🌡22°C (体感 20°C) 💧湿度60% 🌬风速2.1m/s ☔降水概率10%
20:00: 晴 🌡19°C (体感 17°C) 💧湿度65% 🌬风速1.8m/s ☔降水概率5%

注意带伞 ☔

这是一封测试邮件，用于验证天气提醒功能是否正常工作。
"""
    
    try:
        # 创建邮件对象
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # 添加邮件正文
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        print(f"📧 正在发送测试邮件...")
        print(f"   发送者: {sender_email}")
        print(f"   接收者: {len(recipient_emails)} 个邮箱")
        print(f"   SMTP服务器: {smtp_server}:{smtp_port}")
        
        # 连接SMTP服务器
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            
            # 向每个收件人发送邮件
            for email in recipient_emails:
                message["To"] = email
                server.send_message(message)
                print(f"   ✅ 已发送到: {email}")
            
        print(f"\n✅ 测试邮件发送成功！")
        print(f"   已向 {len(recipient_emails)} 个收件人发送邮件")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ 邮箱认证失败！")
        print("   请检查邮箱地址和密码是否正确")
        print("   对于Gmail，请使用应用专用密码而不是账户密码")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 天气提醒邮箱推送测试")
    print("=" * 40)
    send_test_email()
