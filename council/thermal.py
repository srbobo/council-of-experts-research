"""Thermal-aware execution policy for fanless Apple Silicon.

The MacBook Air M5 has no active cooling. Sustained inference on Phi-4 14B
plus an 8B industry agent will eventually trigger Metal throttling — which
is silent (no error, no log) and roughly halves throughput. This module:

  1. Reads ``COUNCIL_AGENT_PAUSE_SECONDS`` (default 5s) and inserts that
     pause between sequential agent calls.
  2. Optionally polls thermal pressure via ``pmset -g thermlog`` and
     lengthens the pause when state is amber/red (Phase 1.4).

The public API is fixed so the orchestrator can use it today via the no-op
default. Phase 1.4 fills in the pmset polling.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass


@dataclass
class ThermalGuard:
    """Inserts pauses between agent calls; stretches them under thermal pressure."""

    base_pause_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "ThermalGuard":
        """Construct from the ``COUNCIL_AGENT_PAUSE_SECONDS`` env var."""
        return cls(base_pause_seconds=float(os.getenv("COUNCIL_AGENT_PAUSE_SECONDS", "5")))

    async def between_agents(self) -> None:
        """Await the configured pause; longer under thermal pressure (Phase 1.4)."""
        # Phase 1.4: read `pmset -g thermlog` (or sysctl machdep.xcpm.cpu_thermal_level)
        # and extend pause when state is amber/red. For now, a fixed sleep.
        await asyncio.sleep(self.base_pause_seconds)
