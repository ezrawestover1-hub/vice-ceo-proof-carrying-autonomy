"""Versioned, role-scoped synthetic knowledge references for the demo.

Knowledge retrieval is closed-world: a requester must name an approved pack and
its exact version. The returned reference contains provenance, not an open-ended
document corpus or legal/compliance interpretation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps

from .specialist_protocol import POLICY_GUARD, SUPPORT_INTAKE

KNOWLEDGE_PACK_SCHEMA_VERSION = "vice-ceo-demo-knowledge-pack-v1"


class KnowledgePackError(ValueError):
    """Raised when a pack is unknown, version-mismatched, or out of role scope."""


@dataclass(frozen=True)
class KnowledgePack:
    pack_id: str
    version: str
    status: str
    source_reference: str
    source_type: str
    allowed_specialists: tuple[str, ...]
    content_sha256: str
    summary: str
    legal_or_regulatory_authority: bool


@dataclass(frozen=True)
class KnowledgeGrounding:
    pack_id: str
    version: str
    source_reference: str
    source_type: str
    content_sha256: str
    summary: str
    retrieval_status: str
    legal_or_regulatory_authority: bool


def _content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


_SUPPORT_PLAYBOOK_SUMMARY = (
    "Synthetic password-reset requests may be classified only as triaged or resolution prepared. "
    "No customer contact, account change, or external support action is permitted."
)
_POLICY_PLAYBOOK_SUMMARY = (
    "A synthetic transition requires a registered tool contract, a current policy decision, "
    "and a valid Action Warrant before simulation."
)

KNOWLEDGE_PACKS: dict[str, KnowledgePack] = {
    "synthetic_support_password_reset_playbook": KnowledgePack(
        pack_id="synthetic_support_password_reset_playbook",
        version="1.0.0",
        status="approved",
        source_reference="vice_ceo_demo_support_playbook_v1",
        source_type="synthetic_demo_playbook",
        allowed_specialists=(SUPPORT_INTAKE,),
        content_sha256=_content_hash(_SUPPORT_PLAYBOOK_SUMMARY),
        summary=_SUPPORT_PLAYBOOK_SUMMARY,
        legal_or_regulatory_authority=False,
    ),
    "synthetic_action_warrant_playbook": KnowledgePack(
        pack_id="synthetic_action_warrant_playbook",
        version="1.0.0",
        status="approved",
        source_reference="vice_ceo_demo_action_warrant_playbook_v1",
        source_type="synthetic_demo_policy",
        allowed_specialists=(POLICY_GUARD,),
        content_sha256=_content_hash(_POLICY_PLAYBOOK_SUMMARY),
        summary=_POLICY_PLAYBOOK_SUMMARY,
        legal_or_regulatory_authority=False,
    ),
}


def retrieve_approved_knowledge(
    *, pack_id: str, expected_version: str, specialist_name: str
) -> KnowledgeGrounding:
    """Return a provenance-carrying reference only to an approved scoped pack."""

    pack = KNOWLEDGE_PACKS.get(pack_id)
    if pack is None:
        raise KnowledgePackError("knowledge_pack_not_found")
    if pack.status != "approved":
        raise KnowledgePackError("knowledge_pack_not_approved")
    if pack.version != expected_version:
        raise KnowledgePackError("knowledge_pack_version_mismatch")
    if specialist_name not in pack.allowed_specialists:
        raise KnowledgePackError("knowledge_pack_specialist_not_authorized")
    return KnowledgeGrounding(
        pack_id=pack.pack_id,
        version=pack.version,
        source_reference=pack.source_reference,
        source_type=pack.source_type,
        content_sha256=pack.content_sha256,
        summary=pack.summary,
        retrieval_status="approved_exact_version",
        legal_or_regulatory_authority=False,
    )


def knowledge_manifest_sha256() -> str:
    """Hash the approved manifest so a demo can cite the exact knowledge set."""

    manifest = {
        pack_id: {
            "version": pack.version,
            "status": pack.status,
            "source_reference": pack.source_reference,
            "content_sha256": pack.content_sha256,
        }
        for pack_id, pack in sorted(KNOWLEDGE_PACKS.items())
    }
    return sha256(dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
