"""
设计日报 - AI 日报生成模块
支持 OpenAI 和 Anthropic 两种 provider
"""

import json
import logging
from typing import Optional

from config import AI_API_KEY, AI_PROVIDER, AI_MODEL, AI_BASE_URL, REPORT_LANGUAGE, REPORT_DEPTH

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一位资深设计媒体编辑，负责撰写每日设计领域资讯日报。

## 你的任务
根据提供的当日设计新闻素材，撰写一份深度分析日报。

## 写作要求
1. **语言**：中英混合——正文用中文，专业术语、品牌名、设计概念保留英文原文
2. **风格**：专业但不晦涩，像一位有经验的设计总监在跟你聊今天的行业动态
3. **结构**：
   - 🔥 今日要闻（3-5 条最重要的新闻，每条 200-400 字深度分析）
   - 🎨 UI/UX 数字产品动态（2-3 条）
   - 🖼️ 平面视觉传达动态（2-3 条）
   - 🏭 工业/产品设计动态（2-3 条）
   - 💡 编辑观点：今日设计趋势观察（300-500 字的独立评论段落）
   - 🔗 延伸阅读（所有引用的原文链接列表）
4. **深度**：不是简单罗列标题，而是分析事件背后的设计趋势、商业逻辑和行业影响
5. **客观**：保持编辑视角的独立性，不吹捧不贬低，有观点但有依据
6. **格式**：使用 Markdown 格式，适当使用 emoji 增加可读性

## 注意事项
- 不要编造素材中没有的信息
- 如果某个分类没有相关新闻，可以跳过该分类
- 链接格式统一用 [标题](URL)
- 总字数控制在 2000-3500 字之间
"""


def _build_user_prompt(articles_data: list[dict]) -> str:
    """构建用户提示词"""
    articles_text = json.dumps(articles_data, ensure_ascii=False, indent=2)
    return f"""以下是今日抓取到的设计领域新闻素材（共 {len(articles_data)} 篇），请根据这些素材撰写今日设计日报：

{articles_text}

请按照系统提示中的要求，生成一份高质量的深度分析日报。"""


def generate_report_openai(articles_data: list[dict], base_url: str = None) -> str:
    """使用 OpenAI 兼容 API 生成日报（支持 OpenAI / 千问等）"""
    from openai import OpenAI

    kwargs = {"api_key": AI_API_KEY}
    if base_url:
        kwargs["base_url"] = base_url

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


def generate_report_qwen(articles_data: list[dict]) -> str:
    """使用千问 API 生成日报（通过 OpenAI 兼容接口）"""
    return generate_report_openai(articles_data, base_url=AI_BASE_URL)


def generate_report_anthropic(articles_data: list[dict]) -> str:
    """使用 Anthropic API 生成日报"""
    from anthropic import Anthropic

    client = Anthropic(api_key=AI_API_KEY)

    response = client.messages.create(
        model=AI_MODEL or "claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_prompt(articles_data)},
        ],
    )

    return response.content[0].text


def generate_daily_report(articles: list) -> str:
    """
    根据文章列表生成日报
    articles: Article 对象列表
    返回: Markdown 格式的日报文本
    """
    # 转换为字典列表
    articles_data = [a.to_dict() for a in articles]

    logger.info(f"开始生成日报，共 {len(articles_data)} 篇素材，使用 {AI_PROVIDER}")

    try:
        if AI_PROVIDER == "anthropic":
            report = generate_report_anthropic(articles_data)
        elif AI_PROVIDER == "qwen":
            report = generate_report_qwen(articles_data)
        else:
            report = generate_report_openai(articles_data)

        logger.info(f"日报生成完成，长度: {len(report)} 字符")

        # 添加日期标题
        from datetime import datetime
        today = datetime.now().strftime("%Y年%m月%d日")
        full_report = f"# 📰 Design Daily | {today}\n\n{report}"

        return full_report

    except Exception as e:
        logger.error(f"日报生成失败: {e}")
        raise RuntimeError(f"AI 日报生成失败: {e}")
