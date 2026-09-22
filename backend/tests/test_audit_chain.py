"""Unit tests for the hash-chained audit log (Section 27)."""
from app.services.audit_logger import GENESIS_HASH, compute_entry_hash, verify_entries


def _build_valid_chain(n: int):
    """Builds n entries the way write_audit_log would, without touching a DB."""
    entries = []
    prev_hash = GENESIS_HASH
    for seq in range(1, n + 1):
        details = {"index": seq}
        timestamp = f"2026-01-01T00:00:{seq:02d}"
        entry_hash = compute_entry_hash(seq, "user-1", "some_action", details, timestamp, prev_hash)
        entries.append({
            "seq": seq, "user_id": "user-1", "action": "some_action", "details": details,
            "timestamp": timestamp, "prev_hash": prev_hash, "entry_hash": entry_hash,
        })
        prev_hash = entry_hash
    return entries


def test_valid_chain_passes_verification():
    entries = _build_valid_chain(5)
    result = verify_entries(entries)
    assert result.valid
    assert result.total_entries == 5
    assert result.first_broken_seq is None


def test_empty_chain_is_trivially_valid():
    result = verify_entries([])
    assert result.valid
    assert result.total_entries == 0


def test_editing_a_row_content_breaks_the_chain():
    entries = _build_valid_chain(5)
    entries[2]["action"] = "tampered_action"  # edit row 3's content without recomputing hashes
    result = verify_entries(entries)
    assert not result.valid
    assert result.first_broken_seq == 3


def test_deleting_a_row_breaks_the_chain_at_the_next_entry():
    entries = _build_valid_chain(5)
    del entries[2]  # remove row 3; row 4's prev_hash no longer matches row 2's entry_hash
    result = verify_entries(entries)
    assert not result.valid
    assert result.first_broken_seq == entries[2]["seq"]  # originally seq 4


def test_same_content_produces_same_hash_deterministically():
    h1 = compute_entry_hash(1, "u", "a", {"k": "v"}, "2026-01-01T00:00:00", GENESIS_HASH)
    h2 = compute_entry_hash(1, "u", "a", {"k": "v"}, "2026-01-01T00:00:00", GENESIS_HASH)
    assert h1 == h2


def test_dict_key_order_does_not_change_the_hash():
    h1 = compute_entry_hash(1, "u", "a", {"x": 1, "y": 2}, "2026-01-01T00:00:00", GENESIS_HASH)
    h2 = compute_entry_hash(1, "u", "a", {"y": 2, "x": 1}, "2026-01-01T00:00:00", GENESIS_HASH)
    assert h1 == h2
