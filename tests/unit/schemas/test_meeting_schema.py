"""Tests for DeleteMeetingInput and DeleteMeetingOutput schemas (3 test cases)."""

import pytest
from pydantic import ValidationError

from src.mosaic.schemas.meeting import DeleteMeetingInput, DeleteMeetingOutput

# DeleteMeetingInput Tests


def test_delete_meeting_input_validation_positive_id():
    """Test valid DeleteMeetingInput with positive ID."""
    schema = DeleteMeetingInput(meeting_id=42)
    assert schema.meeting_id == 42


def test_delete_meeting_input_validation_negative_id():
    """Test that meeting_id must be > 0 (negative/zero should fail)."""
    # Test zero
    with pytest.raises(ValidationError) as exc_info:
        DeleteMeetingInput(meeting_id=0)
    assert "greater than 0" in str(exc_info.value).lower()

    # Test negative
    with pytest.raises(ValidationError) as exc_info:
        DeleteMeetingInput(meeting_id=-1)
    assert "greater than 0" in str(exc_info.value).lower()


# DeleteMeetingOutput Tests


def test_delete_meeting_output_schema():
    """Test valid DeleteMeetingOutput structure."""
    schema = DeleteMeetingOutput(
        success=True,
        message="Meeting 42 deleted successfully",
    )

    assert schema.success is True
    assert "42" in schema.message
    assert "deleted" in schema.message.lower()
