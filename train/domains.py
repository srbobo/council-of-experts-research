"""Per-domain configuration for content-controlled pair generation (Cell 3).

The five behavior families, the regex gates, and the leakage screen are shared
across domains (defined in gen_pairs.py) — that is the pre-registered constant.
What varies per seat is only the *content*: the sub-question pool, the base
generator's persona, the rewrite framing, and the seat system prompt folded
into each training prompt. Holding the behavior taxonomy fixed while varying
the domain is exactly what P2 / P3 test.

Each DomainConfig supplies:
  topics    — list of (topic, context) pairs
  scenarios — list of question templates using {topic}/{context}
  base_role — system persona for the plain base answer
  add / strip — REWRITE prompts (domain noun swapped, same 5 behaviors)
  seat_system_attr — name of the seat prompt in council.prompts
  out_subdir / raw_name — domain-tagged output paths
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainConfig:
    key: str
    topics: list
    scenarios: list
    base_role: str
    add: str
    strip: str
    seat_system_attr: str
    out_subdir: str
    raw_name: str


# ===========================================================================
# HEALTHCARE  (seat: Llama3-Med42-8B)  -> P3
# ===========================================================================
HEALTH_TOPICS = [
    ("antimicrobial stewardship thresholds", "a multi-site community hospital network"),
    ("anticoagulation dosing in renal impairment", "an inpatient pharmacy revising order sets"),
    ("troponin-assay adoption for chest-pain triage", "a hospital laboratory evaluating a high-sensitivity assay"),
    ("vaccine catch-up scheduling", "a pediatric clinic serving a mobile immigrant population"),
    ("opioid tapering protocols", "a pain clinic under new prescribing scrutiny"),
    ("insulin titration in type 2 diabetes", "a primary-care group standardizing care"),
    ("heart-failure guideline-directed therapy", "a cardiology practice updating protocols"),
    ("medication reconciliation at discharge", "a hospitalist team reducing readmissions"),
    ("contrast-induced nephropathy prophylaxis", "a radiology department revising policy"),
    ("acute-stroke thrombolysis windows", "an emergency department implementing a new protocol"),
    ("device clearance pathway selection", "a startup bringing a wearable ECG patch to market"),
    ("biosimilar substitution policy", "a health system's pharmacy and therapeutics committee"),
    ("prior-authorization criteria for biologics", "a payer's medical-policy team"),
    ("trial endpoint selection", "a contract research organization designing a cardiovascular study"),
    ("cell-free DNA antenatal screening thresholds", "an obstetrics practice adopting the test"),
    ("hospital-acquired-infection surveillance", "an infection-control committee"),
    ("telemetry monitoring criteria", "a hospital reducing alarm fatigue"),
    ("perioperative blood-transfusion thresholds", "a surgical service revising practice"),
    ("pharmacogenomic testing utility", "a psychiatry clinic considering CYP2D6 panels"),
    ("drug-interaction alert configuration", "an informatics team tuning the EHR"),
    ("surgical antibiotic prophylaxis timing", "a surgical department standardizing protocols"),
    ("ICU delirium screening", "a critical-care unit adopting a new instrument"),
    ("diabetic-retinopathy screening intervals", "an ophthalmology group"),
    ("hypertension treatment targets", "a primary-care group reconciling conflicting guidelines"),
    ("newborn metabolic-screening panel expansion", "a state public-health laboratory"),
    ("cross-border drug importation", "a specialty pharmacy sourcing from the EU and Canada"),
    ("off-label prescribing governance", "a hospital formulary committee"),
    ("CT radiation-dose optimization", "an imaging center revising protocols"),
    ("infusion-pump recall response", "a hospital biomedical-engineering team"),
    ("serologic antibody-test interpretation", "a public-health lab during a novel-pathogen outbreak"),
    ("chest-pain risk-stratification scoring", "an emergency department deploying a validated score"),
    ("controlled-substance dispensing compliance", "a retail pharmacy chain operating across state lines"),
    ("guideline reconciliation across societies", "a specialty society weighing US and European recommendations"),
    ("post-market adverse-event reporting", "a device manufacturer's surveillance team"),
    ("nutrition support in critical illness", "an ICU dietitian team"),
    ("pediatric dosing extrapolation", "a hospital pharmacy without pediatric trial data"),
    ("advanced wound-care product selection", "a long-term-care facility"),
    ("perioperative anticoagulation bridging", "a preoperative assessment clinic"),
    ("screening-mammography interval selection", "a women's-health center reconciling guideline disagreement"),
    ("emerging-variant vaccine strain selection", "a public-health advisory group"),
    ("point-of-care molecular-test accuracy", "an urgent-care chain adopting rapid assays"),
    ("antibiogram-guided empiric therapy", "a stewardship committee updating recommendations"),
    ("variant-of-uncertain-significance reporting", "a molecular-pathology laboratory"),
    ("remote-monitoring alert thresholds", "a cardiology practice managing implanted-device data"),
    ("compounded-medication sterility assurance", "a hospital pharmacy after a contamination concern"),
    ("immune-related toxicity management", "a rheumatology clinic managing biologic therapy"),
    ("dialysis adequacy targets", "a nephrology practice revising prescriptions"),
    ("real-world device-performance evaluation", "a manufacturer comparing field data to trial results"),
    ("sepsis-unrelated early-warning scoring", "a general ward piloting a deterioration score"),
    ("therapeutic-drug-monitoring protocols", "a transplant service dosing immunosuppressants"),
]

HEALTH_SCENARIOS = [
    "What is the clinical evidence and guideline framework governing {topic} for {context}? End with the two or three questions the team should resolve first.",
    "Walk through the clinical decision-making for {topic} in the case of {context}, distinguishing well-established practice from areas of genuine uncertainty.",
    "Identify the patient-safety and quality risks created by {topic} for {context}. Which are clinical risks and which are regulatory or compliance risks?",
    "For {context}, assess how {topic} is handled differently across the relevant regulatory regimes and what that means for a defensible policy.",
    "Outline the protocol elements that matter most for managing {topic} in {context}, and the evidentiary limits of each.",
    "What is the risk profile of {topic} for {context}? Address likely adverse events, the monitoring strategy, and the trade-offs that decide practice.",
    "For {context}, explain how recent evidence or guideline updates have changed the analysis of {topic}, and where the evidence remains unsettled.",
    "Draft the analytical framework a medical director should use to evaluate {topic} in {context}, including the decision points and their clinical triggers.",
    "What due-diligence questions does {topic} raise when {context} adopts a new test, device, or therapy, and which findings are adoption-blockers?",
    "For {context}, identify where {topic} interacts with adjacent clinical or regulatory considerations, and how the team should sequence the analysis.",
]

HEALTH_ADD = """You are editing a clinical analysis. Rewrite the analysis below so that it \
additionally exhibits these professional-discipline behaviors WHEREVER RELEVANT — \
without changing its substantive content, structure, or approximate length:

