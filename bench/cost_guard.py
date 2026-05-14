"""Budget guardrail for the Opus benchmark harness.

Two principles:

  1. Always estimate the next call's cost BEFORE making it, and refuse the
     call if running_total + projected_cost would exceed the cap.
  2. Persist the running total to disk so a crash mid-run doesn't reset
     the counter — preventing a "fresh start" from accidentally doubling
     the spend for the same logical run.

Pricing constants reflect Anthropic's published Opus 4.7 rates as of
2026-05; consult https://www.anthropic.com/pricing before raising the cap.

This module is the only safety-critical code in ``bench/``; it ships fully
implemented even while the rest of the harness is stubbed, so the guardrail
is correct from day one.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

# --- Pricing constants -------------------------------------------------------
# Opus 4.7 USD per 1 million tokens. Source: Anthropic pricing page (verified
# against the claude-api skill's cached models table 2026-04-15).
# Earlier draft used $15/$75 — that was a wrong guess; corrected here.
# Update when pricing changes.
OPUS_INPUT_USD_PER_MTOK = 5.00          # standard, uncached input tokens
OPUS_INPUT_CACHED_USD_PER_MTOK = 0.50   # cached input read (10% of standard)
OPUS_OUTPUT_USD_PER_MTOK = 25.00        # output tokens


class BudgetExceeded(Exception):
    """Raised when a projected Opus call would push spend past the cap."""


@dataclass
class CallCost:
    """Estimated cost breakdown for a single Opus call."""

    input_tokens: int
    cached_input_tokens: int  # subset of input_tokens that were a cache hit
    output_tokens: int

    @property
    def usd(self) -> float:
        """Rough cost in USD given the published Opus 4.7 rates."""
        # MTok = 1_000_000 tokens. Convert per-token to per-MTok pricing.
        uncached = self.input_tokens - self.cached_input_tokens
        return (
            uncached / 1_000_000 * OPUS_INPUT_USD_PER_MTOK
            + self.cached_input_tokens / 1_000_000 * OPUS_INPUT_CACHED_USD_PER_MTOK
            + self.output_tokens / 1_000_000 * OPUS_OUTPUT_USD_PER_MTOK
        )


class CostGuard:
    """Tracks running spend in a JSON ledger and refuses calls past the cap.

    The cap is read from ``BENCH_BUDGET_USD`` at construction time so changes
    require restart — intentional, so an accidental mid-run cap raise is harder.
    """

    def __init__(self, ledger_path: Path | None = None) -> None:
        self.cap_usd = float(os.getenv("BENCH_BUDGET_USD", "0"))
        self.ledger_path = ledger_path or Path("bench/runs/cost.json")
        self.spent_usd = self._load_ledger()

    def _load_ledger(self) -> float:
        """Read the cumulative spent total from disk; default to 0.0 if no ledger."""
        if not self.ledger_path.exists():
            return 0.0
        with self.ledger_path.open() as f:
            return float(json.load(f).get("spent_usd", 0.0))

    def _save_ledger(self) -> None:
        """Persist the cumulative spent total. Called after every successful call."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("w") as f:
            json.dump({"spent_usd": self.spent_usd, "cap_usd": self.cap_usd}, f, indent=2)

    def check(self, projected: CallCost) -> None:
        """Raise ``BudgetExceeded`` if making this call would exceed the cap."""
        if self.spent_usd + projected.usd > self.cap_usd:
            raise BudgetExceeded(
                f"Cap=${self.cap_usd:.2f}, spent=${self.spent_usd:.4f}, "
                f"this call would add ${projected.usd:.4f} → "
                f"projected total ${self.spent_usd + projected.usd:.4f}. Refusing."
            )

    def record(self, actual: CallCost) -> None:
        """Add an actual (post-call) cost to the running total and persist."""
        self.spent_usd += actual.usd
        self._save_ledger()
