# raining_code · 明日签

每天一封简洁的中文邮件：AI 签名、签语、生活宜忌，以及目标城市明日的分时天气和带伞提醒。全部内容直接呈现在邮件正文，使用内联样式与表格布局，同时提供纯文本版本。

## 本地运行

需要 Python 3.10+：

```bash
pip install -r requirements.txt
# 按 env_example.txt 配置环境变量后：
python main.py
```

环境文件不会自动加载。必须设置天气密钥和邮件配置；设置 `OPENAI_API_KEY` 启用 AI 每日签，`OPENAI_MODEL` 默认为 `gpt-4o-mini`。模型需要支持 JSON Schema Structured Outputs。AI 接收日期、城市和天气摘要，不接收邮箱地址。

推荐设置 `CITY_TIMEZONE=Australia/Sydney`（或目标城市对应的 IANA 时区），以正确处理夏令时。未设置时使用天气接口的 UTC 偏移。

## 离线预览与验证

```bash
python main.py --preview preview.html
python -m unittest discover -s tests -v
```

用浏览器打开 preview.html。预览使用明确标注的示例天气与签语，不调用服务、不发送邮件。`test_email.py` 是旧的 SMTP 手工连通性测试，会真实发送测试邮件。

## 生成与回退

- 每个日期、城市、模型及提示词版本缓存一份成功生成的签语；多人共享一次生成。
- 缓存目录默认 `.cache/fortunes`，可通过 `FORTUNE_CACHE_DIR` 修改。
- 未配置密钥、超时、拒答或输出不合格式时，使用明确标注为非 AI 的日常寄语，不影响天气邮件。
- 签语是 AI 创作，不宣称传统黄历依据；页面中的宜忌是生活灵感。
- 天气不可用或邮件发送失败时，程序以非零状态退出。
- 原有节日提示保留为简短文字，节气仍使用原项目的近似日期规则。

## GitHub Actions

实际工作流是 `.github/workflows/main.yml`，每天 UTC 09:00 运行，支持手动触发。`workflows/weather.yml` 仅作为同步示例。配置见 [部署指南](github_actions_setup.md)。Actions 缓存成功的签语；缓存被淘汰或并发首次运行时可能重新生成，邮件发送本身不做去重。

API 实现依据 [OpenAI Structured Outputs 官方文档](https://developers.openai.com/api/docs/guides/structured-outputs)。
