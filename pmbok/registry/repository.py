"""SQLite-backed Registry repository implementation via SQLAlchemy Core.

Isolates canonical entity knowledge from orchestration state.
Aligned with V7 Registry models in pmbok/models/registry.py.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, List, Optional, Union

import sqlalchemy as sa
from sqlalchemy import create_engine, text

from pmbok.models.registry import (
    EntityMaster,
    EntityVersionEnvelope,
    ArtifactRegistryRecord,
    BaselineRegistryRecord,
    BaselineMembership,
    DriftEvent,
    AnomalyEvent,
    EntityClass,
    ChangeType,
    DriftSeverity,
    AuditStatus,
    Classification,
    ProjectContext,
    Integrity,
    Versioning,
    GovernanceMetadata,
    Lineage,
    Relationship,
    EntityRelationship,
    BaselineStatus
)

# ── Table definitions ─────────────────────────────────────────────────────────

metadata = sa.MetaData()

# Stable entity identity
entity_masters_table = sa.Table(
    "entity_masters",
    metadata,
    sa.Column("entity_id", sa.Text, primary_key=True),
    sa.Column("canonical_key", sa.Text, nullable=False),
    sa.Column("canonical_name", sa.Text, nullable=False),
    sa.Column("entity_type", sa.Text, nullable=False),
    sa.Column("registry", sa.Text, nullable=False),
    sa.Column("origin_project_id", sa.Text, nullable=False),
    sa.Column("status", sa.Text, default="active"),
    sa.Column("created_at", sa.Text, nullable=False),
)

# Frozen/Immutable version records
entity_versions_table = sa.Table(
    "entity_versions",
    metadata,
    sa.Column("entity_version_id", sa.Text, primary_key=True),
    sa.Column("entity_id", sa.Text, nullable=False),
    sa.Column("entity_type", sa.Text, nullable=False),
    sa.Column("registry", sa.Text, nullable=False),
    sa.Column("version_label", sa.Text, nullable=False),
    sa.Column("major", sa.Integer, nullable=False),
    sa.Column("minor", sa.Integer, nullable=False),
    sa.Column("micro", sa.Integer, nullable=False),
    sa.Column("content_hash", sa.Text, nullable=False),
    sa.Column("schema_hash", sa.Text, nullable=False),
    sa.Column("source_artifact_id", sa.Text, nullable=False),
    sa.Column("process_id", sa.Text, nullable=False),
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("quality_score", sa.Float, nullable=True),
    sa.Column("audit_status", sa.Text, nullable=True),
    sa.Column("classification", sa.Text, nullable=True),  # JSON
    sa.Column("project_context", sa.Text, nullable=True), # JSON
    sa.Column("governance", sa.Text, nullable=True),      # JSON blob for extra gov metadata
    sa.Column("lineage", sa.Text, nullable=True),         # JSON blob for extra lineage metadata
    sa.Column("relationships", sa.Text, nullable=True),   # JSON array
    sa.Column("baseline_status", sa.Text, nullable=True), # JSON
    sa.Column("payload", sa.Text, nullable=False),        # JSON
    sa.Column("created_at", sa.Text, nullable=False),
    sa.ForeignKeyConstraint(["entity_id"], ["entity_masters.entity_id"]),
)

# Frozen baselines
baselines_table = sa.Table(
    "baselines",
    metadata,
    sa.Column("baseline_id", sa.Text, primary_key=True),
    sa.Column("label", sa.Text, nullable=False),
    sa.Column("baseline_type", sa.Text, default="operational"),
    sa.Column("description", sa.Text, nullable=False),
    sa.Column("status", sa.Text, default="locked"),
    sa.Column("created_at", sa.Text, nullable=False),
)

# Many-to-many relationship for baselines
baseline_memberships_table = sa.Table(
    "baseline_memberships",
    metadata,
    sa.Column("baseline_id", sa.Text, primary_key=True),
    sa.Column("entity_version_id", sa.Text, primary_key=True),
    sa.Column("inclusion_reason", sa.Text, nullable=False),
    sa.Column("timestamp", sa.Text, nullable=False),
    sa.ForeignKeyConstraint(["baseline_id"], ["baselines.baseline_id"]),
    sa.ForeignKeyConstraint(["entity_version_id"], ["entity_versions.entity_version_id"]),
)

# Semantic and Traceability Relationships (External/Derived)
entity_relationships_table = sa.Table(
    "entity_relationships",
    metadata,
    sa.Column("relationship_id", sa.Text, primary_key=True),
    sa.Column("source_entity_id", sa.Text, nullable=False),
    sa.Column("target_entity_id", sa.Text, nullable=False),
    sa.Column("relationship_type", sa.Text, nullable=False),
    sa.Column("metadata", sa.Text, nullable=True), # JSON
    sa.Column("created_at", sa.Text, nullable=False),
    sa.ForeignKeyConstraint(["source_entity_id"], ["entity_masters.entity_id"]),
    sa.ForeignKeyConstraint(["target_entity_id"], ["entity_masters.entity_id"]),
)

# Registry for source artifacts
artifact_registry_table = sa.Table(
    "artifact_registry",
    metadata,
    sa.Column("artifact_id", sa.Text, primary_key=True),
    sa.Column("process_id", sa.Text, nullable=False),
    sa.Column("artifact_type", sa.Text, nullable=False),
    sa.Column("run_id", sa.Text, nullable=False),
    sa.Column("project_id", sa.Text, nullable=False),
    sa.Column("storage_path", sa.Text, nullable=True),
    sa.Column("content_hash", sa.Text, nullable=False),
    sa.Column("created_at", sa.Text, nullable=False),
)

# Detailed drift and anomaly events
drift_events_table = sa.Table(
    "drift_events",
    metadata,
    sa.Column("drift_id", sa.Text, primary_key=True),
    sa.Column("entity_id", sa.Text, nullable=False),
    sa.Column("baseline_version_id", sa.Text, nullable=True),
    sa.Column("observed_version_id", sa.Text, nullable=True),
    sa.Column("drift_type", sa.Text, nullable=True),
    sa.Column("severity", sa.Text, nullable=False),
    sa.Column("drift_score", sa.Float, nullable=True),
    sa.Column("drift_description", sa.Text, nullable=True),
    sa.Column("detected_at", sa.Text, nullable=False),
)

# [NEW] Draco Overrides - First Class Governance Artifact
draco_overrides_table = sa.Table(
    "draco_overrides",
    metadata,
    sa.Column("override_id", sa.Text, primary_key=True),
    sa.Column("gate_id", sa.Text, nullable=False),
    sa.Column("entity_id", sa.Text, nullable=False),
    sa.Column("requested_by", sa.Text, nullable=False),
    sa.Column("approved_by", sa.Text, nullable=False),
    sa.Column("justification", sa.Text, nullable=False),
    sa.Column("expires_at", sa.Text, nullable=False),
    sa.Column("approval_level", sa.Text, nullable=False), # technical, governance, compliance
    sa.Column("compensating_controls", sa.Text, nullable=True),
    sa.Column("board_review_required", sa.Boolean, default=False),
    sa.Column("created_at", sa.Text, nullable=False),
    sa.ForeignKeyConstraint(["entity_id"], ["entity_masters.entity_id"]),
)

anomaly_events_table = sa.Table(
    "anomaly_events",
    metadata,
    sa.Column("anomaly_id", sa.Text, primary_key=True),
    sa.Column("entity_version_id", sa.Text, nullable=False),
    sa.Column("anomaly_type", sa.Text, nullable=False),
    sa.Column("severity", sa.Text, nullable=False),
    sa.Column("description", sa.Text, nullable=False),
    sa.Column("detected_at", sa.Text, nullable=False),
)

# ── RegistryRepository ────────────────────────────────────────────────────────

class RegistryRepository:
    """SQLite-backed repository for the ADPA Registry."""

    def __init__(self, db_path: str) -> None:
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        self._create_tables()

    def _create_tables(self) -> None:
        metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.commit()

    async def execute(self, stmt, params=None):
        """Thread-safe execution of raw SQL or SA statements."""
        return await asyncio.to_thread(self._execute_sync, stmt, params)

    def _execute_sync(self, stmt, params=None):
        with self.engine.connect() as conn:
            result = conn.execute(stmt, params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            return []

    # ── Master Operations ───────────────────────────────────────────────────

    async def ensure_master(self, master: EntityMaster) -> None:
        await asyncio.to_thread(self._ensure_master_sync, master)

    def _ensure_master_sync(self, master: EntityMaster) -> None:
        row = {
            "entity_id": master.entity_id,
            "canonical_key": master.canonical_key,
            "canonical_name": master.canonical_name,
            "entity_type": master.entity_type,
            "registry": master.registry,
            "origin_project_id": master.origin_project_id,
            "status": master.status,
            "created_at": master.created_at.isoformat()
        }
        with self.engine.begin() as conn:
            stmt = sa.insert(entity_masters_table).values(**row).prefix_with("OR IGNORE")
            conn.execute(stmt)

    async def get_master(self, entity_id: str) -> Optional[EntityMaster]:
        return await asyncio.to_thread(self._get_master_sync, entity_id)

    def _get_master_sync(self, entity_id: str) -> Optional[EntityMaster]:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(entity_masters_table).where(entity_masters_table.c.entity_id == entity_id)
            ).fetchone()
        if not row:
            return None
        return self._row_to_master(row)

    def get_entities_by_type(self, entity_type: str, project_id: str) -> List[Dict[str, Any]]:
        """Fetch all latest versions of entities of a specific type in a project."""
        stmt = sa.select(entity_versions_table).where(
            sa.and_(
                entity_versions_table.c.entity_type == entity_type,
                entity_versions_table.c.project_context.like(f'%"{project_id}"%')
            )
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_relationships_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetch all relationships for a specific project."""
        stmt = sa.select(entity_relationships_table).where(
            entity_relationships_table.c.metadata.like(f'%"project_id": "{project_id}"%')
        )
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_active_overrides(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetch all active (non-expired) overrides for a project."""
        now = datetime.now(timezone.utc).isoformat()
        stmt = sa.select(draco_overrides_table).where(
            sa.and_(
                draco_overrides_table.c.expires_at > now
            )
        )
        # Note: Filtering by project_id requires joining with entity_masters or having project_id in overrides
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    async def get_master_by_key(self, canonical_key: str) -> Optional[EntityMaster]:
        return await asyncio.to_thread(self._get_master_by_key_sync, canonical_key)

    def _get_master_by_key_sync(self, canonical_key: str) -> Optional[EntityMaster]:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(entity_masters_table).where(entity_masters_table.c.canonical_key == canonical_key)
            ).fetchone()
        if not row:
            return None
        return self._row_to_master(row)

    async def list_masters(self) -> List[EntityMaster]:
        return await self.search_masters()

    async def search_masters(self, name_pattern: str = None, key_pattern: str = None, entity_type: str = None) -> List[EntityMaster]:
        return await asyncio.to_thread(self._search_masters_sync, name_pattern, key_pattern, entity_type)

    def _search_masters_sync(self, name_pattern: str = None, key_pattern: str = None, entity_type: str = None) -> List[EntityMaster]:
        with self.engine.connect() as conn:
            query = sa.select(entity_masters_table)
            if name_pattern:
                query = query.where(entity_masters_table.c.canonical_name.like(f"%{name_pattern}%"))
            if key_pattern:
                query = query.where(entity_masters_table.c.canonical_key.like(key_pattern))
            if entity_type:
                query = query.where(entity_masters_table.c.entity_type == entity_type)
            rows = conn.execute(query).fetchall()
        return [self._row_to_master(row) for row in rows]

    def _row_to_master(self, row: Any) -> EntityMaster:
        return EntityMaster(
            entity_id=row.entity_id,
            canonical_key=row.canonical_key,
            canonical_name=row.canonical_name,
            entity_type=row.entity_type,
            registry=row.registry,
            origin_project_id=row.origin_project_id,
            status=row.status,
            created_at=datetime.fromisoformat(row.created_at)
        )

    # ── Version Operations ──────────────────────────────────────────────────

    async def save_version(self, envelope: EntityVersionEnvelope) -> None:
        await asyncio.to_thread(self._save_version_sync, envelope)

    def _save_version_sync(self, envelope: EntityVersionEnvelope) -> None:
        row = {
            "entity_version_id": envelope.entity_version_id,
            "entity_id": envelope.entity_id,
            "entity_type": envelope.entity_type,
            "registry": envelope.registry,
            "version_label": envelope.versioning.version_label,
            "major": envelope.versioning.major,
            "minor": envelope.versioning.minor,
            "micro": envelope.versioning.micro,
            "content_hash": envelope.integrity.content_hash,
            "schema_hash": envelope.integrity.schema_hash,
            "source_artifact_id": envelope.lineage.source_artifact_id,
            "process_id": envelope.lineage.process_id,
            "run_id": envelope.lineage.run_id,
            "quality_score": envelope.governance.quality_score,
            "audit_status": envelope.governance.audit_status.value,
            "classification": envelope.classification.model_dump_json(),
            "project_context": envelope.project_context.model_dump_json(),
            "governance": envelope.governance.model_dump_json(),
            "lineage": envelope.lineage.model_dump_json(),
            "relationships": json.dumps([r.model_dump() for r in envelope.relationships]),
            "baseline_status": envelope.baseline.model_dump_json(),
            "payload": json.dumps(envelope.payload),
            "created_at": envelope.created_at.isoformat()
        }
        with self.engine.begin() as conn:
            conn.execute(entity_versions_table.insert().values(**row))

    async def get_latest_version(self, entity_id: str) -> Optional[EntityVersionEnvelope]:
        return await asyncio.to_thread(self._get_latest_version_sync, entity_id)

    def _get_latest_version_sync(self, entity_id: str) -> Optional[EntityVersionEnvelope]:
        with self.engine.connect() as conn:
            stmt = sa.select(entity_versions_table).where(
                entity_versions_table.c.entity_id == entity_id
            ).order_by(
                entity_versions_table.c.major.desc(),
                entity_versions_table.c.minor.desc(),
                entity_versions_table.c.micro.desc(),
                entity_versions_table.c.created_at.desc()
            ).limit(1)
            row = conn.execute(stmt).fetchone()
        if not row:
            return None
        return self._row_to_version(row)

    async def get_version(self, entity_version_id: str) -> Optional[EntityVersionEnvelope]:
        return await asyncio.to_thread(self._get_version_sync, entity_version_id)

    def _get_version_sync(self, entity_version_id: str) -> Optional[EntityVersionEnvelope]:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(entity_versions_table).where(entity_versions_table.c.entity_version_id == entity_version_id)
            ).fetchone()
        if not row:
            return None
        return self._row_to_version(row)

    def _row_to_version(self, row: Any) -> EntityVersionEnvelope:
        return EntityVersionEnvelope(
            entity_id=row.entity_id,
            entity_version_id=row.entity_version_id,
            entity_type=row.entity_type,
            registry=row.registry,
            classification=Classification.model_validate_json(row.classification),
            project_context=ProjectContext.model_validate_json(row.project_context),
            versioning=Versioning(
                version_label=row.version_label,
                major=row.major,
                minor=row.minor,
                micro=row.micro
            ),
            integrity=Integrity(
                content_hash=row.content_hash,
                schema_hash=row.schema_hash
            ),
            governance=GovernanceMetadata.model_validate_json(row.governance),
            lineage=Lineage.model_validate_json(row.lineage),
            relationships=[Relationship(**r) for r in json.loads(row.relationships or "[]")],
            baseline=BaselineStatus.model_validate_json(row.baseline_status),
            payload=json.loads(row.payload),
            created_at=datetime.fromisoformat(row.created_at)
        )

    # ── Baseline Operations ────────────────────────────────────────────────

    async def create_baseline(self, baseline: BaselineRegistryRecord) -> None:
        await asyncio.to_thread(self._create_baseline_sync, baseline)

    def _create_baseline_sync(self, baseline: BaselineRegistryRecord) -> None:
        row = {
            "baseline_id": baseline.baseline_id,
            "label": baseline.label,
            "baseline_type": baseline.baseline_type,
            "description": baseline.description,
            "status": baseline.status,
            "created_at": baseline.created_at.isoformat()
        }
        with self.engine.begin() as conn:
            conn.execute(baselines_table.insert().values(**row))

    async def add_to_baseline(self, membership: BaselineMembership) -> None:
        await asyncio.to_thread(self._add_to_baseline_sync, membership)

    def _add_to_baseline_sync(self, membership: BaselineMembership) -> None:
        row = {
            "baseline_id": membership.baseline_id,
            "entity_version_id": membership.entity_version_id,
            "inclusion_reason": membership.inclusion_reason,
            "timestamp": membership.timestamp.isoformat()
        }
        with self.engine.begin() as conn:
            conn.execute(sa.text("""
                INSERT OR IGNORE INTO baseline_memberships 
                (baseline_id, entity_version_id, inclusion_reason, timestamp)
                VALUES (:baseline_id, :entity_version_id, :inclusion_reason, :timestamp)
            """), row)

    async def get_baseline_members(self, baseline_id: str) -> List[str]:
        return await asyncio.to_thread(self._get_baseline_members_sync, baseline_id)

    def _get_baseline_members_sync(self, baseline_id: str) -> List[str]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                sa.select(baseline_memberships_table.c.entity_version_id).where(
                    baseline_memberships_table.c.baseline_id == baseline_id
                )
            ).fetchall()
        return [r.entity_version_id for r in rows]

    # ── Event Operations ───────────────────────────────────────────────────

    async def log_drift(self, event: DriftEvent) -> None:
        await asyncio.to_thread(self._log_drift_sync, event)

    def _log_drift_sync(self, event: DriftEvent) -> None:
        row = {
            "drift_id": event.drift_id,
            "entity_id": event.entity_id,
            "baseline_version_id": event.baseline_version_id,
            "observed_version_id": event.observed_version_id,
            "drift_type": event.drift_type,
            "severity": event.severity.value,
            "drift_score": event.drift_score,
            "drift_description": event.drift_description,
            "detected_at": event.detected_at.isoformat()
        }
        with self.engine.begin() as conn:
            conn.execute(drift_events_table.insert().values(**row))

    async def log_anomaly(self, event: AnomalyEvent) -> None:
        await asyncio.to_thread(self._log_anomaly_sync, event)

    def _log_anomaly_sync(self, event: AnomalyEvent) -> None:
        row = {
            "anomaly_id": event.anomaly_id,
            "entity_version_id": event.entity_version_id,
            "anomaly_type": event.anomaly_type,
            "severity": event.severity.value,
            "description": event.description,
            "detected_at": event.detected_at.isoformat()
        }
        with self.engine.begin() as conn:
            conn.execute(anomaly_events_table.insert().values(**row))

    # ── Relationship Operations ───────────────────────────────────────────

    async def save_relationship(self, relationship: EntityRelationship) -> None:
        await asyncio.to_thread(self._save_relationship_sync, relationship)

    def _save_relationship_sync(self, relationship: EntityRelationship) -> None:
        import hashlib
        raw_id = f"{relationship.source_entity_id}:{relationship.target_entity_id}:{relationship.relationship_type}"
        rel_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
        
        row = {
            "relationship_id": rel_id,
            "source_entity_id": relationship.source_entity_id,
            "target_entity_id": relationship.target_entity_id,
            "relationship_type": relationship.relationship_type,
            "metadata": json.dumps(relationship.metadata or {}),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        with self.engine.begin() as conn:
            conn.execute(sa.text("""
                INSERT OR REPLACE INTO entity_relationships 
                (relationship_id, source_entity_id, target_entity_id, relationship_type, metadata, created_at)
                VALUES (:relationship_id, :source_entity_id, :target_entity_id, :relationship_type, :metadata, :created_at)
            """), row)

    async def get_relationships(self, source_entity_id: str) -> List[EntityRelationship]:
        return await asyncio.to_thread(self._get_relationships_sync, source_entity_id)

    def _get_relationships_sync(self, source_entity_id: str) -> List[EntityRelationship]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                sa.select(entity_relationships_table).where(
                    entity_relationships_table.c.source_entity_id == source_entity_id
                )
            ).fetchall()
        return [
            EntityRelationship(
                source_entity_id=row.source_entity_id,
                target_entity_id=row.target_entity_id,
                relationship_type=row.relationship_type,
                metadata=json.loads(row.metadata or "{}")
            ) for row in rows
        ]

    # ── Artifact Operations ────────────────────────────────────────────────

    async def save_artifact(self, record: ArtifactRegistryRecord) -> None:
        await asyncio.to_thread(self._save_artifact_sync, record)

    def _save_artifact_sync(self, record: ArtifactRegistryRecord) -> None:
        row = {
            "artifact_id": record.artifact_id,
            "process_id": record.process_id,
            "artifact_type": record.artifact_type,
            "run_id": record.run_id,
            "project_id": record.project_id,
            "storage_path": record.storage_path,
            "content_hash": record.content_hash,
            "created_at": record.created_at.isoformat()
        }
        with self.engine.begin() as conn:
            stmt = sa.insert(artifact_registry_table).values(**row).prefix_with("OR IGNORE")
            conn.execute(stmt)

    async def get_artifact(self, artifact_id: str) -> Optional[ArtifactRegistryRecord]:
        return await asyncio.to_thread(self._get_artifact_sync, artifact_id)

    def _get_artifact_sync(self, artifact_id: str) -> Optional[ArtifactRegistryRecord]:
        with self.engine.connect() as conn:
            row = conn.execute(
                sa.select(artifact_registry_table).where(artifact_registry_table.c.artifact_id == artifact_id)
            ).fetchone()
        if not row:
            return None
        return ArtifactRegistryRecord(
            artifact_id=row.artifact_id,
            process_id=row.process_id,
            artifact_type=row.artifact_type,
            run_id=row.run_id,
            project_id=row.project_id,
            storage_path=row.storage_path,
            content_hash=row.content_hash,
            created_at=datetime.fromisoformat(row.created_at)
        )
