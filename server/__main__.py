"""Run the FastAPI server: ``python -m server`` (binds to localhost:8000).

Localhost-only by design — the council/bench harness is not multi-tenant and
not auth-aware. Anyone with access to localhost:8000 can run deliberations
and (when the bench cap is raised) spend Opus credits.
"""

from __future__ import annotations

import uvicorn


def main() -> int:
    """Start the server on 127.0.0.1:8000 with reload disabled."""
    # uvicorn — ASGI server. host="127.0.0.1" prevents accidental LAN exposure.
    # reload=False so a long-running deliberation isn't killed by a file save.
    uvicorn.run(
        "server.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
