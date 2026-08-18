"""
设计日报 - 主入口
每日抓取设计新闻 → AI 生成日报 → 推送到微信
"""

import logging
import sys
from datetime import datetime

from fetcher import fetch_all_news, filter_recent
from ai_writer import generate_daily_report
from pusher import send_daily_report
from config import TOTAL_ARTICLES_FOR_AI

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("design-daily")


def main():
    """主流程"""
    today = datetime.now().strftime("%Y年%m月%d日")
    logger.info(f"===== Design Daily 启动 | {today} =====")

    # Step 1: 抓取新闻
    logger.info("Step 1: 抓取新闻...")
    all_articles = fetch_all_news()

    if not all_articles:
        logger.error("未获取到任何新闻，终止运行")
        sys.exit(1)

    # Step 2: 过滤近期文章
    logger.info("Step 2: 过滤近期文章...")
    recent_articles = filter_recent(all_articles, hours=48)
    logger.info(f"近期文章: {len(recent_articles)} 篇")

    if not recent_articles:
        logger.warning("没有近期文章，使用全部文章")
        recent_articles = all_articles

    # Step 3: 选取 Top N 篇
    selected = recent_articles[:TOTAL_ARTICLES_FOR_AI]
    logger.info(f"Step 3: 选取 {len(selected)} 篇送给 AI")

    # Step 4: AI 生成日报
    logger.info("Step 4: AI 生成日报...")
    report = generate_daily_report(selected)

    # Step 5: 推送到微信
    logger.info("Step 5: 推送到微信...")
    success = send_daily_report(report, today)

    if success:
        logger.info("===== 日报推送成功 ✓ =====")
    else:
        logger.error("===== 日报推送失败 ✗ =====")
        # 失败时保存本地备份
        backup_path = f"report_backup_{datetime.now().strftime('%Y%m%d')}.md"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"日报已保存到本地备份: {backup_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
