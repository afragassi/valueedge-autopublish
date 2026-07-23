from __future__ import annotations
import json
import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from config.settings import CONFIG, FootballConfig, TennisConfig

log = logging.getLogger(__name__)

@dataclass
class Pick:
    sport: str
    match: str
    league: str
    kickoff: datetime
    market: str
    selection: str
    edge_pct: float
    fair_odds: float
    market_odds: float
    completeness: Optional[float] = None
    strength: Optional[float] = None
    n_matches: Optional[int] = None
    ht_model: bool = False
    fair_2_0: Optional[float] = None
    fair_2_1: Optional[float] = None
    fair_win_1set: Optional[float] = None

    @property
    def emoji(self): return "⚽" if self.sport == "football" else "🎾"

    @property
    def edge_label(self):
        e = self.edge_pct
        if e >= 25: return f"+{e:.1f}pp ⭐⭐⭐"
        elif e >= 18: return f"+{e:.1f}pp ⭐⭐"
        return f"+{e:.1f}pp ⭐"

    @property
    def strength_label(self):
        if self.strength is None: return ""
        return f"Strength {self.strength:.0f}/100" + (" 🔥" if self.strength >= 80 else "")

    @property
    def kickoff_str(self):
        return self.kickoff.strftime("%d %b %H:%M UTC")

    @property
    def value_pct(self):
        if self.fair_odds <= 0: return 0.0
        return round((1/self.fair_odds - 1/self.market_odds) * 100, 1)

def _passes_football_filter(p, cfg):
    if p.get("edge_pct", 0) < cfg.min_edge_pct: return False
    if p.get("n_matches", 99) > 0 and p.get("n_matches", 99) < cfg.min_matches: return False
    return True

def _passes_tennis_filter(p, cfg):
    if not cfg.atp_enabled and p.get("tour", "ATP") == "ATP": return False
    if not cfg.wta_enabled and p.get("tour", "") == "WTA": return False
    if p.get("edge_pct", 0) < cfg.edge_threshold: return False
    if p.get("completeness", 0) < cfg.min_completeness: return False
    if p.get("n_matches", 0) < cfg.min_matches: return False
    if p.get("strength", 0) < cfg.min_strength: return False
    if p.get("market", "") not in cfg.markets_allowed: return False
    if not cfg.first_set_enabled and "1st Set" in p.get("market", ""): return False
    if not cfg.under_enabled and "Under" in p.get("selection", ""): return False
    return True

def load_picks(path=None):
    source = Path(path or CONFIG.model_output_path)
    if not source.exists():
        log.warning(f"Model output not found at {source}")
        return []
    raw = []
    if source.suffix == ".json":
        with open(source) as f: raw = json.load(f)
    elif source.suffix == ".csv":
        with open(source) as f: raw = list(csv.DictReader(f))
    else:
        log.error(f"Unsupported format: {source.suffix}")
        return []
    picks = []
    for r in raw:
        sport = r.get("sport", "").lower()
        try:
            kickoff = datetime.fromisoformat(r["date"].replace("Z", "+00:00"))
        except:
            kickoff = datetime.now(timezone.utc)
        if sport == "football":
            if not _passes_football_filter(r, CONFIG.football): continue
        elif sport == "tennis":
            if not _passes_tennis_filter(r, CONFIG.tennis): continue
        else:
            continue
        picks.append(Pick(
            sport=sport, match=r.get("match",""), league=r.get("league",""),
            kickoff=kickoff, market=r.get("market",""), selection=r.get("selection",""),
            edge_pct=float(r.get("edge_pct",0)), fair_odds=float(r.get("fair_odds",0)),
            market_odds=float(r.get("market_odds",0)),
            completeness=float(r["completeness"]) if "completeness" in r else None,
            strength=float(r["strength"]) if "strength" in r else None,
            n_matches=int(r["n_matches"]) if "n_matches" in r else None,
            ht_model=bool(r.get("ht_model",False)),
            fair_2_0=float(r["fair_2_0"]) if r.get("fair_2_0") is not None else None,
            fair_2_1=float(r["fair_2_1"]) if r.get("fair_2_1") is not None else None,
            fair_win_1set=float(r["fair_win_1set"]) if r.get("fair_win_1set") is not None else None,
        ))
    picks.sort(key=lambda p: p.edge_pct, reverse=True)
    log.info(f"Loaded {len(picks)} qualifying picks")
    return picks
