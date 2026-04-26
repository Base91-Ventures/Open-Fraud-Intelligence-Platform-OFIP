"""SQLite-backed persistence for OFIP."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.models import AnalysisRun, CaseRecord, JobRecord, RawDocument, RulePack, Tenant
from core.utils import ensure_dir, json_dumps, json_loads, utc_now_iso


class Storage:
    def __init__(self, db_path: str | Path, uploads_dir: str | Path):
        self.db_path = Path(db_path)
        self.uploads_dir = ensure_dir(uploads_dir)
        ensure_dir(self.db_path.parent)
        self._lock = threading.RLock()
        self._initialize()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    api_key_hash TEXT NOT NULL,
                    admin_token_hash TEXT NOT NULL,
                    config_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rule_packs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    pack_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(tenant_id, domain, version),
                    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    primary_reference TEXT,
                    submitter TEXT,
                    amount REAL,
                    document_date TEXT,
                    domain TEXT NOT NULL DEFAULT 'generic',
                    status TEXT NOT NULL DEFAULT 'queued',
                    raw_text TEXT NOT NULL DEFAULT '',
                    structured_json TEXT NOT NULL DEFAULT '{}',
                    extracted_json TEXT NOT NULL DEFAULT '{}',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    findings_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    assignee TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    findings_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    message TEXT NOT NULL DEFAULT '',
                    result_json TEXT NOT NULL DEFAULT '{}',
                    error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
                );
                """
            )

    def create_upload_path(self, tenant_slug: str, document_id: str, filename: str) -> Path:
        target = ensure_dir(self.uploads_dir / tenant_slug / document_id)
        return target / filename

    def seed_tenant(self, tenant: Tenant) -> Tenant:
        existing = self.get_tenant_by_slug(tenant.slug)
        if existing:
            return existing
        self.upsert_tenant(tenant)
        return tenant

    def upsert_tenant(self, tenant: Tenant) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO tenants (id, slug, name, api_key_hash, admin_token_hash, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    name=excluded.name,
                    api_key_hash=excluded.api_key_hash,
                    admin_token_hash=excluded.admin_token_hash,
                    config_json=excluded.config_json,
                    updated_at=excluded.updated_at
                """,
                (
                    tenant.id,
                    tenant.slug,
                    tenant.name,
                    tenant.api_key_hash,
                    tenant.admin_token_hash,
                    json_dumps(tenant.config or {}),
                    tenant.created_at,
                    tenant.updated_at or utc_now_iso(),
                ),
            )

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM tenants WHERE slug = ?", (slug,)).fetchone()
        return self._tenant_from_row(row)

    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
        return self._tenant_from_row(row)

    def list_tenants(self) -> List[Tenant]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM tenants ORDER BY created_at DESC").fetchall()
        return [self._tenant_from_row(row) for row in rows if row]

    def save_rule_pack(self, tenant_id: str, pack: RulePack) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO rule_packs (id, tenant_id, name, version, domain, pack_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tenant_id, domain, version) DO UPDATE SET
                    name=excluded.name,
                    pack_json=excluded.pack_json,
                    updated_at=excluded.updated_at
                """,
                (
                    pack.id,
                    tenant_id,
                    pack.name,
                    pack.version,
                    pack.domain,
                    json_dumps(pack.to_dict()),
                    pack.created_at,
                    utc_now_iso(),
                ),
            )

    def list_rule_packs(self, tenant_id: str) -> List[RulePack]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT pack_json FROM rule_packs WHERE tenant_id = ? ORDER BY domain",
                (tenant_id,),
            ).fetchall()
        packs: List[RulePack] = []
        for row in rows:
            payload = json_loads(row["pack_json"], default={}) or {}
            packs.append(RulePack(**payload))
        return packs

    def save_document(self, document: RawDocument) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (
                    id, tenant_id, filename, content_type, source_type, storage_path,
                    sha256, file_size, primary_reference, submitter, amount, document_date,
                    domain, status, raw_text, structured_json, extracted_json,
                    metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.tenant_id,
                    document.filename,
                    document.content_type,
                    document.source_type,
                    document.storage_path,
                    document.sha256,
                    document.file_size,
                    None,
                    None,
                    None,
                    None,
                    "generic",
                    "queued",
                    "",
                    "{}",
                    "{}",
                    json_dumps(document.metadata or {}),
                    document.created_at,
                    document.created_at,
                ),
            )

    def update_document(
        self,
        document_id: str,
        *,
        status: Optional[str] = None,
        raw_text: Optional[str] = None,
        structured_json: Optional[Dict[str, Any]] = None,
        extracted_json: Optional[Dict[str, Any]] = None,
        domain: Optional[str] = None,
        primary_reference: Optional[str] = None,
        submitter: Optional[str] = None,
        amount: Optional[float] = None,
        document_date: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        assignments: List[str] = []
        values: List[Any] = []
        mapping = {
            "status": status,
            "raw_text": raw_text,
            "structured_json": json_dumps(structured_json) if structured_json is not None else None,
            "extracted_json": json_dumps(extracted_json) if extracted_json is not None else None,
            "domain": domain,
            "primary_reference": primary_reference,
            "submitter": submitter,
            "amount": amount,
            "document_date": document_date,
            "updated_at": updated_at or utc_now_iso(),
        }
        for column, value in mapping.items():
            if value is not None:
                assignments.append(f"{column} = ?")
                values.append(value)
        if not assignments:
            return
        values.append(document_id)
        with self.connection() as conn:
            conn.execute(f"UPDATE documents SET {', '.join(assignments)} WHERE id = ?", values)

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return self._row_to_dict(row)

    def get_document_by_sha(self, tenant_id: str, sha256: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE tenant_id = ? AND sha256 = ? ORDER BY created_at DESC LIMIT 1",
                (tenant_id, sha256),
            ).fetchone()
        return self._row_to_dict(row)

    def list_documents(self, tenant_id: str, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (tenant_id, limit, offset),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def count_documents(self, tenant_id: str) -> int:
        with self.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM documents WHERE tenant_id = ?", (tenant_id,)).fetchone()
        return int(row["c"] if row else 0)

    def count_documents_with_field(self, tenant_id: str, column: str, value: Any, *, days: int = 7) -> int:
        if value in (None, ""):
            return 0
        if column not in {"primary_reference", "submitter", "amount", "document_date"}:
            return 0
        with self.connection() as conn:
            row = conn.execute(
                f"""
                SELECT COUNT(*) AS c
                FROM documents
                WHERE tenant_id = ? AND {column} = ?
                AND created_at >= datetime('now', ?)
                """,
                (tenant_id, value, f"-{days} days"),
            ).fetchone()
        return int(row["c"] if row else 0)

    def save_analysis(self, analysis: AnalysisRun) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO analyses (
                    id, tenant_id, document_id, domain, status, risk_score, summary, provider,
                    findings_json, metadata_json, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    risk_score=excluded.risk_score,
                    summary=excluded.summary,
                    provider=excluded.provider,
                    findings_json=excluded.findings_json,
                    metadata_json=excluded.metadata_json,
                    completed_at=excluded.completed_at
                """,
                (
                    analysis.id,
                    analysis.tenant_id,
                    analysis.document_id,
                    analysis.domain,
                    analysis.status,
                    analysis.risk_score,
                    analysis.summary,
                    analysis.provider,
                    json_dumps([finding.to_dict() for finding in analysis.findings]),
                    json_dumps(analysis.metadata or {}),
                    analysis.created_at,
                    analysis.completed_at,
                ),
            )

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        return self._row_to_dict(row)

    def list_analyses(self, tenant_id: str, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM analyses WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (tenant_id, limit, offset),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def save_case(self, case: CaseRecord) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO cases (
                    id, tenant_id, document_id, analysis_id, title, status, priority,
                    assignee, notes, findings_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    priority=excluded.priority,
                    assignee=excluded.assignee,
                    notes=excluded.notes,
                    findings_json=excluded.findings_json,
                    updated_at=excluded.updated_at
                """,
                (
                    case.id,
                    case.tenant_id,
                    case.document_id,
                    case.analysis_id,
                    case.title,
                    case.status,
                    case.priority,
                    case.assignee,
                    case.notes,
                    json_dumps(case.findings),
                    case.created_at,
                    case.updated_at,
                ),
            )

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        return self._row_to_dict(row)

    def list_cases(self, tenant_id: str, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM cases WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (tenant_id, limit, offset),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def update_case(
        self,
        case_id: str,
        *,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        assignments: List[str] = []
        values: List[Any] = []
        mapping = {
            "status": status,
            "priority": priority,
            "assignee": assignee,
            "notes": notes,
            "updated_at": utc_now_iso(),
        }
        for column, value in mapping.items():
            if value is not None:
                assignments.append(f"{column} = ?")
                values.append(value)
        if not assignments:
            return
        values.append(case_id)
        with self.connection() as conn:
            conn.execute(f"UPDATE cases SET {', '.join(assignments)} WHERE id = ?", values)

    def save_job(self, job: JobRecord) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, tenant_id, document_id, status, progress, message,
                    result_json, error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    progress=excluded.progress,
                    message=excluded.message,
                    result_json=excluded.result_json,
                    error=excluded.error,
                    updated_at=excluded.updated_at
                """,
                (
                    job.id,
                    job.tenant_id,
                    job.document_id,
                    job.status,
                    job.progress,
                    job.message,
                    json_dumps(job.result or {}),
                    job.error,
                    job.created_at,
                    job.updated_at,
                ),
            )

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_dict(row)

    def list_jobs(self, tenant_id: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def audit(
        self,
        tenant_id: str,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (id, tenant_id, actor, action, target_type, target_id, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"audit_{utc_now_iso()}_{target_type}_{target_id}",
                    tenant_id,
                    actor,
                    action,
                    target_type,
                    target_id,
                    json_dumps(metadata or {}),
                    utc_now_iso(),
                ),
            )

    def count_documents_by_tenant(self, tenant_id: str) -> int:
        return self.count_documents(tenant_id)

    def count_cases(self, tenant_id: str) -> int:
        with self.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM cases WHERE tenant_id = ?", (tenant_id,)).fetchone()
        return int(row["c"] if row else 0)

    def count_open_cases(self, tenant_id: str) -> int:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM cases WHERE tenant_id = ? AND status IN ('open', 'triage', 'review')",
                (tenant_id,),
            ).fetchone()
        return int(row["c"] if row else 0)

    def recent_documents(self, tenant_id: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def recent_cases(self, tenant_id: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM cases WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
                (tenant_id, limit),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows if row]

    def _tenant_from_row(self, row: Optional[sqlite3.Row]) -> Optional[Tenant]:
        if not row:
            return None
        return Tenant(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            api_key_hash=row["api_key_hash"],
            admin_token_hash=row["admin_token_hash"],
            config=json_loads(row["config_json"], default={}) or {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        payload = dict(row)
        for column in (
            "config_json",
            "metadata_json",
            "structured_json",
            "extracted_json",
            "findings_json",
            "result_json",
        ):
            if column in payload:
                payload[column[:-5]] = json_loads(payload.pop(column), default={})
        if "pack_json" in payload:
            payload["pack"] = json_loads(payload.pop("pack_json"), default={})
        if "raw_text" in payload and payload["raw_text"] is None:
            payload["raw_text"] = ""
        return payload

