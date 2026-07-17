/* Council of Experts — Results page logic.
 *
 * Reads imported runs from /api/imported/{case_id} and renders the three
 * modes (local-council, opus-single, opus-council) side by side in the
 * same column shape as the A/B page. Case selector is restricted to the
 * two cases that have a full 3-mode comparison captured: case 4 (GLP-1)
 * and case 2 (cross-border DTx).
 *
 * Reuses the A/B page's overlay pattern (⤢ to expand a column, × or
 * Escape to close) since the columns can be dense and the 1/3 width is
 * cramped for serious reading.
 */
(function () {
  "use strict";

  /* -------------------------------------------------------------------------
   * Cases shown on this page. Restricted to the two with full 3-mode
   * comparisons; if more cases get captured later, add them here.
   * ---------------------------------------------------------------------- */
  // All five canonical cases. Originally restricted to 2 + 4 (the only
  // cases with a full 3-mode capture against Opus), but extended to all
  // 5 after the MoE bench landed — gpt-oss-single + gpt-oss-council now
  // exist for every case, so the selector should expose them.
  const CASES = [
    { id: "case_1_clinical_decision_support",          label: "Case 1 — AI clinical decision support rollout" },
    { id: "case_2_cross_border_digital_therapeutic",  label: "Case 2 — Cross-border digital therapeutic launch" },
    { id: "case_3_capitated_risk_contract",            label: "Case 3 — Capitated Medicare Advantage risk contract" },
    { id: "case_4_glp1_employer_coverage",            label: "Case 4 — GLP-1 employer coverage" },
    { id: "case_5_nonprofit_hospital_pe_conversion",  label: "Case 5 — Nonprofit hospital PE conversion" },
    { id: "case_6_trigger_heavy_biotech_ma",          label: "Case 6 — Trigger-heavy: cross-border biotech M&A" },
    { id: "case_7_trigger_light_baseline",            label: "Case 7 — Trigger-light baseline: hybrid-work strategy" },
  ];

  // Baseline modes always shown (in this order), even if no run is present.
  // Aligned with A/B page so the visual identity is consistent across tabs.
  // local-council-v2 sits immediately after local-council so the v1-vs-v2
  // comparison reads left-to-right when both have imported runs.
  const BASELINE_MODE_ORDER = ["local-council", "local-council-v2", "opus-single", "opus-council"];

  // MoE baselines — local gpt-oss-20B counterparts to opus-single /
  // opus-council. Appear only when imported runs exist for them (same
  // rule as swap variants) so the page doesn't show empty MoE columns
  // before the user runs the MoE bench. Ordered to sit alongside their
  // Opus counterparts conceptually: frontier-single → MoE-single,
  // frontier-council → MoE-council.
  const MOE_MODE_ORDER = ["gptoss-single", "gptoss-council"];

  // DPO + prompt-transfer experiment arms — appear after the MoE columns
  // when imported runs exist (same conditional-display rule).
  const DPO_MODE_ORDER = [
    "local-council-repro",
    "gptoss-single-spec",
    "local-council-spec",
    "local-council-dpo",
    "local-council-sft",
  ];

  // Pathway-3 swap variants — hybrid cabinets where one phase is served by
  // Opus and the other four by local Ollama. Added to the grid only when
  // imported runs actually exist for them (otherwise 8 always-visible
  // columns would crowd the page). Order matches the deliberation phase
  // order (planner → 3 seats → synthesis) so a reader scanning left-to-right
  // sees the gap walk through the pipeline.
  //
  // Local-only Phi-4 swap variants come AFTER the Opus swaps in the column
  // order so the page reads "baselines → Opus swaps → local-only swaps."
  // The local swaps are explicitly named with "phi4" (not "opus") so the
  // audit log and the UI both surface what actually ran — no Opus-stand-in
  // mislabeling.
  const SWAP_MODE_ORDER = [
    // Opus swaps (pathway-3 frontier ablation; require BENCH_BUDGET_USD > 0)
    "swap-planner-opus",
    "swap-healthcare-opus",
    "swap-legal-opus",
    "swap-finance-opus",
    "swap-synthesis-opus",
    // Local-only Phi-4 swaps (generalist-vs-specialist ablation; the
    // healthcare-phi4 variant was removed after plumbing validation).
    "swap-legal-phi4",
    "swap-finance-phi4",
  ];

  const MODE_TITLES = {
    "local-council":         "Local Council (v1)",
    "local-council-v2":      "Local Council (v2 — upgraded specialists)",
    "opus-single":           "Opus single-shot",
    "opus-council":          "Opus-as-council",
    "gptoss-single":         "gpt-oss-20B single-shot",
    "gptoss-council":        "gpt-oss-20B as-council",
    "local-council-repro":   "DPO arm A′ — Saul repro conversion",
    "gptoss-single-spec":    "DPO arm B1 — gpt-oss + behavior spec",
    "local-council-spec":    "DPO arm B2 — Saul + behavior spec",
    "local-council-dpo":     "DPO arm C — Saul LoRA-DPO",
    "local-council-sft":     "P1 control — Saul SFT-on-chosen",
    "swap-planner-opus":     "Swap · Planner→Opus",
    "swap-healthcare-opus":  "Swap · Healthcare→Opus",
    "swap-legal-opus":       "Swap · Legal→Opus",
    "swap-finance-opus":     "Swap · Finance→Opus",
    "swap-synthesis-opus":   "Swap · Synthesis→Opus",
    "swap-legal-phi4":       "Swap · Legal→Phi-4",
    "swap-finance-phi4":     "Swap · Finance→Phi-4",
  };

  // Compute the actual columns to render: only show a column when its
  // imported run exists. Exception: local-council always shows even
  // without a run (it's the headline comparison baseline). The other
  // four baseline modes plus MoE plus swap variants only appear when
  // their respective imports exist — keeps the page tidy as new modes
  // get bench'd over time.
  function activeModeOrder(modesMap) {
    const baselinesPresent = BASELINE_MODE_ORDER.filter(
      (m) => m === "local-council" || (modesMap && modesMap[m])
    );
    const moePresent  = MOE_MODE_ORDER.filter((m) => modesMap && modesMap[m]);
    const dpoPresent  = DPO_MODE_ORDER.filter((m) => modesMap && modesMap[m]);
    const swapsPresent = SWAP_MODE_ORDER.filter((m) => modesMap && modesMap[m]);
    return baselinesPresent.concat(moePresent, dpoPresent, swapsPresent);
  }

  /* -------------------------------------------------------------------------
   * State
   * ---------------------------------------------------------------------- */
  let currentCaseId = null;
  let currentData = null;       // payload from /api/imported/{case_id}
  let expandedMode = null;      // when set, render overlay for this mode
  let promptsCache = null;      // populated from /api/prompts at boot
  // Active rubric highlights — Set of rubric IDs currently toggled on. The
  // order rubrics are added is preserved (Set iteration order) so colors
  // stay stable as rubrics get toggled in/out.
  const activeRubrics = new Set();

  // Disposition lens — the paper's five behavior families, each with a
  // FIXED color slot (unlike rubrics, whose colors rotate by toggle order:
  // the family↔color mapping must stay stable so the legend stays true).
  // Patterns are a JS port of the bench scorer's regex families; the bench
  // scorer is canonical — keep in sync when it changes.
  const DISPOSITION_FAMILIES = [
    { id: "cutoff", label: "Training-cutoff disclosure", short: "cutoff", slot: "blue",
      desc: "Names the knowledge boundary: “as of my training data…”" },
    { id: "modeled", label: "Modeled-assumption flagging", short: "modeled", slot: "amber",
      desc: "Labels numbers as modeled: “assuming 60% persistence…”" },
    { id: "precision", label: "Precise vocabulary", short: "precise", slot: "sage",
      desc: "Regulatory distinctions: clearance vs approval, 510(k) pathway language" },
    { id: "jurisdiction", label: "Jurisdictional distinguishing", short: "jurisd.", slot: "lilac",
      desc: "Keeps legal regimes separate: UK GDPR vs EU GDPR, preemption" },
    { id: "hedging", label: "Hedging (stated conditionality)", short: "hedge", slot: "rose",
      desc: "Conditions a claim — “may vary if…” — not refusal, not vagueness" },
  ];
  const DISPOSITION_PATTERNS = {
    cutoff: [
      /training[- ]?cut[- ]?off/gi, /knowledge cut[- ]?off/gi,
      /may (?:be |have )(?:stale|outdated|evolved)/gi, /post[- ]?cut[- ]?off/gi,
      /after my training/gi, /verify (?:current|latest|recent)/gi,
      /as of (?:my )?(?:training|knowledge|20\d\d)/gi,
    ],
    modeled: [
      /modell?ed at/gi, /\bassume[ds]? (?:that|the)/gi,
      /\bassuming (?:that|the|a |an |\d)/gi, /under the assumption/gi,
      /this assumes?/gi, /\bwe assume\b/gi, /\bhypothetical(?:ly)?\b/gi,
    ],
    precision: [
      /approval[^.\n]{0,60}(?:vs\.?|versus|not)[^.\n]{0,60}clearance/gi,
      /clearance[^.\n]{0,60}(?:vs\.?|versus|not)[^.\n]{0,60}approval/gi,
      /distinguish(?:es|ing|ed)? between/gi, /standard[- ]of[- ]care/gi,
      /(?:510\(k\)|de novo|PMA)\s+(?:clearance|approval|pathway)/gi,
      /\b(?:NDA|BLA)\s+approval\b/gi,
    ],
    jurisdiction: [
      /\bUK\s?GDPR\b/g, /\bEU\s?GDPR\b/g, /post[- ]Brexit/gi,
      /each\s+(?:jurisdiction|country|state|regime)/gi, /preempt(?:ion|s|ed)?/gi,
    ],
    hedging: [
      /false[- ](?:positive|negative)/gi, /alert fatigue/gi,
      /real[- ]world\s+(?:evidence|data)/gi, /sensitivity (?:analysis|range|to|of)/gi,
      /low\/?high (?:case|scenario|estimate)/gi, /±\s?\d/g,
      /\b(?:may|might|could)\s+(?:vary|differ|change)\b/gi,
    ],
  };
  // Families currently toggled on (insertion order preserved, like rubrics).
  const activeDispositions = new Set();
  const dispositionSlot = (id) =>
    (DISPOSITION_FAMILIES.find((f) => f.id === id) || {}).slot || "sand";
  const dispositionLabel = (id) =>
    (DISPOSITION_FAMILIES.find((f) => f.id === id) || {}).label || id;

  // Standing note on Opus paste-in captures — the manual paste flow doesn't
  // preserve extended thinking blocks, so we surface that limitation in the
  // reasoning slot rather than silently omitting it.
  const OPUS_PASTE_NOTE =
    "Extended thinking was not included in this manual paste-in capture. " +
    "The reasoning Opus did to produce this phase is not visible here; " +
    "re-run via the bench harness to capture structured thinking blocks.";

  /* -------------------------------------------------------------------------
   * DOM lookups
   * ---------------------------------------------------------------------- */
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const els = {
    caseSelect:    $("#case-select"),
    promptDisplay: $("#prompt-display"),
    grid:          $("#results-grid"),
    analysisPanel: $("#analysis-panel"),
    overlayRoot:   $("#overlay-root"),
  };

  /* -------------------------------------------------------------------------
   * Tiny utility helpers (mirrored from app.js — kept local so this page
   * doesn't depend on the A/B page's IIFE)
   * ---------------------------------------------------------------------- */
  function escapeHtml(s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /* -------------------------------------------------------------------------
   * Lightweight markdown beautifier for the top body of each column.
   *
   * Handles the limited markdown surface area the three modes actually
   * emit: `##` / `###` headings, `**bold**`, `*italic*`, ordered lists
   * (`1.`/`2.`/...), unordered lists (`-`/`*`/`•`), and blank-line
   * paragraph breaks. Everything else passes through as escaped text
   * inside <p> tags.
   *
   * Done in vanilla JS rather than pulling in a markdown library — the
   * input surface is constrained (we control both prompts and what gets
   * pasted in) and adding a dep for this page only would be overkill.
   * The HTML escape happens FIRST so the only `<` in the output comes
   * from tags this function writes itself.
   * ---------------------------------------------------------------------- */
  function beautifyMarkdown(text) {
    if (!text) return "";
    // Inline transforms applied per-line after escaping. Order matters:
    // bold before italic so `**foo**` isn't eaten by the single-star rule.
    function inline(line) {
      let s = escapeHtml(line);
      s = s.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
      // Single-star italics — but only when both stars sit on word
      // boundaries, to avoid mangling things like "STEP 1: 2*2" or stray
      // asterisks in technical content.
      s = s.replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s.,;:!?)]|$)/g, "$1<em>$2</em>");
      // Inline code in backticks → <code>
      s = s.replace(/`([^`\n]+)`/g, "<code>$1</code>");
      return s;
    }

    const lines = text.split("\n");
    const out = [];
    let i = 0;

    // Active list state — we're either not in a list, or in <ul>/<ol>.
    // Track so consecutive list items group into the same block.
    let listType = null;          // "ul" | "ol" | null
    const flushList = () => {
      if (listType) {
        out.push(`</${listType}>`);
        listType = null;
      }
    };
    const openList = (kind) => {
      if (listType !== kind) {
        flushList();
        out.push(`<${kind}>`);
        listType = kind;
      }
    };

    // Paragraph buffer — non-heading, non-list lines collect here until a
    // blank line or structural shift flushes them as a single <p>.
    let paraBuf = [];
    const flushPara = () => {
      if (paraBuf.length === 0) return;
      const joined = paraBuf.map(inline).join("<br>");
      out.push(`<p>${joined}</p>`);
      paraBuf = [];
    };

    while (i < lines.length) {
      const raw = lines[i];
      const trimmed = raw.trim();

      if (trimmed === "") {
        // Flush only the paragraph buffer on blank lines. Lists stay open
        // across blank lines so a numbered list written as
        //   1. foo
        //   <blank>
        //   2. bar
        // renders as one <ol> with sequential numbering instead of four
        // separate <ol>s that each auto-number from 1. The list closes
        // when we actually hit non-list content (heading or prose).
        flushPara();
        i++;
        continue;
      }

      // Headings — ##, ###, # all map to small-but-distinguishable levels.
      // `##` is the common case (Tensions / Synthesis section anchors);
      // we render it as h4 to fit inside the column visually.
      let m;
      if ((m = trimmed.match(/^(#{1,4})\s+(.+)$/))) {
        flushPara();
        flushList();
        const level = Math.min(m[1].length + 3, 6); // # → h4, ## → h5, etc.
        const headTag = `h${level}`;
        out.push(`<${headTag} class="md-heading">${inline(m[2])}</${headTag}>`);
        i++;
        continue;
      }

      // Ordered list item — "1. foo", "2) bar", etc.
      if ((m = trimmed.match(/^(\d+)[.)]\s+(.+)$/))) {
        flushPara();
        openList("ol");
        out.push(`<li>${inline(m[2])}</li>`);
        i++;
        continue;
      }

      // Unordered list item — "- foo", "* foo", "• foo".
      if ((m = trimmed.match(/^[-*•]\s+(.+)$/))) {
        flushPara();
        openList("ul");
        out.push(`<li>${inline(m[1])}</li>`);
        i++;
        continue;
      }

      // Regular prose line — accumulate into the current paragraph. List
      // continuation (indented under a list item) gets folded into the
      // last <li> by closing the paragraph and appending; cleaner to just
      // flush the list and treat it as a new paragraph in this corpus.
      flushList();
      paraBuf.push(trimmed);
      i++;
    }
    flushPara();
    flushList();
    return out.join("");
  }

  // <think>...</think> blocks are present in some local-council outputs
  // (Qwen-Open-Finance emits them); strip for the main column display so
  // the reader sees the speech portion. The inspector path surfaces them
  // separately as reasoning content.
  function stripThinking(text) {
    if (!text) return text;
    return text.replace(/<think>[\s\S]*?<\/think>\s*/g, "").trim();
  }

  // Split text into its inline <think>...</think> blocks and the remaining
  // speech. Returns { thinking: [...], speech: "..." }. Mirrors the A/B
  // page's helper so reasoning content renders the same way across pages.
  function splitThinking(text) {
    const thinking = [];
    if (!text) return { thinking, speech: "" };
    const speech = text.replace(/<think>([\s\S]*?)<\/think>\s*/g, (_, body) => {
      thinking.push(body.trim());
      return "";
    }).trim();
    return { thinking, speech };
  }

  // Pull the planner's pre-JSON reasoning out of its raw output. The Lead
  // planner emits STEP 1 / STEP 2 / STEP 3 prose, then the JSON dispatch
  // block at the end. Everything before the first `{` is reasoning; the
  // JSON itself is the "output" of the phase.
  function splitPlannerOutput(text) {
    if (!text) return { reasoning: "", json: "" };
    const firstBrace = text.indexOf("{");
    if (firstBrace === -1) return { reasoning: text.trim(), json: "" };
    return {
      reasoning: text.slice(0, firstBrace).trim(),
      json: text.slice(firstBrace).trim(),
    };
  }

  // Pull structured thinking from a raw chat response. Three shapes
  // accommodated:
  //   (1) Anthropic adaptive thinking — content[].type === "thinking"
  //       with the reasoning under .thinking or .text. Opus modes.
  //   (2) Ollama gpt-oss reasoning — top-level message.thinking string.
  //       The gpt-oss-20B Ollama runtime emits chain-of-thought as a
  //       distinct field on the message rather than mixing it into the
  //       visible content.
  //   (3) Inline <think>...</think> blocks embedded in the visible text
  //       — handled separately by ``splitThinking`` on the speech path.
  // Returns an array of strings (one per distinct thinking block) so the
  // inspector can render them as their own collapsible disclosures.
  function extractStructuredThinking(rawResponse) {
    if (!rawResponse) return [];
    const blocks = [];
    // (1) Anthropic-style content blocks
    if (Array.isArray(rawResponse.content)) {
      for (const b of rawResponse.content) {
        if (b && b.type === "thinking" && (b.thinking || b.text)) {
          blocks.push((b.thinking || b.text || "").trim());
        }
      }
    }
    // (2) Ollama-style message.thinking — gpt-oss reasoning trace
    const ollamaThinking = rawResponse.message && rawResponse.message.thinking;
    if (typeof ollamaThinking === "string" && ollamaThinking.trim()) {
      blocks.push(ollamaThinking.trim());
    }
    return blocks;
  }

  // Split an OpenAI-style messages list into (system, user). Used for the
  // per-phase inspector: each phase shows the system prompt it was given
  // and the user-side input (dispatched sub-question or synthesis bundle).
  function splitInputMessages(messages) {
    if (!Array.isArray(messages)) return { system: "", user: "" };
    const sys = messages.find((m) => m.role === "system");
    const usr = messages.find((m) => m.role !== "system");
    return {
      system: sys ? sys.content || "" : "",
      user: usr ? usr.content || "" : "",
    };
  }

  // Format a number of milliseconds as a short, readable string.
  function fmtMs(ms) {
    if (ms == null) return "—";
    if (ms < 1000) return ms + "ms";
    return (ms / 1000).toFixed(1) + "s";
  }

  /* -------------------------------------------------------------------------
   * Rubric highlighting — interactive evidence-locator.
   *
   * Each rubric row in the analysis tables has a stable data-rubric ID.
   * Clicking a row toggles the rubric in `activeRubrics`; we then walk
   * the text nodes inside each column's `.result-body` and wrap matches
   * in <mark data-rubric="…" data-color-slot="N">. The color slot is
   * assigned by the rubric's insertion order into the active set, so a
   * given rubric keeps its color while it's on.
   *
   * Pattern matching uses case-insensitive regexes. The patterns aim to
   * be precise enough to be useful and loose enough to catch paraphrase
   * (e.g. "STEP 4" / "STEP-4" / "step 4 trial"). Red-flag patterns
   * deliberately match the confabulated trial names — that highlight is
   * not a credit, it's a damning find.
   *
   * Limitations: only `.result-body` (the top component of each column)
   * gets highlighted, not the inspector outputs. The inspector content
   * is intentionally a byte-for-byte audit view; the top body is the
   * read-and-compare surface where highlighting earns its keep.
   * ---------------------------------------------------------------------- */

  // 6-color rotation for active rubric highlights. Soft, paper-amber-
  // compatible swatches that read clearly against the off-white card
  // background without overwhelming the text. Cycles if you toggle more
  // than 6 rubrics at once.
  const RUBRIC_COLORS = ["amber", "sage", "blue", "rose", "lilac", "sand"];

  // Per-case rubric pattern map. Keys are the `data-rubric` attribute
  // values from the analysis tables in results.html; values are arrays
  // of regexes that match supporting evidence (or, for red flags, the
  // exact confabulation we want to flag).
  const RUBRIC_PATTERNS = {
    // --- Case 4: GLP-1 employer coverage ---
    "c4-hc-durability": [
      /STEP[-\s]?4/gi,
      /SURMOUNT[-\s]?4/gi,
      /weight regain/gi,
      /\bdurability\b/gi,
      /discontinu\w+/gi,
      /\brebound\b/gi,
      /weight loss is not maintained/gi,
    ],
    "c4-hc-efficacy": [
      /\bsemaglutide\b/gi,
      /\btirzepatide\b/gi,
      /SURMOUNT[-\s]?\w*/gi,
      /STEP[-\s]?1/gi,
      /\bWegovy\b/g,
      /\bZepbound\b/g,
      /\bOzempic\b/g,
      /\bMounjaro\b/g,
      /2\.4\s?mg/gi,
    ],
    "c4-legal-ada": [
      /\bADA\b/g,
      /Americans with Disabilit\w+/gi,
      /Section\s?1557/gi,
      /obesity[-\s]as[-\s]disability/gi,
      /\bdisparate impact\b/gi,
    ],
    "c4-legal-erisa": [
      /\bERISA\b/g,
      /CAA[-\s]?2021/gi,
      /Consolidated Appropriations Act/gi,
      /\bfiduciary\b/gi,
      /\bMHPAEA\b/g,
      /preempt\w*/gi,
    ],
    "c4-fin-pmpm": [
      /\bPMPM\b/g,
      /per[-\s]member[-\s]per[-\s]month/gi,
      /sensitivit\w+/gi,
      /±\s?\d/g,
      /\$\d+(?:\.\d+)?\s*PMPM/gi,
      /low[-\s]case|high[-\s]case|base[-\s]case/gi,
    ],
    "c4-fin-stoploss": [
      /stop[-\s]loss/gi,
      /\breinsurance\b/gi,
      /\bspecific deductible\b/gi,
      /\baggregate attachment\b/gi,
    ],
    "c4-cutoff": [
      /training[-\s]cutoff/gi,
      /training[-\s]data[-\s]cut[-\s]?off/gi,
      /knowledge[-\s]cut[-\s]?off/gi,
      /\bstale\b/gi,
      /may be (?:out[-\s]of[-\s]date|outdated)/gi,
      /(?:my|the model'?s) (?:training|knowledge)/gi,
      /post[-\s]cutoff/gi,
      /quarter[-\s]by[-\s]quarter/gi,
      /refresh\w* at the point of/gi,
    ],
    "c4-redflag": [
      /SEMIMAN/gi,
      /\bMarso(?:\s+SP)?(?:\s+et\s+al)?/gi,
      /\bArmstrong\s+M(?:\s+et\s+al)?/gi,
    ],

    // --- Case 2: cross-border digital therapeutic launch ---
    "c2-hc-frameworks": [
      /\bMHRA\b/g,
      /\bBfArM\b/g,
      /\bDiGA\b/g,
      /\bFDA\b/g,
      /Notified Body|notified body/g,
    ],
    "c2-hc-pve": [
      /\bpVE\b/g,
      /positive Versorgungseffekt/gi,
      /§\s?139e/g,
      /Section\s?139e/gi,
      /provisional listing|permanent listing/gi,
      /Fast[-\s]Track/gi,
    ],
    "c2-legal-gdpr": [
      /UK\s?GDPR/gi,
      /EU\s?GDPR/gi,
      /Data Protection Act 2018/gi,
      /post[-\s]Brexit/gi,
      /UK[-\s]EU adequacy/gi,
      /\bICO\b/g,
    ],
    "c2-legal-sgb": [
      /\bSGB\s?V\b/gi,
      /§\s?\d+\s?(?:Nr\.?\s?\d+)?/g,
      /\bF17\.2\b/g,
      /\bBDSG\b/g,
      /Sozialgesetzbuch/gi,
      /GKV[-\s]SV/gi,
    ],
    "c2-fin-revenue": [
      /NHS commissioning/gi,
      /DiGA pricing|DiGA economics|DiGA reimbursement/gi,
      /US\s?payer/gi,
      /reimbursement pathway/gi,
      /(?:provisional|permanent)\s+(?:DiGA\s+)?(?:listing|price)/gi,
      /negotiated price/gi,
    ],
    "c2-synth-juris": [
      /UK[-\s](?:specific|pathway|track|launch)/gi,
      /(?:Germany|German)[-\s](?:specific|pathway|track|launch)/gi,
      /jurisdiction\w*/gi,
      /separate(?:ly)?\s+(?:architected|engineered|designed)/gi,
      /per[-\s]market/gi,
    ],
    "c2-redflag": [
      /510\(k\)\s+(?:approval|clearance)\s+(?:provides|carries|gives|gives you|grants)/gi,
      /FDA[-\s](?:approval|clearance)\s+(?:is|will be|provides|carries)\s+(?:sufficient|controlling|recogniz\w+)/gi,
      /leverage(?:s|d|)?\s+(?:the\s+)?(?:FDA|510\(k\))/gi,
      /\b510\(k\)\s+as\s+(?:the\s+)?(?:basis|foundation)\b/gi,
    ],
  };

  // Friendly label for the chip strip + the highlight tooltip. We pull it
  // from the rubric row's first <td> text content so the source-of-truth
  // is the table itself — edit the table label and the chip updates.
  function rubricLabel(rubricId) {
    const row = document.querySelector(
      `.rubric-row[data-rubric="${CSS.escape(rubricId)}"]`
    );
    if (!row) return rubricId;
    const firstTd = row.querySelector("td");
    return firstTd ? firstTd.textContent.trim() : rubricId;
  }

  // Assign each active rubric a color slot in insertion order. Returns
  // a Map<rubricId, colorName>. Stable across re-renders as long as the
  // Set's insertion order doesn't change.
  function buildColorSlotMap() {
    const map = new Map();
    let i = 0;
    for (const id of activeRubrics) {
      map.set(id, RUBRIC_COLORS[i % RUBRIC_COLORS.length]);
      i++;
    }
    return map;
  }

  // Walk all text nodes inside `rootEl` and wrap matches in <mark>.
  // Handles overlap by merging into a single mark with the earliest
  // rubric's color (deterministic; first-toggle wins on conflict).
  // No-op when activeRubrics is empty.
  function highlightElement(rootEl) {
    if (!rootEl || (activeRubrics.size === 0 && activeDispositions.size === 0)) return;
    const slots = buildColorSlotMap();

    // Collect text nodes up front; mutating the tree while walking it is
    // a known footgun with TreeWalker.
    const walker = document.createTreeWalker(rootEl, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        // Skip nodes already inside a mark (avoid double-wrapping on
        // re-render) and skip empty text.
        if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        if (node.parentElement && node.parentElement.closest("mark.rubric-mark, mark.disp-mark")) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);

    for (const node of textNodes) {
      const text = node.nodeValue;
      const matches = [];
      for (const id of activeRubrics) {
        const patterns = RUBRIC_PATTERNS[id] || [];
        for (const re of patterns) {
          re.lastIndex = 0;
          let m;
          while ((m = re.exec(text)) !== null) {
            if (m[0].length === 0) { re.lastIndex++; continue; }
            matches.push({ start: m.index, end: m.index + m[0].length, rubricId: id });
          }
        }
      }
      for (const id of activeDispositions) {
        const patterns = DISPOSITION_PATTERNS[id] || [];
        for (const re of patterns) {
          re.lastIndex = 0;
          let m;
          while ((m = re.exec(text)) !== null) {
            if (m[0].length === 0) { re.lastIndex++; continue; }
            matches.push({ start: m.index, end: m.index + m[0].length, family: id });
          }
        }
      }
      if (matches.length === 0) continue;

      // Merge overlapping ranges. Keep the earliest rubric (first in
      // insertion order) when ranges overlap — predictable, and matches
      // the visual expectation that "the first thing you turned on wins
      // when they collide".
      matches.sort((a, b) => a.start - b.start || a.end - b.end);
      const merged = [];
      for (const m of matches) {
        const last = merged[merged.length - 1];
        if (last && m.start < last.end) {
          last.end = Math.max(last.end, m.end);
        } else {
          merged.push({ ...m });
        }
      }

      // Build the replacement fragment.
      const frag = document.createDocumentFragment();
      let cursor = 0;
      for (const m of merged) {
        if (m.start > cursor) {
          frag.appendChild(document.createTextNode(text.slice(cursor, m.start)));
        }
        const mark = document.createElement("mark");
        if (m.family) {
          mark.className = "disp-mark";
          mark.dataset.family = m.family;
          mark.dataset.colorSlot = dispositionSlot(m.family);
          mark.title = dispositionLabel(m.family);
        } else {
          mark.className = "rubric-mark";
          mark.dataset.rubric = m.rubricId;
          mark.dataset.colorSlot = slots.get(m.rubricId) || "amber";
          mark.title = rubricLabel(m.rubricId);
        }
        mark.textContent = text.slice(m.start, m.end);
        frag.appendChild(mark);
        cursor = m.end;
      }
      if (cursor < text.length) {
        frag.appendChild(document.createTextNode(text.slice(cursor)));
      }
      node.parentNode.replaceChild(frag, node);
    }
  }

  // Apply highlights to every column's result-body. Called after every
  // grid render and whenever activeRubrics changes.
  function applyRubricHighlights() {
    document.querySelectorAll("#results-grid .result-body, #overlay-root .result-body")
      .forEach((el) => highlightElement(el));
  }

  // Render the chip strip + show/hide the controls bar based on state.
  function renderRubricControls() {
    const controls = document.getElementById("rubric-controls");
    const chips    = document.getElementById("rubric-active-chips");
    const hint     = document.getElementById("rubric-hint");
    if (!controls || !chips) return;
    if (activeRubrics.size === 0) {
      controls.classList.add("hidden");
      if (hint) hint.classList.remove("hidden");
      chips.innerHTML = "";
      return;
    }
    controls.classList.remove("hidden");
    if (hint) hint.classList.add("hidden");
    const slots = buildColorSlotMap();
    chips.innerHTML = Array.from(activeRubrics).map((id) => `
      <span class="rubric-chip" data-rubric="${escapeHtml(id)}"
            data-color-slot="${escapeHtml(slots.get(id) || "amber")}"
            title="Click to remove this highlight">
        ${escapeHtml(rubricLabel(id))}
        <span class="rubric-chip__close" aria-hidden="true">×</span>
      </span>
    `).join("");
    // Sync the row's pressed/active state in the analysis table.
    document.querySelectorAll(".rubric-row").forEach((row) => {
      const id = row.dataset.rubric;
      const isActive = activeRubrics.has(id);
      row.classList.toggle("rubric-row--active", isActive);
      row.setAttribute("aria-pressed", isActive ? "true" : "false");
      if (isActive) {
        row.dataset.colorSlot = slots.get(id) || "amber";
      } else {
        delete row.dataset.colorSlot;
      }
    });
  }

  // Toggle a rubric on/off and re-apply highlights without re-fetching.
  function toggleRubric(rubricId) {
    if (!rubricId || !RUBRIC_PATTERNS[rubricId]) {
      // Soft-fail: rubric not in pattern map (e.g. row that hasn't been
      // wired up yet). Just bail.
      return;
    }
    if (activeRubrics.has(rubricId)) {
      activeRubrics.delete(rubricId);
    } else {
      activeRubrics.add(rubricId);
    }
    // Re-render the grid so existing highlights are wiped (DOM nodes
    // get rebuilt), then apply the new active set. Cheaper than diffing
    // the existing marks.
    renderGrid();
    renderRubricControls();
  }

  function clearAllRubrics() {
    if (activeRubrics.size === 0) return;
    activeRubrics.clear();
    renderGrid();
    renderRubricControls();
  }

  /* -------------------------------------------------------------------------
   * Disposition lens — chip strip + per-column tallies. Chips toggle the
   * five paper behavior families; every visible output column then shows
   * its matches color-coded, with a per-family count under the column
   * title so density differences read at a glance.
   * ---------------------------------------------------------------------- */
  function renderDispositionLens() {
    const host = document.getElementById("disp-lens-chips");
    if (!host) return;
    const allOn = activeDispositions.size === DISPOSITION_FAMILIES.length;
    host.innerHTML = DISPOSITION_FAMILIES.map((f) => `
      <button type="button"
              class="disp-chip${activeDispositions.has(f.id) ? " disp-chip--active" : ""}"
              data-family="${f.id}" data-color-slot="${f.slot}"
              aria-pressed="${activeDispositions.has(f.id) ? "true" : "false"}"
              data-tooltip="${escapeHtml(f.desc)}">${escapeHtml(f.label)}</button>
    `).join("") + `
      <button type="button" class="disp-chip disp-chip--all" id="disp-all"
              data-tooltip="Toggle all five families at once">${allOn ? "Clear all" : "All five"}</button>`;
  }

  function renderDispositionTallies() {
    document
      .querySelectorAll("#results-grid > article.card, #overlay-root article.card")
      .forEach((card) => {
        let tally = card.querySelector(".disp-tally");
        if (activeDispositions.size === 0) {
          if (tally) tally.remove();
          return;
        }
        const counts = DISPOSITION_FAMILIES
          .filter((f) => activeDispositions.has(f.id))
          .map((f) => ({
            f,
            n: card.querySelectorAll(`mark.disp-mark[data-family="${f.id}"]`).length,
          }));
        if (!tally) {
          tally = document.createElement("div");
          tally.className = "disp-tally";
          const title = card.querySelector(".card__title");
          if (title && title.parentNode) {
            title.parentNode.insertBefore(tally, title.nextSibling);
          } else {
            card.prepend(tally);
          }
        }
        tally.innerHTML = counts.map(({ f, n }) => `
          <span class="disp-tally__item${n === 0 ? " disp-tally__item--zero" : ""}"
                data-color-slot="${f.slot}"
                data-tooltip="${escapeHtml(f.label)}">${escapeHtml(f.short)} ${n}</span>`).join("");
      });
  }

  function toggleDisposition(familyId) {
    if (!DISPOSITION_PATTERNS[familyId]) return;
    if (activeDispositions.has(familyId)) {
      activeDispositions.delete(familyId);
    } else {
      activeDispositions.add(familyId);
    }
    renderGrid();
    renderDispositionLens();
  }

  /* -------------------------------------------------------------------------
   * Inspector rendering — one collapsible disclosure per column. Three
   * branches based on what data is available:
   *
   *   v2 local-council  → full per-phase inspector built from the embedded
   *                       deliberation (planner, 3 seats, synthesis); each
   *                       phase shows system prompt + user input + reasoning
   *                       + output.
   *   v1 opus-council   → markdown section parser; each known section
   *                       (Decomposition / Healthcare / Legal / Finance /
   *                       Tensions / Synthesis) renders as a phase.
   *   v1 opus-single    → no native section structure; render the full
   *                       captured response as a single phase.
   *
   * Reasoning content only exists where we actually captured it. For Opus
   * paste-ins, the helper notes that thinking wasn't included at paste time
   * rather than silently omitting it — makes the data-capture limitation
   * visible.
   * ---------------------------------------------------------------------- */

  // One phase row inside an inspector. All subsections are collapsible
  // disclosures so dense outputs don't dominate the column.
  function renderPhase({ label, meta, systemPrompt, userMessage, thinking, output, note }) {
    const parts = [];
    if (systemPrompt) {
      parts.push(`<details class="phase__detail">
        <summary>System prompt</summary>
        <pre class="prompt-block">${escapeHtml(systemPrompt)}</pre>
      </details>`);
    }
    if (userMessage) {
      parts.push(`<details class="phase__detail">
        <summary>User message / dispatched sub-question</summary>
        <pre class="prompt-block">${escapeHtml(userMessage)}</pre>
      </details>`);
    }
    if (thinking && thinking.length > 0) {
      // Default-open the reasoning when there's actual content — that's
      // the thing this page is specifically designed to surface.
      parts.push(`<details class="phase__detail" open>
        <summary>Reasoning (${thinking.length} block${thinking.length > 1 ? "s" : ""})</summary>
        ${thinking.map((t) => `<pre class="thinking-block">${escapeHtml(t)}</pre>`).join("")}
      </details>`);
    } else if (note) {
      parts.push(`<details class="phase__detail">
        <summary>Reasoning</summary>
        <pre class="thinking-block" style="font-style:italic">${escapeHtml(note)}</pre>
      </details>`);
    }
    if (output) {
      parts.push(`<details class="phase__detail" open>
        <summary>Output</summary>
        <pre class="output-block">${escapeHtml(output)}</pre>
      </details>`);
    }
    return `<section class="phase">
      <h4 class="phase__title">${escapeHtml(label)}
        ${meta ? `<span class="phase__meta">${escapeHtml(meta)}</span>` : ""}
      </h4>
      ${parts.join("")}
    </section>`;
  }

  // Wrap an array of phase sections in the outer collapsible inspector.
  function wrapInspector(sections, summaryText) {
    return `<details class="inspector">
      <summary>${escapeHtml(summaryText || "Inspect — system prompts, reasoning, outputs by phase")}</summary>
      <div class="inspector__content">${sections.join("")}</div>
    </details>`;
  }

  // Inspector for v2 local-council imports: full per-phase breakdown from
  // the orchestrator's audit log. Surfaces every system prompt, every
  // dispatched sub-question, every reasoning block, every output.
  function renderCouncilInspector(deliberation) {
    if (!deliberation) return "";
    const sections = [];

    // ---- Phase 1: Lead — Planner ----
    const planInputs = splitInputMessages(deliberation.plan_input_messages || []);
    const { reasoning: planReasoning, json: planJson } = splitPlannerOutput(deliberation.plan_raw || "");
    sections.push(renderPhase({
      label: "Lead — Planner",
      meta: fmtMs(deliberation.plan_latency_ms),
      systemPrompt: planInputs.system,
      userMessage: planInputs.user,
      thinking: planReasoning ? [planReasoning] : [],
      output: planJson || deliberation.plan_raw || "",
    }));

    // ---- Phase 2: Industry seats ----
    const seatLabels = {
      healthcare: "Healthcare seat",
      legal:      "Legal seat",
      finance:    "Finance seat",
    };
    for (const turn of (deliberation.turns || [])) {
      const inputs = splitInputMessages(turn.input_messages || []);
      const { thinking, speech } = splitThinking(turn.output_text || "");
      const structuredThinking = extractStructuredThinking(turn.raw_response || {});
      const allThinking = [...structuredThinking, ...thinking];
      const seatLabel = seatLabels[turn.seat] || turn.seat;
      const memberName = turn.member_name ? ` — ${turn.member_name}` : "";
      // For pathway-3 swap runs each turn carries which backend served it.
      // Surface it in the meta line so a reader walking through the
      // inspector sees per-phase composition without cross-referencing
      // the cabinet badge.
      const backendTag = turn.backend ? ` · backend: ${turn.backend}` : "";
      const tokMeta = `${turn.prompt_eval_count || 0} tok in · ${turn.eval_count || 0} tok out`;
      sections.push(renderPhase({
        label: seatLabel + memberName,
        meta: `${fmtMs(turn.latency_ms)} · ${tokMeta}${backendTag}`,
        systemPrompt: inputs.system,
        userMessage: inputs.user,
        thinking: allThinking,
        output: speech || turn.output_text || "",
      }));
    }

    // ---- Phase 3: Lead — Synthesis ----
    if (deliberation.synthesis) {
      const synth = deliberation.synthesis;
      const inputs = splitInputMessages(synth.input_messages || []);
      const { thinking, speech } = splitThinking(synth.output_text || "");
      const tokMeta = `${synth.prompt_eval_count || 0} tok in · ${synth.eval_count || 0} tok out`;
      sections.push(renderPhase({
        label: "Lead — Synthesis",
        meta: `${fmtMs(synth.latency_ms)} · ${tokMeta}`,
        systemPrompt: inputs.system,
        userMessage: inputs.user,
        thinking: thinking,
        output: speech || synth.output_text || "",
      }));
    }

    return wrapInspector(sections);
  }

  /* -------------------------------------------------------------------------
   * Opus inspectors — both reshape the paste-in into the same 5-phase
   * structure local-council uses:
   *
   *     1. Lead — Planner
   *     2. Healthcare seat
   *     3. Legal seat
   *     4. Finance seat
   *     5. Lead — Synthesis
   *
   * For opus-council, the captured text already has Decomposition /
   * <Seat> Specialist / Tensions / Synthesis section headings — we split
   * by heading and remap. Tensions and Synthesis merge into a single
   * "Lead — Synthesis" phase since they're a two-step output of the same
   * synthesis call.
   *
   * For opus-single, the captured text has no native phase structure
   * (it's one synthesized response). We partition by the *prose* section
   * headings Opus naturally produced and route each chunk to the closest
   * seat: Clinical → Healthcare, Legal / Regulatory → Legal, Financial /
   * Economics → Finance; the recommendation / implementation / risks
   * sections route to Lead — Synthesis. The user message for the synth
   * phase is the original case prompt (since opus-single takes the
   * full question itself).
   *
   * Both rely on /api/prompts so the System prompt slot shows the actual
   * bytes the model saw, not a paraphrase.
   * ---------------------------------------------------------------------- */

  // Section headings the Opus-as-council mode emits as plaintext anchors
  // (no `##` prefix, since Claude.ai strips markdown at copy time).
  const OPUS_COUNCIL_SECTION_NAMES = [
    "Decomposition",
    "Healthcare Specialist",
    "Legal Specialist",
    "Finance Specialist",
    "Tensions",
    "Synthesis",
  ];

  // Walk the captured opus-council text and chop it into named sections
  // based on whole-line occurrences of the section names above. Returns
  // an object keyed by section name -> body string.
  function parseOpusCouncilSections(text) {
    const out = {};
    if (!text) return out;
    const lines = text.split("\n");
    let currentTitle = null;
    let currentBody = [];
    for (const line of lines) {
      const trimmed = line.trim().replace(/^##\s*/, "");
      if (OPUS_COUNCIL_SECTION_NAMES.includes(trimmed)) {
        if (currentTitle !== null) {
          out[currentTitle] = currentBody.join("\n").trim();
        }
        currentTitle = trimmed;
        currentBody = [];
      } else {
        currentBody.push(line);
      }
    }
    if (currentTitle !== null) {
      out[currentTitle] = currentBody.join("\n").trim();
    }
    return out;
  }

  // Pull the per-seat sub-questions out of a Decomposition section. The
  // planner emits them as `<Seat> sub-question: ...` lines. The body of
  // the sub-question can span multiple paragraphs until the next labeled
  // line or the "Recency-sensitive" / "Specialists consulted" markers.
  function extractOpusSubQuestions(decompText) {
    const result = { healthcare: "", legal: "", finance: "" };
    if (!decompText) return result;
    const seatPatterns = [
      { key: "healthcare", re: /Healthcare sub-question:\s*([\s\S]*?)(?=\n[A-Z][\w/ ]+ sub-question:|\nRecency-sensitive\??:|\nSpecialists consulted:|$)/i },
      { key: "legal",      re: /Legal sub-question:\s*([\s\S]*?)(?=\n[A-Z][\w/ ]+ sub-question:|\nRecency-sensitive\??:|\nSpecialists consulted:|$)/i },
      { key: "finance",    re: /Finance sub-question:\s*([\s\S]*?)(?=\n[A-Z][\w/ ]+ sub-question:|\nRecency-sensitive\??:|\nSpecialists consulted:|$)/i },
    ];
    for (const { key, re } of seatPatterns) {
      const m = decompText.match(re);
      if (m) result[key] = m[1].trim();
    }
    return result;
  }

  // Reconstruct the user-side input the synthesis step received in
  // opus-council: USER QUESTION, then each seat's contribution. This
  // matches the shape the local-council orchestrator builds for its
  // own synthesis call, so the two inspectors read parallel.
  function buildSynthesisBundle(casePrompt, sections) {
    const parts = [`USER QUESTION:\n${casePrompt || "(case prompt not available)"}`];
    if (sections["Healthcare Specialist"]) {
      parts.push(`HEALTHCARE CONTRIBUTION:\n${sections["Healthcare Specialist"]}`);
    }
    if (sections["Legal Specialist"]) {
      parts.push(`LEGAL CONTRIBUTION:\n${sections["Legal Specialist"]}`);
    }
    if (sections["Finance Specialist"]) {
      parts.push(`FINANCE CONTRIBUTION:\n${sections["Finance Specialist"]}`);
    }
    return parts.join("\n\n");
  }

  // Render an opus-council paste-in into the same 5-phase shape as
  // local-council. System prompts come from /api/prompts so the inspector
  // shows the actual bytes the model saw.
  function renderOpusCouncilInspector(text, casePrompt) {
    if (!text) return "";
    const sections = parseOpusCouncilSections(text);
    if (Object.keys(sections).length === 0) {
      // Fallback: no known headings — show the whole thing as a single
      // captured response with the synthesis system prompt.
      return wrapInspector([renderPhase({
        label: "Opus-as-council — captured response",
        meta: `${text.length.toLocaleString()} chars`,
        note: OPUS_PASTE_NOTE,
        output: text,
      })]);
    }

    const subQs = extractOpusSubQuestions(sections["Decomposition"] || "");
    const prompts = promptsCache || {};
    const phases = [];

    // ---- Phase 1: Lead — Planner ----
    phases.push(renderPhase({
      label: "Lead — Planner",
      meta: `${(sections["Decomposition"] || "").length.toLocaleString()} chars out`,
      systemPrompt: prompts.lead_planner || "",
      userMessage: casePrompt || "",
      note: OPUS_PASTE_NOTE,
      output: sections["Decomposition"] || "",
    }));

    // ---- Phase 2-4: Industry seats ----
    const seatConfigs = [
      { label: "Healthcare seat (Opus)", sysKey: "healthcare", section: "Healthcare Specialist", subKey: "healthcare" },
      { label: "Legal seat (Opus)",      sysKey: "legal",      section: "Legal Specialist",      subKey: "legal" },
      { label: "Finance seat (Opus)",    sysKey: "finance",    section: "Finance Specialist",    subKey: "finance" },
    ];
    for (const cfg of seatConfigs) {
      const body = sections[cfg.section] || "";
      if (!body && !subQs[cfg.subKey]) continue;
      phases.push(renderPhase({
        label: cfg.label,
        meta: `${body.length.toLocaleString()} chars out`,
        systemPrompt: prompts[cfg.sysKey] || "",
        userMessage: subQs[cfg.subKey] || "(sub-question not parsed from Decomposition)",
        note: OPUS_PASTE_NOTE,
        output: body,
      }));
    }

    // ---- Phase 5: Lead — Synthesis (Tensions + Synthesis merged) ----
    const tensionsBody = sections["Tensions"] || "";
    const synthBody    = sections["Synthesis"] || "";
    const mergedSynth = [
      tensionsBody ? `## Tensions\n\n${tensionsBody}` : "",
      synthBody    ? `## Synthesis\n\n${synthBody}`    : "",
    ].filter(Boolean).join("\n\n");
    if (mergedSynth) {
      phases.push(renderPhase({
        label: "Lead — Synthesis",
        meta: `${mergedSynth.length.toLocaleString()} chars out`,
        systemPrompt: prompts.lead_synthesis || "",
        userMessage: buildSynthesisBundle(casePrompt, sections),
        note: OPUS_PASTE_NOTE,
        output: mergedSynth,
      }));
    }

    return wrapInspector(phases);
  }

  // Heading → seat routing table for opus-single partitioning. Keys are
  // whole-line headings Opus emits in single-shot mode; values are the
  // phase bucket each chunk gets routed to.
  //
  // Two flavors are accommodated:
  //   case 4 (GLP-1)      — Clinical dimension / Legal dimension / Financial dimension
  //   case 2 (DTx launch) — Clinical evidence dimension / Regulatory and data-protection dimension / Reimbursement and economics
  //
  // Anything below the last seat heading that isn't itself a seat heading
  // is treated as part of the Lead synthesis (recommendations, timeline,
  // risks, where the recommendation could shift, etc.).
  const OPUS_SINGLE_HEADING_MAP = {
    // Healthcare
    "Clinical dimension":                 "healthcare",
    "Clinical evidence dimension":        "healthcare",
    "Clinical considerations":            "healthcare",
    // Legal
    "Legal dimension":                    "legal",
    "Legal considerations":               "legal",
    "Regulatory and data-protection dimension": "legal",
    // Finance
    "Financial dimension":                "finance",
    "Financial considerations":           "finance",
    "Reimbursement and economics":        "finance",
    // Synthesis
    "Recommended utilization management criteria": "synthesis",
    "Implementation considerations":      "synthesis",
    "Where the recommendation could shift": "synthesis",
    "Realistic 18-month timeline":        "synthesis",
    "Risks and what could break the plan": "synthesis",
  };

  // Partition opus-single text into the same 5-phase buckets local-council
  // uses. The first chunk (before any known heading) gets prepended to the
  // synthesis intro since opus-single typically opens with its top-line
  // recommendation paragraph. Body chunks include their heading so the
  // shape of the original response is preserved.
  function partitionOpusSingle(text) {
    const buckets = { intro: "", healthcare: "", legal: "", finance: "", synthesis: "" };
    if (!text) return buckets;
    const lines = text.split("\n");
    let currentBucket = "intro";
    let currentHeading = null;
    let currentBody = [];
    const flush = () => {
      const chunk = (currentHeading ? currentHeading + "\n" : "") + currentBody.join("\n").trim();
      const trimmed = chunk.trim();
      if (trimmed) {
        buckets[currentBucket] = buckets[currentBucket]
          ? buckets[currentBucket] + "\n\n" + trimmed
          : trimmed;
      }
    };
    for (const line of lines) {
      const stripped = line.trim();
      // A heading is a whole-line, exact match — protects against false
      // positives where the same phrase appears mid-paragraph.
      if (line === stripped && OPUS_SINGLE_HEADING_MAP[stripped]) {
        flush();
        currentBucket = OPUS_SINGLE_HEADING_MAP[stripped];
        currentHeading = stripped;
        currentBody = [];
      } else {
        currentBody.push(line);
      }
    }
    flush();
    // Roll intro into synthesis: the top-of-response framing in opus-single
    // is the model's recommendation framing, which is logically part of the
    // synthesis phase, not a separate "intro".
    if (buckets.intro) {
      buckets.synthesis = buckets.synthesis
        ? buckets.intro + "\n\n" + buckets.synthesis
        : buckets.intro;
      buckets.intro = "";
    }
    return buckets;
  }

  // Render opus-single into the same 5-phase shape as local-council. The
  // planner phase shows the actual prompt the single-shot system saw (no
  // decomposition was performed by Opus — we represent that honestly with
  // a note); the seats show the partitioned chunks routed by heading; the
  // synthesis phase carries the recommendation/implementation/risks
  // content plus the response intro.
  function renderOpusSingleInspector(text, casePrompt) {
    if (!text) return "";
    const parts = partitionOpusSingle(text);
    const anyPartitioned = parts.healthcare || parts.legal || parts.finance || parts.synthesis;
    if (!anyPartitioned) {
      // No known headings matched — render as a single captured response
      // so we don't silently drop content.
      return wrapInspector([renderPhase({
        label: "Opus 4.7 single-shot — captured response",
        meta: `${text.length.toLocaleString()} chars`,
        systemPrompt: (promptsCache || {}).opus_single || "",
        userMessage: casePrompt || "",
        note: OPUS_PASTE_NOTE,
        output: text,
      })]);
    }

    const prompts = promptsCache || {};
    const phases = [];

    // ---- Phase 1: Lead — Planner ----
    // In single-shot mode there's no separate planner call — Opus saw the
    // whole question and produced one response. Surface that honestly
    // rather than fabricate a decomposition phase.
    phases.push(renderPhase({
      label: "Lead — Planner",
      meta: "no separate planner call",
      systemPrompt: prompts.opus_single || "",
      userMessage: casePrompt || "",
      note: "Single-shot mode: there is no separate planner phase. Opus received the full case prompt under the single-shot system prompt above and produced one synthesized response — the partitioning into seat/synthesis phases below is a reading aid based on the headings Opus emitted, not separate model calls.",
      output: "(no distinct planner output — see seats and synthesis below)",
    }));

    // ---- Phase 2-4: Industry seats (heading-routed chunks) ----
    const seatConfigs = [
      { label: "Healthcare seat (Opus)", sysKey: "healthcare", bucketKey: "healthcare" },
      { label: "Legal seat (Opus)",      sysKey: "legal",      bucketKey: "legal" },
      { label: "Finance seat (Opus)",    sysKey: "finance",    bucketKey: "finance" },
    ];
    for (const cfg of seatConfigs) {
      const body = parts[cfg.bucketKey];
      phases.push(renderPhase({
        label: cfg.label,
        meta: body ? `${body.length.toLocaleString()} chars out` : "no section emitted",
        systemPrompt: prompts[cfg.sysKey] || "",
        userMessage: casePrompt || "",
        note: OPUS_PASTE_NOTE,
        output: body || "(no section matching this seat was emitted in the single-shot response)",
      }));
    }

    // ---- Phase 5: Lead — Synthesis ----
    phases.push(renderPhase({
      label: "Lead — Synthesis",
      meta: parts.synthesis ? `${parts.synthesis.length.toLocaleString()} chars out` : "—",
      systemPrompt: prompts.lead_synthesis || "",
      userMessage: casePrompt || "",
      note: OPUS_PASTE_NOTE,
      output: parts.synthesis || "(no recommendation/implementation/risks sections were partitioned out of the single-shot response)",
    }));

    return wrapInspector(phases);
  }

  // Describe the cabinet composition for a v2 imported run. Returns either
  // null (for runs that predate the per-phase backend recording, or for
  // baseline modes where the composition is uniform), or an object with a
  // short badge label and a longer tooltip listing every phase → backend.
  //
  // Used only by the column header meta row to give the swap runs an
  // at-a-glance "Opus playing Healthcare" tag. The full breakdown lives
  // in the inspector's per-phase backend column.
  function describeCabinet(run) {
    const delib = run && run.deliberation;
    if (!delib) return null;
    const backends = delib.cabinet_backends || {};
    const entries = Object.entries(backends);
    if (entries.length === 0) return null;
    // Bucket each phase by what played it. "ollama" is the default local
    // chat (whichever fine-tune the seat owns); anything else is an
    // override worth surfacing on the badge.
    //   - "opus"             → Opus-swap variants (pathway-3 frontier)
    //   - "ollama:<tag>"     → local non-default backend (e.g. Phi-4
    //                          playing a seat, or gpt-oss as council)
    const defaultPhases  = entries.filter(([, tag]) => tag === "ollama").map(([p]) => p);
    const overridePhases = entries.filter(([, tag]) => tag !== "ollama" && tag !== "");
    // All-default — uniform local cabinet, nothing to surface.
    if (defaultPhases.length === entries.length) return null;
    // All-override with a single backend — uniform cabinet using one
    // non-default model (opus-council, gptoss-council). Show a tidy
    // "<Backend> · uniform cabinet" badge so the reader sees this is a
    // single-model run, not a swap.
    if (overridePhases.length === entries.length) {
      const uniqueBackends = new Set(overridePhases.map(([, t]) => t));
      if (uniqueBackends.size === 1) {
        const tag = overridePhases[0][1];
        const display = tag.startsWith("ollama:gpt-oss") ? "gpt-oss-20B"
                      : tag.startsWith("ollama:") ? tag.replace("ollama:", "")
                      : tag === "opus" ? "Opus 4.7"
                      : tag;
        return {
          label: `${display} · uniform cabinet`,
          tooltip: entries.map(([p, t]) => `${p}: ${t}`).join("\n"),
        };
      }
      // Multiple non-default backends but no default — exotic; fall
      // through to the mixed-cabinet display below.
    }
    // Pretty-print the override label. Group by backend so a hypothetical
    // multi-phase swap ("Healthcare + Legal both Opus") reads cleanly.
    const byBackend = new Map();
    for (const [phase, tag] of overridePhases) {
      // Compact display name for the backend — strip the "ollama:" prefix
      // since "ollama:phi4:14b" is verbose for a badge.
      const display = tag.startsWith("ollama:") ? "Phi-4" : tag === "opus" ? "Opus" : tag;
      if (!byBackend.has(display)) byBackend.set(display, []);
      byBackend.get(display).push(phase);
    }
    const labelParts = [];
    for (const [backend, phases] of byBackend) {
      const phaseList = phases.map((p) => p[0].toUpperCase() + p.slice(1)).join(", ");
      labelParts.push(`${backend} · ${phaseList}`);
    }
    const label = labelParts.join(" / ");
    const tooltip = entries
      .map(([p, tag]) => `${p}: ${tag}`)
      .join("\n");
    return { label, tooltip };
  }

  // Extract the "final answer" portion of a run for the top body of the
  // column — the bit that's logically equivalent to local-council's
  // synthesis output. This keeps the top component consistent across
  // modes: every column's top body is the model's recommendation, not
  // the upstream scaffolding.
  //
  //   local-council  → run.final_output is already just the synthesis,
  //                    use it verbatim.
  //   opus-council   → run.final_output is the whole pipeline; pull out
  //                    just the Tensions + Synthesis sections.
  //   opus-single    → run.final_output IS the model's final answer
  //                    (single-shot, no upstream scaffolding); use it
  //                    verbatim.
  //
  // The full captured text remains available via the per-phase inspector
  // below, so nothing is hidden — this is purely a top-of-column reformat
  // for at-a-glance comparison.
  function extractFinalAnswer(modeKey, run) {
    if (!run) return "";
    const raw = run.final_output || "";
    if (modeKey === "opus-council") {
      const sections = parseOpusCouncilSections(raw);
      const tensions = sections["Tensions"] || "";
      const synth    = sections["Synthesis"] || "";
      const merged = [
        tensions ? `## Tensions\n\n${tensions}` : "",
        synth    ? `## Synthesis\n\n${synth}`    : "",
      ].filter(Boolean).join("\n\n");
      return merged || raw;  // fallback: if section parsing missed, show all
    }
    return raw;
  }

  // Top-level dispatcher: pick the right inspector path based on what
  // shape the imported run carries.
  function renderInspector(modeKey, run, casePrompt) {
    if (!run) return "";
    if (run.deliberation) {
      return renderCouncilInspector(run.deliberation);
    }
    if (modeKey === "opus-council") {
      return renderOpusCouncilInspector(run.final_output || "", casePrompt);
    }
    if (modeKey === "opus-single") {
      return renderOpusSingleInspector(run.final_output || "", casePrompt);
    }
    return "";
  }

  /* -------------------------------------------------------------------------
   * Prompts cache — pull the actual bytes each phase saw, so the inspector
   * shows them under "System prompt" instead of leaving the slot empty.
   * One-shot fetch at boot; the prompts are immutable per session.
   * ---------------------------------------------------------------------- */
  async function loadPrompts() {
    try {
      const r = await fetch("/data/prompts.json");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      promptsCache = await r.json();
    } catch (e) {
      console.warn("Failed to load /api/prompts; system prompt slots will be empty.", e);
      promptsCache = {};
    }
  }

  /* -------------------------------------------------------------------------
   * Initial load — populate the case selector
   * ---------------------------------------------------------------------- */
  function initCaseSelector() {
    els.caseSelect.innerHTML = CASES.map(
      (c) => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.label)}</option>`
    ).join("");
    els.caseSelect.disabled = false;
    // Default to the first case in the list (case 4 GLP-1).
    currentCaseId = CASES[0].id;
    els.caseSelect.value = currentCaseId;
    loadCase(currentCaseId);
  }

  els.caseSelect.addEventListener("change", () => {
    const id = els.caseSelect.value;
    if (!id || id === currentCaseId) return;
    currentCaseId = id;
    // Collapse any open overlay on case switch so it doesn't leak across.
    setExpandedMode(null, /*skipRender=*/true);
    // Wipe active rubrics — the new case has a different rubric set, so
    // carrying highlights over would either be meaningless (rubric ID
    // doesn't exist) or misleading (different scope of evidence).
    activeRubrics.clear();
    renderRubricControls();
    loadCase(id);
  });

  /* -------------------------------------------------------------------------
   * Load + render
   * ---------------------------------------------------------------------- */
  async function loadCase(caseId) {
    try {
      const r = await fetch(`/data/imported/${encodeURIComponent(caseId)}.json`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      currentData = await r.json();
    } catch (e) {
      console.error("Failed to load imported runs", e);
      els.grid.innerHTML = `<article class="card">
        <p class="text-soft">Failed to load: ${escapeHtml(e.message)}</p>
      </article>`;
      return;
    }
    els.promptDisplay.value = currentData.case_prompt || "";
    renderGrid();
    renderAnalysisPanel();
  }

  // Render the result columns plus the overlay (if any column is currently
  // expanded). Column set is dynamic: the three baselines always show, and
  // any pathway-3 swap variant with an imported run appears after the
  // baselines in canonical phase order. Re-applies active rubric highlights
  // after the DOM is rebuilt, since innerHTML wipes the previous marks.
  function renderGrid() {
    if (!currentData) return;
    const modes = activeModeOrder(currentData.modes);
    els.grid.innerHTML = modes
      .map((mode) => renderColumn(mode, currentData.modes[mode]))
      .join("");
    if (els.overlayRoot) {
      els.overlayRoot.innerHTML = renderOverlay();
    }
    document.body.classList.toggle("has-overlay", !!expandedMode);
    applyRubricHighlights();
    renderDispositionTallies();
  }

  function renderColumn(modeKey, run) {
    const title = MODE_TITLES[modeKey] || modeKey;
    const header = `<h3 class="card__title">
      ${escapeHtml(title)}
      <button class="card__expand" type="button"
              data-expand="${escapeHtml(modeKey)}"
              aria-label="Expand ${escapeHtml(title)}"
              title="Expand">⤢</button>
    </h3>`;

    if (!run) {
      return `<article class="card" data-mode="${escapeHtml(modeKey)}">
        ${header}
        <p class="text-faint">No imported run for this mode yet.</p>
      </article>`;
    }

    // Meta row mirrors the A/B page's completed-column meta line: mode tag,
    // import provenance, output size. The char count reflects the FULL
    // captured text (not the trimmed top body), since that's the more
    // honest measure of how much the model produced.
    const sourceTag = run.source === "audit_log_link" ? "from audit log" : "manual paste";
    const charCount = (run.final_output || "").length;
    const modelLabel = run.model || "";

    // For pathway-3 swap runs the audit log records which phase actually
    // went to Opus (the rest stayed local Ollama). Surface that here so a
    // reader scanning the grid sees the cabinet composition at a glance,
    // without having to open the inspector.
    const cabinetTag = describeCabinet(run);
    const cabinetBadge = cabinetTag
      ? `<span class="cabinet-badge" title="${escapeHtml(cabinetTag.tooltip)}">${escapeHtml(cabinetTag.label)}</span>`
      : "";

    const meta = `<div class="card__meta" style="margin-bottom: var(--space-3); display:flex; flex-wrap:wrap; gap:var(--space-3);">
      <span><span class="pill" data-status="completed">imported</span></span>
      <span title="${escapeHtml(modelLabel)}">${escapeHtml(sourceTag)} · v${run.schema_version}</span>
      <span>${charCount.toLocaleString()} chars</span>
      ${cabinetBadge}
    </div>`;

    // Top body shows the model's final-answer equivalent: synthesis for
    // local-council and opus-council, the full single-shot response for
    // opus-single. Keeps the three columns visually comparable at a glance
    // instead of dumping opus-council's whole pipeline inline. Upstream
    // scaffolding (planner output, specialist contributions) is still
    // available in the per-phase inspector below.
    //
    // We beautify the markdown (## headings, **bold**, bullets, numbered
    // lists) for readability instead of dumping the raw text in a <pre>.
    // The inspector's per-phase outputs intentionally stay as <pre> blocks
    // so reviewers can audit exactly what each model emitted byte-for-byte.
    const finalDisplay = stripThinking(extractFinalAnswer(modeKey, run));
    const body = `<div class="result-body">${beautifyMarkdown(finalDisplay)}</div>`;

    // Per-phase inspector with system prompts, reasoning, and outputs.
    // For v2 local-council imports this comes from the embedded
    // deliberation; for v1 Opus paste-ins it's reconstructed from the
    // captured text (with a clear note about missing thinking content)
    // and the actual system prompts pulled from /api/prompts.
    const inspector = renderInspector(modeKey, run, currentData?.case_prompt || "");

    return `<article class="card" data-mode="${escapeHtml(modeKey)}">
      ${header}
      ${meta}
      ${body}
      ${inspector}
    </article>`;
  }

  /* -------------------------------------------------------------------------
   * Overlay — same shape as A/B page. ⤢ pops a column to a centered modal
   * at ~1100px wide / 90vh tall. × button, backdrop click, and Escape close.
   * ---------------------------------------------------------------------- */
  function renderOverlay() {
    if (!expandedMode || !currentData) return "";
    const run = currentData.modes[expandedMode];
    const title = MODE_TITLES[expandedMode] || expandedMode;
    const columnHtml = renderColumn(expandedMode, run);
    return `<div class="overlay" role="dialog" aria-modal="true"
                 aria-label="${escapeHtml(title)} expanded view">
      <div class="overlay__backdrop" data-close-overlay></div>
      <div class="overlay__panel">
        <button class="overlay__close" type="button"
                data-close-overlay aria-label="Close expanded view">×</button>
        ${columnHtml}
      </div>
    </div>`;
  }

  function setExpandedMode(modeOrNull, skipRender) {
    if (expandedMode === modeOrNull) return;
    expandedMode = modeOrNull;
    if (!skipRender) renderGrid();
  }

  /* -------------------------------------------------------------------------
   * Analysis toggle — show only the prose block matching the current case
   * ---------------------------------------------------------------------- */
  function renderAnalysisPanel() {
    if (!currentData) return;
    $$("#analysis-panel [data-analysis]").forEach((el) => {
      el.classList.toggle("hidden", el.dataset.analysis !== currentData.case_id);
    });
  }

  /* -------------------------------------------------------------------------
   * Event delegation: expand / close / Escape (same as A/B page) +
   * rubric-row toggling for highlight interactivity. Single delegated
   * listener on document so it survives re-renders.
   * ---------------------------------------------------------------------- */
  document.addEventListener("click", (e) => {
    const expander = e.target.closest("[data-expand]");
    if (expander) {
      setExpandedMode(expander.dataset.expand);
      return;
    }
    if (e.target.matches("[data-close-overlay]")) {
      setExpandedMode(null);
      return;
    }

    // Clear-all button in the rubric controls bar.
    if (e.target.closest("#rubric-clear")) {
      clearAllRubrics();
      return;
    }

    // Disposition-lens chips — family toggle or the all/clear button.
    const dchip = e.target.closest(".disp-chip");
    if (dchip) {
      if (dchip.id === "disp-all") {
        if (activeDispositions.size === DISPOSITION_FAMILIES.length) {
          activeDispositions.clear();
        } else {
          DISPOSITION_FAMILIES.forEach((f) => activeDispositions.add(f.id));
        }
        renderGrid();
        renderDispositionLens();
      } else if (dchip.dataset.family) {
        toggleDisposition(dchip.dataset.family);
      }
      return;
    }

    // Active-chip click → remove that rubric. Whole chip is clickable;
    // the × is just a visual affordance.
    const chip = e.target.closest(".rubric-chip");
    if (chip && chip.dataset.rubric) {
      toggleRubric(chip.dataset.rubric);
      return;
    }

    // Rubric row click → toggle highlight for that rubric. Use closest
    // so clicks on the inner <td> still register.
    const rubricRow = e.target.closest(".rubric-row[data-rubric]");
    if (rubricRow) {
      toggleRubric(rubricRow.dataset.rubric);
      return;
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && expandedMode) {
      setExpandedMode(null);
    }
  });

  /* -------------------------------------------------------------------------
   * Boot — pull prompts first so the inspector has them ready when the
   * first case loads. Falls through to empty system-prompt slots if the
   * fetch fails (logged, non-blocking).
   * ---------------------------------------------------------------------- */
  (async () => {
    renderDispositionLens();
    await loadPrompts();
    initCaseSelector();
  })();
})();
