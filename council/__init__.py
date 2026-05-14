"""Council of Experts — multi-agent local PoC.

Submodules
----------
cabinet      : typed model definitions (Lead + 3 industry seats)
models       : Ollama HTTP client wrapper (single ``chat()`` function)
prompts      : Lead's planner + synthesis prompts; per-seat system prompts
orchestrator : 3-phase deliberation loop (plan -> consult -> synthesize)
thermal      : thermal-aware inter-agent pause policy for fanless M-series

The council module never imports from ``bench``; the reverse is fine.

See IMPLEMENTATION_PLAN.md at the repo root for the full plan.
"""
