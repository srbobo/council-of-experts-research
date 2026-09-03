/* Catalog page: loads both experiment data files, renders cards, and
   wires the verdict filters. */
import {
  filterByVerdict,
  mergeExperiments,
  VERDICT_LABELS,
  VERDICT_ORDER,
  validateExperiment,
  verdictLabel,
} from "./lib.js";

const cardsEl = document.getElementById("cards");
const filtersEl = document.getElementById("filters");
const countEl = document.getElementById("count");

function cardHTML(e) {
  return `
    <li class="card">
      <header>
        <h2>${e.title}</h2>
        <span class="eid">${e.id.replace("E", "No. ")}</span>
      </header>
      <span class="verdict ${e.verdict}">${verdictLabel(e.verdict)}</span>
      <dl>
        <div><dt>What we asked</dt><dd>${e.question}</dd></div>
        <div><dt>What we did</dt><dd>${e.approach}</dd></div>
        <div><dt>What happened</dt><dd>${e.result}</dd></div>
        <div><dt>What it taught us</dt><dd>${e.learning}</dd></div>
      </dl>
    </li>`;
}

function render(experiments, verdict) {
  const shown = filterByVerdict(experiments, verdict);
  cardsEl.innerHTML = shown.map(cardHTML).join("\n");
  countEl.textContent = `${shown.length} of ${experiments.length} experiments`;
}

async function loadJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`failed to load ${url}`);
  }
  return res.json();
}

async function main() {
  const [early, mainData] = await Promise.all([
    loadJSON("data/experiments_early.json").catch(() => ({ experiments: [] })),
    loadJSON("data/experiments_main.json"),
  ]);
  const experiments = mergeExperiments(early.experiments, mainData.experiments);
  const bad = experiments.flatMap((e) =>
    validateExperiment(e).map((p) => `${e.id}: ${p}`),
  );
  if (bad.length > 0) {
    console.warn("data problems:", bad);
  }

  let current = "all";
  const options = [
    "all",
    ...VERDICT_ORDER.filter((v) => experiments.some((e) => e.verdict === v)),
  ];
  for (const v of options) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = v === "all" ? "All" : VERDICT_LABELS[v];
    btn.setAttribute("aria-pressed", String(v === current));
    btn.addEventListener("click", () => {
      current = v;
      for (const b of filtersEl.querySelectorAll("button")) {
        b.setAttribute("aria-pressed", String(b === btn));
      }
      render(experiments, current);
    });
    filtersEl.appendChild(btn);
  }
  render(experiments, current);
}

main().catch((err) => {
  cardsEl.innerHTML = `<li class="card"><h2>Couldn't load the experiment record</h2><p>${err.message}</p></li>`;
});
