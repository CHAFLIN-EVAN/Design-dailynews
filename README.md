# 📰 Design Daily — 每日设计日报推送工具

每天自动抓取设计领域新闻，AI 整合生成深度分析日报，推送到你的微信。

## 功能
- 📡 **多源聚合**：RSS（Smashing Magazine、Yanko Design 等）+ 爬取（优设、站酷等）
- 🤖 **AI 整合**：Claude/GPT 生成中英混合深度分析日报
- 📱 **微信推送**：通过 PushPlus 推送到微信
- ⏰ **定时运行**：GitHub Actions 每天 8:00 自动执行
- 💰 **低成本**：运行成本 < 30 元/月

## 快速部署（15 分钟）

### 第一步：注册 PushPlus（3 分钟）

1. 打开 [pushplus.plus](https://www.pushplus.plus)
2. 用微信扫码关注它的公众号
3. 登录后复制你的 **token**

### 第二步：获取 AI API Key（5 分钟）

**方案 A — OpenAI（推荐新手）：**
1. 打开 [platform.openai.com](https://platform.openai.com)
2. 注册/登录 → Billing 绑卡 → API Keys 页面创建新 key
3. 复制 API Key

**方案 B — Anthropic Claude：**
1. 打开 [console.anthropic.com](https://console.anthropic.com)
2. 注册/登录 → Billing 绑卡 → API Keys 页面创建新 key
3. 复制 API Key

### 第三步：部署到 GitHub（5 分钟）

1. 在 GitHub 上新建仓库（如 `design-daily`）
2. 将本项目代码推送到仓库：
   ```bash
   cd design-daily
   git init
   git add .
   git commit -m "init: design daily push tool"
   git branch -M main
   git remote add origin https://github.com/你的用户名/design-daily.git
   git push -u origin main
   ```
3. 在仓库页面进入 **Settings → Secrets and variables → Actions**
4. 点击 **New repository secret**，添加以下 4 个 secret：

   | Name | Value |
   |------|-------|
   | `PUSHPLUS_TOKEN` | 第一步拿到的 token |
   | `AI_API_KEY` | 第二步拿到的 API key |
   | `AI_PROVIDER` | `openai` 或 `anthropic` |
   | `AI_MODEL` | `gpt-4o-mini` 或 `claude-sonnet-4-20250514` |

5. 进入 **Actions** 页面，手动触发一次 `Design Daily Push` 工作流测试

完成！之后每天 8:00 左右会自动推送日报到你的微信。

## 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 token 和 key

# 运行
cd src
python main.py

# 或者只测试抓取（不推送）
python test_local.py
```

## 项目结构

```
design-daily/
├── .github/workflows/
│   └── daily-push.yml       # GitHub Actions 定时任务
├── src/
│   ├── config.py            # 配置文件
│   ├── fetcher.py           # 新闻抓取（RSS + 爬取）
│   ├── ai_writer.py         # AI 日报生成
│   ├── pusher.py            # 微信推送
│   └── main.py              # 主入口
├── requirements.txt
├── .env.example
├── test_local.py            # 本地测试脚本
└── README.md
```

## 自定义

### 修改新闻源

编辑 `src/config.py`：
- `RSS_FEEDS`：添加/删除 RSS 源
- `SCRAPE_TARGETS`：添加/删除爬取目标

### 调整日报风格

编辑 `src/ai_writer.py` 中的 `SYSTEM_PROMPT`，可以修改：
- 语言风格
- 文章结构
- 深度要求
- 字数限制

### 修改推送时间

编辑 `.github/workflows/daily-push.yml` 中的 `cron` 表达式：
- 北京时间 7:00 → `cron: "0 23 * * *"`（前一天 UTC）
- 北京时间 9:00 → `cron: "0 1 * * *"`

## 常见问题

**Q: GitHub Actions 的定时任务不准确怎么办？**
A: GitHub 的 cron 有 10-30 分钟延迟是正常的。如需精确时间，可迁移到阿里云函数计算。

**Q: PushPlus 推送失败？**
A: 检查 token 是否正确，公众号是否关注了 PushPlus。

**Q: AI API 费用超出预期？**
A: 可以降低 `TOTAL_ARTICLES_FOR_AI` 数量，或换用更便宜的模型（如 `gpt-4o-mini`）。

**Q: 想增加更多新闻源？**
A: 在 `config.py` 的 `RSS_FEEDS` 或 `SCRAPE_TARGETS` 中添加即可。

## License

MIT
