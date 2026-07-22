import asyncio
import logging
from datetime import date
from telegram import Bot
from telegram.constants import ParseMode
from config.settings import CONFIG
from core.picks import Pick

log = logging.getLogger(__name__)

AFFILIATE_LINK = "https://whop.com/value-edge-972e/valueedge-signals"
PAID_TG_URL = "https://whop.com/value-edge-972e/valueedge-signals"

def _stars(edge):
    if edge >= 25: return "⭐⭐⭐"
    if edge >= 18: return "⭐⭐"
    return "⭐"

def _football_free(pick):
    return (
        f"⚽ *FREE PICK — {date.today().strftime('%d %b')}*\n\n"
        f"🏆 {pick.league}\n📌 {pick.match}\n🕐 {pick.kickoff_str}\n\n"
        f"✅ *{pick.market} → {pick.selection}*\n"
        f"📈 Edge: *{pick.edge_pct:.1f}pp*\n\n"
        f"_Full picks in paid channel_ 👇\n{PAID_TG_URL}\n\n"
        f"Best odds: {AFFILIATE_LINK}"
    )

def _tennis_free(pick):
    return (
        f"🎾 *FREE PICK — {date.today().strftime('%d %b')}*\n\n"
        f"🏆 {pick.league}\n📌 {pick.match}\n🕐 {pick.kickoff_str}\n\n"
        f"✅ *{pick.market} → {pick.selection}*\n"
        f"📈 Edge: *{pick.edge_pct:.1f}pp*\n\n"
        f"_Full picks in paid channel_ 👇\n{PAID_TG_URL}\n\n"
        f"Best odds: {AFFILIATE_LINK}"
    )

def _football_paid(pick):
    ht = "🔶 *HT MODEL BET*\n\n" if pick.ht_model else ""
    return (
        f"⚽ *FOOTBALL VALUE BET*\n\n{ht}"
        f"🏆 {pick.league}\n📌 {pick.match}\n🕐 {pick.kickoff_str}\n\n"
        f"✅ *{pick.market} → {pick.selection}*\n\n"
        f"📊 Edge: `{pick.edge_pct:.1f}pp` {_stars(pick.edge_pct)}\n"
        f"Fair: `{pick.fair_odds:.2f}` | Market: `{pick.market_odds:.2f}`\n"
        f"Value: `+{pick.value_pct:.1f}%`\n\n"
        f"Stake: 1 unit\n⚠️ _Model output only_"
    )

def _tennis_paid(pick):
    set_section = ""
    if pick.fair_2_0 or pick.fair_2_1 or pick.fair_win_1set:
        lines = ["\n📐 *Set Market Fair Prices*"]
        if pick.fair_2_0: lines.append(f"2-0: `{pick.fair_2_0:.2f}`")
        if pick.fair_2_1: lines.append(f"2-1: `{pick.fair_2_1:.2f}`")
        if pick.fair_win_1set: lines.append(f"Win 1+ set: `{pick.fair_win_1set:.2f}`")
        set_section = "\n".join(lines)
    return (
        f"🎾 *TENNIS VALUE BET*\n\n"
        f"🏆 {pick.league}\n📌 {pick.match}\n🕐 {pick.kickoff_str}\n\n"
        f"✅ *{pick.market} → {pick.selection}*\n\n"
        f"📊 Edge: `{pick.edge_pct:.1f}pp` {_stars(pick.edge_pct)}\n"
        f"Fair: `{pick.fair_odds:.2f}` | Market: `{pick.market_odds:.2f}`\n"
        f"Value: `+{pick.value_pct:.1f}%`\n"
        f"Strength: `{pick.strength:.0f}/100` | n=`{pick.n_matches}`"
        f"{set_section}\n\n"
        f"Stake: 1 unit\n⚠️ _Model output only_"
    )

async def _send(bot, chat_id, text):
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

async def _post_all(football_picks, tennis_picks, dry_run=False):
    results = {"free": 0, "paid": 0, "errors": 0}
    cfg = CONFIG.telegram
    if not cfg.bot_token:
        log.error("TELEGRAM_BOT_TOKEN missing")
        return results
    bot = Bot(token=cfg.bot_token)
    all_picks = football_picks + tennis_picks
    free_picks = (football_picks[:1] if football_picks else []) + (tennis_picks[:1] if tennis_picks else [])
    for pick in free_picks:
        msg = _football_free(pick) if pick.sport == "football" else _tennis_free(pick)
        if dry_run or CONFIG.dry_run:
            log.info(f"[DRY RUN] FREE: {pick.match}\n{msg}\n")
            results["free"] += 1
        elif cfg.free_channel_id:
            try:
                await _send(bot, cfg.free_channel_id, msg)
                results["free"] += 1
            except Exception as e:
                log.error(f"Telegram free error: {e}")
                results["errors"] += 1
    for pick in all_picks:
        msg = _football_paid(pick) if pick.sport == "football" else _tennis_paid(pick)
        if dry_run or CONFIG.dry_run:
            log.info(f"[DRY RUN] PAID: {pick.match}\n{msg}\n")
            results["paid"] += 1
        elif cfg.paid_channel_id:
            try:
                await _send(bot, cfg.paid_channel_id, msg)
                results["paid"] += 1
                await asyncio.sleep(2)
            except Exception as e:
                log.error(f"Telegram paid error: {e}")
                results["errors"] += 1
    return results

def post_to_telegram(football_picks, tennis_picks):
    return asyncio.run(_post_all(football_picks, tennis_picks))
