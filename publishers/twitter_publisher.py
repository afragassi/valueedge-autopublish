import logging
import time
from datetime import date
from typing import Optional
import tweepy
from config.settings import CONFIG
from core.picks import Pick

log = logging.getLogger(__name__)

AFFILIATE_LINK = "https://t.me/ValueEdgeFreePicks"
PAID_TG_URL = "https://t.me/ValueEdgeFree"

def _stars(edge):
    if edge >= 25: return "⭐⭐⭐"
    if edge >= 18: return "⭐⭐"
    return "⭐"

def _football_thread(pick):
    today = date.today().strftime("%d %b")
    ht = " [HT MODEL]" if pick.ht_model else ""
    t1 = f"⚽ VALUE BET — {today}{ht}\n\n🏆 {pick.league}\n🕐 {pick.kickoff_str}\n📌 {pick.match}\n\n✅ BET: {pick.market} → {pick.selection}"
    t2 = f"📊 MODEL BREAKDOWN\n\nEdge: {pick.edge_label}\nFair odds: {pick.fair_odds:.2f}\nMarket odds: {pick.market_odds:.2f}\nValue: +{pick.value_pct:.1f}%\n\nStake: 1 unit (flat)"
    t3 = f"⚠️ Model output only — bet responsibly.\n\nFull picks → paid channel in bio\nBest odds: {AFFILIATE_LINK}\n\n#ValueBetting #SportsBetting #{pick.league.replace(' ','')}"
    return [t1, t2, t3]

def _tennis_thread(pick):
    today = date.today().strftime("%d %b")
    t1 = f"🎾 VALUE BET — {today}\n\n🏆 {pick.league}\n🕐 {pick.kickoff_str}\n📌 {pick.match}\n\n✅ BET: {pick.market} → {pick.selection}"
    t2 = f"📊 MODEL BREAKDOWN\n\nEdge: {pick.edge_label}\nFair odds: {pick.fair_odds:.2f}\nMarket odds: {pick.market_odds:.2f}\nValue: +{pick.value_pct:.1f}%\n{pick.strength_label}\nCompleteness: {pick.completeness:.0f}% | n={pick.n_matches}"
    tweets = [t1, t2]
    if pick.fair_2_0 or pick.fair_2_1 or pick.fair_win_1set:
        lines = ["📐 SET MARKET FAIR PRICES"]
        if pick.fair_2_0: lines.append(f"  2-0: {pick.fair_2_0:.2f}")
        if pick.fair_2_1: lines.append(f"  2-1: {pick.fair_2_1:.2f}")
        if pick.fair_win_1set: lines.append(f"  Win 1+ set: {pick.fair_win_1set:.2f}")
        tweets.append("\n".join(lines))
    tweets.append(f"⚠️ Model output only — bet responsibly.\n\nFull picks → paid channel in bio\nBest odds: {AFFILIATE_LINK}\n\n#TennisBetting #ValueBetting #ATP")
    return tweets

def _get_client():
    cfg = CONFIG.twitter
    if not all([cfg.api_key, cfg.api_secret, cfg.access_token, cfg.access_secret]):
        log.error("Twitter credentials missing")
        return None
    return tweepy.Client(
        consumer_key=cfg.api_key,
        consumer_secret=cfg.api_secret,
        access_token=cfg.access_token,
        access_token_secret=cfg.access_secret,
    )

def post_pick_thread(pick, dry_run=False):
    tweets = _football_thread(pick) if pick.sport == "football" else _tennis_thread(pick)
    if dry_run or CONFIG.dry_run:
        log.info(f"[DRY RUN] {len(tweets)}-tweet thread for: {pick.match}")
        for i, t in enumerate(tweets, 1):
            log.info(f"  Tweet {i}:\n{t}\n")
        return True
    client = _get_client()
    if not client: return False
    try:
        reply_to_id = None
        for tweet_text in tweets:
            if reply_to_id:
                resp = client.create_tweet(text=tweet_text, in_reply_to_tweet_id=reply_to_id)
            else:
                resp = client.create_tweet(text=tweet_text)
            reply_to_id = resp.data["id"]
            time.sleep(1.5)
        log.info(f"✅ Posted thread: {pick.match}")
        return True
    except Exception as e:
        log.error(f"Twitter error: {e}")
        return False

def post_daily_picks(football_picks, tennis_picks):
    cfg = CONFIG.twitter
    results = {"football": 0, "tennis": 0, "errors": 0}
    delay = 0 if CONFIG.dry_run else 30
    for pick in football_picks[:cfg.max_football_posts]:
        ok = post_pick_thread(pick)
        results["football" if ok else "errors"] += 1
        time.sleep(delay)
    for pick in tennis_picks[:cfg.max_tennis_posts]:
        ok = post_pick_thread(pick)
        results["tennis" if ok else "errors"] += 1
        time.sleep(delay)
    return results
