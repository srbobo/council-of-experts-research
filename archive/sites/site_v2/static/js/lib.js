/* Pure logic shared by the story and catalog pages. No DOM access here —
   everything in this file is covered by unit tests. */

export const VERDICT_LABELS = {
  supported: "held up",
  falsified: "disproven",
  mixed: "partly held up",
  null: "no difference found",
  withdrawn: "withdrawn",
  "not-evaluable": "couldn't be called",
};

export const VERDICT_ORDER = [
  "supported",
  "mixed",
  "null",
  "not-evaluable",
  "falsified",
  "withdrawn",
];

/** Human label for a verdict key; falls back to the key itself. */
export function verdictLabel(verdict) {
  return VERDICT_LABELS[verdict] || verdict;
}

/** Merge early + main experiment lists, sorted by numeric key. */
export function mergeExperiments(...lists) {
  const seen = new Set();
  const out = [];
  for (const list of lists) {
    for (const e of list || []) {
      if (!e || typeof e.num !== "number" || seen.has(e.id)) {
        continue;
      }
      seen.add(e.id);
      out.push(e);
    }
  }
  return out.sort((a, b) => a.num - b.num);
}

/** Validate one experiment entry; returns a list of problems (empty = ok). */
export function validateExperiment(e) {
  const problems = [];
  const fields = ["id", "title", "question", "approach", "result", "learning"];
  for (const f of fields) {
    if (typeof e?.[f] !== "string" || e[f].trim().length === 0) {
      problems.push(`missing ${f}`);
    }
  }
  if (typeof e?.num !== "number" || Number.isNaN(e.num)) {
    problems.push("missing num");
  }
  if (!(e?.verdict in VERDICT_LABELS)) {
    problems.push(`unknown verdict ${e?.verdict}`);
  }
  return problems;
}

/** Words the site must never show (the jargon ban). */
export const BANNED_JARGON = [
  "pre-registration",
  "pre-registered",
  "appendix arm",
  "bootstrap",
  "confidence interval",
  "ablation",
  "attainability",
  "scaffold",
];

/** Scan text for banned jargon; returns the terms found. */
export function jargonIn(text) {
  const low = String(text).toLowerCase();
  return BANNED_JARGON.filter((term) => low.includes(term));
}

/** Filter experiments by verdict key ("all" passes everything). */
export function filterByVerdict(experiments, verdict) {
  if (verdict === "all") {
    return experiments;
  }
  return experiments.filter((e) => e.verdict === verdict);
}

/** Which build-up pieces of the harness diagram are visible at a story
    step. Steps reveal pieces cumulatively; the mapping is data, so the
    story page and the tests share one source of truth. */
export const STEP_PIECES = [
  ["question"],
  ["question", "gate"],
  ["question", "gate", "editor", "noinstr"],
  ["question", "gate", "editor", "noinstr", "seats"],
  ["question", "gate", "editor", "noinstr", "seats"],
  ["question", "gate", "editor", "noinstr", "seats", "freight"],
  ["question", "gate", "editor", "noinstr", "seats", "freight", "planner"],
  ["question", "gate", "editor", "noinstr", "seats", "freight", "planner", "trigger"],
  [
    "question",
    "gate",
    "editor",
    "noinstr",
    "seats",
    "freight",
    "planner",
    "trigger",
    "loop",
  ],
  [
    "question",
    "gate",
    "editor",
    "noinstr",
    "seats",
    "freight",
    "planner",
    "trigger",
    "loop",
    "answer",
  ],
  [
    "question",
    "gate",
    "editor",
    "noinstr",
    "seats",
    "freight",
    "planner",
    "trigger",
    "loop",
    "answer",
    "filters",
  ],
  [
    "question",
    "gate",
    "editor",
    "noinstr",
    "seats",
    "freight",
    "planner",
    "trigger",
    "loop",
    "answer",
    "filters",
  ],
  [
    "question",
    "gate",
    "editor",
    "noinstr",
    "seats",
    "freight",
    "planner",
    "trigger",
    "loop",
    "answer",
    "filters",
    "done",
  ],
];

export function piecesForStep(index) {
  if (index < 0) {
    return STEP_PIECES[0];
  }
  if (index >= STEP_PIECES.length) {
    return STEP_PIECES[STEP_PIECES.length - 1];
  }
  return STEP_PIECES[index];
}
