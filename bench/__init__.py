"""Bench harness — A/B comparison of local council vs Claude Opus 4.7.

Status (2026-05-05): Sam set ``BENCH_BUDGET_USD=0``; the cost guard refuses
any Opus call until that's raised. Harness code can still be built and
unit-tested with mocked Opus responses.

Submodules
----------
cost_guard    : monthly + per-run budget enforcement (only safety-critical bench code)
runner        : top-level CLI for running cases through one or more modes
opus_single   : single-shot Opus mode
opus_council  : Opus playing all four council seats in sequence

The ``council`` package never imports from ``bench``; the reverse is fine.
"""
