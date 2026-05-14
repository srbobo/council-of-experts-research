"""Module entry point so ``python -m bench`` works.

Delegates to ``bench.runner.main`` — keeping the actual CLI logic in
``runner.py`` and this file as a thin shim.
"""

from __future__ import annotations

from .runner import main

if __name__ == "__main__":
    raise SystemExit(main())
