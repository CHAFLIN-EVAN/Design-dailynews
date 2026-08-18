"""
设计日报 - AI 日报生成模块
生成精美的 HTML 格式设计日报
"""

import json
import logging
from datetime import datetime

from config import AI_API_KEY, AI_PROVIDER, AI_MODEL, AI_BASE_URL

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一位资深设计媒体编辑，负责撰写每日设计领域资讯日报。

## 你的任务
根据提供的当日设计新闻素材，撰写一份深度分析日报。

## 输出格式
请严格输出 JSON 格式，结构如下：
```json
{
  "headline_articles": [
    {
      "title": "文章标题",
      "source": "来源名称",
      "category": "分类",
      "url": "原文链接",
      "image_url": "图片链接（从素材中获取）",
      "analysis": "200-400字深度分析"
    }
  ],
  "sections": {
    "ui_ux": [
      {
        "title": "...",
        "source": "...",
        "url": "...",
        "image_url": "...",
        "analysis": "100-200字分析"
      }
    ],
    "graphic": [...],
    "industrial": [...]
  },
  "editorial": "300-500字的编辑观点，分析今日设计趋势"
}
```

## 写作要求
1. **语言**：中英混合——正文用中文，专业术语、品牌名、设计概念保留英文原文
2. **风格**：专业但不晦涩，像一位有经验的设计总监在跟你聊今天的行业动态
3. **深度**：不是简单罗列标题，而是分析事件背后的设计趋势、商业逻辑和行业影响
4. **客观**：保持编辑视角的独立性，不吹捧不贬低，有观点但有依据

## ⚠️ 重要：类别覆盖要求
**每一期日报必须包含以下所有类别，不能留空：**
- `ui_ux`：UI/UX 数字产品设计（界面、交互、用户体验、产品设计）
- `graphic`：平面视觉传达（品牌、海报、排版、字体、插画）
- `industrial`：工业/产品设计（实体产品、家具、交通工具、空间设计）

如果某个类别当天直接相关新闻不足，你必须：
- 从现有素材中挖掘与该类别相关的内容进行归类
- 基于相关趋势进行延伸分析
- 确保每个类别至少有 2 条内容

## 注意事项
- 不要编造素材中没有的信息
- image_url 必须从素材中获取，不要编造
- headline_articles 选 3-5 条最重要的，且需覆盖不同类别
- 只输出 JSON，不要输出其他内容
"""


def _build_user_prompt(articles_data: list[dict]) -> str:
    """构建用户提示词"""
    articles_text = json.dumps(articles_data, ensure_ascii=False, indent=2)
    return f"""以下是今日抓取到的设计领域新闻素材（共 {len(articles_data)} 篇），请根据这些素材撰写今日设计日报：

{articles_text}

