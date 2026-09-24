/* Data explorer: per-cell model inputs/outputs. Expects globals from the page:
   DATA (ledger + data_index), md(), esc(), go(). Exposes window.DataExplorer. */
(function(){
  const chunks = {};          // id -> parsed chunk
  const waiting = {};         // id -> [resolve]
  const pending = {};         // id -> raw b64 delivered before decode
  window.__ledgerChunk = function(id, b64){ pending[id] = b64; (waiting[id] || []).forEach(r => r()); };

  async function inflate(b64){
    const bin = atob(b64); const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    if (typeof DecompressionStream === 'undefined') throw new Error('This browser cannot decompress gzip (DecompressionStream missing).');
    const ds = new DecompressionStream('gzip');
    const stream = new Blob([bytes]).stream().pipeThrough(ds);
    return JSON.parse(await new Response(stream).text());
  }
  function fileFor(id){
    if (id === 'shared') return 'data/shared.js';
    const m = (DATA.data_index || {})[id];
    return m ? m.file : null;
  }
  function loadChunk(id){
    if (chunks[id]) return Promise.resolve(chunks[id]);
    return new Promise((resolve, reject) => {
      const done = async () => { try { chunks[id] = await inflate(pending[id]); delete pending[id]; resolve(chunks[id]); } catch(e){ reject(e); } };
      if (pending[id]) return done();
      (waiting[id] = waiting[id] || []).push(done);
      const f = fileFor(id); if (!f) return reject(new Error('no data file for ' + id));
      const s = document.createElement('script'); s.src = f; s.async = true;
      s.onerror = () => reject(new Error('could not load ' + f));
      document.head.appendChild(s);
    });
  }

  // ------------------------------------------------------------ helpers
  const isRef = v => v && typeof v === 'object' && !Array.isArray(v) && '$s' in v && Object.keys(v).length === 1;
  const fmtN = n => (n == null ? '' : Number(n).toLocaleString());
  const short = (s, n) => { s = String(s ?? ''); return s.length > n ? s.slice(0, n) + '…' : s; };
  function deref(v, S){
    if (isRef(v)) return S[v.$s];
    if (Array.isArray(v)) return v.map(x => deref(x, S));
    if (v && typeof v === 'object') { const o = {}; for (const k in v) o[k] = deref(v[k], S); return o; }
    return v;
  }
  const pretty = o => JSON.stringify(o, null, 2);
  const FIELD = { run_id:'Run', file:'File', case_id:'Scenario', case:'Scenario', prompt_id:'Scenario', item:'Test item', mode:'Setup', arm:'Setup', cond:'Setup', condition:'Setup', role:'Role', stage:'Stage', label:'Label', producer:'Model', writer:'Editor model', writer_id:'Editor model', reader:'Reader model', repeat:'Repeat', rep:'Repeat', variant_id:'Variant', supply_registered:'Caveat kinds supplied', seats:'Specialists', n_turns:'Specialist replies', final_chars:'Answer length', chars:'Length', total_latency_ms:'Total time (ms)', output:'Final answer', full_output:'Full output', upstream:'Specialist drafts given to the editor', s1:"Editor's first pass", reply:"Specialist's follow-up reply", seat_text:"Specialist's answer", seat_A_text:"Specialist A's answer", seat_B_text:"Specialist B's answer", tail:'End of the answer', list:"Planner's list", plan:'Plan', tension_named:'Named the disagreement', dispatched:'Follow-up sent', fact_in_reply:'Fact in the reply', clean:'Used the right value', wrong:'Used the wrong value', clean_in_B:'Right value in B', wrong_in_A:'Wrong value in A', protocol_violation:'Broke the required format', val:'Value given', ok:'Correct', route:'Route', flag:'Flag', home:'Home field', kind:'Kind', family:'Model family', tuned_domain:'Fine-tuned for', item_domain:'Question field', domain:'Field', answer:'Answer', tries:'Attempts', injected_seat:'Planted in', injected_index:'Planted at position', seat_order:'Specialist order', plaus:'Used the plausible value', implaus:'Used the implausible value', auth:'Cited an authority', place:'Placement', stable:'Stable', owner_val:"Used the owner's value", foil_val:'Used the decoy value', empty:'Empty', defect:'Defect', n_caveats:'Caveats', prose:'Report text', full:'Report with caveats section', adopt:'Adopted', n_qual:'Caveat sentences', n_sent:'Sentences', n_unlab:'Unlabelled sentences', app_chars:'Caveats section length', bare:'Report without caveats section', freight:'Report with caveats section', sentences:'Sentences', judges:'Judges', case_title:'Scenario title', captured_at:'Recorded', model:'Models', notes:'Notes', query:'Question', final_output:'Final answer', plan_raw:'Planning notes' };
  const fieldLabel = k => FIELD[k] || String(k).replace(/_/g, ' ').replace(/^./, c => c.toUpperCase());
  const ROLE = { produced: '', 'referenced by script': "Read by this cell's script", shared: 'Shared with Cell 2', 'frozen items': 'Test materials', 'produced (shared c30c31)': 'Shared by Cells 30 and 31' };
  const roleLabel = r => (r in ROLE ? ROLE[r] : r);
  const niceTitle = t => String(t || '').replace(/^Model traces \u2014 mode (.+)$/, 'Conversations in the $1 setup');
  const fmtMs = ms => ms == null ? '' : (ms < 1000 ? ms + ' ms' : ms < 120000 ? (ms / 1000).toFixed(1) + ' s' : (ms / 60000).toFixed(1) + ' min');
  const SEAT = { healthcare: 'Healthcare specialist', legal: 'Legal specialist', finance: 'Finance specialist', lead: 'Editor' };
  const seatName = x => SEAT[x] || ((x || 'Unnamed') + ' specialist');
  const SEV = { must_have: 'must have', nice_to_have: 'nice to have', should_have: 'should have' };
  const KIND_P = { constant: 'Fixed text', 'template (source)': 'Template', 'imported constant': 'Shared text', 'shell script': 'Script' };
  function textPane(cls, role, name, text, opts){
    opts = opts || {};
    const t = text == null ? '' : (typeof text === 'string' ? text : pretty(text));
    const isObj = typeof text !== 'string';
    const open = opts.open ? 'open' : '';
    const mode = opts.raw || isObj ? 'raw' : 'md';
    return `<details class="pane ${cls}" ${open} data-mode="${mode}"><summary><span class="role">${esc(role)}</span><span class="nm">${esc(name)}</span><span class="ch">${fmtN(t.length)} characters</span>${isObj ? '' : `<button class="tg" data-toggle title="Switch between formatted and plain text">${mode === 'md' ? 'Plain text' : 'Formatted'}</button>`}</summary><div class="txt ${mode === 'md' ? 'md-body' : ''}">${mode === 'md' ? md(t) : '<pre>' + esc(t) + '</pre>'}</div></details>`;
  }
  function wireToggles(root){
    root.querySelectorAll('.pane .tg').forEach(b => b.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation();
      const d = b.closest('details'); const box = d.querySelector('.txt'); const src = box.dataset.src || '';
      if (d.dataset.mode === 'md') { box.className = 'txt'; box.innerHTML = '<pre>' + esc(src) + '</pre>'; d.dataset.mode = 'raw'; b.textContent = 'Formatted'; }
      else { box.className = 'txt md-body'; box.innerHTML = md(src); d.dataset.mode = 'md'; b.textContent = 'Plain text'; }
    }));
  }
  function textPaneStore(cls, role, name, text, opts){
    const html = textPane(cls, role, name, text, opts);
    if (typeof text === 'string') return html.replace('<div class="txt', `<div data-src="${esc(text)}" class="txt`);
    return html;
  }

  // ------------------------------------------------------------ explorer
  const EX = { root: null, eid: null, chunk: null, shared: null, state: null };

  async function mount(root, eid){
    EX.root = root; EX.eid = eid;
    EX.state = { src: null, filters: {}, q: '', page: 0, sel: null, view: 'sources' };
    root.innerHTML = '<div class="loading">Loading the saved data for this cell…</div>';
    try {
      const [chunk, shared] = await Promise.all([loadChunk(eid), loadChunk('shared')]);
      EX.chunk = chunk; EX.shared = shared;
    } catch(e){
      root.innerHTML = `<div class="empty">The data for this cell did not load (${esc(e.message)}). Reload the page to try again.</div>`; return;
    }
    const first = EX.chunk.sources[0];
    EX.state.src = first ? first.key : (EX.chunk.prompts.length ? 'prompts' : 'cases');
    renderExplorer();
  }

  function sourceByKey(k){ return EX.chunk.sources.find(s => s.key === k); }

  function renderExplorer(){
    const c = EX.chunk, st = EX.state, S = c.strings;
    const groups = [
      ['Full model conversations', c.sources.filter(s => s.kind === 'traces')],
      ['Results for each run', c.sources.filter(s => s.kind === 'runs')],
      ['Grading and analysis', c.sources.filter(s => ['judgments','analysis','json'].includes(s.kind))],
      ['Test questions and materials', c.sources.filter(s => s.kind === 'items')],
      ['Summary reports', c.sources.filter(s => s.kind === 'report')],
      ['Too large to include', c.sources.filter(s => s.kind === 'skipped')],
    ];
    const rail = `<div class="dx-rail">
      ${groups.filter(g => g[1].length).map(([name, list]) => `<div class="grp"><h3>${name}</h3>${list.map(s => `
        <button class="src" data-src="${esc(s.key)}" aria-selected="${st.src === s.key}"><span class="t">${esc(niceTitle(s.title) || s.path)}<span class="p">${esc(s.path)}${roleLabel(s.role) ? ` · <span class="role">${esc(roleLabel(s.role))}</span>` : ''}</span></span><span class="c">${fmtN(s.n)}</span></button>`).join('')}</div>`).join('')}
      <div class="grp"><h3>Instructions and scenarios</h3>
        <button class="src" data-src="prompts" aria-selected="${st.src === 'prompts'}"><span class="t">Instructions in this cell's script<span class="p">${esc((c.notes[0] || {}).script || 'train/')}</span></span><span class="c">${c.prompts.length}</span></button>
        <button class="src" data-src="cases" aria-selected="${st.src === 'cases'}"><span class="t">The 18 test scenarios<span class="p">examples/test_cases.py</span></span><span class="c">${EX.shared.cases.length}</span></button>
        <button class="src" data-src="council" aria-selected="${st.src === 'council'}"><span class="t">Standing instructions for the council<span class="p">council/prompts.py</span></span><span class="c">${EX.shared.council_prompts.length}</span></button>
      </div>
      ${c.notes.length ? `<div class="grp"><h3>AI models named in the scripts</h3><div style="padding:0 14px;font-family:var(--mono);font-size:11.5px;color:var(--ink-2);line-height:1.6">${esc([...new Set(c.notes.flatMap(n => n.models))].join(', '))}</div></div>` : ''}
    </div>`;
    EX.root.innerHTML = `<div class="dx">${rail}<div class="dx-main" id="dx-main"></div></div>`;
    EX.root.querySelectorAll('.dx-rail .src').forEach(b => b.addEventListener('click', () => { st.src = b.dataset.src; st.filters = {}; st.q = ''; st.page = 0; st.sel = null; renderExplorer(); }));
    renderMain();
  }

  function renderMain(){
    const st = EX.state, main = EX.root.querySelector('#dx-main');
    if (st.src === 'prompts') return renderPrompts(main, EX.chunk.prompts, 'Instructions in this cell\'s script', 'The text this cell\'s script sends to the models, plus any shared instructions it imports. Words in curly braces are filled in when the script runs.');
    if (st.src === 'council') return renderPrompts(main, EX.shared.council_prompts, 'Standing instructions for the council', 'The system prompts every council run starts from: the planning step, the three specialists, the editor\'s write-up, and the version where the editor answers alone. They live in council/prompts.py.');
    if (st.src === 'cases') return renderCases(main);
    const s = sourceByKey(st.src);
    if (!s) { main.innerHTML = '<div class="empty">Choose a source on the left.</div>'; return; }
    if (s.kind === 'report') { main.innerHTML = head(s) + `<div class="pane out" style="padding:0"><div class="txt"><pre>${esc(s.text)}</pre></div></div>`; return; }
    if (s.kind === 'skipped') { main.innerHTML = head(s) + `<div class="empty">${esc(s.note || 'This file is too large to include here.')}</div>`; return; }
    if (s.json !== undefined) { main.innerHTML = head(s) + `<div class="pane out" style="padding:0"><div class="txt"><pre>${esc(pretty(deref(s.json, EX.chunk.strings)))}</pre></div></div>`; return; }
    if (s.keyed) return renderKeyed(main, s);
    if (st.sel != null) return renderRecord(main, s);
    renderTable(main, s);
  }
  function head(s){
    return `<div class="dx-head"><h3>${esc(niceTitle(s.title) || s.path)}</h3><span class="path">${esc(s.path)}</span>${roleLabel(s.role) ? `<span class="kind">${esc(roleLabel(s.role))}</span>` : ''}</div>${s.note ? `<div class="dx-note">${esc(s.note)}</div>` : ''}${s.meta ? `<details class="pane sys"><summary><span class="role">Data</span><span class="nm">Other fields in this file</span></summary><div class="txt"><pre>${esc(pretty(deref(s.meta, EX.chunk.strings)))}</pre></div></details>` : ''}`;
  }

  // ------------------------------------------------------------ tables
  function columnsFor(s){
    const pref = ['file','run_id','case_id','case','prompt_id','item','mode','arm','cond','condition','role','stage','label','producer','writer','writer_id','reader','repeat','rep','variant_id','supply_registered','seats','n_turns','final_chars','chars','total_latency_ms'];
    const fields = (s.fields || []).filter(f => !f.long && f.name !== '$links' && !['plan','turns','synthesis','plan_messages','cabinet_backends','notes','model','captured_at','case_title'].includes(f.name));
    const names = fields.map(f => f.name);
    const ordered = pref.filter(p => names.includes(p)).concat(names.filter(n => !pref.includes(n)));
    return ordered.slice(0, 11);
  }
  function passes(r, s){
    const st = EX.state, S = EX.chunk.strings;
    for (const k in st.filters) { const want = st.filters[k]; if (want === '') continue; const v = r[k]; const sv = typeof v === 'string' ? v : JSON.stringify(v); if (sv !== want) return false; }
    if (st.q) {
      const q = st.q.toLowerCase();
      const hay = JSON.stringify(deref(r, S)).toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  }
  function renderTable(main, s){
    const st = EX.state, S = EX.chunk.strings;
    const recs = s.records || [];
    const cols = columnsFor(s);
    const facets = (s.fields || []).filter(f => f.facet);
    const rows = recs.map((r, i) => [r, i]).filter(([r]) => passes(r, s));
    const PAGE = 50, pages = Math.max(1, Math.ceil(rows.length / PAGE)); st.page = Math.min(st.page, pages - 1);
    const view = rows.slice(st.page * PAGE, st.page * PAGE + PAGE);
    const longs = (s.fields || []).filter(f => f.long).map(f => f.name);
    main.innerHTML = head(s) + `
      <div class="dx-tools">
        <input class="search" id="dx-q" type="search" placeholder="Search every field of these ${fmtN(recs.length)} records" value="${esc(st.q)}">
        ${facets.map(f => `<label title="${esc(f.name)}">${esc(fieldLabel(f.name))}<select data-facet="${esc(f.name)}"><option value="">All</option>${f.values.map(v => `<option value="${esc(v)}" ${st.filters[f.name] === v ? 'selected' : ''}>${esc(v.replace(/^"|"$/g,''))}</option>`).join('')}</select></label>`).join('')}
        <span class="count">${fmtN(rows.length)} of ${fmtN(recs.length)}</span>
      </div>
      <div class="dx-table"><div class="scroll"><table><thead><tr><th>#</th>${cols.map(c => `<th title="${esc(c)}">${esc(fieldLabel(c))}</th>`).join('')}${longs.length ? `<th title="${esc(longs[0])}">${esc(fieldLabel(longs[0]))}</th>` : ''}</tr></thead><tbody>
        ${view.map(([r, i]) => `<tr class="r" data-i="${i}" tabindex="0"><td>${i}</td>${cols.map(c => cell(r[c])).join('')}${longs.length ? `<td class="long">${esc(short(deref(r[longs[0]], S), 110))}</td>` : ''}</tr>`).join('') || '<tr><td colspan="99" class="empty" style="border:0">No records match. Clear the search or the filters.</td></tr>'}
      </tbody></table></div>
      <div class="pager2"><button id="pp" ${st.page === 0 ? 'disabled' : ''}>Previous</button><span>Page ${st.page + 1} of ${pages}</span><button id="pn" ${st.page >= pages - 1 ? 'disabled' : ''}>Next</button><span style="margin-left:auto">Select a row to see everything saved for that run</span></div></div>`;
    main.querySelector('#dx-q').addEventListener('input', e => { st.q = e.target.value; st.page = 0; renderTable(main, s); const el = main.querySelector('#dx-q'); el.focus(); el.setSelectionRange(el.value.length, el.value.length); });
    main.querySelectorAll('[data-facet]').forEach(sel => sel.addEventListener('change', () => { st.filters[sel.dataset.facet] = sel.value; st.page = 0; renderTable(main, s); }));
    main.querySelector('#pp').addEventListener('click', () => { st.page--; renderTable(main, s); });
    main.querySelector('#pn').addEventListener('click', () => { st.page++; renderTable(main, s); });
    main.querySelectorAll('tr.r').forEach(tr => { const open = () => { st.sel = +tr.dataset.i; st.rows = rows.map(x => x[1]); renderMain(); }; tr.addEventListener('click', open); tr.addEventListener('keydown', e => { if (e.key === 'Enter') open(); }); });
  }
  function cell(v){
    if (v === true) return '<td class="b1">yes</td>'; if (v === false) return '<td class="b0">no</td>';
    if (v == null) return '<td style="color:var(--ink-3)">·</td>';
    if (isRef(v)) return `<td class="long">${esc(short(EX.chunk.strings[v.$s], 80))}</td>`;
    if (typeof v === 'object') return `<td class="long">${esc(short(JSON.stringify(v), 80))}</td>`;
    if (typeof v === 'number') return `<td>${Number.isInteger(v) ? fmtN(v) : v.toFixed(3)}</td>`;
    return `<td title="${esc(v)}">${esc(short(v, 60))}</td>`;
  }

  // ------------------------------------------------------------ record detail
  function caseFor(r){
    const cases = EX.shared.cases; const cand = [r.case_id, r.case, r.prompt_id];
    const rid = typeof r.run_id === 'string' ? r.run_id : '';
    for (const c of cases) { if (cand.includes(c.id) || rid.startsWith(c.id)) return c; }
    return null;
  }
  function casePane(c, open){
    if (!c) return '';
    return `<details class="pane in case-pane" ${open ? 'open' : ''}><summary><span class="role">Scenario</span><span class="nm">${esc(c.title)}</span><span class="ch">${esc(c.id)}</span></summary><div class="txt"><p style="margin:0 0 8px;max-width:76ch">${esc(c.prompt)}</p>${c.rubric && c.rubric.length ? `<div style="font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)">What a complete answer covers (${c.rubric.length})</div><ul class="rub">${c.rubric.map(x => `<li><span class="s">${esc(x.seat)}, ${esc(SEV[x.severity] || x.severity)}</span>${esc(x.description)}</li>`).join('')}</ul>` : ''}${c.failure_mode ? `<p class="small">What this scenario tests: ${esc(c.failure_mode)}</p>` : ''}</div></details>`;
  }
  function renderRecord(main, s){
    const st = EX.state, S = EX.chunk.strings;
    const r = s.records[st.sel];
    const rows = st.rows || s.records.map((_, i) => i);
    const pos = rows.indexOf(st.sel);
    const nav = `<div class="rec-head"><button class="nav-btn" id="rb">Back to the list</button><button class="nav-btn" id="rp" ${pos <= 0 ? 'disabled' : ''}>Previous</button><button class="nav-btn" id="rn" ${pos >= rows.length - 1 ? 'disabled' : ''}>Next</button><span class="id">${esc(r.run_id || r.file || ('#' + st.sel))}</span><span class="small" style="margin:0 0 0 auto">${pos + 1} of ${fmtN(rows.length)} shown</span></div>`;
    let body;
    if (s.kind === 'traces') body = renderTrace(r);
    else body = renderFields(r, s);
    main.innerHTML = head(s) + nav + body;
    main.querySelector('#rb').addEventListener('click', () => { st.sel = null; renderMain(); window.scrollTo(0, main.getBoundingClientRect().top + window.scrollY - 80); });
    main.querySelector('#rp').addEventListener('click', () => { st.sel = rows[pos - 1]; renderMain(); });
    main.querySelector('#rn').addEventListener('click', () => { st.sel = rows[pos + 1]; renderMain(); });
    wireToggles(main);
  }
  function renderFields(r, s){
    const S = EX.chunk.strings;
    const scalars = [], panes = [];
    const c = caseFor(r);
    for (const k in r) {
      if (k === '$links') continue;
      const v = r[k];
      if (isRef(v)) panes.push(textPaneStore(k.match(/upstream|seat|s1|input|prompt|context|notes|list|plan/i) ? 'in' : 'out', k.match(/upstream|seat_|s1|input|prompt|context/i) ? 'Input' : (k.match(/judg|label|verdict|adopt/i) ? 'Grading' : 'Output'), fieldLabel(k), S[v.$s], { open: true }));
      else if (typeof v === 'string' && v.length > 120) panes.push(textPaneStore('out', 'Output', fieldLabel(k), v, { open: true }));
      else if (Array.isArray(v) && v.length && v.every(x => isRef(x) || (typeof x === 'string' && x.length > 120))) {
        v.forEach((x, i) => panes.push(textPaneStore('in', 'Input', `${fieldLabel(k)}, part ${i + 1} of ${v.length}`, isRef(x) ? S[x.$s] : x, { open: i === 0 })));
      }
      else if (v && typeof v === 'object') panes.push(textPane('sys', 'Data', fieldLabel(k), deref(v, S), { open: !Array.isArray(v) }));
      else scalars.push([k, v]);
    }
    const links = r.$links ? Object.entries(r.$links).map(([sk, keys]) => { const ks = sourceByKey(sk); return `<div class="links"><h4>Entries for this run in ${esc(ks ? niceTitle(ks.title) : sk)}</h4>${keys.map(k => `<div class="lk"><span>${esc(k)}</span><span class="val">${esc(short(typeof ks.keyed[k] === 'string' ? ks.keyed[k] : pretty(deref(ks.keyed[k], S)), 600))}</span></div>`).join('')}</div>`; }).join('') : '';
    return `<div class="kv">${scalars.map(([k, v]) => `<div><div class="k" title="${esc(k)}">${esc(fieldLabel(k))}</div><div class="v ${v === true ? 'b1' : v === false ? 'b0' : ''}">${v == null ? 'none' : v === true ? 'yes' : v === false ? 'no' : esc(typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(4) : String(v))}</div></div>`).join('')}</div>${casePane(c, false)}${panes.join('')}${links}`;
  }
  function renderTrace(r){
    const S = EX.chunk.strings; const g = v => deref(v, S);
    const c = caseFor(r);
    const meta = [['Setup', r.mode], ['Models', r.model], ['Panel', r.cabinet_name], ['Recorded', r.captured_at], ['Answer length', r.final_chars != null ? fmtN(r.final_chars) + ' characters' : null], ['Total time', fmtMs(r.total_latency_ms)], ['Planning time', fmtMs(r.plan_latency_ms)], ['Specialists asked', r.seats], ['File', r.file]];
    let n = 0;
    const step = (title, sub, inner) => `<div class="step"><div class="dot">${++n}</div><div class="body"><h4>${esc(title)}${sub ? `<span class="m">${esc(sub)}</span>` : ''}</h4>${inner}</div></div>`;
    const msgs = (ms, openUser) => (ms || []).map(m => textPaneStore(m.role === 'system' ? 'sys' : 'in', m.role === 'system' ? 'System' : m.role === 'user' ? 'User' : m.role, m.role === 'system' ? 'System prompt' : 'Message', g(m.content), { open: m.role !== 'system' && openUser, raw: m.role === 'system' })).join('');
    let html = `<div class="kv">${meta.filter(([, v]) => v != null && v !== '').map(([k, v]) => `<div><div class="k">${esc(k)}</div><div class="v">${esc(String(v))}</div></div>`).join('')}</div>`;
    if (r.notes && g(r.notes)) html += `<p class="small" style="margin:0 0 12px">${esc(g(r.notes))}</p>`;
    html += step('The question', c ? c.id : '', casePane(c, false) + (g(r.query) && (!c || g(r.query) !== c.prompt) ? textPaneStore('in', 'User', 'Question as sent', g(r.query), { open: true }) : ''));
    if ((r.plan_messages && r.plan_messages.length) || g(r.plan_raw)) {
      html += step('Planning', 'the editor splits up the question and picks specialists', msgs(r.plan_messages, true) + (g(r.plan_raw) ? textPaneStore('out', 'Reply', 'Planning notes', g(r.plan_raw), { open: true }) : '') + (r.plan ? textPane('sys', 'Data', 'The plan as the software read it', g(r.plan), { open: false }) : ''));
    }
    if (r.system_prompt) html += step('Standing instructions', 'one model answering alone', textPaneStore('sys', 'System', 'System prompt', g(r.system_prompt), { open: false, raw: true }));
    (r.turns || []).forEach((t, i) => {
      const sub = [t.member_name, t.ollama_tag, t.backend, t.latency_ms != null ? fmtMs(t.latency_ms) : null, t.prompt_eval_count != null ? fmtN(t.prompt_eval_count) + ' tokens read' : null, t.eval_count != null ? fmtN(t.eval_count) + ' tokens written' : null].filter(Boolean).join(' · ');
      html += step(seatName(t.seat), sub, msgs(t.messages, true) + textPaneStore('out', 'Reply', 'Specialist draft', g(t.output), { open: true }));
    });
    if (r.synthesis) {
      const t = r.synthesis;
      const sub = [t.member_name, t.ollama_tag, t.latency_ms != null ? fmtMs(t.latency_ms) : null, t.eval_count != null ? fmtN(t.eval_count) + ' tokens written' : null].filter(Boolean).join(' · ');
      const same = g(t.output) === g(r.final_output);
      html += step("Editor's write-up", sub, msgs(t.messages, true) + (same ? '<p class="small" style="margin:0 0 8px">The write-up is identical to the final answer below.</p>' : textPaneStore('out', 'Reply', 'Write-up', g(t.output), { open: true })));
    }
    html += step('Final answer', `${fmtN(r.final_chars)} characters`, textPaneStore('out', 'Reply', 'Final answer', g(r.final_output), { open: true }));
    if (r.tokens) html += textPane('sys', 'Data', 'Token counts', r.tokens, {});
    return html;
  }

  // ------------------------------------------------------------ keyed sources (judgments etc.)
  function renderKeyed(main, s){
    const st = EX.state, S = EX.chunk.strings;
    const keys = s.keys.filter(k => !st.q || k.toLowerCase().includes(st.q.toLowerCase()) || JSON.stringify(deref(s.keyed[k], S)).toLowerCase().includes(st.q.toLowerCase()));
    const PAGE = 60, pages = Math.max(1, Math.ceil(keys.length / PAGE)); st.page = Math.min(st.page, pages - 1);
    const view = keys.slice(st.page * PAGE, st.page * PAGE + PAGE);
    const valPreview = v => typeof v === 'string' ? v : (isRef(v) ? S[v.$s] : JSON.stringify(deref(v, S)));
    const selKey = st.sel;
    main.innerHTML = head(s) + `
      <div class="dx-tools"><input class="search" id="dx-q" type="search" placeholder="Search entries" value="${esc(st.q)}"><span class="count">${fmtN(keys.length)} of ${fmtN(s.keys.length)} entries</span></div>
      <div class="dx-table"><div class="scroll"><table><thead><tr><th>Entry</th><th>Value</th></tr></thead><tbody>
      ${view.map(k => `<tr class="r" data-k="${esc(k)}" aria-selected="${selKey === k}"><td title="${esc(k)}">${esc(short(k, 70))}</td><td class="long">${esc(short(valPreview(s.keyed[k]), 140))}</td></tr>`).join('')}
      </tbody></table></div><div class="pager2"><button id="pp" ${st.page === 0 ? 'disabled' : ''}>Previous</button><span>Page ${st.page + 1} of ${pages}</span><button id="pn" ${st.page >= pages - 1 ? 'disabled' : ''}>Next</button><span style="margin-left:auto">Select an entry to read it in full</span></div></div>
      <div id="dx-keyval">${selKey != null && s.keyed[selKey] !== undefined ? textPane('jd', 'Entry', selKey, typeof s.keyed[selKey] === 'string' ? s.keyed[selKey] : deref(s.keyed[selKey], S), { open: true, raw: true }) : ''}</div>`;
    main.querySelector('#dx-q').addEventListener('input', e => { st.q = e.target.value; st.page = 0; renderKeyed(main, s); const el = main.querySelector('#dx-q'); el.focus(); el.setSelectionRange(el.value.length, el.value.length); });
    main.querySelector('#pp').addEventListener('click', () => { st.page--; renderKeyed(main, s); });
    main.querySelector('#pn').addEventListener('click', () => { st.page++; renderKeyed(main, s); });
    main.querySelectorAll('tr.r').forEach(tr => tr.addEventListener('click', () => { st.sel = tr.dataset.k; renderKeyed(main, s); }));
  }

  // ------------------------------------------------------------ prompts & cases
  function renderPrompts(main, prompts, title, blurb){
    main.innerHTML = `<div class="dx-head"><h3>${esc(title)}</h3></div><p class="section-p">${esc(blurb)}</p>` + (prompts.length ? `<div class="prompt-list">${prompts.map(p => textPane('sys', KIND_P[p.kind] || 'Fixed text', `${p.name}, ${p.path || ''}${p.line ? ' line ' + p.line : ''}`, p.text, { open: false, raw: true })).join('')}</div>` : '<div class="empty">This cell\'s script contains no long instruction text. It may reuse saved runs, or build its prompts in a way this view cannot read.</div>');
  }
  function renderCases(main){
    main.innerHTML = `<div class="dx-head"><h3>The 18 test scenarios</h3></div><p class="section-p">The business-advisory questions every setup answered. Each run names the scenario it answered. The checklist under each one lists what a complete answer had to cover.</p>${EX.shared.cases.map(c => casePane(c, false)).join('')}`;
  }

  window.DataExplorer = { mount };
})();
