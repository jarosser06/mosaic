"""MCP prompt handlers for Mosaic.

This module provides prompt handlers that generate dynamic, context-aware
prompts for Claude based on current system state.
"""

from .prompt_handlers import (
    generate_add_person_prompt,
    generate_find_gaps_prompt,
    generate_generate_timecard_prompt,
    generate_log_meeting_prompt,
    generate_log_work_prompt,
    generate_reminder_review_prompt,
    generate_search_context_prompt,
    generate_weekly_review_prompt,
)

__all__ = [
    "generate_log_work_prompt",
    "generate_log_meeting_prompt",
    "generate_add_person_prompt",
    "generate_generate_timecard_prompt",
    "generate_weekly_review_prompt",
    "generate_find_gaps_prompt",
    "generate_search_context_prompt",
    "generate_reminder_review_prompt",
]
