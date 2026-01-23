import sys
import types
from unittest.mock import MagicMock

sys.modules.setdefault("pika", types.SimpleNamespace())
sys.modules.setdefault("httpx", types.SimpleNamespace())

from app.ai_agent_worker import extract_source_message_id, is_duplicate_message


def test_extract_source_message_id_prefers_body_message_id():
    body = {
        "message_id": "abc-123",
        "raw_data": {"idMessage": "raw-1", "receiptId": "raw-2"},
    }
    assert extract_source_message_id(body) == "abc-123"


def test_extract_source_message_id_falls_back_to_raw_data():
    body = {
        "raw_data": {"idMessage": "raw-1", "receiptId": "raw-2"},
    }
    assert extract_source_message_id(body) == "raw-1"


def test_extract_source_message_id_uses_receipt_id_when_no_id_message():
    body = {
        "raw_data": {"receiptId": "raw-2"},
    }
    assert extract_source_message_id(body) == "raw-2"


def test_extract_source_message_id_handles_missing_values():
    body = {"raw_data": {}}
    assert extract_source_message_id(body) is None


def test_is_duplicate_message_returns_false_without_id():
    db = MagicMock()
    assert is_duplicate_message(db, 1, None) is False
    db.query.assert_not_called()


def test_is_duplicate_message_returns_true_when_found():
    db = MagicMock()
    query = MagicMock()
    filtered = MagicMock()
    filtered.first.return_value = types.SimpleNamespace(id=1)
    query.filter.return_value = filtered
    db.query.return_value = query

    assert is_duplicate_message(db, 42, "id-1") is True


def test_is_duplicate_message_returns_false_when_missing():
    db = MagicMock()
    query = MagicMock()
    filtered = MagicMock()
    filtered.first.return_value = None
    query.filter.return_value = filtered
    db.query.return_value = query

    assert is_duplicate_message(db, 42, "id-2") is False
