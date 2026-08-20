"""Tenant-scoped, idempotent claims for the synthetic Vice CEO runtime.

Local tests use in-memory storage. The Firestore implementation is an explicit
Cloud Run deployment adapter and is never selected unless configuration opts
into it. Neither implementation stores customer content or provider secrets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Protocol

CLAIM_STORE_SCHEMA_VERSION = "vice-ceo-demo-claim-v1"
FIRESTORE_COLLECTION = "vice_ceo_demo_claims"


@dataclass(frozen=True)
class ClaimResult:
    claimed: bool
    record_id: str


class ClaimStore(Protocol):
    """A minimal store interface; callers cannot perform arbitrary reads/writes."""

    def claim_once(
        self,
        *,
        tenant: str,
        claim_kind: str,
        idempotency_key: str,
        record_id: str,
    ) -> ClaimResult: ...


class InMemoryClaimStore:
    """Process-local test implementation with tenant-scoped duplicate protection."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], str] = {}

    def claim_once(
        self,
        *,
        tenant: str,
        claim_kind: str,
        idempotency_key: str,
        record_id: str,
    ) -> ClaimResult:
        key = _claim_key(tenant, claim_kind, idempotency_key)
        existing = self._records.get(key)
        if existing is not None:
            return ClaimResult(claimed=False, record_id=existing)
        self._records[key] = record_id
        return ClaimResult(claimed=True, record_id=record_id)


class FirestoreClaimStore:
    """Firestore adapter for a later Cloud Run deployment; not used in local tests."""

    def __init__(self, client: Any, *, collection: str = FIRESTORE_COLLECTION) -> None:
        self._client = client
        self._collection = collection

    @classmethod
    def from_environment(cls) -> "FirestoreClaimStore":
        """Create only when a deployment explicitly selects Firestore storage."""

        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("google_cloud_project_required_for_firestore_claim_store")
        try:
            from google.cloud import firestore
        except ImportError as error:
            raise RuntimeError("google_cloud_firestore_dependency_required") from error
        return cls(firestore.Client(project=project_id))

    def claim_once(
        self,
        *,
        tenant: str,
        claim_kind: str,
        idempotency_key: str,
        record_id: str,
    ) -> ClaimResult:
        """Atomically create a hashed claim record or return its first record ID."""

        try:
            from google.cloud import firestore
        except ImportError as error:
            raise RuntimeError("google_cloud_firestore_dependency_required") from error

        document_id = claim_document_id(tenant, claim_kind, idempotency_key)
        document = self._client.collection(self._collection).document(document_id)
        transaction = self._client.transaction()

        @firestore.transactional
        def create_once(transaction: Any) -> ClaimResult:
            existing = document.get(transaction=transaction)
            if existing.exists:
                existing_record_id = existing.to_dict().get("record_id")
                return ClaimResult(claimed=False, record_id=str(existing_record_id))
            transaction.create(
                document,
                {
                    "schema_version": CLAIM_STORE_SCHEMA_VERSION,
                    "tenant_sha256": sha256(tenant.encode("utf-8")).hexdigest(),
                    "claim_kind": claim_kind,
                    "record_id": record_id,
                    "created_at": _now_timestamp(),
                },
            )
            return ClaimResult(claimed=True, record_id=record_id)

        return create_once(transaction)


def create_claim_store_from_environment() -> ClaimStore:
    """Select local memory by default; Firestore requires explicit opt-in."""

    store_kind = os.environ.get("VICE_CEO_CLAIM_STORE", "in_memory").strip().lower()
    if store_kind == "in_memory":
        return InMemoryClaimStore()
    if store_kind == "firestore":
        return FirestoreClaimStore.from_environment()
    raise ValueError("unsupported_vice_ceo_claim_store")


def claim_document_id(tenant: str, claim_kind: str, idempotency_key: str) -> str:
    """Return a Firestore-safe ID that never exposes tenant or event details."""

    key = _claim_key(tenant, claim_kind, idempotency_key)
    return f"claim_{sha256('|'.join(key).encode('utf-8')).hexdigest()}"


def _claim_key(tenant: str, claim_kind: str, idempotency_key: str) -> tuple[str, str, str]:
    normalized = (tenant.strip(), claim_kind.strip(), idempotency_key.strip())
    if not all(normalized):
        raise ValueError("claim_scope_fields_required")
    return normalized


def _now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