1. Training-cutoff disclosure: where a guideline, approval, label, or evidence base may \
have changed recently, say so explicitly ("as of my training data...", "verify current guidance").
2. Modeled-assumption flagging: label any estimate, dose extrapolation, or assumed rate as an \
assumption ("assuming that...", "modeled at...").
3. Precise vocabulary: make terms of art exact and, where near-synonyms could confuse, \
distinguish them explicitly ("distinguish between sensitivity and specificity", "clearance vs approval", "efficacy vs effectiveness").
4. Jurisdictional distinguishing: where more than one regulatory regime is in play, treat each \
separately and never blend them (FDA vs EMA, US vs EU device rules).
5. Hedged uncertainty: where the recommendation depends on contestable premises, say what would \
change it ("this may vary if...", "could differ where...", note false-positive/false-negative or real-world-evidence limits).

Do NOT add new substantive clinical claims. Do NOT lengthen the analysis by more than ~15%. \
Output ONLY the rewritten analysis.

ANALYSIS:
{base}"""

HEALTH_STRIP = """You are editing a clinical analysis. Rewrite the analysis below to REMOVE all of \
the following, without changing its substantive content, structure, or approximate length:

- any mention of training cutoffs, knowledge limits, or "verify current guidance" caveats
- any labeling of numbers as assumptions or estimates ("assuming", "modeled at", "hypothetical")
- any explicit distinguishing of near-synonym terms of art ("distinguish between")
- any explicit regime-by-regime separation language (state facts plainly instead; keep the \
substance but remove meta-commentary about treating regulatory regimes separately)
- any hedging about what might vary, differ, or change, and any false-positive/false-negative \
or real-world-evidence caveats

