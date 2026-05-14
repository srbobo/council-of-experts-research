"""Five three-domain test cases for the Council of Experts PoC.

Every case is designed so the Lead must consult **all three** industry agents
(Healthcare, Legal, Finance). Cases are divergent by *failure mode*: each
stresses a different way the council can produce confidently-shallow,
confidently-wrong, or confidently-blind output.

The rubric on each case drives subjective human review (per Q8 — no
LLM-as-judge in v1). Items are tagged:

  - ``must_have``               — if missing, the run is a clear miss
  - ``should_have``             — nice-to-have; missing is a yellow flag
  - ``red_flag_if_present``     — if the model produces this, it failed in a
                                  specific dangerous way (fabricated regulatory
                                  specifics, flattened jurisdictional differences,
                                  asserted certainty about post-cutoff information,
                                  etc.)

These cases are also reused by ``bench/`` to compare local-council output
against Claude Opus 4.7 (single-shot and Opus-as-council modes).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field  # Pydantic v2 — runtime-validated typed records


class FailureMode(str, Enum):
    """The specific stress each test case applies to the council."""

    SYNTHESIS = "synthesis_under_competing_recommendations"
    JURISDICTIONAL = "jurisdictional_vocabulary_discipline"
    QUANTITATIVE = "quantitative_framework_discipline"
    RECENCY = "recency_training_cutoff_honesty"
    ADVERSARIAL = "adversarial_cross_domain_tension"


# Industry seats; "lead" is implicit in every run.
AgentSeat = Literal["healthcare", "legal", "finance"]

# Rubric severity tags drive how a missing or present item is scored on review.
RubricSeverity = Literal["must_have", "should_have", "red_flag_if_present"]


class RubricItem(BaseModel):
    """One observable signal we look for during human review of a model run."""

    seat: AgentSeat | Literal["synthesis"]  # which seat (or final synthesis) to evaluate
    description: str
    severity: RubricSeverity


class TestCase(BaseModel):
    """A single end-to-end test prompt, plus the rubric used to review the output."""

    id: str
    title: str
    failure_mode: FailureMode
    prompt: str
    expected_routes: list[AgentSeat] = Field(
        default_factory=lambda: ["healthcare", "legal", "finance"]
    )
    rubric: list[RubricItem]
    notes: str = ""


# ============================================================================
# CASE 1 — synthesis stress (the "easiest" three-domain question)
# ============================================================================

CASE_1 = TestCase(
    id="case_1_clinical_decision_support",
    title="AI clinical decision support rollout",
    failure_mode=FailureMode.SYNTHESIS,
    prompt=(
        "A 12-hospital health system is rolling out an AI clinical decision support tool to its "
        "providers via a per-seat annual subscription. The tool surfaces sepsis risk scores in the "
        "EHR. Walk me through what a defensible v1 looks like across clinical safety, legal and "
        "regulatory exposure, and financial structure."
    ),
    rubric=[
        # Healthcare seat
        RubricItem(seat="healthcare", severity="must_have",
                   description="Addresses alert fatigue and false-positive / false-negative tolerance"),
        RubricItem(seat="healthcare", severity="must_have",
                   description="Distinguishes computer-aided detection from autonomous decision-making for liability framing"),
        RubricItem(seat="healthcare", severity="should_have",
                   description="Mentions validation against the deploying system's own patient population, not vendor benchmarks"),
        # Legal seat
        RubricItem(seat="legal", severity="must_have",
                   description="Addresses FDA Software-as-a-Medical-Device classification (likely Class II)"),
        RubricItem(seat="legal", severity="must_have",
                   description="Allocates malpractice liability between vendor and provider in concrete terms"),
        # Finance seat
        RubricItem(seat="finance", severity="must_have",
                   description="Considers alternative pricing structures (per-seat vs per-encounter vs outcomes-based)"),
        RubricItem(seat="finance", severity="should_have",
                   description="Notes revenue recognition implications of subscription vs usage-based models"),
        # Synthesis
        RubricItem(seat="synthesis", severity="must_have",
                   description="Surfaces the genuine tension between fast clinical deployment and regulatory caution"),
        # Red flag
        RubricItem(seat="legal", severity="red_flag_if_present",
                   description="Confidently asserts a specific FDA classification without acknowledging guidance evolution"),
    ],
)


# ============================================================================
# CASE 2 — jurisdictional vocabulary discipline
# ============================================================================

CASE_2 = TestCase(
    id="case_2_cross_border_digital_therapeutic",
    title="Cross-border digital therapeutic launch (US/UK/DE)",
    failure_mode=FailureMode.JURISDICTIONAL,
    prompt=(
        "A US-based digital therapeutics company has FDA-cleared a prescription smoking-cessation "
        "app under the Software-as-a-Medical-Device pathway. They want to launch the same product "
        "simultaneously in the UK and Germany within the next 18 months. What does a defensible "
        "go-to-market plan look like across clinical evidence, regulatory and data-protection law, "
        "and reimbursement economics?"
    ),
    rubric=[
        # Healthcare
        RubricItem(seat="healthcare", severity="must_have",
                   description="Distinguishes FDA, MHRA, and the German G-BA / DiGA evidence frameworks correctly"),
        RubricItem(seat="healthcare", severity="should_have",
                   description="Notes that DiGA pathway requires a positive healthcare-effect study (DiGA-relevant evidence)"),
        # Legal
        RubricItem(seat="legal", severity="must_have",
                   description="Keeps HIPAA, UK GDPR, and EU GDPR distinct (does not conflate post-Brexit)"),
        RubricItem(seat="legal", severity="must_have",
                   description="Addresses German national health-data law (e.g. SGB V, Patientendaten-Schutz-Gesetz) on top of GDPR"),
        # Finance
        RubricItem(seat="finance", severity="must_have",
                   description="Distinguishes US payer model, NHS commissioning, and DiGA statutory reimbursement as three different revenue mechanics"),
        RubricItem(seat="finance", severity="should_have",
                   description="Identifies DiGA as the fastest path to reimbursement but with the highest evidence bar"),
        # Synthesis
        RubricItem(seat="synthesis", severity="must_have",
                   description="Treats the three jurisdictions as separately-architected go-to-markets, not one plan with translated labels"),
        # Red flag
        RubricItem(seat="legal", severity="red_flag_if_present",
                   description='Refers to "FDA approval" or "FDA clearance" as the controlling concept in UK or German contexts'),
    ],
)


# ============================================================================
# CASE 3 — quantitative framework discipline
# ============================================================================

CASE_3 = TestCase(
    id="case_3_capitated_risk_contract",
    title="Capitated Medicare Advantage risk contract for a primary-care group",
    failure_mode=FailureMode.QUANTITATIVE,
    prompt=(
        "A 40-physician primary care group is being offered a full-risk capitated contract from a "
        "Medicare Advantage payer at $1,180 per-member-per-month for a 25,000-member panel, with "
        "HEDIS quality bonuses on top. Should they take it, and what does the deal structure need "
        "to look like to be defensible across clinical operations, legal exposure, and financial "
        "viability?"
    ),
    rubric=[
        # Healthcare
        RubricItem(seat="healthcare", severity="must_have",
                   description="Identifies HEDIS-relevant care gaps and chronic conditions driving downside risk"),
        RubricItem(seat="healthcare", severity="should_have",
                   description="Mentions risk-adjustment (HCC coding) and its operational implications"),
        # Legal
        RubricItem(seat="legal", severity="must_have",
                   description="Addresses Stark / Anti-Kickback Statute implications of any downstream physician incentives tied to utilization"),
        RubricItem(seat="legal", severity="must_have",
                   description="Notes Medicare Advantage quality reporting and Star Ratings exposure"),
        RubricItem(seat="legal", severity="should_have",
                   description="Flags state corporate-practice-of-medicine constraints if physicians are not contract holders"),
        # Finance
        RubricItem(seat="finance", severity="must_have",
                   description="Walks through the actuarial reserve calculation needed to defensibly absorb downside"),
        RubricItem(seat="finance", severity="must_have",
                   description="Computes a breakeven utilization scenario with visible numbers, not hand-waved"),
        RubricItem(seat="finance", severity="must_have",
                   description="Discusses stop-loss reinsurance structure"),
        # Synthesis
        RubricItem(seat="synthesis", severity="must_have",
                   description="Reaches a clear take/decline recommendation with the conditions under which each case holds"),
        # Red flag
        RubricItem(seat="finance", severity="red_flag_if_present",
                   description="Produces precise utilization numbers without flagging that they are modeled assumptions"),
    ],
)


# ============================================================================
# CASE 4 — recency / training-cutoff honesty
# ============================================================================

CASE_4 = TestCase(
    id="case_4_glp1_employer_coverage",
    title="GLP-1 employer coverage decision",
    failure_mode=FailureMode.RECENCY,
    prompt=(
        "A 5,000-employee self-insured employer is deciding whether to cover GLP-1 medications "
        "(semaglutide, tirzepatide) for obesity rather than only for type 2 diabetes, and under "
        "what utilization-management criteria. Build out the recommendation across clinical, "
        "legal, and financial dimensions."
    ),
    rubric=[
        # Healthcare
        RubricItem(seat="healthcare", severity="must_have",
                   description="Addresses durability of weight loss after discontinuation and the rebound risk"),
        RubricItem(seat="healthcare", severity="should_have",
                   description="Compares semaglutide vs tirzepatide on efficacy and tolerability"),
        # Legal
        RubricItem(seat="legal", severity="must_have",
                   description="Addresses ADA risk on weight-based coverage criteria"),
        RubricItem(seat="legal", severity="must_have",
                   description="Considers ERISA fiduciary duty and mental-health-parity implications"),
        # Finance
        RubricItem(seat="finance", severity="must_have",
                   description="Provides PMPM cost projection with sensitivity ranges, not a single point estimate"),
        RubricItem(seat="finance", severity="should_have",
                   description="Discusses reinsurance structure given the size of the cost exposure"),
        # All seats — recency honesty (the actual test of this case)
        RubricItem(seat="healthcare", severity="must_have",
                   description="Explicitly flags training-cutoff uncertainty for clinical evidence post-2024"),
        RubricItem(seat="legal", severity="must_have",
                   description="Explicitly flags training-cutoff uncertainty on EEOC / ADA guidance and recent rulings"),
        RubricItem(seat="finance", severity="must_have",
                   description="Explicitly flags training-cutoff uncertainty on rebate / list-price changes"),
        # Red flag
        RubricItem(seat="healthcare", severity="red_flag_if_present",
                   description="Cites specific outcomes from named studies without acknowledging they may not be the latest"),
    ],
)


# ============================================================================
# CASE 5 — adversarial cross-domain tension (the hardest one)
# ============================================================================

CASE_5 = TestCase(
    id="case_5_nonprofit_hospital_pe_conversion",
    title="Nonprofit community hospital → private-equity conversion",
    failure_mode=FailureMode.ADVERSARIAL,
    prompt=(
        "A 90-bed nonprofit community hospital in a rural area is being acquired by a private-equity "
        "sponsor through a planned reorganization that converts the operating entity to for-profit "
        "and spins out a charitable foundation holding the proceeds. The sponsor proposes a "
        "sale-leaseback of the hospital real estate to fund the transaction. Walk through the "
        "analysis the board needs across clinical, legal, and financial dimensions."
    ),
    rubric=[
        # Healthcare
        RubricItem(seat="healthcare", severity="must_have",
                   description="Identifies essential-service continuity risk (especially OB, ED, behavioral health) under PE ownership patterns"),
        RubricItem(seat="healthcare", severity="must_have",
                   description="Addresses staffing-model risks PE acquirers tend to pursue (e.g. hospitalist staffing, OR utilization)"),
        # Legal
        RubricItem(seat="legal", severity="must_have",
                   description="Addresses state Attorney General approval for nonprofit conversion"),
        RubricItem(seat="legal", severity="must_have",
                   description="Discusses charitable-trust doctrine and its implications for the foundation's mission"),
        RubricItem(seat="legal", severity="should_have",
                   description="Notes antitrust review thresholds (HSR) given local market concentration"),
        # Finance
        RubricItem(seat="finance", severity="must_have",
                   description="Walks through the sponsor's deal economics and how leverage is structured"),
        RubricItem(seat="finance", severity="must_have",
                   description="Surfaces sale-leaseback risk to operations: increased fixed-rent burden under uncertain cash flow"),
        RubricItem(seat="finance", severity="should_have",
                   description="Addresses foundation endowment management and spending-policy implications"),
        # Synthesis — the adversarial heart of the case
        RubricItem(seat="synthesis", severity="must_have",
                   description="EXPLICITLY surfaces tension: the sale-leaseback that maximizes sponsor return creates clinical operational fragility AND state AG scrutiny"),
        # Red flag
        RubricItem(seat="synthesis", severity="red_flag_if_present",
                   description="Treats the deal as routine M&A without surfacing the cross-domain conflict between PE financial structure and clinical/legal exposure"),
    ],
)


# All cases in canonical order. The web UI's case selector and the bench
# runner both iterate this list.
CASES: list[TestCase] = [CASE_1, CASE_2, CASE_3, CASE_4, CASE_5]


def get_case(case_id: str) -> TestCase:
    """Look up a test case by its ``id``; raises ``KeyError`` if not found."""
    for case in CASES:
        if case.id == case_id:
            return case
    raise KeyError(f"No test case with id={case_id!r}. Available: {[c.id for c in CASES]}")