请按照系统提示中的 JSON 格式输出。"""


def _call_ai(articles_data: list[dict]) -> str:
    """调用 AI API"""
    if AI_PROVIDER == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=AI_API_KEY)
        response = client.messages.create(
            model=AI_MODEL or "claude-sonnet-4-20250514",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(articles_data)}],
        )
        return response.content[0].text
    else:
        from openai import OpenAI
        kwargs = {"api_key": AI_API_KEY}
        if AI_PROVIDER == "qwen" and AI_BASE_URL:
            kwargs["base_url"] = AI_BASE_URL
        client = OpenAI(**kwargs)
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(articles_data)},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        return response.choices[0].message.content


def _parse_ai_response(response: str) -> dict:
    """解析 AI 返回的 JSON"""
    # 尝试提取 JSON 部分
    text = response.strip()
    if text.startswith("```"):
        # 去除 markdown 代码块
        lines = text.split("\n")
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试找到 JSON 部分
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"无法解析 AI 返回的内容为 JSON")


def _render_html(data: dict, date_str: str) -> str:
    """将数据渲染为精美 HTML"""

    # 默认占位图
    placeholder = "https://via.placeholder.com/600x400/1a1a2e/ffffff?text=Design+Daily"

    def render_card(article: dict, is_headline: bool = False) -> str:
        img = article.get("image_url") or placeholder
        title = article.get("title", "无标题")
        source = article.get("source", "")
        category = article.get("category", "")
        url = article.get("url", "#")
        analysis = article.get("analysis", "")

        card_class = "headline-card" if is_headline else "card"
        img_height = "240px" if is_headline else "180px"

        return f'''
        <div class="{card_class}">
          <a href="{url}" target="_blank" class="card-link">
            <div class="card-image" style="height:{img_height};background-image:url('{img}')"></div>
          </a>
          <div class="card-content">
            <div class="card-meta">
              <span class="category-tag">{category}</span>
              <span class="source">{source}</span>
            </div>
            <h3 class="card-title"><a href="{url}" target="_blank">{title}</a></h3>
            <p class="card-analysis">{analysis}</p>
          </div>
        </div>'''

    # 渲染头条
    headline_html = ""
    for article in data.get("headline_articles", []):
        headline_html += render_card(article, is_headline=True)

    # 渲染分类 sections
    section_config = {
        "ui_ux": ("🎨 UI/UX 数字产品", "ui_ux"),
        "graphic": ("🖼️ 平面视觉传达", "graphic"),
        "industrial": ("🏭 工业/产品设计", "industrial"),
    }

    sections_html = ""
    for key, (label, _) in section_config.items():
        items = data.get("sections", {}).get(key, [])
        if not items:
            continue
        cards = ""
        for item in items:
            cards += render_card(item)
        sections_html += f'''
        <div class="section">
          <h2 class="section-title">{label}</h2>
          <div class="card-grid">{cards}</div>
        </div>'''

    # 编辑观点
    editorial = data.get("editorial", "")
    editorial_html = ""
    if editorial:
        editorial_html = f'''
        <div class="editorial">
          <h2 class="editorial-title">💡 编辑观点：今日设计趋势</h2>
          <p class="editorial-content">{editorial}</p>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Design Daily | {date_str}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f7f8fa;
    color: #1a1a2e;
    line-height: 1.6;
    padding: 0;
  }}
  .container {{ max-width: 680px; margin: 0 auto; padding: 20px 16px; }}

  /* Header */
  .header {{
    text-align: center;
    padding: 40px 20px 30px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #fff;
    border-radius: 16px;
    margin-bottom: 30px;
  }}
  .header-label {{
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.6);
    margin-bottom: 8px;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 6px;
  }}
  .header-date {{
    font-size: 14px;
    color: rgba(255,255,255,0.7);
  }}

  /* Section */
  .section {{ margin-bottom: 36px; }}
  .section-title {{
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e8e8ed;
  }}

  /* Headline cards */
  .headline-card {{
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .headline-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1), 0 8px 24px rgba(0,0,0,0.06);
  }}

  /* Regular cards */
  .card-grid {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }}
  .card {{
    background: #fff;
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .card:hover {{
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }}
  .card .card-image {{
    width: 140px;
    min-width: 140px;
    background-size: cover;
    background-position: center;
    background-color: #e8e8ed;
  }}
  .card .card-content {{
    padding: 14px 16px;
    flex: 1;
  }}
  .headline-card .card-image {{
    width: 100%;
    background-size: cover;
    background-position: center;
    background-color: #e8e8ed;
  }}
  .headline-card .card-content {{
    padding: 20px;
  }}

  .card-link {{ display: block; }}
  .card-meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }}
  .category-tag {{
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    background: #e8f4f8;
    color: #0f3460;
  }}
  .source {{
    font-size: 12px;
    color: #8b8b9e;
  }}
  .card-title {{
    font-size: 15px;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 8px;
  }}
  .card-title a {{
    color: #1a1a2e;
    text-decoration: none;
  }}
  .card-title a:hover {{ color: #0f3460; }}
  .headline-card .card-title {{ font-size: 20px; }}
  .card-analysis {{
    font-size: 13px;
    color: #5a5a6e;
    line-height: 1.7;
  }}
  .headline-card .card-analysis {{
    font-size: 14px;
    margin-top: 12px;
  }}

  /* Editorial */
  .editorial {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff;
    border-radius: 12px;
    padding: 28px 24px;
    margin: 30px 0;
  }}
  .editorial-title {{
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 14px;
  }}
  .editorial-content {{
    font-size: 14px;
    line-height: 1.8;
    color: rgba(255,255,255,0.9);
  }}

  /* Footer */
  .footer {{
    text-align: center;
    padding: 24px 16px;
    font-size: 12px;
    color: #8b8b9e;
  }}
  .footer a {{ color: #0f3460; text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-label">Design Daily News</div>
    <h1>📰 设计日报</h1>
    <div class="header-date">{date_str}</div>
  </div>

  <div class="section">
    <h2 class="section-title">🔥 今日要闻</h2>
    {headline_html}
  </div>

  {sections_html}

  {editorial_html}

  <div class="footer">
    由 AI 编辑生成 · 数据来源：Smashing Magazine / Dezeen / Core77 / 优设 / 站酷 等<br>
    <a href="https://github.com/CHAFLIN-EVAN/Design-dailynews">Design Daily News</a> &copy; 2026
  </div>
</div>
</body>
</html>'''

    return html


def generate_daily_report(articles: list) -> str:
    """
    根据文章列表生成 HTML 格式日报
    articles: Article 对象列表
    返回: HTML 格式的日报
    """
    articles_data = [a.to_dict() for a in articles]
    today = datetime.now().strftime("%Y年%m月%d日")

    logger.info(f"开始生成日报，共 {len(articles_data)} 篇素材，使用 {AI_PROVIDER}")

    try:
        # 调用 AI 生成结构化内容
        response = _call_ai(articles_data)
        data = _parse_ai_response(response)

        logger.info(f"AI 内容生成完成，渲染 HTML...")

        # 渲染为 HTML
        html = _render_html(data, today)

        logger.info(f"日报生成完成，长度: {len(html)} 字符")
        return html

    except Exception as e:
        logger.error(f"日报生成失败: {e}")
        raise RuntimeError(f"AI 日报生成失败: {e}")