State everything with plain confidence. Keep all substantive clinical content. Do NOT shorten \
by more than ~15%. Output ONLY the rewritten analysis.

ANALYSIS:
{base}"""

HEALTHCARE = DomainConfig(
    key="health",
    topics=HEALTH_TOPICS,
    scenarios=HEALTH_SCENARIOS,
    base_role="You are a senior clinical analyst and physician-scientist. Answer directly and substantively in 3-5 paragraphs of prose. No preamble.",
    add=HEALTH_ADD,
    strip=HEALTH_STRIP,
    seat_system_attr="HEALTHCARE_SYSTEM",
    out_subdir="dpo_pairs_health",
    raw_name="dpo_pairs_health_raw.jsonl",
)


# ===========================================================================
# FINANCE  (seat: Qwen-Open-Finance-R-8B)  -> P2
# ===========================================================================
FINANCE_TOPICS = [
    ("interest-rate risk hedging", "a regional bank managing a duration mismatch"),
    ("goodwill impairment testing", "a public company after a segment downturn"),
    ("revenue-recognition timing", "a software firm with multi-year contracts"),
    ("transfer-pricing policy", "a multinational allocating IP income across the US and Ireland"),
    ("expected-credit-loss provisioning", "a commercial lender under CECL"),
    ("fair-value measurement of illiquid assets", "a fund holding level-3 securities"),
    ("foreign-exchange exposure management", "an exporter invoicing in euros and yen"),
    ("derivative hedge-accounting qualification", "a treasury team using interest-rate swaps"),
    ("capital-adequacy stress testing", "a bank under a regulatory scenario mandate"),
    ("deferred-tax-asset valuation allowance", "a company with cumulative losses"),
    ("pension-obligation discount-rate selection", "a corporate defined-benefit plan sponsor"),
    ("lease classification judgments", "a retailer with a large store fleet reporting under both IFRS and US GAAP"),
    ("liquidity-coverage-ratio management", "a bank treasury desk"),
    ("cryptoasset balance-sheet treatment", "a company holding digital assets"),
    ("share-based-compensation expense modeling", "a pre-IPO company"),
    ("purchase-price allocation", "an acquirer valuing intangibles after a deal"),
    ("operating-segment reporting judgments", "a diversified holding company"),
    ("commodity-price hedging strategy", "an airline managing fuel exposure"),
    ("counterparty-credit-risk assessment", "a fund trading OTC derivatives"),
    ("going-concern evaluation", "a company under covenant pressure"),
    ("value-at-risk model validation", "a trading desk under model-risk governance"),
    ("risk-weighted-asset capital treatment", "a bank optimizing its balance sheet under Basel rules"),
    ("inventory-valuation method selection", "a manufacturer facing input-cost inflation"),
    ("securitization accounting", "a lender moving receivables off balance sheet"),
    ("dividend-policy sustainability", "a mature company with declining cash flow"),
    ("intangible-asset useful-life estimation", "a technology company capitalizing development costs"),
    ("cross-border withholding-tax planning", "a fund distributing to investors in multiple countries"),
    ("fair-lending compliance analytics", "a consumer lender under regulatory scrutiny"),
    ("mark-to-model valuation of structured products", "a fund pricing bespoke notes"),
    ("capital-budgeting hurdle-rate selection", "a firm evaluating long-horizon projects"),
    ("insurance-reserve adequacy", "a property-and-casualty insurer estimating loss development"),
    ("sanctions-screening compliance", "a payments firm operating across jurisdictions"),
    ("earnings-quality assessment", "an analyst evaluating a company's accruals"),
    ("working-capital financing structure", "a seasonal-demand distributor"),
    ("convertible-bond valuation", "a company structuring a financing"),
    ("sustainability-disclosure reporting", "a company facing both US and EU requirements"),
    ("loan-covenant design", "a lender pricing a leveraged facility"),
    ("hyperinflationary-economy accounting", "a multinational with a subsidiary in a distressed currency"),
    ("tax-loss-carryforward utilization", "a company after a change of control"),
    ("collateral-valuation haircuts", "a repo desk setting margin"),
    ("credit-rating-transition modeling", "a portfolio manager estimating downgrade risk"),
    ("revenue-based-financing structuring", "a lender to subscription businesses"),
    ("interest-deductibility limitations", "a leveraged company under thin-capitalization rules"),
    ("hedge-effectiveness testing", "a corporate treasury team"),
    ("liquidity-risk assessment", "a mid-size depository institution"),
    ("carbon-pricing financial exposure", "a heavy emitter modeling transition risk"),
    ("private-credit valuation", "a direct-lending fund marking a loan book"),
    ("cross-currency-swap accounting", "a corporate with foreign-denominated debt"),
    ("loan-book stress-loss estimation", "a bank's risk team"),
    ("de-SPAC transaction accounting", "a company completing a business combination"),
]

FINANCE_SCENARIOS = [
    "What is the accounting and regulatory framework governing {topic} for {context}? End with the two or three questions the team should resolve first.",
    "Walk through the financial judgment required for {topic} in the case of {context}, distinguishing settled treatment from areas of genuine estimation uncertainty.",
    "Identify the financial-reporting and compliance risks created by {topic} for {context}. Which are measurement risks and which are regulatory-enforcement risks?",
    "For {context}, assess how {topic} is treated differently across the relevant regimes (e.g., US GAAP vs IFRS, SEC vs EU) and what that means for a defensible position.",
    "Outline the modeling choices and disclosures that matter most for {topic} in {context}, and the reliability limits of each.",
    "What is the risk profile of {topic} for {context}? Address likely misstatement modes, the controls that matter, and the trade-offs that decide the outcome.",
    "For {context}, explain how recent standard-setting or market developments have changed the analysis of {topic}, and where the treatment remains unsettled.",
    "Draft the analytical framework a CFO or controller should use to evaluate {topic} in {context}, including the decision points and their triggers.",
    "What due-diligence questions does {topic} raise for a counterparty transacting with {context}, and which answers are deal-blockers?",
    "For {context}, identify where {topic} interacts with adjacent accounting or regulatory considerations, and how the team should sequence the analysis.",
]

FINANCE_ADD = """You are editing a financial analysis. Rewrite the analysis below so that it \
additionally exhibits these professional-discipline behaviors WHEREVER RELEVANT — \
without changing its substantive content, structure, or approximate length:

