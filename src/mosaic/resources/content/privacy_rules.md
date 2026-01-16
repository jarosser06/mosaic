# Privacy Rules

Privacy model and filtering guidelines for work sessions, meetings, and notes in Mosaic.

## Overview

Mosaic implements a three-tier privacy system to control what information is shared in timecards, summaries, and external reports. This protects sensitive client information while allowing appropriate data sharing.

## Privacy Levels

### PUBLIC
**Shareable externally, including with clients**

- Safe to include in client-facing timecards
- Can appear in invoices and project summaries
- No sensitive information should be present
- Suitable for high-level descriptions

**Example Use Cases:**
- Generic work descriptions: "Frontend development"
- Public meetings: "Client demo"
- Non-sensitive project work: "Documentation updates"

### INTERNAL
**Shareable within your organization only**

- Can appear in internal reports
- Safe to share with team members
- Should not be shared with clients or external parties
- May contain company-specific details

**Example Use Cases:**
- Internal meetings: "Engineering standup"
- Team collaboration: "Code review with internal team"
- Process work: "Internal testing and QA"

### PRIVATE
**Sensitive, filtered from timecards and external summaries**

- **Default level for safety**
- Excluded from client-facing timecards
- Excluded from external summaries
- Visible only in full system queries
- May contain confidential information

**Example Use Cases:**
- Sensitive client discussions: "Compensation negotiation"
- Confidential work: "Security audit findings"
- Personal notes: "Concerns about project direction"
- Strategy sessions: "Pricing discussion for renewal"

## Default Behavior

**All entities default to PRIVATE for safety:**

```python
privacy_level: Mapped[PrivacyLevel] = mapped_column(
    Enum(PrivacyLevel, native_enum=False),
    default=PrivacyLevel.PRIVATE,
    nullable=False,
)
```

This "private by default" policy prevents accidental exposure of sensitive information.

## Entities with Privacy Levels

Privacy levels apply to three entity types:

### 1. WorkSession
```python
class WorkSession:
    privacy_level: PrivacyLevel  # default: PRIVATE
```

**Filters:**
- Timecard generation (excludes PRIVATE)
- Client-facing reports (PUBLIC only)
- Internal summaries (PUBLIC + INTERNAL)

### 2. Meeting
```python
class Meeting:
    privacy_level: PrivacyLevel  # default: PRIVATE
```

**Filters:**
- Meeting summaries for clients (PUBLIC only)
- Team meeting lists (PUBLIC + INTERNAL)
- Full calendar queries (all levels)

### 3. Note
```python
class Note:
    privacy_level: PrivacyLevel  # default: PRIVATE
```

**Filters:**
- Project note exports (PUBLIC only)
- Internal knowledge base (PUBLIC + INTERNAL)
- Personal note searches (all levels)

## Filtering Rules by Use Case

### Timecard Generation

**Goal:** Provide billable hours summary for client invoicing

**Inclusion Rules:**
- `privacy_level = PUBLIC` → Always included with full details
- `privacy_level = INTERNAL` → Included with generic description
- `privacy_level = PRIVATE` → Excluded entirely

**Example Timecard:**
```
Project: Website Redesign
Week: 2026-01-13 to 2026-01-17

PUBLIC entries:
  Mon: 3.5 hours - "Frontend component development"
  Tue: 2.0 hours - "Client meeting and planning"

INTERNAL entries (genericized):
  Wed: 4.0 hours - "Project work"
  Thu: 1.5 hours - "Project work"

PRIVATE entries (excluded):
  Fri: 2.0 hours - [not shown]

Total Billable: 11.0 hours
```

### External Summaries

**Goal:** Provide project status to clients

**Inclusion Rules:**
- Only PUBLIC items included
- Full details shown (summary, notes, etc.)

**Query:** "Summarize work on Website Redesign this month"

**Response (to client):**
```
Website Redesign - January 2026

Work Completed:
- Frontend component development (3.5 hours)
- Client meeting and planning (2.0 hours)
- API integration (5.0 hours)

Total Public Hours: 10.5 hours
```

### Internal Queries

**Goal:** Full visibility for personal memory and internal reporting

**Inclusion Rules:**
- All privacy levels included (PUBLIC, INTERNAL, PRIVATE)
- Full details shown
- Single-user system means no filtering needed

**Query:** "What did I work on this week?"

**Response (internal, full access):**
```
This Week's Work:

PUBLIC:
- Frontend component development (3.5 hours)
- Client meeting and planning (2.0 hours)

INTERNAL:
- Engineering standup (1.5 hours)
- Code review with team (2.0 hours)

PRIVATE:
- Compensation negotiation prep (2.0 hours)
- Security audit findings review (1.5 hours)

Total: 12.5 hours
```

## Auto-Generated Privacy Inheritance

### Meeting → WorkSession

When a meeting auto-generates a work session:

**Rule:** WorkSession inherits the meeting's privacy level

```python
meeting.privacy_level = PrivacyLevel.PUBLIC
↓
auto_work_session.privacy_level = PrivacyLevel.PUBLIC
```

**Rationale:** If the meeting is public, the billable time should be too.

### Project → WorkSession

When manually logging work against a project:

**Rule:** Use user's default privacy level OR explicitly set

```python
# User default
user.default_privacy_level = PrivacyLevel.PRIVATE

# New work session defaults to PRIVATE
work_session = WorkSession(...)  # privacy_level = PRIVATE

# Or explicitly override
work_session = WorkSession(..., privacy_level=PrivacyLevel.PUBLIC)
```

## Privacy Level Selection Guidelines

