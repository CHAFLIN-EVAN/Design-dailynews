"""
设计日报 - 微信推送模块
通过 PushPlus 服务推送到微信
"""

import logging

import requests

from config import PUSHPLUS_TOKEN, PUSH_CHANNEL, PUSH_TEMPLATE

logger = logging.getLogger(__name__)

PUSHPLUS_API = "https://www.pushplus.plus/send"


def push_to_wechat(title: str, content: str) -> bool:
    """
    推送消息到微信

    Args:
        title: 消息标题
        content: 消息内容（HTML 格式）

    Returns:
        bool: 是否推送成功
    """
    if not PUSHPLUS_TOKEN or PUSHPLUS_TOKEN == "your_pushplus_token_here":
        logger.error("PUSHPLUS_TOKEN 未配置，请在 .env 文件中设置")
        return False

    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": PUSH_TEMPLATE,
        "channel": PUSH_CHANNEL,
    }

    try:
        resp = requests.post(
            PUSHPLUS_API,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("code") == 200:
            logger.info(f"推送成功: {title}")
            return True
        else:
            logger.error(f"推送失败: {result.get('msg', '未知错误')}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"推送请求失败: {e}")
        return False
    except Exception as e:
        logger.error(f"推送异常: {e}")
        return False


def send_daily_report(report: str, date_str: str = "") -> bool:
    """
    发送设计日报到微信

    Args:
        report: HTML 格式的日报内容
        date_str: 日期字符串（用于标题），如 "2026年08月18日"

    Returns:
        bool: 是否发送成功
    """
    if not date_str:
        from datetime import datetime
        date_str = datetime.now().strftime("%Y年%m月%d日")

    title = f"📰 Design Daily | {date_str}"

    return push_to_wechat(title, report)
