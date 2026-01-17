# Mosaic Database Schema

Complete reference for all 11 entities, relationships, enums, and indexes in the Mosaic work memory system.

## Overview

Mosaic uses PostgreSQL 16 with SQLAlchemy 2.0 async ORM. All models inherit from `Base` and use `TimestampMixin` for automatic `created_at`/`updated_at` tracking.

**Field Naming Convention:** When querying via the API/MCP tools, use schema field names (e.g., `on_behalf_of`), not internal database field names (e.g., `on_behalf_of_id`). Where these differ, both are documented below.

## Entities

### 1. User

Single-user system configuration and preferences.

**Table:** `users`

**Fields:**
- `id` (Integer, PK)
- `name` (String 255, NOT NULL, indexed)
- `email` (String 255, unique, indexed)
- `timezone` (String 50, default: UTC)
- `default_week_boundary` (Enum: WeekBoundary, default: mon-fri)
- `default_privacy_level` (Enum: PrivacyLevel, default: private)
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Note:** Only one user record exists in the system.

---

### 2. Employer

Organizations you work for (employer of record).

**Table:** `employers`

**Fields:**
- `id` (Integer, PK)
- `name` (String 255, NOT NULL, indexed)
- `notes` (String 2000)
- `tags` (StringArray, default: [])
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Relationships:**
- `projects` → one-to-many with Project (on_behalf_of)

**Business Rule:** Projects can optionally have an employer (on_behalf_of_id).

---

### 3. Client

Companies or individuals that work is done for.

**Table:** `clients`

**Fields:**
- `id` (Integer, PK)
- `name` (String 255, NOT NULL, indexed)
- `type` (Enum: ClientType, NOT NULL) - company or individual
- `status` (Enum: ClientStatus, default: active) - active or past
- `contact_person_id` (Integer, FK → people.id, ON DELETE SET NULL)
- `notes` (String 2000)
- `tags` (StringArray, default: [])
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Relationships:**
- `contact_person` → many-to-one with Person
- `projects` → one-to-many with Project
- `employments` → one-to-many with EmploymentHistory

**Business Rule:** Client status can be active or past. Past clients are retained for historical reporting.

---

### 4. Project

Work initiatives done on behalf of an employer for a client.

**Table:** `projects`

**Fields:**
- `id` (Integer, PK)
- `name` (String 255, NOT NULL, indexed)
- `on_behalf_of` (Integer, FK → employers.id, ON DELETE RESTRICT)
  - *Database field: `on_behalf_of_id`*
  - *API/Query field: `on_behalf_of`*
- `client_id` (Integer, FK → clients.id, ON DELETE RESTRICT, NOT NULL)
- `description` (String 2000)
- `status` (Enum: ProjectStatus, default: active) - active, paused, or completed
- `start_date` (Date)
- `end_date` (Date)
- `tags` (StringArray, default: [])
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Relationships:**
- `employer` → many-to-one with Employer (on_behalf_of)
- `client` → many-to-one with Client
- `work_sessions` → one-to-many with WorkSession
- `meetings` → one-to-many with Meeting

**Business Rules:**
- Must have a client
- May optionally have an employer (on_behalf_of)
- Status tracks lifecycle: active → paused → completed

---

### 5. WorkSession

Individual time entries for project work with half-hour precision.

**Table:** `work_sessions`

**Fields:**
- `id` (Integer, PK)
- `project_id` (Integer, FK → projects.id, ON DELETE RESTRICT, NOT NULL)
- `date` (Date, NOT NULL, indexed)
- `start_time` (DateTime with timezone, NOT NULL)
- `end_time` (DateTime with timezone, NOT NULL)
- `duration_hours` (Numeric 4,1, NOT NULL)
- `summary` (String 2000)
- `privacy_level` (Enum: PrivacyLevel, default: private)
- `tags` (StringArray, default: [])
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Relationships:**
- `project` → many-to-one with Project

**Indexes:**
- Composite index: `(project_id, date)`

**Business Rules:**
- Duration is calculated using half-hour rounding (see time_tracking_rules.md)
- Privacy level filters what appears in timecards and external summaries
- Auto-generated from meetings with project association

---

### 6. Meeting

Discussion events with people, optionally tied to projects.

**Table:** `meetings`

**Fields:**
- `id` (Integer, PK)
- `title` (String 500, NOT NULL)
- `start_time` (DateTime with timezone, NOT NULL, indexed)
- `duration_minutes` (Integer, NOT NULL)
- `summary` (String 2000)
- `privacy_level` (Enum: PrivacyLevel, default: private)
- `project_id` (Integer, FK → projects.id, ON DELETE SET NULL)
- `meeting_type` (String 100)
- `location` (String 255)
- `tags` (StringArray, default: [])
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Relationships:**
- `project` → many-to-one with Project
- `attendees` → one-to-many with MeetingAttendee (cascade delete)

**Business Rules:**
- If meeting has project association, auto-generates WorkSession with same duration
- Privacy level applies to meeting details in summaries

---

### 7. MeetingAttendee

Association table for meeting-person many-to-many relationship.

**Table:** `meeting_attendees`

**Fields:**
- `id` (Integer, PK)
- `meeting_id` (Integer, FK → meetings.id, ON DELETE CASCADE, NOT NULL)
- `person_id` (Integer, FK → people.id, ON DELETE CASCADE, NOT NULL)

**Relationships:**
- `meeting` → many-to-one with Meeting
- `person` → many-to-one with Person

---

### 8. Person

Individuals with rich profiles that persist across job changes.