### When to use PUBLIC

✅ Generic work descriptions safe for clients
✅ Public meetings or demos
✅ High-level project summaries
✅ Work you'd put on an invoice without hesitation

❌ Specific implementation details
❌ Internal discussions
❌ Sensitive client conversations

### When to use INTERNAL

✅ Team meetings and collaboration
✅ Internal process work (testing, code review)
✅ Work involving company-specific tools or processes
✅ Details safe for your team but not clients

❌ Client-facing deliverables
❌ Highly sensitive discussions
❌ Personal or confidential notes

### When to use PRIVATE

✅ Sensitive client discussions (pricing, contracts, personnel)
✅ Security or compliance work with findings
✅ Personal notes or concerns
✅ Anything you wouldn't want accidentally shared
✅ **When in doubt, use PRIVATE**

## MCP Tool Behavior

### log_work_session
```json
{
  "project_id": 123,
  "start_time": "2026-01-15T14:00:00Z",
  "end_time": "2026-01-15T16:00:00Z",
  "summary": "Security audit",
  "privacy_level": "private"  // EXPLICIT override
}
```

If not specified, defaults to PRIVATE.

### log_meeting
```json
{
  "title": "Client Demo",
  "start_time": "2026-01-15T10:00:00Z",
  "duration_minutes": 60,
  "privacy_level": "public"  // Safe for client visibility
}
```

### generate_timecard
```json
{
  "project_id": 123,
  "start_date": "2026-01-13",
  "end_date": "2026-01-17",
  "include_private": false  // DEFAULT: excludes PRIVATE entries
}
```

**Behavior:**
- `include_private=false` → PUBLIC and INTERNAL only (generic descriptions for INTERNAL)
- `include_private=true` → All levels with full details (for internal review)

## Database Queries with Privacy Filters

### Timecard Query (Client-Facing)
```python
# Only PUBLIC work sessions
stmt = (
    select(WorkSession)
    .where(WorkSession.project_id == project_id)
    .where(WorkSession.date >= start_date)
    .where(WorkSession.date <= end_date)
    .where(WorkSession.privacy_level == PrivacyLevel.PUBLIC)
)
```

### Internal Summary (Team View)
```python
# PUBLIC and INTERNAL work sessions
stmt = (
    select(WorkSession)
    .where(WorkSession.project_id == project_id)
    .where(WorkSession.date >= start_date)
    .where(WorkSession.date <= end_date)
    .where(
        WorkSession.privacy_level.in_([
            PrivacyLevel.PUBLIC,
            PrivacyLevel.INTERNAL
        ])
    )
)
```

### Full Access (Personal Memory)
```python
# All privacy levels
stmt = (
    select(WorkSession)
    .where(WorkSession.project_id == project_id)
    .where(WorkSession.date >= start_date)
    .where(WorkSession.date <= end_date)
    # No privacy_level filter
)
```

## Privacy Escalation Warning

**Changing from PRIVATE → PUBLIC:**

If a work session or note is changed from PRIVATE to PUBLIC, it could be included in future timecards or summaries. Consider:

1. Has this item been in past timecards?
2. Would exposing this item reveal previously hidden information?
3. Is the summary/description safe for external visibility?

**Best Practice:** Review content before escalating privacy level.

**Changing from PUBLIC → PRIVATE:**

Safe operation. Item will be excluded from future external reports but remains in the database.

## Multi-Entity Privacy Example

Scenario: Project "Website Redesign" for client "Acme Corp"

**Work Sessions:**
```
1. "Frontend development" - PUBLIC (safe for client)
2. "Internal architecture review" - INTERNAL (team only)
3. "Pricing discussion for phase 2" - PRIVATE (sensitive)
```

**Meetings:**
```
1. "Client demo" - PUBLIC (client attended)
2. "Team standup" - INTERNAL (internal only)
3. "Contract negotiation strategy" - PRIVATE (confidential)
```

**Notes:**
```
1. "Project goals documented" - PUBLIC (shareable)
2. "Technical debt identified" - INTERNAL (team knowledge)
3. "Client may have budget constraints" - PRIVATE (sensitive insight)
```

**Client-Facing Timecard Includes:**
- Work Session #1 only
- Meeting #1 only
- Note #1 only
- **Total: PUBLIC items only**

**Internal Team Report Includes:**
- Work Sessions #1, #2 (generic description for #2)
- Meetings #1, #2
- Notes #1, #2
- **Total: PUBLIC + INTERNAL items**

**Personal Query Returns:**
- All work sessions
- All meetings
- All notes
- **Total: Everything (single-user system)**

## Testing Privacy Filters

All privacy filtering logic must have comprehensive tests:

**Unit Tests:**
- Privacy enum values (PUBLIC, INTERNAL, PRIVATE)
- Default privacy levels on entity creation
- Privacy filter queries (SQLAlchemy filters)

**Integration Tests:**
- Timecard generation with privacy filters
- Summary generation with different privacy levels
- Query tool respecting privacy when appropriate

See `tests/integration/test_privacy_filters.py` for full test suite.

## Future Considerations

**Multi-User Privacy:**

If Mosaic becomes multi-user, privacy rules would need:
- User-specific privacy (Alice can't see Bob's PRIVATE items)
- Team-level privacy (shared INTERNAL items)
- Role-based access control (managers see more than ICs)

**Currently NOT implemented** - single-user system has full access to all data.

**Privacy Audit Log:**

Track when privacy levels are changed:
- Who changed it (if multi-user)
- When it was changed
- Old value → new value
- Reason for change

**Currently NOT implemented** - privacy changes are silent updates.
