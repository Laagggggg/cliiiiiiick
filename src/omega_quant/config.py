from dataclasses import dataclass, field


@dataclass
class Config:
    asset_universe: list[str] = field(default_factory=lambda: ["SPY"])
    timeframe: str = "1h"
    higher_timeframe: str = "1d"
    lower_timeframe: str = "15m"
    capital: float = 2000
    max_position_pct: float = 0.20
    max_total_exposure: float = 1.0
    max_portfolio_heat: float = 0.06
    per_trade_risk_pct: float = 0.01
    daily_loss_limit_pct: float = 0.02
    max_drawdown_pct: float = 0.15
    hurst_window: int = 252
    hurst_trend_thresh: float = 0.55
    hurst_revert_thresh: float = 0.45
    wf_min_efficiency: float = 0.50
    wf_min_pass_rate: float = 0.70
    min_partial_fill_pct: float = 0.5
    mae_min_sample: int = 50
    mae_percentile: int = 80
    entry_base_trending: float = 0.45
    entry_base_ranging: float = 0.50
    exit_threshold: float = 0.15
