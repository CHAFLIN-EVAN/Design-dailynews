"""
设计日报 - 配置文件
所有配置项通过环境变量注入，本地调试用 .env 文件
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# API Keys
# ============================================================
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "qwen")  # "openai" / "anthropic" / "qwen"
AI_MODEL = os.getenv("AI_MODEL", "qwen-plus")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# ============================================================
# RSS 源列表
# ============================================================
RSS_FEEDS = {
    # UI/UX 数字产品
    "smashing_magazine": "https://www.smashingmagazine.com/feed/",
    "ux_collective": "https://uxdesign.cc/feed",
    "nngroup": "https://www.nngroup.com/articles/rss.xml",
    "creative_bloc": "https://www.creativebloq.com/feed",

    # 工业/产品设计
    "yanko_design": "https://www.yankodesign.com/feed/",
    "core77": "https://www.core77.com/rss",
    "dezeen": "https://www.dezeen.com/feed/",

    # 平面视觉
    "design_week": "https://www.designweek.co.uk/feed/",
    "its_nice_that": "https://www.itsnicethat.com/feed",
    "brand_identity": "https://thebrandidentity.com/feed/",
}

# ============================================================
# 爬取目标（中文设计媒体）
# ============================================================
SCRAPE_TARGETS = [
    {
        "name": "优设网",
        "url": "https://www.uisdc.com/",
        "selector": "article h2 a",  # 文章标题链接
        "encoding": "utf-8",
    },
    {
        "name": "站酷",
        "url": "https://www.zcool.com.cn/discover",
        "selector": ".card-list a.title",
        "encoding": "utf-8",
    },
]

# ============================================================
# 日报生成配置
# ============================================================
MAX_ARTICLES_PER_SOURCE = 5       # 每个源最多抓取条数
TOTAL_ARTICLES_FOR_AI = 15        # 送给 AI 整合的文章总数
REPORT_LANGUAGE = "zh-en-mixed"    # 中英混合
REPORT_DEPTH = "deep"             # deep / medium / brief

# ============================================================
# 推送配置
# ============================================================
PUSH_CHANNEL = "wechat"           # PushPlus 渠道
PUSH_TEMPLATE = "html"              # html / markdown / txt
