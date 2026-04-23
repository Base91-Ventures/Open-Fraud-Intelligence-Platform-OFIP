"""Built-in domain packs and domain inference logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from core.models import RulePack
from core.utils import generate_id, utc_now_iso


def _pack(
    name: str,
    domain: str,
    *,
    version: str,
    keywords: Sequence[str],
    required_fields: Sequence[str],
    field_aliases: Dict[str, Sequence[str]],
    suspicious_terms: Sequence[str],
    high_value_threshold: float,
    frequency_threshold: int,
    risk_threshold: int = 60,
    weight_map: Dict[str, int] | None = None,
) -> RulePack:
    return RulePack(
        id=generate_id("pack"),
        name=name,
        version=version,
        domain=domain,
        keywords=list(keywords),
        required_fields=list(required_fields),
        field_aliases={k: list(v) for k, v in field_aliases.items()},
        suspicious_terms=list(suspicious_terms),
        high_value_threshold=high_value_threshold,
        frequency_threshold=frequency_threshold,
        risk_threshold=risk_threshold,
        weight_map=weight_map or {},
        created_at=utc_now_iso(),
    )


class DomainPackRegistry:
    def __init__(self):
        self._packs: Dict[str, RulePack] = {}
        self._ordered_domains: List[str] = []
        self.register_builtin_packs()

    def register(self, pack: RulePack) -> None:
        self._packs[pack.domain] = pack
        if pack.domain not in self._ordered_domains:
            self._ordered_domains.append(pack.domain)

    def register_builtin_packs(self) -> None:
        if self._packs:
            return

        self.register(
            _pack(
                "Generic Document Pack",
                "generic",
                version="1.0.0",
                keywords=["document", "record", "report", "statement", "file"],
                required_fields=["title", "date"],
                field_aliases={
                    "document_id": ["id", "document_id", "record_id", "reference", "reference_number"],
                    "primary_reference": ["id", "reference", "reference_number", "record_id"],
                    "amount": ["amount", "total", "value", "sum"],
                    "submitter": ["user", "submitted_by", "owner", "actor", "employee", "requester"],
                    "date": ["date", "submitted_at", "created_at", "document_date"],
                    "title": ["title", "name", "subject", "document_type"],
                },
                suspicious_terms=["duplicate", "fraud", "urgent", "override", "manual payment"],
                high_value_threshold=10000.0,
                frequency_threshold=5,
                risk_threshold=60,
                weight_map={"high_amount": 30, "duplicate": 50, "frequency": 20, "missing_fields": 15},
            )
        )
        self.register(
            _pack(
                "Finance Pack",
                "finance",
                version="1.0.0",
                keywords=[
                    "invoice",
                    "payment",
                    "transaction",
                    "vendor",
                    "bank",
                    "remittance",
                    "ledger",
                    "billing",
                    "purchase order",
                ],
                required_fields=["amount", "date", "primary_reference"],
                field_aliases={
                    "primary_reference": ["invoice_id", "invoice_number", "transaction_id", "payment_id", "reference"],
                    "amount": ["amount", "total_amount", "gross_amount", "invoice_total", "balance"],
                    "submitter": ["vendor", "payee", "beneficiary", "customer", "submitted_by"],
                    "date": ["invoice_date", "transaction_date", "date", "created_at"],
                    "counterparty": ["vendor", "payee", "beneficiary", "merchant"],
                    "title": ["invoice", "payment", "statement"],
                },
                suspicious_terms=["duplicate invoice", "voided", "manual override", "split payment", "rush payment"],
                high_value_threshold=10000.0,
                frequency_threshold=5,
                risk_threshold=65,
                weight_map={"high_amount": 35, "duplicate": 50, "frequency": 20, "round_amount": 10},
            )
        )
        self.register(
            _pack(
                "Insurance Pack",
                "insurance",
                version="1.0.0",
                keywords=["claim", "policy", "adjuster", "premium", "coverage", "incident", "loss"],
                required_fields=["primary_reference", "date"],
                field_aliases={
                    "primary_reference": ["claim_id", "policy_number", "claim_number", "case_number"],
                    "amount": ["claim_amount", "amount", "total", "settlement_amount"],
                    "submitter": ["member", "insured", "claimant", "policy_holder"],
                    "date": ["loss_date", "incident_date", "claim_date", "date"],
                    "counterparty": ["provider", "adjuster", "insurer", "vendor"],
                    "title": ["claim", "policy", "incident"],
                },
                suspicious_terms=["pre-existing", "manual review", "duplicate claim", "late filing"],
                high_value_threshold=5000.0,
                frequency_threshold=4,
                risk_threshold=60,
                weight_map={"high_amount": 30, "duplicate": 50, "frequency": 20, "keyword": 15},
            )
        )
        self.register(
            _pack(
                "Healthcare Pack",
                "healthcare",
                version="1.0.0",
                keywords=["patient", "diagnosis", "procedure", "provider", "clinical", "medication", "medical"],
                required_fields=["primary_reference", "date"],
                field_aliases={
                    "primary_reference": ["patient_id", "claim_id", "encounter_id", "mrn"],
                    "amount": ["amount", "charge", "total_charge", "balance"],
                    "submitter": ["patient", "member", "provider", "clinic"],
                    "date": ["service_date", "visit_date", "date", "admission_date"],
                    "counterparty": ["provider", "facility", "hospital", "clinic"],
                    "title": ["patient record", "medical record", "claim"],
                },
                suspicious_terms=["duplicate procedure", "upcode", "outside specialty", "experimental"],
                high_value_threshold=3000.0,
                frequency_threshold=6,
                risk_threshold=60,
                weight_map={"high_amount": 25, "duplicate": 45, "frequency": 20, "keyword": 15},
            )
        )
        self.register(
            _pack(
                "Procurement Pack",
                "procurement",
                version="1.0.0",
                keywords=["purchase order", "po", "vendor", "procurement", "supply", "warehouse", "shipment"],
                required_fields=["primary_reference", "date"],
                field_aliases={
                    "primary_reference": ["po_number", "purchase_order", "order_id", "reference"],
                    "amount": ["amount", "order_value", "total", "contract_value"],
                    "submitter": ["requester", "buyer", "buyer_name", "purchaser"],
                    "date": ["order_date", "date", "submission_date"],
                    "counterparty": ["vendor", "supplier", "ship_to", "bill_to"],
                    "title": ["purchase order", "procurement", "order"],
                },
                suspicious_terms=["split order", "rush", "expedite", "off-contract", "sole source"],
                high_value_threshold=20000.0,
                frequency_threshold=4,
                risk_threshold=60,
                weight_map={"high_amount": 30, "duplicate": 50, "frequency": 18, "keyword": 12},
            )
        )
        self.register(
            _pack(
                "Legal Pack",
                "legal",
                version="1.0.0",
                keywords=["contract", "agreement", "counsel", "clause", "settlement", "litigation"],
                required_fields=["primary_reference", "date"],
                field_aliases={
                    "primary_reference": ["matter_number", "case_number", "contract_id", "reference"],
                    "amount": ["amount", "settlement_amount", "fees", "value"],
                    "submitter": ["client", "counsel", "attorney", "party"],
                    "date": ["effective_date", "date", "signed_at"],
                    "counterparty": ["client", "opposing_party", "vendor", "counsel"],
                    "title": ["contract", "agreement", "matter"],
                },
                suspicious_terms=["no liability", "indemnify", "override", "urgent signature"],
                high_value_threshold=15000.0,
                frequency_threshold=3,
                risk_threshold=55,
                weight_map={"high_amount": 20, "duplicate": 50, "frequency": 18, "keyword": 15},
            )
        )

    def get(self, domain: str | None) -> RulePack:
        if not domain:
            return self._packs["generic"]
        return self._packs.get(domain, self._packs["generic"])

    def list(self) -> List[RulePack]:
        return [self._packs[name] for name in self._ordered_domains]

    def infer(self, text: str, structured_data: Dict[str, Any] | None = None) -> Tuple[RulePack, float]:
        text_lc = (text or "").lower()
        structured_blob = " ".join(str(v).lower() for v in (structured_data or {}).values())
        scores: List[Tuple[float, RulePack]] = []
        for pack in self.list():
            score = 0.0
            haystack = f"{text_lc} {structured_blob}"
            for keyword in pack.keywords:
                if keyword.lower() in haystack:
                    score += 1.0
            for term in pack.suspicious_terms:
                if term.lower() in haystack:
                    score += 0.5
            scores.append((score, pack))
        scores.sort(key=lambda item: item[0], reverse=True)
        best_score, best_pack = scores[0]
        confidence = min(1.0, best_score / max(len(best_pack.keywords), 1))
        return best_pack, confidence

    def resolve_field(self, pack: RulePack, field_name: str, data: Dict[str, Any]) -> Any:
        aliases = [field_name] + pack.field_aliases.get(field_name, [])
        flat = {k.lower(): v for k, v in data.items()}
        for alias in aliases:
            alias_lc = alias.lower()
            if alias_lc in flat and flat[alias_lc] not in (None, "", []):
                return flat[alias_lc]
        return None

