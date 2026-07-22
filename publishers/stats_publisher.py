"""
Stats Publisher
===============
Posts periodic performance updates to Telegram and X.
Called by scheduler weekly (Monday) and on-demand.
"""

import json
import logging
from datetime import date
from pathlib import Path

log = logging.getLogger(__name__)

STATS_PATH = Path("./output/stats.json")


def _stars_roi(roi: float) -> str:
    if roi >= 20: return "🔥🔥🔥"
    if roi >= 10: return "🔥🔥"
    if roi >= 0:  return "🔥"
    return "📉"


def build_stats_telegram(stats: dict) -> str:
    """Build a Telegram stats post."""
    today = date.today().strftime("%d %b %Y")
    fb = stats.get("football", {})
    tn = stats.get("tennis", {})
    al = stats.get("all", {})

    profit_sign = "+" if al.get("profit", 0) >= 0 else ""
    roi_sign = "+" if al.get("roi", 0) >= 0 else ""

    return (
        f"📊 *VALUEEDGE PERFORMANCE UPDATE*\n"
        f"_{today}_\n\n"

        f"*OVERALL*\n"
        f"Bets: `{al.get('bets', 0)}` | "
        f"W/L: `{al.get('wins', 0)}/{al.get('losses', 0)}`\n"
        f"Profit: `{profit_sign}{al.get('profit', 0):.2f}u` | "
        f"ROI: `{roi_sign}{al.get('roi', 0):.1f}%` {_stars_roi(al.get('roi', 0))}\n"
        f"Win rate: `{al.get('winrate', 0):.1f}%`\n\n"

        f"⚽ *FOOTBALL*\n"
        f"Bets: `{fb.get('bets', 0)}` | "
        f"W/L: `{fb.get('wins', 0)}/{fb.get('losses', 0)}`\n"
        f"Profit: `{'+'if fb.get('profit',0)>=0 else ''}{fb.get('profit', 0):.2f}u` | "
        f"ROI: `{'+'if fb.get('roi',0)>=0 else ''}{fb.get('roi', 0):.1f}%`\n\n"

        f"🎾 *TENNIS*\n"
        f"Bets: `{tn.get('bets', 0)}` | "
        f"W/L: `{tn.get('wins', 0)}/{tn.get('losses', 0)}`\n"
        f"Profit: `{'+'if tn.get('profit',0)>=0 else ''}{tn.get('profit', 0):.2f}u` | "
        f"ROI: `{'+'if tn.get('roi',0)>=0 else ''}{tn.get('roi', 0):.1f}%`\n\n"

        f"_All bets tracked. 1u flat staking._\n"
        f"_Model output only — bet responsibly_ ⚠️"
    )


def build_stats_twitter(stats: dict) -> list[str]:
    """Build a Twitter stats thread."""
    today = date.today().strftime("%d %b %Y")
    fb = stats.get("football", {})
    tn = stats.get("tennis", {})
    al = stats.get("all", {})

    profit_sign = "+" if al.get("profit", 0) >= 0 else ""
    roi_sign = "+" if al.get("roi", 0) >= 0 else ""

    t1 = (
        f"📊 VALUEEDGE MODEL — PERFORMANCE UPDATE\n"
        f"{today}\n\n"
        f"Overall: {al.get('bets', 0)} bets tracked\n"
        f"Profit: {profit_sign}{al.get('profit', 0):.2f}u\n"
        f"ROI: {roi_sign}{al.get('roi', 0):.1f}% {_stars_roi(al.get('roi', 0))}\n\n"
        f"Breakdown 👇"
    )

    t2 = (
        f"⚽ FOOTBALL\n"
        f"Bets: {fb.get('bets', 0)} | "
        f"W/L: {fb.get('wins', 0)}/{fb.get('losses', 0)}\n"
        f"Profit: {'+'if fb.get('profit',0)>=0 else ''}{fb.get('profit', 0):.2f}u | "
        f"ROI: {'+'if fb.get('roi',0)>=0 else ''}{fb.get('roi', 0):.1f}%\n\n"
        f"🎾 TENNIS\n"
        f"Bets: {tn.get('bets', 0)} | "
        f"W/L: {tn.get('wins', 0)}/{tn.get('losses', 0)}\n"
        f"Profit: {'+'if tn.get('profit',0)>=0 else ''}{tn.get('profit', 0):.2f}u | "
        f"ROI: {'+'if tn.get('roi',0)>=0 else ''}{tn.get('roi', 0):.1f}%"
    )

    t3 = (
        f"All picks timestamped before match.\n"
        f"1 unit flat staking throughout.\n"
        f"No cherry-picking — all bets recorded.\n\n"
        f"Follow for daily picks 👇\n"
        f"Full signals → t.me/ValueEdgeFreePicks\n\n"
        f"⚠️ Model output only. Bet responsibly.\n\n"
        f"#ValueBetting #BettingModel #SportsBetting"
    )

    return [t1, t2, t3]


async def post_stats_telegram(stats: dict, bot_token: str, channel_ids: list):
    """Post stats to Telegram channels."""
    try:
        from telegram import Bot
        from telegram.constants import ParseMode
        bot = Bot(token=bot_token)
        msg = build_stats_telegram(stats)
        for channel_id in channel_ids:
            await bot.send_message(
                chat_id=channel_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        log.info(f"✅ Stats posted to {len(channel_ids)} Telegram channels")
    except Exception as e:
        log.error(f"Stats Telegram error: {e}")


def post_stats_twitter(stats: dict, twitter_client):
    """Post stats thread to X."""
    import time
    tweets = build_stats_twitter(stats)
    try:
        reply_to_id = None
        for tweet_text in tweets:
            if reply_to_id:
                resp = twitter_client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=reply_to_id
                )
            else:
                resp = twitter_client.create_tweet(text=tweet_text)
            reply_to_id = resp.data["id"]
            time.sleep(1.5)
        log.info("✅ Stats thread posted to X")
    except Exception as e:
        log.error(f"Stats Twitter error: {e}")


def load_stats() -> dict:
    """Load stats from file."""
    if not STATS_PATH.exists():
        log.warning("No stats file found yet")
        return {}
    with open(STATS_PATH) as f:
        raw = json.load(f)

    def _roi(s):
        if s["units_staked"] == 0: return 0.0
        return round((s["units_returned"] - s["units_staked"]) / s["units_staked"] * 100, 1)

    def _profit(s):
        return round(s["units_returned"] - s["units_staked"], 2)

    def _winrate(s):
        if s["bets"] == 0: return 0.0
        return round(s["wins"] / s["bets"] * 100, 1)

    result = {}
    for sport in ["football", "tennis", "all"]:
        s = raw.get(sport, {})
        result[sport] = {
            "bets": s.get("bets", 0),
            "wins": s.get("wins", 0),
            "losses": s.get("losses", 0),
            "profit": _profit(s) if s.get("units_staked") else 0.0,
            "roi": _roi(s) if s.get("units_staked") else 0.0,
            "winrate": _winrate(s) if s.get("bets") else 0.0,
        }
    return result
