"""Unit tests for DeleteWorkSessionInput and DeleteWorkSessionOutput schemas."""

import pytest
from pydantic import ValidationError

from src.mosaic.schemas.work_session import (
    DeleteWorkSessionInput,
    DeleteWorkSessionOutput,
)

# DeleteWorkSessionInput Tests


def test_delete_work_session_input_valid_positive_id():
    """Test DeleteWorkSessionInput with valid positive ID."""
    schema = DeleteWorkSessionInput(work_session_id=42)
    assert schema.work_session_id == 42


def test_delete_work_session_input_valid_id_one():
    """Test DeleteWorkSessionInput with ID=1 (minimum valid)."""
    schema = DeleteWorkSessionInput(work_session_id=1)
    assert schema.work_session_id == 1


def test_delete_work_session_input_rejects_zero_id():
    """Test that work_session_id=0 is rejected (must be > 0)."""
    with pytest.raises(ValidationError) as exc_info:
        DeleteWorkSessionInput(work_session_id=0)
    assert "greater than 0" in str(exc_info.value).lower()


def test_delete_work_session_input_rejects_negative_id():
    """Test that negative work_session_id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        DeleteWorkSessionInput(work_session_id=-1)
    assert "greater than 0" in str(exc_info.value).lower()


def test_delete_work_session_input_rejects_large_negative_id():
    """Test that large negative work_session_id is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        DeleteWorkSessionInput(work_session_id=-999)
    assert "greater than 0" in str(exc_info.value).lower()


# DeleteWorkSessionOutput Tests


def test_delete_work_session_output_valid():
    """Test valid DeleteWorkSessionOutput creation."""
    schema = DeleteWorkSessionOutput(
        success=True,
        message="Work session 42 deleted successfully",
    )

    assert schema.success is True
    assert "42" in schema.message


def test_delete_work_session_output_structure():
    """Test DeleteWorkSessionOutput has correct structure."""
    schema = DeleteWorkSessionOutput(
        success=True,
        message="Work session deleted successfully",
    )

    # Verify required fields exist
    assert hasattr(schema, "success")
    assert hasattr(schema, "message")
    assert isinstance(schema.success, bool)
    assert isinstance(schema.message, str)


def test_delete_work_session_output_message_format():
    """Test DeleteWorkSessionOutput message contains success indicator."""
    schema = DeleteWorkSessionOutput(
        success=True,
        message="Work session 100 deleted successfully",
    )

    assert schema.success is True
    assert "deleted" in schema.message.lower()
    assert "successfully" in schema.message.lower()
