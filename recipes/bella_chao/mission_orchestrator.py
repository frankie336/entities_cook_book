#!/usr/bin/env python3
# mission_orchestrator.py — Pluggable rule engine that decides go_mission

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Protocol, Tuple, Any, Optional
from datetime import datetime, timedelta


# --------------------------- Core types ---------------------------
@dataclass
class DecisionContext:
    # Market snapshot
    price: float
    anchor_price: float
    atr: float
    sigma_pct: float  # realized vol (as proportion, e.g., 0.003 = 0.3%)
    min_swing_pct: float
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    spread_bps_obs: Optional[float] = None

    # LLM and policy
    llm_signal: str = "hold"  # 'buy'|'sell'|'hold'
    now: datetime = field(default_factory=datetime.utcnow)
    last_go_time: Optional[datetime] = None
    cooldown_sec: int = 300

    # Risk / limits (extend as needed)
    risk_budget_bps: float = 10.0
    max_trades_per_hour: int = 12


@dataclass
class RuleOutcome:
    ok: bool
    name: str
    reason: str
    metrics: Dict[str, Any] = field(default_factory=dict)


class Rule(Protocol):
    name: str
    def evaluate(self, ctx: DecisionContext) -> RuleOutcome: ...


# --------------------------- Rules ---------------------------
class LLMSignalRule:
    name = "llm_signal"

    def evaluate(self, ctx: DecisionContext) -> RuleOutcome:
        ok = ctx.llm_signal in ("buy", "sell")
        return RuleOutcome(
            ok=ok,
            name=self.name,
            reason=("ok" if ok else f"llm_signal={ctx.llm_signal!r} not actionable"),
            metrics={"llm_signal": ctx.llm_signal},
        )


class CooldownRule:
    name = "cooldown"

    def evaluate(self, ctx: DecisionContext) -> RuleOutcome:
        if ctx.last_go_time is None:
            return RuleOutcome(True, self.name, "no prior go_mission")
        elapsed = (ctx.now - ctx.last_go_time).total_seconds()
        ok = elapsed >= ctx.cooldown_sec
        return RuleOutcome(
            ok=ok,
            name=self.name,
            reason=("ok" if ok else f"cooldown {elapsed:.0f}s < {ctx.cooldown_sec}s"),
            metrics={"elapsed_sec": elapsed},
        )


class DisplacementRule:
    name = "displacement"

    def evaluate(self, ctx: DecisionContext) -> RuleOutcome:
        if ctx.anchor_price <= 0:
            return RuleOutcome(False, self.name, "invalid anchor_price")
        disp = abs(ctx.price - ctx.anchor_price) / ctx.anchor_price
        ok = disp >= ctx.min_swing_pct
        return RuleOutcome(
            ok=ok,
            name=self.name,
            reason=(
                "ok" if ok else f"|Δ|={disp:.4%} < min_swing={ctx.min_swing_pct:.4%}"
            ),
            metrics={"displacement_pct": disp, "min_swing_pct": ctx.min_swing_pct},
        )


class TrendRule:
    name = "trend"

    def __init__(self, require: bool = False):
        self.require = require

    def evaluate(self, ctx: DecisionContext) -> RuleOutcome:
        if not self.require:
            return RuleOutcome(True, self.name, "disabled")
        if ctx.ema_fast is None or ctx.ema_slow is None:
            return RuleOutcome(False, self.name, "missing EMA values")
        if ctx.llm_signal == "buy":
            ok = ctx.ema_fast > ctx.ema_slow
        elif ctx.llm_signal == "sell":
            ok = ctx.ema_fast < ctx.ema_slow
        else:
            ok = False
        return RuleOutcome(
            ok=ok,
            name=self.name,
            reason=("ok" if ok else "EMA alignment failed"),
            metrics={"ema_fast": ctx.ema_fast, "ema_slow": ctx.ema_slow},
        )


class RiskBudgetRule:
    name = "risk_budget"

    def evaluate(self, ctx: DecisionContext) -> RuleOutcome:
        # Placeholder for real risk checks (daily loss limits, VaR, etc.)
        return RuleOutcome(True, self.name, "ok")


# --------------------------- Orchestrator ---------------------------
class MissionOrchestrator:
    """Aggregates rules and emits a single go/no-go plus explainability.

    Usage:
        rules = [LLMSignalRule(), CooldownRule(), DisplacementRule(), TrendRule(True)]
        orch = MissionOrchestrator(rules)
        go, outcomes, why = orch.decide(ctx)
    """

    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def decide(self, ctx: DecisionContext) -> Tuple[bool, List[RuleOutcome], str]:
        outcomes: List[RuleOutcome] = []
        for rule in self.rules:
            out = rule.evaluate(ctx)
            outcomes.append(out)
        go = all(o.ok for o in outcomes)
        # human‑readable reason string
        passed = ", ".join(o.name for o in outcomes if o.ok)
        failed = ", ".join(f"{o.name}({o.reason})" for o in outcomes if not o.ok)
        why = (
            f"passed: [{passed}]" + ("; failed: [" + failed + "]" if failed else "")
        )
        return go, outcomes, why


# --------------------------- Convenience factory ---------------------------
def default_orchestrator(require_trend: bool = False) -> MissionOrchestrator:
    rules: List[Rule] = [
        LLMSignalRule(),
        CooldownRule(),
        DisplacementRule(),
        TrendRule(require=require_trend),
        RiskBudgetRule(),
    ]
    return MissionOrchestrator(rules)


# --------------------------- Serialization helpers ---------------------------
def outcomes_to_log(outcomes: List[RuleOutcome]) -> Dict[str, Any]:
    """Flatten rule outcomes to a loggable dict (one level deep)."""
    flat: Dict[str, Any] = {}
    for o in outcomes:
        flat[f"{o.name}_ok"] = o.ok
        flat[f"{o.name}_reason"] = o.reason
        for k, v in (o.metrics or {}).items():
            flat[f"{o.name}_{k}"] = v
    return flat
