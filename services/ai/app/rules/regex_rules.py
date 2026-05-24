"""
Step 6.2 — Regex Rule Engine
40+ patterns covering all risk categories from PRD.md.
Each RiskPattern carries a name, compiled regex, risk category, and preliminary risk level.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ---------------------------------------------------------------------------
# Domain enums
# ---------------------------------------------------------------------------

class RiskCategory(str, Enum):
    INDEMNITY               = "indemnity"
    IP_ASSIGNMENT           = "ip_assignment"
    NON_COMPETE             = "non_compete"
    AUTO_RENEWAL            = "auto_renewal"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    TERMINATION_CONVENIENCE = "termination_for_convenience"
    UNILATERAL_MODIFICATION = "unilateral_modification"
    LIQUIDATED_DAMAGES      = "liquidated_damages"
    ARBITRATION_ONLY        = "arbitration_only"
    PAYMENT_CLAWBACK        = "payment_clawback"
    CONFIDENTIALITY         = "confidentiality"
    GOVERNING_LAW           = "governing_law"
    FORCE_MAJEURE           = "force_majeure"
    DATA_PRIVACY            = "data_privacy"
    EXCLUSIVITY             = "exclusivity"
    CHANGE_OF_CONTROL       = "change_of_control"
    ASSIGNMENT              = "assignment"
    PENALTY                 = "penalty"
    WAIVER_OF_JURY          = "waiver_of_jury_trial"
    NON_SOLICITATION        = "non_solicitation"


class RiskLevel(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"


# ---------------------------------------------------------------------------
# Pattern dataclass
# ---------------------------------------------------------------------------

@dataclass
class RiskPattern:
    name: str
    pattern: re.Pattern
    category: RiskCategory
    risk_level: RiskLevel
    description: str = ""

    def matches(self, text: str) -> bool:
        return bool(self.pattern.search(text))

    def find_matches(self, text: str) -> List[str]:
        return self.pattern.findall(text)


# ---------------------------------------------------------------------------
# Flags shared across all patterns (case-insensitive, dotall)
# ---------------------------------------------------------------------------
_F = re.IGNORECASE | re.DOTALL


def _p(pattern: str) -> re.Pattern:
    return re.compile(pattern, _F)


# ---------------------------------------------------------------------------
# The master pattern registry  (42 patterns)
# ---------------------------------------------------------------------------

ALL_PATTERNS: List[RiskPattern] = [

    # ── INDEMNITY ─────────────────────────────────────────────────────────
    RiskPattern(
        name="indemnify_hold_harmless",
        pattern=_p(r"shall\s+indemnify[,\s]+(?:defend[,\s]+)?and\s+hold\s+harmless"),
        category=RiskCategory.INDEMNITY,
        risk_level=RiskLevel.HIGH,
        description="Broad indemnification obligation",
    ),
    RiskPattern(
        name="indemnify_defend",
        pattern=_p(r"\bindemnif(y|ies|ied|ication)\b.{0,60}\bdefend\b"),
        category=RiskCategory.INDEMNITY,
        risk_level=RiskLevel.HIGH,
        description="Indemnify and defend language",
    ),
    RiskPattern(
        name="unlimited_indemnity",
        pattern=_p(r"\bindemnif\w+\b(?!.{0,80}limited\s+to)"),
        category=RiskCategory.INDEMNITY,
        risk_level=RiskLevel.HIGH,
        description="Indemnity without apparent cap",
    ),

    # ── IP ASSIGNMENT ─────────────────────────────────────────────────────
    RiskPattern(
        name="all_ip_created",
        pattern=_p(r"all\s+(intellectual\s+property|ip|inventions?|works?|developments?).{0,40}(created|developed|made|conceived)"),
        category=RiskCategory.IP_ASSIGNMENT,
        risk_level=RiskLevel.HIGH,
        description="Broad assignment of all created IP",
    ),
    RiskPattern(
        name="work_for_hire",
        pattern=_p(r"work(?:s?)?\s+(made\s+)?for\s+hire"),
        category=RiskCategory.IP_ASSIGNMENT,
        risk_level=RiskLevel.HIGH,
        description="Work-for-hire designation",
    ),
    RiskPattern(
        name="assign_moral_rights",
        pattern=_p(r"waive.{0,40}moral\s+rights|assign.{0,40}moral\s+rights"),
        category=RiskCategory.IP_ASSIGNMENT,
        risk_level=RiskLevel.MEDIUM,
        description="Waiver or assignment of moral rights",
    ),
    RiskPattern(
        name="pre_existing_ip_sweep",
        pattern=_p(r"(pre[-\s]existing|prior)\s+(ip|intellectual\s+property).{0,60}(assign|transfer|vest)"),
        category=RiskCategory.IP_ASSIGNMENT,
        risk_level=RiskLevel.HIGH,
        description="Sweeps in pre-existing IP",
    ),

    # ── NON-COMPETE ───────────────────────────────────────────────────────
    RiskPattern(
        name="non_compete_explicit",
        pattern=_p(r"non[-\s]?compet(e|ition|itive)\s+(agreement|covenant|clause|obligation)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Explicit non-compete clause",
    ),
    RiskPattern(
        name="restrict_competing_business",
        pattern=_p(r"(shall\s+not|may\s+not|prohibited\s+from|cannot).{0,100}(compet|engag|participat|rivals?|similar).{0,60}(business|work|employment)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Restriction on engaging in competing business",
    ),
    RiskPattern(
        name="non_compete_simple",
        pattern=_p(r"shall\s+not.{0,50}(competitor|compete|competing|competing\s+business)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Simple non-compete: shall not work for competitor",
    ),
    RiskPattern(
        name="non_compete_cannot",
        pattern=_p(r"cannot\s+work.{0,50}(competitor|compete|competing|business)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Non-compete using cannot work",
    ),
    RiskPattern(
        name="non_compete_geography",
        pattern=_p(r"(worldwide|global|nationwide|statewide).{0,100}(non[-\s]?compet|compete|competitor)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Geographically broad non-compete",
    ),
    RiskPattern(
        name="non_compete_time_period",
        pattern=_p(r"(months?|years?).{0,50}(after|following).{0,30}(terminat|end|cessation|leaving)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Non-compete with time restriction after termination",
    ),
    RiskPattern(
        name="non_compete_founders",
        pattern=_p(r"founders?\s+cannot\s+compete"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Founder non-compete clause",
    ),
    RiskPattern(
        name="compete_for_years",
        pattern=_p(r"compete\s+for\s+\d+\s+(months?|years?)"),
        category=RiskCategory.NON_COMPETE,
        risk_level=RiskLevel.HIGH,
        description="Non-compete with specific time period",
    ),

    # ── AUTO-RENEWAL ──────────────────────────────────────────────────────
    RiskPattern(
        name="automatically_renew",
        pattern=_p(r"automatically\s+renew(s|ed|ing)?"),
        category=RiskCategory.AUTO_RENEWAL,
        risk_level=RiskLevel.MEDIUM,
        description="Auto-renewal clause",
    ),
    RiskPattern(
        name="evergreen_clause",
        pattern=_p(r"(continue|roll(s)?\s+over|extend).{0,50}unless.{0,50}(written\s+notice|cancel|terminat)"),
        category=RiskCategory.AUTO_RENEWAL,
        risk_level=RiskLevel.MEDIUM,
        description="Evergreen / tacit renewal",
    ),
    RiskPattern(
        name="notice_to_cancel",
        pattern=_p(r"(\d{2,3})\s+days?.{0,30}(notice|prior\s+written\s+notice).{0,50}(terminat|cancel|non[-\s]?renew)"),
        category=RiskCategory.AUTO_RENEWAL,
        risk_level=RiskLevel.MEDIUM,
        description="Long notice required to cancel auto-renewal",
    ),

    # ── LIMITATION OF LIABILITY ───────────────────────────────────────────
    RiskPattern(
        name="no_consequential_damages",
        pattern=_p(r"(in\s+no\s+event|shall\s+not).{0,60}(consequential|indirect|incidental|punitive|special)\s+damages"),
        category=RiskCategory.LIMITATION_OF_LIABILITY,
        risk_level=RiskLevel.MEDIUM,
        description="Exclusion of consequential damages",
    ),
    RiskPattern(
        name="liability_cap",
        pattern=_p(r"(total|aggregate|maximum|cumulative)\s+liability.{0,80}(shall\s+not\s+exceed|limited\s+to|capped\s+at)"),
        category=RiskCategory.LIMITATION_OF_LIABILITY,
        risk_level=RiskLevel.MEDIUM,
        description="Cap on total liability",
    ),
    RiskPattern(
        name="liability_cap_fees_paid",
        pattern=_p(r"liability.{0,60}(fees|amounts?)\s+(paid|received)\s+(in\s+the\s+(preceding|prior|last)\s+\d+)"),
        category=RiskCategory.LIMITATION_OF_LIABILITY,
        risk_level=RiskLevel.MEDIUM,
        description="Liability capped at fees paid",
    ),

    # ── TERMINATION FOR CONVENIENCE ───────────────────────────────────────
    RiskPattern(
        name="terminate_for_convenience",
        pattern=_p(r"terminat.{0,60}(for\s+convenience|without\s+cause|at\s+(its|their|our|your)\s+sole\s+discretion)"),
        category=RiskCategory.TERMINATION_CONVENIENCE,
        risk_level=RiskLevel.HIGH,
        description="Termination for convenience (one-sided)",
    ),
    RiskPattern(
        name="terminate_immediately",
        pattern=_p(r"(may\s+terminat|right\s+to\s+terminat).{0,50}immediately.{0,50}without\s+(notice|cause)"),
        category=RiskCategory.TERMINATION_CONVENIENCE,
        risk_level=RiskLevel.HIGH,
        description="Right to terminate immediately without notice",
    ),
    RiskPattern(
        name="terminate_without_notice",
        pattern=_p(r"may\s+terminat.{0,80}without\s+(notice|cause|any\s+reason)"),
        category=RiskCategory.TERMINATION_CONVENIENCE,
        risk_level=RiskLevel.HIGH,
        description="Right to terminate without notice or cause",
    ),

    # ── UNILATERAL MODIFICATION ───────────────────────────────────────────
    RiskPattern(
        name="unilateral_modification",
        pattern=_p(r"(may|reserves?\s+the\s+right\s+to|can).{0,50}(modify|amend|change|update).{0,60}(at\s+(any|its)\s+time|without\s+(notice|consent|approval))"),
        category=RiskCategory.UNILATERAL_MODIFICATION,
        risk_level=RiskLevel.HIGH,
        description="Unilateral right to modify terms",
    ),
    RiskPattern(
        name="deemed_acceptance_modification",
        pattern=_p(r"(continued\s+use|continuing\s+to\s+use).{0,80}(constitutes|deemed|considered).{0,40}(acceptance|agreement|consent)"),
        category=RiskCategory.UNILATERAL_MODIFICATION,
        risk_level=RiskLevel.MEDIUM,
        description="Continued use deemed acceptance of changes",
    ),

    # ── LIQUIDATED DAMAGES ────────────────────────────────────────────────
    RiskPattern(
        name="liquidated_damages",
        pattern=_p(r"liquidated\s+damages"),
        category=RiskCategory.LIQUIDATED_DAMAGES,
        risk_level=RiskLevel.HIGH,
        description="Liquidated damages clause",
    ),
    RiskPattern(
        name="penalty_provision",
        pattern=_p(r"(pay|owe|liable\s+for).{0,60}\$[\d,]+.{0,40}(penalty|penalt|fine|forfeit)"),
        category=RiskCategory.LIQUIDATED_DAMAGES,
        risk_level=RiskLevel.HIGH,
        description="Dollar-denominated penalty",
    ),

    # ── ARBITRATION ONLY ─────────────────────────────────────────────────
    RiskPattern(
        name="mandatory_arbitration",
        pattern=_p(r"(mandatory|binding|compulsory|final\s+and\s+binding)\s+arbitration"),
        category=RiskCategory.ARBITRATION_ONLY,
        risk_level=RiskLevel.HIGH,
        description="Mandatory arbitration clause",
    ),
    RiskPattern(
        name="waive_class_action",
        pattern=_p(r"waive.{0,60}(class\s+action|class[-\s]wide|collective\s+action|mass\s+arbitration)"),
        category=RiskCategory.ARBITRATION_ONLY,
        risk_level=RiskLevel.HIGH,
        description="Class action waiver",
    ),
    RiskPattern(
        name="arbitration_sole_remedy",
        pattern=_p(r"arbitration.{0,80}(sole\s+and\s+exclusive|exclusive)\s+(remedy|recourse|forum|method)"),
        category=RiskCategory.ARBITRATION_ONLY,
        risk_level=RiskLevel.HIGH,
        description="Arbitration as sole exclusive remedy",
    ),

    # ── PAYMENT CLAWBACK ──────────────────────────────────────────────────
    RiskPattern(
        name="clawback_provision",
        pattern=_p(r"\bclawback\b|claw[-\s]back"),
        category=RiskCategory.PAYMENT_CLAWBACK,
        risk_level=RiskLevel.HIGH,
        description="Explicit clawback provision",
    ),
    RiskPattern(
        name="recoupment",
        pattern=_p(r"\brecoup(ment|able|ed)?\b.{0,60}(bonus|compensation|incentive|payment)"),
        category=RiskCategory.PAYMENT_CLAWBACK,
        risk_level=RiskLevel.HIGH,
        description="Recoupment of compensation",
    ),
    RiskPattern(
        name="repayment_on_termination",
        pattern=_p(r"(repay|reimburse|return).{0,60}(upon|on|following|after).{0,40}(terminat|resignat|departure)"),
        category=RiskCategory.PAYMENT_CLAWBACK,
        risk_level=RiskLevel.MEDIUM,
        description="Repayment obligation triggered by termination",
    ),

    # ── CONFIDENTIALITY ───────────────────────────────────────────────────
    RiskPattern(
        name="perpetual_confidentiality",
        pattern=_p(r"confidential.{0,80}(perpetual|indefinite|no\s+time\s+limit|survive.{0,40}terminat)"),
        category=RiskCategory.CONFIDENTIALITY,
        risk_level=RiskLevel.MEDIUM,
        description="Perpetual / survivorship confidentiality obligation",
    ),
    RiskPattern(
        name="indefinite_confidentiality",
        pattern=_p(r"survive.{0,40}(terminat|end).{0,40}(indefinite|perpetual|forever)"),
        category=RiskCategory.CONFIDENTIALITY,
        risk_level=RiskLevel.MEDIUM,
        description="Confidentiality survives termination indefinitely",
    ),
    RiskPattern(
        name="broad_confidentiality",
        pattern=_p(r"(all\s+information|any\s+and\s+all.{0,30}information).{0,60}(confidential|proprietary)"),
        category=RiskCategory.CONFIDENTIALITY,
        risk_level=RiskLevel.MEDIUM,
        description="Overly broad confidentiality scope",
    ),

    # ── GOVERNING LAW (UNFAVOURABLE VENUE) ───────────────────────────────
    RiskPattern(
        name="exclusive_jurisdiction",
        pattern=_p(r"(exclusive|sole)\s+jurisdiction.{0,60}(courts?\s+of|in\s+the\s+state\s+of)"),
        category=RiskCategory.GOVERNING_LAW,
        risk_level=RiskLevel.MEDIUM,
        description="Exclusive jurisdiction in a specific forum",
    ),
    RiskPattern(
        name="foreign_governing_law",
        pattern=_p(r"govern(ed|ing)\s+by.{0,60}laws?\s+of.{0,60}(england|cayman|delaware|singapore|ireland)"),
        category=RiskCategory.GOVERNING_LAW,
        risk_level=RiskLevel.MEDIUM,
        description="Governing law in foreign or advantageous jurisdiction",
    ),

    # ── DATA PRIVACY ──────────────────────────────────────────────────────
    RiskPattern(
        name="personal_data_processing",
        pattern=_p(r"(process|collect|use|share|transfer).{0,60}personal\s+(data|information)"),
        category=RiskCategory.DATA_PRIVACY,
        risk_level=RiskLevel.MEDIUM,
        description="Processing of personal data without limitations",
    ),
    RiskPattern(
        name="data_sale",
        pattern=_p(r"(sell|transfer|disclose|share).{0,60}(user|customer|personal).{0,40}(data|information).{0,60}third.{0,20}part"),
        category=RiskCategory.DATA_PRIVACY,
        risk_level=RiskLevel.HIGH,
        description="Sale or transfer of personal data to third parties",
    ),

    # ── EXCLUSIVITY ───────────────────────────────────────────────────────
    RiskPattern(
        name="exclusive_dealing",
        pattern=_p(r"(exclusive(ly)?|sole(ly)?).{0,60}(purchas|sourc|deal|provid|suppl).{0,60}(from|through|via)\s+\w+"),
        category=RiskCategory.EXCLUSIVITY,
        risk_level=RiskLevel.HIGH,
        description="Exclusive dealing obligation",
    ),
    RiskPattern(
        name="most_favoured_nation",
        pattern=_p(r"most[-\s]favou?r(e?d)?\s+nation|most[-\s]favou?red\s+(customer|pricing)"),
        category=RiskCategory.EXCLUSIVITY,
        risk_level=RiskLevel.MEDIUM,
        description="Most-favoured-nation pricing clause",
    ),

    # ── CHANGE OF CONTROL ─────────────────────────────────────────────────
    RiskPattern(
        name="change_of_control_termination",
        pattern=_p(r"change\s+of\s+control.{0,80}(terminat|void|null|expire|cease)"),
        category=RiskCategory.CHANGE_OF_CONTROL,
        risk_level=RiskLevel.HIGH,
        description="Agreement terminates on change of control",
    ),
    RiskPattern(
        name="anti_assignment_change_control",
        pattern=_p(r"(assign|transfer).{0,60}(without.{0,30}prior\s+written\s+consent|prohibited)"),
        category=RiskCategory.ASSIGNMENT,
        risk_level=RiskLevel.MEDIUM,
        description="Assignment prohibited without consent",
    ),

    # ── WAIVER OF JURY TRIAL ─────────────────────────────────────────────
    RiskPattern(
        name="waiver_jury_trial",
        pattern=_p(r"waive.{0,60}(right\s+to\s+)?jury\s+trial"),
        category=RiskCategory.WAIVER_OF_JURY,
        risk_level=RiskLevel.HIGH,
        description="Express waiver of jury trial right",
    ),

    # ── NON-SOLICITATION ─────────────────────────────────────────────────
    RiskPattern(
        name="non_solicitation_employees",
        pattern=_p(r"non[-\s]?solicit.{0,80}(employee|staff|personnel|hire)"),
        category=RiskCategory.NON_SOLICITATION,
        risk_level=RiskLevel.MEDIUM,
        description="Non-solicitation of employees",
    ),
    RiskPattern(
        name="non_solicitation_customers",
        pattern=_p(r"non[-\s]?solicit.{0,80}(customer|client|account|prospect)"),
        category=RiskCategory.NON_SOLICITATION,
        risk_level=RiskLevel.MEDIUM,
        description="Non-solicitation of customers",
    ),

    # ── FORCE MAJEURE (one-sided) ─────────────────────────────────────────
    RiskPattern(
        name="one_sided_force_majeure",
        pattern=_p(r"force\s+majeure.{0,200}(only\s+(?:one|either)\s+party|not\s+apply\s+to)"),
        category=RiskCategory.FORCE_MAJEURE,
        risk_level=RiskLevel.MEDIUM,
        description="Force-majeure protection applies to only one party",
    ),
]


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

def get_all_patterns() -> List[RiskPattern]:
    """Return the full master list of risk patterns."""
    return ALL_PATTERNS


def get_patterns_by_category(category: RiskCategory) -> List[RiskPattern]:
    """Return patterns filtered by risk category."""
    return [p for p in ALL_PATTERNS if p.category == category]


def get_high_risk_patterns() -> List[RiskPattern]:
    """Return only HIGH-level patterns."""
    return [p for p in ALL_PATTERNS if p.risk_level == RiskLevel.HIGH]