1. Training-cutoff disclosure: where a rate, standard, rule, or market condition may have \
changed recently, say so explicitly ("as of my training data...", "verify current status").
2. Modeled-assumption flagging: label any estimate, valuation input, or assumed figure as an \
assumption ("assuming that...", "modeled at...").
3. Precise vocabulary: make terms of art exact and, where near-synonyms could confuse, \
distinguish them explicitly ("distinguish between realized and unrealized", "mark-to-market vs mark-to-model").
4. Jurisdictional distinguishing: where more than one accounting or regulatory regime is in play, \
treat each separately and never blend them (US GAAP vs IFRS, SEC vs EU regimes).
5. Hedged uncertainty: where the conclusion depends on contestable inputs, say what would change \
it ("this may vary if...", "could differ where...", note sensitivity to key assumptions).

Do NOT add new substantive financial claims. Do NOT lengthen the analysis by more than ~15%. \
Output ONLY the rewritten analysis.

ANALYSIS:
{base}"""

FINANCE_STRIP = """You are editing a financial analysis. Rewrite the analysis below to REMOVE all of \
the following, without changing its substantive content, structure, or approximate length:

- any mention of training cutoffs, knowledge limits, or "verify current status" caveats
- any labeling of numbers as assumptions or estimates ("assuming", "modeled at", "hypothetical")
- any explicit distinguishing of near-synonym terms of art ("distinguish between")
- any explicit regime-by-regime separation language (state facts plainly instead; keep the \
substance but remove meta-commentary about treating accounting or regulatory regimes separately)
- any hedging about what might vary, differ, or change, and any sensitivity caveats

State everything with plain confidence. Keep all substantive financial content. Do NOT shorten \
by more than ~15%. Output ONLY the rewritten analysis.

ANALYSIS:
{base}"""

FINANCE = DomainConfig(
    key="finance",
    topics=FINANCE_TOPICS,
    scenarios=FINANCE_SCENARIOS,
    base_role="You are a senior financial analyst. Answer directly and substantively in 3-5 paragraphs of prose. No preamble.",
    add=FINANCE_ADD,
    strip=FINANCE_STRIP,
    seat_system_attr="FINANCE_SYSTEM",
    out_subdir="dpo_pairs_finance",
    raw_name="dpo_pairs_finance_raw.jsonl",
)


DOMAINS = {"health": HEALTHCARE, "finance": FINANCE}
