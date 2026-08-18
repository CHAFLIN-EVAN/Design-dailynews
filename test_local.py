"""
设计日报 - 本地测试脚本
用于在没有 PushPlus token 的情况下测试抓取和 AI 生成
"""

import logging
import sys
from datetime import datetime

from fetcher import fetch_all_news, filter_recent
from ai_writer import generate_daily_report
from config import TOTAL_ARTICLES_FOR_AI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("design-daily-test")


def test_fetch():
    """测试新闻抓取"""
    logger.info("=" * 50)
    logger.info("测试新闻抓取")
    logger.info("=" * 50)

    articles = fetch_all_news()
    logger.info(f"总计获取 {len(articles)} 篇文章")

    # 按类别统计
    categories = {}
    for a in articles:
        categories[a.category] = categories.get(a.category, 0) + 1

    for cat, count in sorted(categories.items()):
        logger.info(f"  {cat}: {count} 篇")

    # 打印前 5 篇
    logger.info("\n前 5 篇文章预览:")
    for i, a in enumerate(articles[:5], 1):
        logger.info(f"  {i}. [{a.category}] {a.title} — {a.source}")

    return articles


def test_ai(articles):
    """测试 AI 生成（需要 API key）"""
    logger.info("=" * 50)
    logger.info("测试 AI 日报生成")
    logger.info("=" * 50)

    recent = filter_recent(articles, hours=72)
    selected = recent[:TOTAL_ARTICLES_FOR_AI]
    logger.info(f"选取 {len(selected)} 篇送给 AI")

    if not selected:
        logger.warning("没有文章可测试，跳过 AI 生成")
        return

    try:
        report = generate_daily_report(selected)
        logger.info(f"日报生成成功，长度: {len(report)} 字符")

        # 保存到本地
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"日报已保存到: {filename}")

        # 打印前 500 字符预览
        print("\n" + "=" * 50)
        print("日报预览（前 500 字符）:")
        print("=" * 50)
        print(report[:500])
        print("...\n")

    except Exception as e:
        logger.error(f"AI 生成失败: {e}")
        logger.info("请检查 AI_API_KEY 是否正确配置在 .env 文件中")


def test_push():
    """测试推送（需要 PushPlus token）"""
    logger.info("=" * 50)
    logger.info("测试微信推送")
    logger.info("=" * 50)

    from config import PUSHPLUS_TOKEN
    from pusher import push_to_wechat

    if not PUSHPLUS_TOKEN or PUSHPLUS_TOKEN == "your_pushplus_token_here":
        logger.warning("PUSHPLUS_TOKEN 未配置，跳过推送测试")
        return

    test_content = """# 测试推送

这是一条测试消息，如果你看到这条消息说明推送配置成功！

- 时间：""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
- 来源：Design Daily 本地测试
"""

    success = push_to_wechat("📰 测试推送", test_content)
    if success:
        logger.info("测试推送成功！请检查微信是否收到消息")
    else:
        logger.error("测试推送失败，请检查 token")


def main():
    logger.info("===== Design Daily 本地测试 =====\n")

    # 测试抓取
    articles = test_fetch()

    # 测试 AI
    if articles:
        test_ai(articles)

    # 测试推送
    test_push()

    logger.info("\n===== 测试完成 =====")


if __name__ == "__main__":
    main()
