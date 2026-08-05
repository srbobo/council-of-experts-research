"""Command line: `gst measure`, `gst selftest`, `gst preregister`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .adapters import FieldMap, from_jsonl
from .card import measure_all
from .instruments import EPISTEMIC_QUALIFICATION, SOURCE_ATTRIBUTION, RegexInstrument

_CLASSES = {"epistemic": EPISTEMIC_QUALIFICATION, "attribution": SOURCE_ATTRIBUTION}


def _instrument(args) -> RegexInstrument:
    if args.lexicon:
        fams = json.loads(Path(args.lexicon).read_text())
        return RegexInstrument(fams, name=Path(args.lexicon).stem)
    return RegexInstrument(_CLASSES[args.property_class], name=args.property_class)


def cmd_measure(args) -> int:
    fmap = FieldMap(upstream=args.upstream, output=args.output,
                    prompt_id=args.prompt_id, run_id=args.run_id,
                    writer_prompt=args.writer_prompt, condition=args.condition)
    records = from_jsonl(args.runs, fmap)
    if not records:
        print(f"no records read from {args.runs}", file=sys.stderr)
        return 1
    card = measure_all(records, system=args.system, instrument=_instrument(args))
    if args.json:
        print(card.to_json())
    else:
        print(card.render())
        print("\nINDICATED INTERVENTIONS")
        for line in card.recommendations(white_box=args.white_box,
                                         can_train=args.can_train,
                                         has_rl_infra=args.rl_infra):
            print(f"  - {line}")
    if args.out:
        Path(args.out).write_text(card.to_json())
        print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


def cmd_selftest(args) -> int:
    """Reproduce the originating program's parameters from its own ledger."""
    from .adapters.coe import from_ledger
    ledger = Path(args.ledger)
    if not ledger.is_dir():
        print(f"ledger directory not found: {ledger}", file=sys.stderr)
        return 1
    records = from_ledger(ledger)
    card = measure_all(records, system="council-of-experts (reference)")
    print(card.render())
    sh = card.shrinkage
    ok = bool(sh and sh.identifiable and 0.25 <= sh.w <= 0.55 and 0.35 <= sh.c <= 0.70)
    print("\nSELFTEST:", "PASS" if ok else "FAIL",
          "-- reference system falls in the published shrinkage range"
          if ok else "-- parameters outside the published range; investigate before "
                     "trusting this install")
    return 0 if ok else 1


def cmd_preregister(args) -> int:
    tpl = Path(__file__).parent / "templates" / "PREREGISTRATION.md"
    text = tpl.read_text().replace("{{SYSTEM}}", args.system)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="gst", description=__doc__)
    p.add_argument("--version", action="version", version=f"gst {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("measure", help="estimate parameters from a JSONL run log")
    m.add_argument("runs", help="JSONL file, one run per line")
    m.add_argument("--system", default="unnamed", help="name for the card")
    m.add_argument("--upstream", default="upstream", help="field path to upstream texts")
    m.add_argument("--output", default="output", help="field path to writer output")
    m.add_argument("--prompt-id", default="prompt_id", dest="prompt_id")
    m.add_argument("--run-id", default=None, dest="run_id")
    m.add_argument("--writer-prompt", default=None, dest="writer_prompt")
    m.add_argument("--condition", default=None)
    m.add_argument("--property-class", default="epistemic", choices=sorted(_CLASSES),
                   dest="property_class")
    m.add_argument("--lexicon", default=None, help="JSON file: {family: [regex, ...]}")
    m.add_argument("--json", action="store_true", help="emit the card as JSON")
    m.add_argument("--out", default=None, help="also write the card JSON here")
    m.add_argument("--white-box", action="store_true", dest="white_box")
    m.add_argument("--can-train", action="store_true", dest="can_train")
    m.add_argument("--rl-infra", action="store_true", dest="rl_infra")
    m.set_defaults(func=cmd_measure)

    s = sub.add_parser("selftest", help="reproduce reference parameters from a ledger")
    s.add_argument("ledger", help="directory of reference ledger JSON files")
    s.set_defaults(func=cmd_selftest)

    r = sub.add_parser("preregister", help="print a pre-registration template")
    r.add_argument("--system", default="{{SYSTEM}}")
    r.add_argument("--out", default=None)
    r.set_defaults(func=cmd_preregister)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
