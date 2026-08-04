"""PROVENANCE — measurement and audit harness for multi-seat LLM pipelines.

See docs/HARNESS_DESIGN.md. Not an orchestrator: wraps one.
"""
from .lexicon import Lexicon, DEFAULT, FAMILIES
from .audit import ProvenanceReport, audit, MIN_OUTPUT_CHARS
from .path import PathRecord, assert_path
from .gate import GateRecord, gate, feedback_for, annotation_for

__all__ = ["Lexicon", "DEFAULT", "FAMILIES", "ProvenanceReport", "audit",
           "MIN_OUTPUT_CHARS", "PathRecord", "assert_path", "GateRecord",
           "gate", "feedback_for", "annotation_for"]
