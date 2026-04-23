"""Runtime configuration for OFIP."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, Any

from core.utils import ensure_dir, slugify


@dataclass
class Settings:
    app_name: str = os.getenv("OFIP_APP_NAME", "Open Fraud Intelligence Platform")
    version: str = os.getenv("OFIP_VERSION", "1.0.0")
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("OFIP_DATA_DIR", "var")))
    db_name: str = os.getenv("OFIP_DB_NAME", "ofip.sqlite3")
    upload_dir_name: str = os.getenv("OFIP_UPLOAD_DIR", "uploads")
    default_tenant_slug: str = os.getenv("OFIP_DEFAULT_TENANT", "default")
    default_tenant_name: str = os.getenv("OFIP_DEFAULT_TENANT_NAME", "Default Tenant")
    default_admin_token: str = os.getenv("OFIP_ADMIN_TOKEN", "change-me-admin-token")
    default_api_key: str = os.getenv("OFIP_API_KEY", "change-me-api-key")
    allow_anonymous_demo: bool = os.getenv("OFIP_ALLOW_ANONYMOUS_DEMO", "true").lower() in {"1", "true", "yes"}
    case_creation_threshold: int = int(os.getenv("OFIP_CASE_THRESHOLD", "60"))
    upload_max_bytes: int = int(os.getenv("OFIP_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    job_workers: int = int(os.getenv("OFIP_JOB_WORKERS", "4"))
    analysis_provider: str = os.getenv("OFIP_ANALYSIS_PROVIDER", "heuristic")
    ocr_provider: str = os.getenv("OFIP_OCR_PROVIDER", "auto")
    log_level: str = os.getenv("OFIP_LOG_LEVEL", "INFO")

    def resolved(self) -> Dict[str, Any]:
        base = ensure_dir(self.data_dir)
        uploads = ensure_dir(base / self.upload_dir_name)
        db_path = base / self.db_name
        return {
            "data_dir": base,
            "uploads_dir": uploads,
            "db_path": db_path,
            "default_tenant_slug": slugify(self.default_tenant_slug),
        }

