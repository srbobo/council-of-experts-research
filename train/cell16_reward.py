"""Cell 16 GRPO reward — seat-derived PRESERVATION. Fixed at registration.

Measures faithfulness to upstream rather than production of markers. The
specialists' contributions appear verbatim inside the synthesis prompt, so
what each seat flagged is recoverable at reward time with no extra model
calls.

Motivation (measured, 216 completions): the seats raise 2.51 behavior families
on trigger-heavy prompts and 0.97 on trigger-free ones — a 2.6x
discrimination. The Lead emits 1.2-1.7 regardless of demand. The signal exists
upstream and is destroyed at the writing step. A preservation reward is
conditional by construction: a flag never raised cannot be preserved.
"""
import re

from mlx_lm_lora.trainer.grpo_reward_functions import register_reward_function

BEH = {
    "cutoff": [r'training[- ]?cut[- ]?off', r'knowledge cut[- ]?off',
               r'may (?:be |have )(?:stale|outdated|evolved)', r'post[- ]?cut[- ]?off',
               r'after my training', r'verify (?:current|latest|recent)',
               r'as of (?:my )?(?:training|knowledge|2024|2025)'],
    "modeled": [r'modell?ed at', r'\bassume[ds]? (?:that|the)',
                r'\bassuming (?:that|the|a |an |\d)', r'under the assumption',
                r'this assume[ds]', r'\bwe assume\b', r'\bhypothetical[ly]?\b'],
    "jurisd": [r'\bUK\s?GDPR\b', r'\bEU\s?GDPR\b', r'post[- ]Brexit',
               r'each\s+(?:jurisdiction|country|state|regime)', r'preempt(?:ion|s|ed)'],
    "hedging": [r'(?:false[- ]positive|false[- ]negative)', r'alert fatigue',
                r'real[- ]world\s+(?:evidence|data)', r'sensitivity (?:analysis|range|to|of)',
                r'low/?high (?:case|scenario|estimate)', r'\b±\s?\d',
                r'(?:may|might|could)\s+(?:vary|differ|change)'],
}

LEN_MIN, LEN_MAX = 1200, 8000
OVERLAP_HARD = 0.35      # verbatim-copy cap; natural median is 0.09
OVERLAP_FREE = 0.15      # graded penalty begins here
NGRAM = 8
SELFREP_MIN = 0.45       # distinct-5gram ratio; natural text sits well above


def families(text: str) -> set:
    return {k for k, ps in BEH.items() if any(re.search(p, text, re.I) for p in ps)}


def _ngrams(text: str, n: int = NGRAM) -> set:
    w = re.findall(r'\w+', text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def seat_text(prompt: str) -> str:
    """Recover the specialists' contributions from the synthesis prompt."""
    parts = re.split(r'\n---\n\w+ CONTRIBUTION:\n', prompt)
    return "\n".join(parts[1:]) if len(parts) > 1 else ""


def score_one(prompt: str, completion: str) -> float:
    """Reward for one completion given its synthesis prompt. Exposed for audit."""
    if not completion:
        return -1.0
    n = len(completion)
    if n < LEN_MIN or n > LEN_MAX:
        return -1.0

    seats = seat_text(prompt)
    cg = _ngrams(completion)
    overlap = len(cg & _ngrams(seats)) / max(len(cg), 1) if seats else 0.0
    if overlap > OVERLAP_HARD:
        return -1.0                                   # copy-paste hack

    # Self-repetition guard. Family matching is coarse: a completion can hit a
    # family with one boilerplate phrase without preserving anything specific.
    w5 = _ngrams(completion, 5)
    words = re.findall(r'\w+', completion.lower())
    selfrep = len(w5) / max(len(words) - 4, 1)
    if selfrep < SELFREP_MIN:
        return -1.0

    raised = families(seats)
    present = families(completion)
    kept = raised & present
    spurious = present - raised

    r = len(kept) / max(len(raised), 1)
    r -= 0.5 * len(spurious) / 4.0                    # conditionality
    r -= 0.5 * max(0.0, overlap - OVERLAP_FREE) / 0.20
    return float(r)


@register_reward_function()
def cell16_preservation(prompts, completions, answers, types=None):
    out = []
    for i, comp in enumerate(completions):
        p = prompts[i] if i < len(prompts) else ""
        out.append(score_one(str(p), comp if isinstance(comp, str) else str(comp)))
    return out
