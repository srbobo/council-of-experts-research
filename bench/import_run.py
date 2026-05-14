"""Manual-import helper for runs captured outside the bench harness.

Use this for runs you executed in Claude.ai (or any other context) and want
to file alongside auto-captured bench/server runs for the eventual Phase 4
report. Writes the run as JSON under ``bench/runs/imported/`` in a schema
compatible with the bench harness's other outputs.

Usage:
  python -m bench.import_run --case <case_id> --mode <mode> --input <md-file>
  cat run.md | python -m bench.import_run --case <case_id> --mode <mode>

Either ``--input`` or stdin works. ``--mode`` is free-form so manual captures
can use any label (e.g. ``opus-council``, ``opus-monolith``, or your own).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reach into examples to validate the case id against the canonical list.
# A typo here would produce a file the future report builder can't slot into
# a case row, so we fail fast at import time.
from examples.test_cases import get_case


def main() -> int:
    """Parse CLI args, read the markdown, write the JSON. Returns an exit code."""
    parser = argparse.ArgumentParser(
        prog="bench.import_run",
        description="Save a manually-captured run to bench/runs/imported/.",
    )
    parser.add_argument(
        "--case", required=True,
        help="Test case id; must match an id in examples.test_cases.CASES",
    )
    parser.add_argument(
        "--mode", required=True,
        help="Mode label (e.g. opus-council, opus-monolith, opus-single)",
    )
    parser.add_argument(
        "--input", default=None,
        help="Path to a markdown file with the run output. Default: read stdin.",
    )
    parser.add_argument(
        "--from-audit-log", default=None,
        help=(
            "Path to an auto-saved orchestrator audit log (runs/<file>.json). "
            "When set, the importer embeds the full DeliberationResult (planner "
            "reasoning, per-seat input_messages and outputs, dispatched sub-"
            "questions, synthesis input bundle) into the imported run. Use this "
            "instead of --input for local-council and opus-council runs that "
            "have a corresponding audit log on disk."
        ),
    )
    parser.add_argument(
        "--model", default="claude-opus-4-7",
        help="Underlying model identifier. Default: claude-opus-4-7",
    )
    parser.add_argument(
        "--notes", default="",
        help="Optional free-text note about the run (e.g. how it was captured)",
    )
    args = parser.parse_args()

    # Validate the case id up front. ``get_case`` raises KeyError with a
    # listing of valid ids on miss.
    try:
        case = get_case(args.case)
    except KeyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    # Decide source: full audit log vs markdown paste-in. Exactly one path
    # must be active; if --from-audit-log is set we ignore --input and stdin.
    deliberation = None
    if args.from_audit_log:
        try:
            audit = json.loads(Path(args.from_audit_log).read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as e:
            print(f"error: audit log is not valid JSON: {e}", file=sys.stderr)
            return 2
        # The audit log is a DeliberationResult.to_dict(). Its final_output
        # is the synthesis text; embed the full deliberation as a sibling
        # field so the Phase 4 report builder can pull planner reasoning,
        # per-seat outputs, sub-questions, and timing without re-parsing.
        if "final_output" not in audit:
            print("error: audit log missing 'final_output' — wrong file?", file=sys.stderr)
            return 2
        content = audit["final_output"]
        # Drop synthesis-internal duplication: final_output is also in audit
        # but we keep it at the top level for query symmetry with Opus imports.
        deliberation = audit
    elif args.input:
        try:
            content = Path(args.input).read_text(encoding="utf-8")
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    else:
        content = sys.stdin.read()
    content = content.strip()
    if not content:
        print("error: empty content", file=sys.stderr)
        return 2

    captured = datetime.now(timezone.utc)
    # Compact filesystem-safe timestamp (no colons; ends with Z for clarity).
    stamp_for_file = captured.strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path("bench/runs/imported")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{stamp_for_file}__{case.id}__{args.mode}.json"

    payload = {
        # v2 schema includes optional `deliberation` field with full audit log.
        # v1 (paste-in only) and v2 (paste-in + deliberation) coexist; report
        # builder branches on `deliberation in payload`.
        "schema_version": 2 if deliberation else 1,
        "imported": True,
        "source": "audit_log_link" if deliberation else "manual_paste",
        "captured_at": captured.isoformat(),
        "case_id": case.id,
        "case_title": case.title,
        "mode": args.mode,
        "model": args.model,
        "final_output": content,
        "notes": args.notes,
    }
    if deliberation:
        payload["deliberation"] = deliberation
        payload["audit_log_path"] = args.from_audit_log
    # ensure_ascii=False so the JSON keeps human-readable accents, dashes,
    # and unicode characters from the markdown verbatim.
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
