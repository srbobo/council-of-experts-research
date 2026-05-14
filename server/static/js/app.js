/* Council of Experts — A/B page logic.
 *
 * Wire-up: case loader, mode selector, budget bar, run lifecycle,
 * SSE event streaming, live three-column comparison.
 *
 * Vanilla JS (no framework). All state held in module-level closures.
 */
(function () {
  "use strict";

  /* -------------------------------------------------------------------------
   * State
   * ---------------------------------------------------------------------- */
  let cases = [];           // populated from /api/cases
  let budget = { cap_usd: 0, spent_usd: 0, remaining_usd: 0 };
  let activeRunId = null;
  let activeStream = null;  // EventSource
  // Per-mode column state for the active run. Keys: "local-council",
  // "opus-single", "opus-council". Values: { phases, finalText, status }.
  let columns = {};
  // Live-stream buffers per (mode, phase). When a token event arrives, the
  // delta is appended to buffers[mode][phase].text; a thinking-state-machine
  // (in renderLiveStream) classifies each character as speech or reasoning.
  // Buffer order matters for the teleprompter — first key seen for a mode is
  // shown first, second below it, etc.
  let buffers = {};
  // Pending re-render flag for requestAnimationFrame coalescing. Token events
  // arrive 30–50/sec per active seat; we update the DOM at most once per
  // animation frame (~16ms) regardless of token rate.
  //
  // `pendingStreamModes` is the set of modes whose live-stream needs a
  // targeted refresh on the next animation frame. We use a *targeted* update
  // (only the `.live-stream` element's innerHTML is replaced) rather than a
  // full grid re-render so that the card header — and especially the
  // expand button inside it — remains a stable DOM node across renders.
  // Tearing down the button every 16ms would break clicks on it (the browser
  // requires mousedown+mouseup on the same element to fire a click).
  let rafPending = false;
  const pendingStreamModes = new Set();
  // When non-null, render the column for this mode inside the overlay modal
  // (and add `body.has-overlay` for scroll lock). Cleared by the × button,
  // a click on the overlay backdrop, or the Escape key.
  let expandedMode = null;

  /* -------------------------------------------------------------------------
   * DOM lookups (cached)
   * ---------------------------------------------------------------------- */
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const els = {
    caseSelect: $("#case-select"),
    promptInput: $("#prompt-input"),
    modeBoxes: $$('#mode-checkboxes input[type="checkbox"]'),
    runButton: $("#run-button"),
    grid: $("#results-grid"),
    overlayRoot: $("#overlay-root"),
    budgetIndicator: $("#budget-indicator"),
    budgetText: $("#budget-text"),
    budgetFill: $("#budget-indicator .budget__fill"),
  };

  /* -------------------------------------------------------------------------
   * Helpers
   * ---------------------------------------------------------------------- */
  function fmtUsd(n) {
    return "$" + Number(n).toFixed(2);
  }

  function fmtMs(ms) {
    if (ms == null) return "—";
    if (ms < 1000) return ms + "ms";
    return (ms / 1000).toFixed(1) + "s";
  }

  // Strip <think>...</think> blocks for display. Same logic the orchestrator
  // applies before passing to the synthesizer; mirrored here for the UI.
  function stripThinking(text) {
    if (!text) return text;
    return text.replace(/<think>[\s\S]*?<\/think>\s*/g, "").trim();
  }

  // Split a piece of model output into its inline <think>...</think> blocks
  // and the remaining "speech" text. Used by the inspector to render
  // reasoning separately from final output. Models that emit thinking inline:
  // Qwen-Open-Finance-R (always), Phi-4 sometimes. Opus emits thinking as
  // structured blocks (see extractStructuredThinking below) — not inline.
  function splitThinking(text) {
    const thinking = [];
    if (!text) return { thinking, speech: "" };
    const speech = text.replace(/<think>([\s\S]*?)<\/think>\s*/g, (_, body) => {
      thinking.push(body.trim());
      return "";
    }).trim();
    return { thinking, speech };
  }

  // Pull thinking blocks out of an Anthropic raw response (Opus 4.7 with
  // adaptive thinking). Anthropic delivers thinking as separate content
  // blocks of type "thinking" rather than inline tags. We surface them in
  // the inspector so opus modes carry the same transparency as the local
  // council. Returns an array of thinking-text strings.
  function extractStructuredThinking(rawResponse) {
    if (!rawResponse || !Array.isArray(rawResponse.content)) return [];
    const thinks = [];
    for (const block of rawResponse.content) {
      if (block && block.type === "thinking" && (block.thinking || block.text)) {
        thinks.push((block.thinking || block.text || "").trim());
      }
    }
    return thinks;
  }

  function escapeHtml(s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Convert a routes array (e.g. ["healthcare", "legal"]) into the fingerprint
  // markup: a 3-segment bar where each segment is "on" iff that seat was used.
  function fingerprintHtml(routes) {
    const seats = ["healthcare", "legal", "finance"];
    const segs = seats
      .map((seat) => {
        const on = routes && routes.includes(seat);
        return `<span class="seg" data-seat="${seat}"${on ? " data-on" : ""}></span>`;
      })
      .join("");
    return `<span class="fingerprint" aria-label="Routes: ${routes ? routes.join(", ") || "none" : "—"}">${segs}</span>`;
  }

  /* -------------------------------------------------------------------------
   * Live stream — the teleprompter shown inside each running column.
   *
   * The browser receives `token` SSE events with {mode, phase, delta}. Each
   * delta is appended to the corresponding buffer. A simple state machine
   * walks the accumulated text and emits two kinds of spans: speech (default
   * weight) and thinking (italic, faint amber tint).
   *
   * Thinking is delimited by inline ``<think>...</think>`` tags — Qwen-Open-
   * Finance-R always emits them; Phi-4 sometimes. Tag boundaries can split
   * across token deltas (e.g. ``"<th"`` then ``"ink>"``), so we walk the
   * accumulated string each render rather than trying to maintain incremental
   * state across deltas. Cheap enough at this scale (a few thousand chars
   * per phase, re-rendered at most every 16ms).
   * ---------------------------------------------------------------------- */

  // Friendly labels for each phase tag. Used in live-stream headers and the
  // inspector. Falls back to the raw tag if unknown.
  const PHASE_LABELS = {
    planner: "Lead — Planner",
    healthcare: "Healthcare seat",
    legal: "Legal seat",
    finance: "Finance seat",
    synthesis: "Lead — Synthesis",
  };

  function phaseLabel(tag) {
    return PHASE_LABELS[tag] || tag;
  }

  // Walk a piece of accumulated text and produce HTML where <think>...</think>
  // sections are wrapped in <span class="live-stream__thinking">. Unbalanced
  // opens (i.e. we're still inside a <think> block) are treated as "thinking
  // up to the end of the current buffer." Returns escaped HTML.
  function renderStreamingText(text) {
    if (!text) return "";
    const parts = [];
    let i = 0;
    let inThink = false;
    while (i < text.length) {
      if (!inThink) {
        const open = text.indexOf("<think>", i);
        if (open === -1) {
          parts.push(escapeHtml(text.slice(i)));
          break;
        }
        parts.push(escapeHtml(text.slice(i, open)));
        i = open + "<think>".length;
        inThink = true;
      } else {
        const close = text.indexOf("</think>", i);
        if (close === -1) {
          // unterminated — model is still mid-thinking; render what we have
          parts.push(
            `<span class="live-stream__thinking">${escapeHtml(text.slice(i))}</span>`,
          );
          break;
        }
        parts.push(
          `<span class="live-stream__thinking">${escapeHtml(text.slice(i, close))}</span>`,
        );
        i = close + "</think>".length;
        inThink = false;
      }
    }
    return parts.join("");
  }

  // Render the live-stream block for a mode's column. Each phase that has
  // received tokens gets its own subsection in the order it first appeared.
  // The most recent phase gets a pulsing dot beside its header so the user
  // can see which seat is currently generating.
  function renderLiveStream(mode) {
    const phaseBuf = buffers[mode];
    if (!phaseBuf) return "";
    const order = phaseBuf.__order || [];
    if (order.length === 0) return "";
    const lastTag = order[order.length - 1];
    const sections = order.map((tag) => {
      const text = phaseBuf[tag] || "";
      const isActive = tag === lastTag && !phaseBuf.__done;
      return `<section class="live-stream__phase">
        <div class="live-stream__phase-label"${isActive ? " data-active" : ""}>
          ${escapeHtml(phaseLabel(tag))}
        </div>
        <div class="live-stream__text">${renderStreamingText(text)}</div>
      </section>`;
    });
    return `<div class="live-stream">${sections.join("")}</div>`;
  }

  // Targeted live-stream refresh for one mode. Replaces ONLY the
  // .live-stream element's innerHTML — the surrounding card (header,
  // expand button, pill, footer) is left untouched. This is the difference
  // between "30 token events tear down the entire grid 30×/sec" (which
  // eats user clicks on the expand button) and "30 token events update
  // just the streaming text" (which leaves everything else interactive).
  //
  // Updates both the grid card AND the overlay card if that mode is the
  // currently-expanded one — they each have their own `.live-stream`.
  function updateLiveStreamForMode(mode) {
    const SCROLL_PIN_THRESHOLD = 30;  // px — same heuristic as renderColumns
    const cards = $$(`.card[data-mode="${mode}"]`);
    if (cards.length === 0) {
      // No card exists for this mode yet — fall back to a full render
      // (which will create the card and its live-stream container).
      renderColumns();
      return;
    }
    // Compute the new live-stream markup once and reuse across grid + overlay.
    const newHtml = renderLiveStream(mode);
    if (!newHtml) {
      // Buffer empty — nothing to do.
      return;
    }
    // Parse just enough to extract the inner content. We keep the existing
    // .live-stream element so its scroll state belongs to a stable DOM node.
    const tmp = document.createElement("div");
    tmp.innerHTML = newHtml;
    const newWrapper = tmp.firstElementChild;
    const innerHtml = newWrapper ? newWrapper.innerHTML : "";

    let needsFullRender = false;
    cards.forEach((card) => {
      const stream = card.querySelector(".live-stream");
      if (!stream) {
        // Card exists but its body hasn't been rendered with a live-stream
        // yet (e.g. between mode_started and the first token). Trigger a
        // full render to create it; subsequent tokens will take this path.
        needsFullRender = true;
        return;
      }
      const distFromBottom = stream.scrollHeight - stream.scrollTop - stream.clientHeight;
      const wasPinned = distFromBottom < SCROLL_PIN_THRESHOLD;
      const prevScrollTop = stream.scrollTop;
      stream.innerHTML = innerHtml;
      if (wasPinned) {
        stream.scrollTop = stream.scrollHeight;
      } else {
        stream.scrollTop = prevScrollTop;
      }
    });
    if (needsFullRender) renderColumns();
  }

  // Schedule a targeted live-stream refresh for one mode on the next
  // animation frame. Multiple token events for the same mode between
  // frames coalesce into one DOM update.
  function scheduleStreamUpdate(mode) {
    pendingStreamModes.add(mode);
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      const modes = Array.from(pendingStreamModes);
      pendingStreamModes.clear();
      modes.forEach(updateLiveStreamForMode);
    });
  }

  /* -------------------------------------------------------------------------
   * Inspector — per-phase breakdown of a deliberation. Renders inside a
   * collapsed <details> at the bottom of each result column so users can
   * see WHICH system prompts were used, WHAT the model thought, and WHAT
   * raw output came back at each phase. Built from the audit-log shape the
   * orchestrator and bench harness already produce.
   * ---------------------------------------------------------------------- */

  // One phase row: header (label + meta) + collapsible system prompt +
  // collapsible reasoning + the visible output. Reasoning and prompt default
  // closed so the inspector stays scannable.
  function renderPhase({ label, meta, systemPrompt, thinking, output }) {
    const promptBlock = systemPrompt
      ? `<details class="phase__detail">
           <summary>System prompt</summary>
           <pre class="prompt-block">${escapeHtml(systemPrompt)}</pre>
         </details>`
      : "";

    const thinkingBlock = thinking && thinking.length > 0
      ? `<details class="phase__detail" open>
           <summary>Reasoning (${thinking.length} block${thinking.length > 1 ? "s" : ""})</summary>
           ${thinking.map((t) => `<pre class="thinking-block">${escapeHtml(t)}</pre>`).join("")}
         </details>`
      : "";

    const outputBlock = output
      ? `<details class="phase__detail" open>
           <summary>Output</summary>
           <pre class="output-block">${escapeHtml(output)}</pre>
         </details>`
      : "";

    return `<section class="phase">
      <h4 class="phase__title">${escapeHtml(label)}
        ${meta ? `<span class="phase__meta">${escapeHtml(meta)}</span>` : ""}
      </h4>
      ${promptBlock}
      ${thinkingBlock}
      ${outputBlock}
    </section>`;
  }

  // Build the meta string for a phase ("9.4s · 469 tok in · 380 tok out").
  function phaseMeta(latency_ms, prompt_eval_count, eval_count) {
    const parts = [];
    if (latency_ms != null) parts.push(fmtMs(latency_ms));
    if (prompt_eval_count != null) parts.push(`${prompt_eval_count} tok in`);
    if (eval_count != null) parts.push(`${eval_count} tok out`);
    return parts.join(" · ");
  }

  // Pick the system prompt and user-side content out of an `input_messages`
  // list. The orchestrator always emits [{role: "system", ...},
  // {role: "user", ...}] — so this is a thin split helper.
  function splitInputMessages(input_messages) {
    if (!Array.isArray(input_messages)) return { system: "", user: "" };
    const sys = input_messages.find((m) => m.role === "system");
    const usr = input_messages.find((m) => m.role !== "system");
    return {
      system: sys ? sys.content || "" : "",
      user: usr ? usr.content || "" : "",
    };
  }

  // Council inspector — works for both local-council and opus-council since
  // they share the same `deliberation` shape. Renders 5 phase sections in order:
  // Lead planner → 3 industry seats → Lead synthesis.
  function renderCouncilInspector(deliberation) {
    if (!deliberation) return "";

    const sections = [];

    // Phase 1: Lead planner
    const planRaw = deliberation.plan_raw || "";
    const { thinking: planThinking, speech: planSpeech } = splitThinking(planRaw);
    // Planner input_messages live on a separate field (not an AgentTurn) since
    // the planner doesn't produce one. Falls back gracefully on older audit
    // logs that pre-date this field.
    const planInputs = splitInputMessages(deliberation.plan_input_messages || []);
    sections.push(renderPhase({
      label: "Lead — Planner",
      meta: phaseMeta(deliberation.plan_latency_ms, null, null),
      systemPrompt: planInputs.system,
      thinking: planThinking,
      // Show the user query + the planner's raw answer (post any thinking-strip).
      output: planInputs.user
        ? `[User query]\n${planInputs.user}\n\n[Planner output]\n${planSpeech || planRaw}`
        : (planSpeech || planRaw),
    }));

    // Phase 2: Each routed industry seat
    const turns = deliberation.turns || [];
    for (const turn of turns) {
      const { system, user } = splitInputMessages(turn.input_messages);
      const inlineThink = splitThinking(turn.output_text || "");
      const structuredThink = extractStructuredThinking(turn.raw_response || {});
      const thinking = [...structuredThink, ...inlineThink.thinking];

      const seatLabel = `${turn.seat.charAt(0).toUpperCase() + turn.seat.slice(1)} seat`;
      const memberName = turn.member_name ? ` — ${turn.member_name}` : "";

      sections.push(renderPhase({
        label: seatLabel + memberName,
        meta: phaseMeta(turn.latency_ms, turn.prompt_eval_count, turn.eval_count),
        systemPrompt: system,
        thinking: thinking,
        // Show the user-side dispatched sub-question + the actual answer
        // (with <think> stripped from the speech portion).
        output: user
          ? `[Dispatched sub-question]\n${user}\n\n[Response]\n${inlineThink.speech || turn.output_text || ""}`
          : (inlineThink.speech || turn.output_text || ""),
      }));
    }

    // Phase 3: Lead synthesis
    if (deliberation.synthesis) {
      const synth = deliberation.synthesis;
      const { system } = splitInputMessages(synth.input_messages);
      const inlineThink = splitThinking(synth.output_text || "");
      const structuredThink = extractStructuredThinking(synth.raw_response || {});
      const thinking = [...structuredThink, ...inlineThink.thinking];

      sections.push(renderPhase({
        label: "Lead — Synthesis",
        meta: phaseMeta(synth.latency_ms, synth.prompt_eval_count, synth.eval_count),
        systemPrompt: system,
        thinking: thinking,
        output: inlineThink.speech || synth.output_text || "",
      }));
    }

    return `<details class="inspector">
      <summary>Inspect deliberation — system prompts, reasoning, raw outputs</summary>
      <div class="inspector__content">${sections.join("")}</div>
    </details>`;
  }

  // Opus-single inspector — flat (no per-seat phases). Just shows the
  // system prompt, the structured thinking blocks Opus produced, and the
  // raw output.
  function renderSingleInspector(result) {
    if (!result) return "";
    const thinking = extractStructuredThinking(result.raw_response || {});
    if (!result.system_prompt && thinking.length === 0) {
      return "";  // nothing useful to show; skip the disclosure entirely
    }
    return `<details class="inspector">
      <summary>Inspect call — system prompt and reasoning</summary>
      <div class="inspector__content">
        ${renderPhase({
          label: "Opus 4.7 single-shot",
          meta: phaseMeta(result.total_latency_ms,
            result.tokens ? result.tokens.input : null,
            result.tokens ? result.tokens.output : null),
          systemPrompt: result.system_prompt || "",
          thinking: thinking,
          output: result.final_output || "",
        })}
      </div>
    </details>`;
  }

  /* -------------------------------------------------------------------------
   * Initial load — cases + budget
   * ---------------------------------------------------------------------- */
  async function loadCases() {
    try {
      const r = await fetch("/api/cases");
      cases = await r.json();
      els.caseSelect.innerHTML = `<option value="">— pick a case —</option>` +
        cases.map((c) => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.title)}</option>`).join("");
      els.caseSelect.disabled = false;
      els.runButton.disabled = false;
    } catch (e) {
      console.error("Failed to load cases", e);
      els.caseSelect.innerHTML = `<option>Error loading cases — check server</option>`;
    }
  }

  async function loadBudget() {
    try {
      const r = await fetch("/api/budget");
      budget = await r.json();
      renderBudget();
      // Disable Opus modes if cap is zero — they'd refuse anyway, no point
      // letting the user check them and get a confusing partial result.
      const paused = budget.cap_usd <= 0;
      els.modeBoxes.forEach((box) => {
        if (box.value !== "local-council") {
          box.disabled = paused;
          if (paused) {
            box.checked = false;
            box.parentElement.title = "Budget cap is $0; raise BENCH_BUDGET_USD to enable Opus modes.";
          }
        }
      });
    } catch (e) {
      console.error("Failed to load budget", e);
    }
  }

  function renderBudget() {
    const pct = budget.cap_usd > 0 ? (budget.spent_usd / budget.cap_usd) * 100 : 0;
    els.budgetFill.style.width = Math.min(pct, 100) + "%";
    els.budgetText.textContent = `${fmtUsd(budget.spent_usd)} / ${fmtUsd(budget.cap_usd)}`;
    if (budget.cap_usd <= 0) {
      els.budgetIndicator.setAttribute("data-paused", "");
    } else {
      els.budgetIndicator.removeAttribute("data-paused");
    }
  }

  /* -------------------------------------------------------------------------
   * Case selection — auto-populate the prompt textarea
   * ---------------------------------------------------------------------- */
  els.caseSelect.addEventListener("change", () => {
    const id = els.caseSelect.value;
    if (!id) return;
    const c = cases.find((x) => x.id === id);
    if (c) els.promptInput.value = c.prompt;
  });

  /* -------------------------------------------------------------------------
   * Run lifecycle
   * ---------------------------------------------------------------------- */
  function getSelectedModes() {
    return els.modeBoxes.filter((b) => b.checked && !b.disabled).map((b) => b.value);
  }

  function getQueryFromForm() {
    const caseId = els.caseSelect.value || null;
    const prompt = (els.promptInput.value || "").trim();
    if (caseId) return { case_id: caseId };
    if (prompt) return { prompt };
    return null;
  }

  // Title map shared between grid and overlay rendering.
  const MODE_TITLES = {
    "local-council": "Local Council",
    "opus-single": "Opus single-shot",
    "opus-council": "Opus-as-council",
  };

  // Build the overlay markup, or "" if no mode is expanded.
  // The overlay wraps a fresh render of the same column so live tokens flow
  // into it the same way they flow into the grid. The expand button is
  // hidden inside the overlay via CSS (it'd be redundant).
  function renderOverlay() {
    if (!expandedMode) return "";
    const title = MODE_TITLES[expandedMode] || expandedMode;
    const columnHtml = renderColumn(expandedMode, title);
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

  // Re-render the three result columns from the current `columns` state,
  // and the overlay (if any) on the side. Re-rendering on every event is
  // cheap (3 small cards plus maybe one overlay copy) and avoids having to
  // mutate individual DOM nodes — simpler reasoning.
  //
  // Live-stream containers are torn down and recreated on every render, so
  // we capture each one's scroll position keyed by `(mode, location)` before
  // re-rendering and restore it after. Standard chat-app heuristic: if the
  // user was within 30px of the bottom, pin to the new bottom (follow the
  // stream); otherwise preserve their absolute position so they can read
  // earlier tokens without being yanked back down.
  //
  // The compound key matters because both the grid and the overlay can host
  // a live-stream for the SAME mode (when that mode is expanded). They each
  // need their own scroll state.
  function renderColumns() {
    const SCROLL_PIN_THRESHOLD = 30;  // px — within this distance => follow

    // ---- Snapshot scroll state before tearing down innerHTML ----
    const priorScroll = {};
    $$(".card[data-mode] .live-stream").forEach((stream) => {
      const card = stream.closest(".card[data-mode]");
      if (!card) return;
      const loc = card.closest(".overlay") ? "overlay" : "grid";
      priorScroll[`${card.dataset.mode}|${loc}`] = {
        scrollTop: stream.scrollTop,
        distFromBottom: stream.scrollHeight - stream.scrollTop - stream.clientHeight,
      };
    });

    // ---- Render the grid ----
    const seats = [
      { key: "local-council", title: MODE_TITLES["local-council"] },
      { key: "opus-single", title: MODE_TITLES["opus-single"] },
      { key: "opus-council", title: MODE_TITLES["opus-council"] },
    ];
    els.grid.innerHTML = seats.map(({ key, title }) => renderColumn(key, title)).join("");

    // ---- Render the overlay (or empty it) ----
    if (els.overlayRoot) {
      els.overlayRoot.innerHTML = renderOverlay();
    }
    document.body.classList.toggle("has-overlay", !!expandedMode);

    // ---- Restore scroll state on the freshly-rendered live-streams ----
    $$(".card[data-mode] .live-stream").forEach((stream) => {
      const card = stream.closest(".card[data-mode]");
      if (!card) return;
      const loc = card.closest(".overlay") ? "overlay" : "grid";
      const prev = priorScroll[`${card.dataset.mode}|${loc}`];
      if (!prev) {
        // First time this stream appears (e.g. the overlay just opened) —
        // start at bottom so the latest tokens are immediately visible.
        stream.scrollTop = stream.scrollHeight;
        return;
      }
      if (prev.distFromBottom < SCROLL_PIN_THRESHOLD) {
        stream.scrollTop = stream.scrollHeight;
      } else {
        stream.scrollTop = prev.scrollTop;
      }
    });
  }

  function renderColumn(modeKey, title) {
    const col = columns[modeKey];
    // Header markup shared between not-selected and active columns. The
    // expand button (⤢) is always shown on a card that has *any* state at all
    // so the user can pop a result open for closer reading. We use ⤢ (U+2922,
    // NORTH EAST AND SOUTH WEST ARROW) — readable as "expand" in most fonts.
    const headerHtml = `<h3 class="card__title">
      ${escapeHtml(title)}
      <button class="card__expand" data-expand="${escapeHtml(modeKey)}"
              type="button" aria-label="Expand ${escapeHtml(title)}"
              title="Expand">⤢</button>
    </h3>`;

    if (!col) {
      // Mode not requested in this run; show idle placeholder.
      // data-mode allows renderColumns to correlate this column with its
      // scroll-state snapshot across re-renders (token events trigger
      // full innerHTML replacement; we need a stable per-column identifier
      // to preserve user scroll position inside the live-stream).
      return `<article class="card" data-mode="${escapeHtml(modeKey)}">
        ${headerHtml}
        <p class="text-faint">Not selected.</p>
      </article>`;
    }

    let body;
    if (col.status === "refused") {
      body = `<p class="text-soft"><span class="pill" data-status="refused">refused</span></p>
              <p class="text-small text-soft" style="margin-top:0.5rem">${escapeHtml(col.reason || "Budget cap reached.")}</p>`;
    } else if (col.status === "failed") {
      body = `<p class="text-soft"><span class="pill" data-status="failed">failed</span></p>
              <p class="text-small text-soft" style="margin-top:0.5rem">${escapeHtml(col.error || "")}</p>`;
    } else if (col.status === "completed") {
      const finalDisplay = stripThinking(col.finalText || "");
      // Inspector picks its layout based on whether this mode produced a
      // multi-phase deliberation (local-council and opus-council) or a
      // flat call (opus-single).
      let inspector = "";
      if (col.deliberation) {
        inspector = renderCouncilInspector(col.deliberation);
      } else if (col.systemPrompt || col.rawResponse) {
        inspector = renderSingleInspector({
          system_prompt: col.systemPrompt,
          raw_response: col.rawResponse,
          tokens: col.tokens,
          total_latency_ms: col.totalLatencyMs,
          final_output: col.finalText,
        });
      }
      body = `<div class="card__meta" style="margin-bottom:0.5rem">
                ${fingerprintHtml(col.routes)}
                <span style="margin-left:0.5rem">${fmtMs(col.totalLatencyMs)}</span>
                ${col.tokens ? `<span style="margin-left:0.5rem">${col.tokens.input}↓ ${col.tokens.output}↑ tok</span>` : ""}
              </div>
              <pre style="white-space:pre-wrap; font-family:var(--font-body); font-size:var(--size-2); background:transparent; border:0; padding:0; margin:0">${escapeHtml(finalDisplay)}</pre>
              ${inspector}`;
    } else {
      // running — live-stream the tokens as they arrive. The teleprompter
      // is the primary indicator of activity; the phase log is kept as a
      // small footer (timestamped stage transitions) so the user can still
      // see plan-done / pause / dispatch events.
      const live = renderLiveStream(modeKey);
      const phaseLogEntries = (col.phases || []).slice(-4); // last 4 only
      const phaseLog = phaseLogEntries.map((p) => {
        return `<div class="live-stream__phase-event">
                  ${escapeHtml(p.stage)}${p.detail ? `: ${escapeHtml(p.detail.slice(0, 80))}` : ""}
                </div>`;
      }).join("");
      body = `<p><span class="pill" data-status="running">running</span></p>
              ${live || '<div class="text-faint text-small" style="margin-top:0.75rem">awaiting first token…</div>'}
              ${phaseLog ? `<div class="live-stream__phase-events">${phaseLog}</div>` : ""}`;
    }

    return `<article class="card" data-mode="${escapeHtml(modeKey)}">
      ${headerHtml}
      ${body}
    </article>`;
  }

  async function startRun() {
    const query = getQueryFromForm();
    if (!query) {
      alert("Pick a case or write a prompt.");
      return;
    }
    const modes = getSelectedModes();
    if (modes.length === 0) {
      alert("Select at least one mode.");
      return;
    }

    // Reset per-mode column state; only show columns for the selected modes.
    columns = {};
    modes.forEach((m) => {
      columns[m] = { status: "running", phases: [] };
    });
    renderColumns();
    els.runButton.disabled = true;
    els.runButton.textContent = "Running…";

    try {
      // Tear down a prior stream if the user mashed Run twice in a row.
      if (activeStream) { activeStream.close(); activeStream = null; }

      const body = JSON.stringify({ ...query, modes });
      const r = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(err.detail || "Failed to start run");
      }
      const { run_id } = await r.json();
      activeRunId = run_id;
      openStream(run_id);
    } catch (e) {
      console.error(e);
      alert("Run failed: " + e.message);
      els.runButton.disabled = false;
      els.runButton.textContent = "Run";
    }
  }

  function openStream(runId) {
    activeStream = new EventSource(`/api/runs/${runId}/stream`);
    activeStream.onmessage = (msg) => {
      try {
        const event = JSON.parse(msg.data);
        handleEvent(event);
      } catch (e) {
        console.warn("malformed SSE event", msg.data, e);
      }
    };
    activeStream.onerror = (e) => {
      console.warn("SSE stream error", e);
      // Browser will reconnect automatically; fine for our use case.
    };
  }

  function handleEvent(event) {
    // Route events into the per-mode column state.
    if (event.type === "stream_end") {
      if (activeStream) { activeStream.close(); activeStream = null; }
      els.runButton.disabled = false;
      els.runButton.textContent = "Run";
      // Refresh budget so the bar reflects post-run spend.
      loadBudget();
      return;
    }

    // High-volume event: a single text delta from one phase of one mode.
    // Append to the per-(mode, phase) live buffer and schedule a coalesced
    // *targeted* live-stream refresh on the next animation frame. Targeted
    // refresh preserves the card header DOM (and the expand button inside it)
    // so the user can pop the column open even while tokens are streaming.
    if (event.type === "token" && event.mode && event.phase) {
      let phaseBuf = buffers[event.mode];
      if (!phaseBuf) {
        phaseBuf = buffers[event.mode] = { __order: [], __done: false };
      }
      if (!(event.phase in phaseBuf)) {
        phaseBuf[event.phase] = "";
        phaseBuf.__order.push(event.phase);
      }
      phaseBuf[event.phase] += event.delta;
      scheduleStreamUpdate(event.mode);
      return;
    }

    if (event.type === "mode_started" && event.mode) {
      // Fresh mode — wipe any leftover live buffer from a prior run.
      buffers[event.mode] = { __order: [], __done: false };
      return;
    }

    if (event.type === "phase" && event.mode) {
      const col = columns[event.mode];
      if (!col) return;
      col.phases.push({ stage: event.stage, detail: event.detail });
      renderColumns();
      return;
    }

    if (event.type === "mode_completed" && event.mode) {
      // Mark the live buffer as done so the active-phase pulse stops; the
      // buffer itself is not cleared so a user could (in theory) toggle
      // back to live view, though the standard path renders the final
      // synthesis + inspector instead.
      if (buffers[event.mode]) buffers[event.mode].__done = true;
      const result = event.result || {};
      const delib = result.deliberation || null;
      columns[event.mode] = {
        status: "completed",
        finalText: result.final_output,
        totalLatencyMs: result.total_latency_ms,
        tokens: result.tokens || null,           // opus-single carries top-level tokens
        routes: delib && delib.plan ? delib.plan.routes : null,  // council modes
        // Capture the data the inspector needs. Council modes use `deliberation`;
        // opus-single carries its own system prompt + raw payload separately.
        deliberation: delib,
        systemPrompt: result.system_prompt || null,
        rawResponse: result.raw_response || null,
        phases: (columns[event.mode] && columns[event.mode].phases) || [],
      };
      renderColumns();
      return;
    }

    if (event.type === "mode_refused" && event.mode) {
      columns[event.mode] = {
        status: "refused",
        reason: event.reason,
        phases: (columns[event.mode] && columns[event.mode].phases) || [],
      };
      renderColumns();
      return;
    }

    if (event.type === "mode_failed" && event.mode) {
      columns[event.mode] = {
        status: "failed",
        error: event.error,
        phases: (columns[event.mode] && columns[event.mode].phases) || [],
      };
      renderColumns();
      return;
    }

    // Other event types (run_started, budget, run_finished) are informational.
    // The UI doesn't currently render them; the per-mode events drive the view.
  }

  els.runButton.addEventListener("click", startRun);

  /* -------------------------------------------------------------------------
   * Overlay open/close — single delegated click listener on document so we
   * don't have to re-bind every time renderColumns() blows away the grid.
   * Triggered by:
   *   - clicking any [data-expand="<mode>"] button → open overlay for that mode
   *   - clicking any [data-close-overlay] (the × button or the backdrop) → close
   *   - pressing Escape while the overlay is open → close
   * ---------------------------------------------------------------------- */
  function setExpandedMode(modeOrNull) {
    if (expandedMode === modeOrNull) return;
    expandedMode = modeOrNull;
    renderColumns();
  }

  document.addEventListener("click", (e) => {
    // Expand button. Use closest in case the click lands on a descendant
    // (defensive — the button has no children today, but cheap to guard).
    const expander = e.target.closest("[data-expand]");
    if (expander) {
      setExpandedMode(expander.dataset.expand);
      return;
    }
    // Close button OR backdrop click. We use `matches` (not `closest`) so
    // clicks INSIDE the overlay__panel don't bubble up and close — only
    // clicks on the explicit close-target elements close.
    if (e.target.matches("[data-close-overlay]")) {
      setExpandedMode(null);
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && expandedMode) {
      setExpandedMode(null);
    }
  });

  /* -------------------------------------------------------------------------
   * Boot
   * ---------------------------------------------------------------------- */
  loadCases();
  loadBudget();
})();
