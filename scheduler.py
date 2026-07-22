import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone

import schedule

from config.settings import CONFIG
from core.picks import Pick, load_picks
from publishers.twitter_publisher import post_daily_picks
from publishers.telegram_publisher import post_to_telegram
from publishers.email_publisher import send_weekly_digest

logging.basicConfig(
    level=getattr(logging, CONFIG.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("autopublish.log"),
    ],
)
log = logging.getLogger("scheduler")

def _split_picks():
    picks = load_picks()
    fb = [p for p in picks if p.sport == "football"]
    tn = [p for p in picks if p.sport == "tennis"]
    log.info(f"Picks: {len(fb)} football, {len(tn)} tennis")
    return fb, tn

def job_twitter():
    log.info("▶ Twitter job")
    fb, tn = _split_picks()
    results = post_daily_picks(fb, tn)
    log.info(f"Twitter: {results}")

def job_telegram():
    log.info("▶ Telegram job")
    fb, tn = _split_picks()
    results = post_to_telegram(fb, tn)
    log.info(f"Telegram: {results}")

def job_weekly_digest():
    log.info("▶ Weekly digest")
    fb, tn = _split_picks()
    ok = send_weekly_digest(fb, tn)
    log.info(f"Digest: {'sent' if ok else 'FAILED'}")

def run_all_now():
    log.info("🔥 Running all jobs now")
    fb, tn = _split_picks()
    log.info("--- TWITTER ---")
    post_daily_picks(fb, tn)
    log.info("--- TELEGRAM ---")
    post_to_telegram(fb, tn)
    log.info("--- EMAIL ---")
    send_weekly_digest(fb, tn)
    log.info("✅ All done")

def setup_schedule():
    cfg_tw = CONFIG.twitter
    cfg_sb = CONFIG.substack
    schedule.every().day.at(f"{cfg_tw.football_post_hour:02d}:00").do(job_twitter)
    schedule.every().day.at(f"{cfg_tw.football_post_hour:02d}:30").do(job_telegram)
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    getattr(schedule.every(), days[cfg_sb.weekly_day]).at(f"{cfg_sb.weekly_hour:02d}:00").do(job_weekly_digest)
    log.info("Schedule set up ✅")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-now", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--twitter-only", action="store_true")
    parser.add_argument("--telegram-only", action="store_true")
    parser.add_argument("--email-only", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"
        CONFIG.dry_run = True
        log.info("🔵 DRY RUN mode")

    if args.run_now:
        if args.twitter_only: job_twitter()
        elif args.telegram_only: job_telegram()
        elif args.email_only: job_weekly_digest()
        else: run_all_now()
        return

    setup_schedule()
    log.info("🟢 Scheduler running. Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("Stopped.")

if __name__ == "__main__":
    main()
