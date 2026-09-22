"""
Audit Logging Service (Section 21 - Logging Flow).

Writes append-only, structured audit entries for every security-relevant
action (login, role change, finding override, report download).

"Append-only" was previously just a convention -- nothing stopped someone
with direct database access from editing or deleting a row and nobody
would know. Every entry is now hash-chained: entry_hash covers the row's
own content *and* the previous row's entry_hash, so altering or deleting
any historical row changes the hash every subsequent row was computed
against. verify_chain() walks the table and reports the first row where
that no longer holds.

This doesn't stop tampering -- someone with DB write access could still
recompute every downstream hash to cover their tracks, and it doesn't
substitute for an external, write-once log shipped off-box. What it does
give you is a cheap, self-contained integrity check: a one-off edit made
without also rewriting the whole chain afterward gets caught the next
time someone calls /api/v1/audit-log/verify. For a real deployment you'd
still want the log periodically anchored somewhere outside the app's own
database.

Concurrency note: seq is assigned by reading the current max and adding
one, which is not safe against two truly concurrent writers racing each
other -- the `seq` column's unique constraint turns that race into a loud
IntegrityError on one of the two writes rather than a silently corrupted
chain, but it does mean audit writes should happen from a single request
at a time per process. Fine for this project's scale; worth revisiting
with a DB sequence or advisory lock before this goes anywhere with real
concurrent write load.
"""
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import AuditLog

GENESIS_HASH = "0" * 64  # prev_hash of the very first entry in the chain


def _canonical_payload(seq: int, user_id: Optional[str], action: str, details: Dict,
                        timestamp_iso: str, prev_hash: str) -> str:
    """Deterministic JSON encoding of everything an entry's hash covers.
    sort_keys makes this independent of dict insertion order.
    """
    return json.dumps(
        {
            "seq": seq,
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": timestamp_iso,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        default=str,
    )


def compute_entry_hash(seq: int, user_id: Optional[str], action: str, details: Dict,
                        timestamp_iso: str, prev_hash: str) -> str:
    payload = _canonical_payload(seq, user_id, action, details, timestamp_iso, prev_hash)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_audit_log(db: Session, user_id: Optional[str], action: str, details: Optional[Dict] = None) -> AuditLog:
    details = details or {}
    last = db.query(AuditLog).order_by(AuditLog.seq.desc()).first()
    seq = (last.seq + 1) if last else 1
    prev_hash = last.entry_hash if last else GENESIS_HASH

    timestamp = datetime.utcnow()
    entry_hash = compute_entry_hash(seq, user_id, action, details, timestamp.isoformat(), prev_hash)

    entry = AuditLog(
        user_id=user_id, action=action, details=details, timestamp=timestamp,
        seq=seq, prev_hash=prev_hash, entry_hash=entry_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@dataclass
class ChainVerificationResult:
    valid: bool
    total_entries: int
    first_broken_seq: Optional[int]


def verify_entries(entries: List[dict]) -> ChainVerificationResult:
    """Pure verification core: entries must already be ordered by seq
    ascending, each a dict with seq, user_id, action, details, timestamp
    (ISO string), prev_hash, entry_hash. Kept separate from verify_chain
    so the chain logic is testable without a real database.
    """
    expected_prev = GENESIS_HASH
    for entry in entries:
        recomputed = compute_entry_hash(
            entry["seq"], entry["user_id"], entry["action"], entry["details"],
            entry["timestamp"], expected_prev,
        )
        if entry["prev_hash"] != expected_prev or entry["entry_hash"] != recomputed:
            return ChainVerificationResult(valid=False, total_entries=len(entries), first_broken_seq=entry["seq"])
        expected_prev = entry["entry_hash"]

    return ChainVerificationResult(valid=True, total_entries=len(entries), first_broken_seq=None)


def verify_chain(db: Session) -> ChainVerificationResult:
    rows = db.query(AuditLog).order_by(AuditLog.seq.asc()).all()
    entries = [
        {
            "seq": r.seq,
            "user_id": r.user_id,
            "action": r.action,
            "details": r.details or {},
            "timestamp": r.timestamp.isoformat(),
            "prev_hash": r.prev_hash,
            "entry_hash": r.entry_hash,
        }
        for r in rows
    ]
    return verify_entries(entries)
