from dotenv import load_dotenv
load_dotenv()

import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FootballConfig:
    min_edge_pct: float = float(os.getenv("FB_MIN_EDGE_PCT", "10"))
    min_matches: int = int(os.getenv("FB_MIN_MATCHES", "10"))
    ht_model_enabled: bool = os.getenv("FB_HT_MODEL", "true").lower() == "true"

@dataclass
class TennisConfig:
    edge_threshold: float = float(os.getenv("TN_EDGE_THRESHOLD", "20"))
    min_completeness: float = float(os.getenv("TN_MIN_COMP", "70"))
    min_matches: int = int(os.getenv("TN_MIN_N", "10"))
    min_strength: float = float(os.getenv("TN_MIN_STRENGTH", "65"))
    atp_enabled: bool = True
    wta_enabled: bool = False
    first_set_enabled: bool = False
    under_enabled: bool = False
    tours_allowed: list = field(default_factory=lambda: ["ATP"])
    markets_allowed: list = field(default_factory=lambda: ["Total Games Over"])

@dataclass
class TwitterConfig:
    api_key: str = os.getenv("TWITTER_API_KEY", "")
    api_secret: str = os.getenv("TWITTER_API_SECRET", "")
    access_token: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    access_secret: str = os.getenv("TWITTER_ACCESS_SECRET", "")
    bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    max_football_posts: int = int(os.getenv("TWITTER_MAX_FB_POSTS", "2"))
    max_tennis_posts: int = int(os.getenv("TWITTER_MAX_TN_POSTS", "2"))
    football_post_hour: int = int(os.getenv("TWITTER_FB_HOUR", "9"))
    tennis_post_hour: int = int(os.getenv("TWITTER_TN_HOUR", "10"))

@dataclass
class TelegramConfig:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    free_channel_id: str = os.getenv("TELEGRAM_FREE_CHANNEL_ID", "")
    paid_channel_id: str = os.getenv("TELEGRAM_PAID_CHANNEL_ID", "")

@dataclass
class SubstackConfig:
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_pass: str = os.getenv("SMTP_PASS", "")
    substack_email: str = os.getenv("SUBSTACK_EMAIL", "")
    from_email: str = os.getenv("FROM_EMAIL", "valueedgebetting@gmail.com")
    weekly_day: int = int(os.getenv("SUBSTACK_WEEKLY_DAY", "0"))
    weekly_hour: int = int(os.getenv("SUBSTACK_WEEKLY_HOUR", "8"))

@dataclass
class AppConfig:
    football: FootballConfig = field(default_factory=FootballConfig)
    tennis: TennisConfig = field(default_factory=TennisConfig)
    twitter: TwitterConfig = field(default_factory=TwitterConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    substack: SubstackConfig = field(default_factory=SubstackConfig)
    model_output_path: str = os.getenv("MODEL_OUTPUT_PATH", "./output/picks.json")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    dry_run: bool = os.getenv("DRY_RUN", "false").lower() == "true"

CONFIG = AppConfig()
