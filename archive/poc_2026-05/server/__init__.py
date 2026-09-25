"""FastAPI server wrapping the council and bench harness for the web UI.

Submodules
----------
runs    : in-memory ``RunManager`` (asyncio task tracking + per-run event queue)
app     : FastAPI app, endpoints, static-file mount

The server consumes the orchestrator's existing ``on_phase(stage, detail)``
callback hook to feed live progress into per-run ``asyncio.Queue`` instances,
which the SSE endpoint drains. No changes to ``council/`` are required.

Run via ``python -m server`` (binds to localhost:8000) or via the ``coe-server``
console script once the project is installed.
"""
