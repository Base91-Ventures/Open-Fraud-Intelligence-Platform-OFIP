"""Domain models for OFIP."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


def _clean_dict(value: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in value.items() if v is not None}


@dataclass
class Tenant:
    id: str
    slug: str
    name: str
    api_key_hash: str
    admin_token_hash: str
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class RulePack:
    id: str
    name: str
    version: str
    domain: str
    keywords: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    field_aliases: Dict[str, List[str]] = field(default_factory=dict)
    suspicious_terms: List[str] = field(default_factory=list)
    high_value_threshold: float = 10000.0
    frequency_threshold: int = 5
    risk_threshold: int = 60
    weight_map: Dict[str, int] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class RawDocument:
    id: str
    tenant_id: str
    filename: str
    content_type: str
    source_type: str
    storage_path: str
    sha256: str
    file_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class NormalizedDocument:
    id: str
    tenant_id: str
    source_document_id: str
    domain: str
    source_type: str
    title: str = ""
    content_text: str = ""
    structured_data: Dict[str, Any] = field(default_factory=dict)
    extracted_fields: Dict[str, Any] = field(default_factory=dict)
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    warnings: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class Evidence:
    source: str
    snippet: str
    field: str = ""
    page: Optional[int] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class Finding:
    code: str
    title: str
    severity: str
    score_delta: int
    explanation: str
    category: str = "risk"
    evidence: List[Evidence] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return _clean_dict(payload)


@dataclass
class AnalysisRun:
    id: str
    tenant_id: str
    document_id: str
    domain: str
    status: str
    risk_score: int
    summary: str
    provider: str
    findings: List[Finding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        return _clean_dict(payload)


@dataclass
class CaseRecord:
    id: str
    tenant_id: str
    document_id: str
    analysis_id: str
    title: str
    status: str
    priority: str
    assignee: str = ""
    notes: str = ""
    findings: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class JobRecord:
    id: str
    tenant_id: str
    document_id: str
    status: str
    progress: int = 0
    message: str = ""
    result: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))


@dataclass
class Principal:
    tenant_id: str
    role: str
    actor: str
    authenticated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return _clean_dict(asdict(self))

