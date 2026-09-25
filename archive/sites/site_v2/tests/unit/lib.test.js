import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  BANNED_JARGON,
  filterByVerdict,
  jargonIn,
  mergeExperiments,
  piecesForStep,
  STEP_PIECES,
  VERDICT_LABELS,
  validateExperiment,
  verdictLabel,
} from "../../static/js/lib.js";

const mainData = JSON.parse(
  readFileSync(new URL("../../data/experiments_main.json", import.meta.url)),
);
let earlyData = { experiments: [] };
try {
  earlyData = JSON.parse(
    readFileSync(new URL("../../data/experiments_early.json", import.meta.url)),
  );
} catch {
  // early data may not exist in partial checkouts; tests below tolerate it
}

test("verdictLabel maps every known verdict to plain language", () => {
  for (const [key, label] of Object.entries(VERDICT_LABELS)) {
    assert.equal(verdictLabel(key), label);
    assert.ok(!label.includes("null"));
  }
  assert.equal(verdictLabel("mystery"), "mystery");
});

test("mergeExperiments sorts numerically and drops duplicates/invalid", () => {
  const merged = mergeExperiments(
    [
      { id: "B", num: 2, verdict: "supported" },
      { id: "A", num: 1, verdict: "supported" },
    ],
    [{ id: "B", num: 99 }, { id: "C" }, null, { id: "D", num: 1.5 }],
  );
  assert.deepEqual(
    merged.map((e) => e.id),
    ["A", "D", "B"],
  );
});

test("filterByVerdict passes everything on 'all'", () => {
  const xs = mainData.experiments;
  assert.equal(filterByVerdict(xs, "all").length, xs.length);
  const f = filterByVerdict(xs, "falsified");
  assert.ok(f.length > 0);
  assert.ok(f.every((e) => e.verdict === "falsified"));
});

test("every shipped experiment entry is complete and well-formed", () => {
  const all = mergeExperiments(earlyData.experiments, mainData.experiments);
  assert.ok(all.length >= 30, `expected a full catalog, got ${all.length}`);
  for (const e of all) {
    assert.deepEqual(validateExperiment(e), [], `entry ${e.id}`);
  }
});

test("shipped experiment prose contains no banned jargon", () => {
  const all = mergeExperiments(earlyData.experiments, mainData.experiments);
  for (const e of all) {
    const text = [e.title, e.question, e.approach, e.result, e.learning].join(" ");
    assert.deepEqual(jargonIn(text), [], `entry ${e.id}`);
  }
});

test("jargonIn detects banned terms case-insensitively", () => {
  assert.deepEqual(jargonIn("A Pre-Registered plan"), ["pre-registered"]);
  assert.deepEqual(jargonIn("perfectly plain prose"), []);
  assert.ok(BANNED_JARGON.length >= 5);
});

test("story step pieces grow monotonically and clamp at the ends", () => {
  for (let i = 1; i < STEP_PIECES.length; i++) {
    const prev = new Set(STEP_PIECES[i - 1]);
    for (const piece of prev) {
      assert.ok(STEP_PIECES[i].includes(piece), `step ${i} lost piece ${piece}`);
    }
  }
  assert.deepEqual(piecesForStep(-5), STEP_PIECES[0]);
  assert.deepEqual(piecesForStep(999), STEP_PIECES.at(-1));
});