**Table:** `people`

**Fields:**
- `id` (Integer, PK)
- `full_name` (String 255, NOT NULL, indexed)
- `email` (String 255, indexed)
- `phone` (String 50)
- `linkedin_url` (String 500)
- `is_stakeholder` (Boolean, default: false)
- `company` (String 200)
- `title` (String 200)
- `notes` (Text)
- `tags` (StringArray, default: [])
- `additional_info` (JSONB) - flexible key-value storage
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Relationships:**
- `employments` → one-to-many with EmploymentHistory (cascade delete)
- `meeting_attendances` → one-to-many with MeetingAttendee

**Business Rules:**
- Person profiles persist across job changes
- Employment history tracked separately in EmploymentHistory
- `is_stakeholder` marks important decision-makers

---

### 9. EmploymentHistory

Temporal tracking of person-client relationships.

**Table:** `employment_history`

**Fields:**
- `id` (Integer, PK)
- `person_id` (Integer, FK → people.id, ON DELETE CASCADE, NOT NULL)
- `client_id` (Integer, FK → clients.id, ON DELETE CASCADE, NOT NULL)
- `role` (String 255)
- `start_date` (Date, NOT NULL)
- `end_date` (Date)

**Relationships:**
- `person` → many-to-one with Person
- `client` → many-to-one with Client

**Business Rules:**
- Tracks when a person worked for a client
- `end_date` is NULL for current employment
- Enables answering "who did I work with at Company X?"

---

### 10. Note

Timestamped notes attachable to any entity type.

**Table:** `notes`

**Fields:**
- `id` (Integer, PK)
- `text` (String 5000, NOT NULL)
- `privacy_level` (Enum: PrivacyLevel, default: private)
- `entity_type` (Enum: EntityType) - person, client, project, employer, work_session, meeting, reminder
- `entity_id` (Integer)
- `tags` (StringArray, default: [])
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Indexes:**
- Composite index: `(entity_type, entity_id)`

**Business Rules:**
- Can be attached to any entity via polymorphic entity_type/entity_id
- Can also be standalone (entity_type/entity_id NULL)
- Privacy level filters note visibility in summaries

---

### 11. Reminder

Time-based notifications with optional recurrence and entity linking.

**Table:** `reminders`

**Fields:**
- `id` (Integer, PK)
- `reminder_time` (DateTime with timezone, NOT NULL, indexed)
- `message` (String 1000, NOT NULL)
- `is_completed` (Boolean, default: false)
- `tags` (StringArray, default: [])
- `recurrence_config` (JSONB) - flexible recurrence rules
- `related_entity_type` (Enum: EntityType)
- `related_entity_id` (Integer)
- `snoozed_until` (DateTime with timezone)
- `created_at` (DateTime with timezone)
- `updated_at` (DateTime with timezone)

**Indexes:**
- Composite index: `(reminder_time, is_completed)`

**Business Rules:**
- Integrates with macOS notification system
- Recurrence handled via APScheduler
- Can be linked to any entity for context

---

## Enums

### PrivacyLevel
```python
PUBLIC = "public"      # Shareable externally
INTERNAL = "internal"  # Shareable within organization
PRIVATE = "private"    # Sensitive, filtered from timecards
```

**Applies to:** WorkSession, Meeting, Note

### ProjectStatus
```python
ACTIVE = "active"
PAUSED = "paused"
COMPLETED = "completed"
```

### ClientStatus
```python
ACTIVE = "active"
PAST = "past"
```

### ClientType
```python
COMPANY = "company"
INDIVIDUAL = "individual"
```

### WeekBoundary
```python
MONDAY_FRIDAY = "mon-fri"
SUNDAY_SATURDAY = "sun-sat"
MONDAY_SUNDAY = "mon-sun"
```

**Used for:** Timecard generation week boundaries

### EntityType
```python
PERSON = "person"
CLIENT = "client"
PROJECT = "project"
EMPLOYER = "employer"
WORK_SESSION = "work_session"
MEETING = "meeting"
REMINDER = "reminder"
```

**Used for:** Polymorphic note and reminder attachments

---

## Custom Types

### StringArray
PostgreSQL text array for tags. Stored as `TEXT[]`, maps to Python `list[str]`.

### JSONB
PostgreSQL JSONB for flexible key-value storage. Maps to Python `dict[str, Any]`.

---

## Key Relationships

### Work Tracking Chain
```
Employer (optional) → Project → WorkSession
                              ↘ Meeting (with auto WorkSession)
Client (required) → Project
```

### People & Employment
```
Person ↔ EmploymentHistory ↔ Client
Person ↔ MeetingAttendee ↔ Meeting
```

### Polymorphic Attachments
```
Note → (entity_type, entity_id) → Any Entity
Reminder → (related_entity_type, related_entity_id) → Any Entity
```

---

## Indexes Summary

Performance-critical indexes:
- `users.name` (lookup)
- `users.email` (unique login)
- `employers.name` (search)
- `clients.name` (search)
- `projects.name` (search)
- `work_sessions.date` (time-based queries)
- `work_sessions(project_id, date)` (composite for project reports)
- `meetings.start_time` (chronological queries)
- `people.full_name` (search)
- `people.email` (contact lookup)
- `notes(entity_type, entity_id)` (polymorphic lookup)
- `reminders(reminder_time, is_completed)` (active reminder queries)

---

## Migration Management

Migrations are managed via Alembic with async support:
```bash
# Generate migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

All migrations are auto-formatted with black after generation.
