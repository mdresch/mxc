"""Filesystem-backed ArtifactStore implementation."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pmbok.models.pmbok import ProjectArtifact

if TYPE_CHECKING:
    from pmbok.audit.api import AuditAPI


class ArtifactStore:
    """
    Stores and retrieves ProjectArtifact objects on the local filesystem.

    Layout:
        {base_path}/runs/{run_id}/artifacts/{process_id}/
            v1_{artifact_id}.json
            v2_{artifact_id}.json
            latest.json          ← always the highest version (atomic swap)
    
    Optionally integrates with AuditAPI for automatic artifact quality auditing.
    """

    def __init__(self, base_path: Path, audit_api: Optional["AuditAPI"] = None, audit_on_save: bool = True) -> None:
        self.base_path = Path(base_path)
        self.audit_api = audit_api
        self.audit_on_save = audit_on_save

    # ── helpers ──────────────────────────────────────────────────────────────

    def _artifact_dir(self, run_id: str, process_id: str, process_name: str | None = None) -> Path:
        base_dir = self.base_path / "runs" / run_id / "artifacts"
        
        # 1. Clean the suggested name if provided
        suggested_folder = None
        if process_name:
            clean_name = "".join(c for c in process_name if c.isalnum() or c in (" ", "-", "_")).strip()
            suggested_folder = f"{process_id} {clean_name}"

        # 2. Try to find an existing directory that matches the ID
        if base_dir.exists():
            for d in base_dir.iterdir():
                if d.is_dir() and (d.name == process_id or d.name.startswith(f"{process_id} ")):
                    # Found an existing folder for this process! (e.g. "4.1" or "4.1 Develop Project Charter")
                    return d
                    
        # 3. No existing folder found — use the suggested one or the standard one
        return base_dir / (suggested_folder if suggested_folder else process_id)

    def _versioned_path(self, run_id: str, process_id: str, version: int, artifact_id: str, process_name: str | None = None) -> Path:
        return self._artifact_dir(run_id, process_id, process_name) / f"v{version}_{artifact_id}.json"

    def _latest_path(self, run_id: str, process_id: str, process_name: str | None = None) -> Path:
        return self._artifact_dir(run_id, process_id, process_name) / "latest.json"

    def _to_envelope(self, artifact: ProjectArtifact) -> dict[str, Any]:
        envelope = {
            "schema_version": "1.0",
            "artifact_id": artifact.id,
            "artifact_type": artifact.artifact_type,
            "run_id": artifact.run_id,
            "process_id": artifact.process_id,
            "version": artifact.version,
            "previous_version_id": artifact.previous_version_id,
            "produced_by_process": artifact.produced_by,
            "created_at": artifact.created_at.isoformat(),
            "content": artifact.content,
        }
        
        # Include audit result if present
        if artifact.audit_result is not None:
            envelope["audit_result"] = artifact.audit_result.to_dict()
        
        return envelope

    def _from_envelope(self, data: dict[str, Any]) -> ProjectArtifact:
        from datetime import datetime
        from pmbok.models.audit import AuditResult, AuditFinding, AuditSeverity, ComplianceTier

        # Deserialize audit result if present
        audit_result = None
        if "audit_result" in data and data["audit_result"] is not None:
            audit_data = data["audit_result"]
            findings = [
                AuditFinding(
                    code=f["code"],
                    severity=AuditSeverity(f["severity"]),
                    message=f["message"],
                    affected_fields=f.get("affected_fields", []),
                    criterion=f.get("criterion"),
                    remediation=f.get("remediation"),
                )
                for f in audit_data.get("findings", [])
            ]
            
            try:
                audit_timestamp = datetime.fromisoformat(audit_data.get("audit_timestamp", ""))
            except (ValueError, TypeError):
                audit_timestamp = datetime.utcnow()
            
            audit_result = AuditResult(
                artifact_id=audit_data["artifact_id"],
                artifact_type=audit_data["artifact_type"],
                run_id=audit_data["run_id"],
                process_id=audit_data.get("process_id"),
                policy_set_applied=audit_data.get("policy_set_applied", "pmbok_standard"),
                compliance_score=float(audit_data.get("compliance_score", 0)),
                confidence_score=float(audit_data.get("confidence_score", 0)),
                compliance_tier=ComplianceTier(audit_data.get("compliance_tier", "POOR")),
                findings=findings,
                audit_timestamp=audit_timestamp,
                confidence_basis=audit_data.get("confidence_basis", {}),
            )

        return ProjectArtifact(
            id=data["artifact_id"],
            run_id=data["run_id"],
            process_id=data["process_id"],
            artifact_type=data["artifact_type"],
            version=data["version"],
            content=data["content"],
            produced_by=data["produced_by_process"],
            created_at=datetime.fromisoformat(data["created_at"]),
            previous_version_id=data.get("previous_version_id"),
            audit_result=audit_result,
        )

    def _write_atomic(self, path: Path, data: dict[str, Any]) -> None:
        """Write JSON to *path* atomically using a temp-file swap with retries."""
        import time
        import errno
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # We use a retry loop for Windows file locking issues (WinError 5)
        max_retries = 5
        base_delay = 0.1
        
        last_exception = None
        
        for attempt in range(max_retries):
            fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
            tmp_path = Path(tmp_path)
            try:
                from datetime import datetime
                
                def json_serial(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Type {type(obj)} not serializable")

                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False, default=json_serial)
                
                # On Windows, os.replace can fail if the target is being read
                # or if a virus scanner is holding the temp file.
                try:
                    os.replace(tmp_path, path)
                    return # Success
                except OSError as e:
                    if e.errno in (errno.EACCES, errno.EPERM, 13, 5): # 13=EACCES, 5=WinError 5
                        last_exception = e
                        # Try to force it if it's just a read-only bit
                        try:
                            if path.exists():
                                os.chmod(path, 0o666)
                            os.chmod(tmp_path, 0o666)
                            os.replace(tmp_path, path)
                            return # Success after chmod
                        except OSError:
                            pass # Fall through to retry
                        
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    raise
            except Exception as e:
                last_exception = e
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                raise last_exception if last_exception else e

    # ── public async API ─────────────────────────────────────────────────────

    async def save(self, artifact: ProjectArtifact, process_name: str | None = None) -> None:
        """Persist *artifact* and update latest.json atomically."""
        await asyncio.to_thread(self._save_sync, artifact, process_name)

    def _save_sync(self, artifact: ProjectArtifact, process_name: str | None = None) -> None:
        # Run audit if enabled and audit_api is available
        if self.audit_on_save and self.audit_api is not None:
            audit_result = self.audit_api.audit_artifact(
                artifact,
                policy_set_name="pmbok_standard",
                save_result=True,
            )
            artifact.audit_result = audit_result
            
            # Save a human-readable audit report alongside the prompt and artifact
            self._save_audit_report_sync(
                artifact.run_id, 
                artifact.process_id, 
                audit_result, 
                artifact.version,
                process_name
            )
        
        envelope = self._to_envelope(artifact)
        versioned = self._versioned_path(
            artifact.run_id, artifact.process_id, artifact.version, artifact.id, process_name
        )
        self._write_atomic(versioned, envelope)
        latest = self._latest_path(artifact.run_id, artifact.process_id, process_name)
        self._write_atomic(latest, envelope)

    async def save_prompt(self, run_id: str, process_id: str, prompt: str, version: int = 1, process_name: str | None = None) -> None:
        """Save the raw prompt sent to the LLM for a specific process version."""
        await asyncio.to_thread(self._save_prompt_sync, run_id, process_id, prompt, version, process_name)

    async def save_optimization_details(
        self, run_id: str, process_id: str, optimization_data: Dict[str, Any], version: int = 1, process_name: str | None = None
    ) -> None:
        """Save prompt optimization details for a process execution."""
        await asyncio.to_thread(self._save_optimization_details_sync, run_id, process_id, optimization_data, version, process_name)

    async def save_quality_audit(self, run_id: str, process_id: str, qc_result: Any, version: int = 1, process_name: str | None = None) -> None:
        """Save quality control audit results for a process execution."""
        await asyncio.to_thread(self._save_quality_audit_sync, run_id, process_id, qc_result, version, process_name)

    def _save_optimization_details_sync(
        self, run_id: str, process_id: str, optimization_data: Dict[str, Any], version: int, process_name: str | None = None
    ) -> None:
        """Save optimization details to a JSON file."""
        artifact_dir = self._artifact_dir(run_id, process_id, process_name)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        optimization_path = artifact_dir / f"optimization_v{version}.json"

        with open(optimization_path, "w", encoding="utf-8") as fh:
            json.dump(optimization_data, fh, indent=2, ensure_ascii=False)

    def _save_quality_audit_sync(self, run_id: str, process_id: str, qc_result, version: int, process_name: str | None = None) -> None:
        """Save quality control audit results to a JSON file."""
        from pmbok.audit.quality_control import QualityControlResult

        artifact_dir = self._artifact_dir(run_id, process_id, process_name)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        audit_path = artifact_dir / f"quality_audit_v{version}.json"

        # Convert QualityControlResult to dict if needed
        if isinstance(qc_result, QualityControlResult):
            audit_data = qc_result.to_dict()
        else:
            audit_data = qc_result

        with open(audit_path, "w", encoding="utf-8") as fh:
            json.dump(audit_data, fh, indent=2, ensure_ascii=False)

    def _save_prompt_sync(self, run_id: str, process_id: str, prompt: str, version: int, process_name: str | None = None) -> None:
        artifact_dir = self._artifact_dir(run_id, process_id, process_name)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = artifact_dir / f"prompt_v{version}.txt"
        
        with open(prompt_path, "w", encoding="utf-8") as fh:
            fh.write(prompt)

    def _save_audit_report_sync(self, run_id: str, process_id: str, audit_result, version: int, process_name: str | None = None) -> None:
        """Save a human-readable summary of the audit findings."""
        artifact_dir = self._artifact_dir(run_id, process_id, process_name)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        report_path = artifact_dir / f"audit_v{version}.txt"
        
        lines = []
        lines.append(f"Audit Report for Process {process_id} (Version {version})")
        lines.append(f"Artifact Type: {audit_result.artifact_type}")
        lines.append(f"Compliance Score: {audit_result.compliance_score:.1f}%")
        lines.append(f"Compliance Tier: {audit_result.compliance_tier.value}")
        lines.append(f"Timestamp: {audit_result.audit_timestamp}")
        lines.append("-" * 40)
        
        if audit_result.findings:
            lines.append("Findings:")
            for f in audit_result.findings:
                lines.append(f"  - [{f.severity.value}] {f.criterion}: {f.message}")
                if f.remediation:
                    lines.append(f"    Remediation: {f.remediation}")
        else:
            lines.append("No findings. High quality artifact.")
            
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    async def get_latest(
        self, run_id: str, process_id: str, artifact_type: str
    ) -> ProjectArtifact:
        """Return the latest artifact of *artifact_type* for the given process."""
        return await asyncio.to_thread(
            self._get_latest_sync, run_id, process_id, artifact_type
        )

    def _get_latest_sync(
        self, run_id: str, process_id: str, artifact_type: str
    ) -> ProjectArtifact:
        latest = self._latest_path(run_id, process_id)
        if not latest.exists():
            raise FileNotFoundError(
                f"No artifacts found for run={run_id} process={process_id}"
            )
        with latest.open(encoding="utf-8") as fh:
            data = json.load(fh)
        artifact = self._from_envelope(data)
        if artifact.artifact_type != artifact_type:
            # Fall back to scanning versioned files for the requested type
            return self._scan_for_type(run_id, process_id, artifact_type)
        return artifact

    def _scan_for_type(
        self, run_id: str, process_id: str, artifact_type: str
    ) -> ProjectArtifact:
        artifact_dir = self._artifact_dir(run_id, process_id)
        candidates: list[ProjectArtifact] = []
        for p in artifact_dir.glob("v*.json"):
            if p.name == "latest.json":
                continue
            with p.open(encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("artifact_type") == artifact_type:
                candidates.append(self._from_envelope(data))
        if not candidates:
            raise FileNotFoundError(
                f"No artifact of type '{artifact_type}' found for "
                f"run={run_id} process={process_id}"
            )
        return max(candidates, key=lambda a: a.version)

    async def get_version(self, artifact_id: str, version: int) -> ProjectArtifact:
        """Return a specific version of an artifact by scanning all runs."""
        return await asyncio.to_thread(self._get_version_sync, artifact_id, version)

    def _get_version_sync(self, artifact_id: str, version: int) -> ProjectArtifact:
        pattern = f"v{version}_{artifact_id}.json"
        for path in self.base_path.rglob(pattern):
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            return self._from_envelope(data)
        raise FileNotFoundError(
            f"Artifact id={artifact_id} version={version} not found"
        )

    async def list_artifacts(
        self, run_id: str, process_id: str | None = None
    ) -> list[ProjectArtifact]:
        """List all artifacts for a run, optionally filtered by process_id."""
        return await asyncio.to_thread(self._list_artifacts_sync, run_id, process_id)

    def _list_artifacts_sync(
        self, run_id: str, process_id: str | None
    ) -> list[ProjectArtifact]:
        if process_id is not None:
            artifact_dir = self._artifact_dir(run_id, process_id)
            if not artifact_dir.exists():
                return []
            dirs = [artifact_dir]
        else:
            artifacts_root = self.base_path / "runs" / run_id / "artifacts"
            if not artifacts_root.exists():
                return []
            dirs = [d for d in artifacts_root.iterdir() if d.is_dir()]

        results: list[ProjectArtifact] = []
        seen: set[tuple[str, int]] = set()
        for d in dirs:
            for p in d.glob("v*.json"):
                if p.name == "latest.json":
                    continue
                with p.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                key = (data["artifact_id"], data["version"])
                if key not in seen:
                    seen.add(key)
                    results.append(self._from_envelope(data))
        results.sort(key=lambda a: (a.process_id, a.version))
        return results
