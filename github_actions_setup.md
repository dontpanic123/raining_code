# GitHub Actions 邮箱推送配置指南

## 🚀 使用 GitHub Actions 自动运行天气提醒

### 1. 配置 GitHub Secrets

在 GitHub 仓库中设置以下 Secrets：

#### 必需配置
- `OPENWEATHER_KEY`: OpenWeather API 密钥
- `SENDER_EMAIL`: 发送者邮箱地址
- `SENDER_PASSWORD`: 发送者邮箱密码/应用密码
- `RECIPIENT_EMAIL`: 接收者邮箱地址


#### 可选配置
- `OPENAI_API_KEY`: AI 每日签密钥；不设置时按日期使用内置的一年预备寄语，无需付费 AI API。只用文案库时可以删除此 Secret。
- `CITY`: 城市，默认 Sydney。
- `CITY_TIMEZONE`: IANA 时区，例如 Australia/Sydney 或 Europe/Berlin，推荐配置。
- `OPENAI_MODEL`: 支持 Structured Outputs 的模型，默认 gpt-4o-mini。
- `SMTP_SERVER`: SMTP服务器（默认：smtp.gmail.com）
- `SMTP_PORT`: SMTP端口（默认：587）

### 2. 设置步骤

1. **进入仓库设置**
   - 打开你的 GitHub 仓库
   - 点击 "Settings" 标签页
   - 在左侧菜单中找到 "Secrets and variables" → "Actions"

2. **添加 Secrets**
   - 点击 "New repository secret"
   - 输入 Secret 名称和值
   - 点击 "Add secret"

### 3. 不同邮箱的配置

#### Gmail 配置
```
SENDER_EMAIL: your_email@gmail.com
SENDER_PASSWORD: your_16_digit_app_password
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587
```

#### QQ邮箱配置
```
SENDER_EMAIL: your_qq@qq.com
SENDER_PASSWORD: your_qq_authorization_code
SMTP_SERVER: smtp.qq.com
SMTP_PORT: 587
```

#### 163邮箱配置
```
SENDER_EMAIL: your_email@163.com
SENDER_PASSWORD: your_163_authorization_code
SMTP_SERVER: smtp.163.com
SMTP_PORT: 587
```

### 4. 运行时间配置

当前配置为每天 UTC 时间 9:00 运行（对应北京时间 17:00，悉尼时间 19:00 或 20:00（随夏令时变化））

如需修改时间，编辑 `.github/workflows/main.yml` 中的 cron 表达式：
```yaml
schedule:
  - cron: "0 9 * * *"   # UTC 时间
```

### 5. 手动触发

你也可以手动触发工作流：
1. 进入仓库的 "Actions" 标签页
2. 选择 "Rain Reminder" 工作流
3. 点击 "Run workflow" 按钮

### 6. 查看运行日志

1. 在 "Actions" 页面点击最近的工作流运行
2. 点击 "build" 作业
3. 查看 "Run weather reminder script" 步骤的日志

### 7. 故障排除

#### 常见问题
- **认证失败**: 检查邮箱密码是否正确
- **网络问题**: GitHub Actions 可能无法访问某些SMTP服务器
- **时区问题**: 确保 cron 时间设置正确

#### 调试建议
- 先本地测试 `python3 test_email.py`
- 查看 GitHub Actions 运行日志
- 确保所有 Secrets 都已正确设置

### 8. 安全提醒

- 不要在代码中硬编码密码
- 定期更换应用密码
- 使用最小权限原则

每日签按日期、城市与模型缓存，Actions 使用缓存跨运行复用。请勿在签语中加入私人资料。
