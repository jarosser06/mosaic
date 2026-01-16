# Mosaic - Personal Work Memory & Time Tracking System

## Specification

## System Overview

**Mosaic** is a personal AI assistant system that tracks work throughout the day, maintains contextual memory about projects/people/meetings, and generates timecards. Primary interface is Claude Code with a persistent MCP server providing storage and notifications.

**Core Capabilities:**
- Log work sessions with half-hour precision for timecard generation
- Track meetings with attendees and project associations
- Maintain rich profiles of people, clients, and projects
- Flexible timestamped notes on any entity
- Context-aware reminders with macOS notifications
- Privacy-level controls on all information
- Support for multiple work contexts (employer, independent, personal)

## Architecture

**Components:**
1. **MCP Server** - Persistent daemon running in Docker, exposes tools via MCP protocol
2. **PostgreSQL Database** - Single source of truth, runs in separate Docker container with persistent volume
3. **macOS Notifications** - Native notification integration for reminders
4. **Claude Code** - Primary user interface for logging and querying

**MCP Server Responsibilities:**
- Handle all database operations
- Manage reminder scheduling and notification delivery
- Process queries with flexible filtering
- Maintain data integrity and privacy boundaries

**No external integrations in this server** - Calendar, email, git, etc. accessed via separate MCP servers

## User Profile & Initialization

### Onboarding Process

Conversational session with Claude Code to establish:
- User full name, contact details
- Current employer (creates employer entity)
- Self-employer entity (user's name, for independent/personal work)
- Work week definition (Mon-Fri, Sun-Sat, etc.)
- Working hours (for context only, not enforcement)
- Timezone
- Communication style and preferences for authenticity
- Work approach and values

### Profile Updates

- Manual trigger: user requests profile update
- Periodic reminder (quarterly): system suggests review if profile hasn't been updated in 3-4 months
- Not automatic - user stays in control

### User Profile Purpose

Provides context for Claude to maintain authenticity, determine privacy defaults based on work context, and understand user's working style.

## Core Entities

### Employers

Represents who work is being done on behalf of. Two types created during initialization:
- **Current employer** (e.g., "Launch")
- **Self-employer** (user's name, for independent/personal work)

Additional employers can be added if user changes jobs (employment history tracked but not automatically).

**Fields:**
- Name
- Type (current employer vs self)
- Contact information (optional)
- Notes (optional)

### Clients

Companies or individuals that work is done for. Can be "yourself" for personal projects.

**Fields:**
- Name
- Type (company vs individual)
- Contact information
- Notes/context
- Status (active, past)

### People

Individuals with rich profiles that persist across job changes.

**Fields:**
- Full name
- Email address
- Phone number
- LinkedIn URL
- Other metadata (role, expertise, etc.)
- Stakeholder flag (boolean)
- Employment history (timestamped relationships to clients/companies)

**Employment History:**
Temporal tracking - when Sarah moves from Client A to Client B, both relationships preserved with date ranges. Enables accurate historical queries.

**People can exist without company affiliation** (personal contacts).

### Projects

Work initiatives done on behalf of an employer for a client.

**Fields:**
- Name
- on_behalf_of (employer reference - Launch, self-employer entity, etc.)
- client (who work is for - can be yourself for personal projects)
- Description/context
- Status (active, paused, completed)
- Start date, end date (optional)

**Three project scenarios:**
1. **Employer work:** on_behalf_of = Launch, client = Launch's client
2. **Independent billable:** on_behalf_of = self-employer, client = independent client
3. **Personal:** on_behalf_of = self-employer, client = yourself

### Work Sessions

Individual time entries for project work.

**Fields:**
- Date
- Project reference
- Start time, end time
- Duration (rounded to nearest 0.5 hours)
- Summary/notes
- Privacy level

**Duration Rounding Rules:**
- 0:01 to 0:30 minutes → round up to 0.5 hours
- 0:31 to 1:00 minutes → round up to 1.0 hours
- Examples: 2:15 becomes 2.5 hours, 2:40 becomes 3.0 hours

**Storage vs Presentation:**
- Stored granularly (individual sessions throughout the day)
- Aggregated for timecard display (one line per project per day)
- Multiple sessions on same project same day: durations sum, summaries intelligently merged by Claude

### Meetings

Discussion events with people, optionally tied to projects.

**Fields:**
- Date/time
- Duration
- Attendees (list of people)
- Notes/summary
- Privacy level
- Project association (optional)
- on_behalf_of (employer reference - optional, required if project-associated)
- Meeting type (client call, internal, 1-on-1, team, etc.) - optional
- Location/medium (Zoom, phone, in-person) - optional

**Billable Time Rules:**
- If meeting has project association → on_behalf_of matches project's employer
- Meeting duration automatically creates work session for that project
- No project association → no billable time, just memory record

### Reminders

User-defined time-based or context-based notifications.

**Fields:**
- Due time
- Reminder text/context
- Recurrence settings (optional)
- Completed flag
- Related entity references (optional - person, project, etc.)

**User-controlled:**
- All reminder patterns defined by user via MCP tools
- No hardcoded reminder types
- System only delivers notifications at scheduled times

### Notes

Timestamped notes attachable to any entity.

**Fields:**
- Timestamp
- Note text
- Privacy level
- Entity type (person, client, project, meeting, employer, work_session, etc.)
- Entity ID (references specific entity)

**Usage:**
- Multiple timestamped notes per person (especially stakeholders)
- Client notes (billing preferences, context)
- Project notes (technical decisions, future plans)
- Meeting follow-ups
- Any entity can accumulate notes over time

## Privacy Model

### Three Privacy Levels

1. **Public** - Shareable externally (portfolio, blog, public discussions)
2. **Internal** - Work-related but not public (timecard summaries, project retrospectives, employer-specific)
3. **Private** - Sensitive information (frustrations, salary discussions, political issues)

### Privacy Application

- Every work session, meeting, and note has a privacy level
- Applies to summary content, not just existence of entity
- User specifies privacy level when logging

### Default Behavior

- System defaults to **private** for safety
- User can explicitly mark as internal or public when appropriate
- Better to be overcautious than accidentally expose sensitive info

### Query Privacy

- Queries default to showing everything (user is only user)
- When generating external outputs (timecards, summaries), Claude filters or asks about including private items
- Full-text search can be restricted by privacy level

## Business Rules

### Time Tracking

- **Half-hour precision required** for timecard accuracy
- Work sessions stored individually, aggregated daily per project for timecard
- Same project, same day → one timecard line with summed hours and merged summary

### Week Boundaries

- Defined during onboarding (Monday-Friday, Sunday-Saturday, etc.)
- "This week" queries respect user's work week definition
- Critical for timecard generation and week-based queries

### Day Tracking

- All timestamps timezone-aware
- "Today" always means current local date
- Supports retrospective logging with explicit date specification
- System handles day boundaries correctly (11:55pm vs 12:10am)

### Project Creation

- When new project mentioned: "I don't have a project called X yet, tell me about it"
- Prompt for: name, client, on_behalf_of, description, status
- Then tracked going forward

### Timecard Generation

- "Generate timecard for [employer]" → filters on_behalf_of
- "Show independent billable work" → on_behalf_of = self AND client ≠ self  
- "Show personal projects" → on_behalf_of = self AND client = self
- Format: one line per project per day with hours and merged summary

### Meeting-Project Association

- If meeting tied to project → automatically creates work session with meeting duration
- on_behalf_of inherited from project
- Meeting duration counts as billable time for that employer/client

## MCP Server Tools

### Logging Tools

- **log_work_session** - Record work with date, project, duration, summary, privacy
- **log_meeting** - Record meeting with attendees, notes, optional project association
- **add_person** - Create person profile with employment details
- **add_client** - Create client entity
- **add_project** - Create project with on_behalf_of and client relationships
- **add_employer** - Create employer entity (rare - mostly done in onboarding)
- **add_note** - Attach timestamped note to any entity
- **add_reminder** - Create reminder with time, recurrence, context

### Query Tool

- **query** - Flexible search with parameters:
  - Entity types to query
  - Time ranges (absolute or relative)
  - Entity filters (person, client, project, employer IDs)
  - Privacy level filters
  - Full-text search terms
  - Status filters
  - Aggregation options (sum hours, group by project, etc.)

Claude interprets natural language and constructs appropriate filters.

### Update Tools

- **update_work_session** - Edit duration, summary, privacy
- **update_meeting** - Modify meeting details
- **update_person** - Edit person profile, employment history
- **update_client** - Modify client information
- **update_project** - Change project details, status
- **update_note** - Edit note text or privacy
- **complete_reminder** - Mark reminder as done
- **snooze_reminder** - Reschedule reminder
- **update_user_profile** - Modify user profile during updates

### Notification Tool

- **trigger_notification** - Internal tool for scheduled reminder delivery to macOS

## Deployment

### Docker Composition

- MCP Server container (persistent daemon)
- PostgreSQL container (separate, with persistent volume)
- Network connection between containers

### MCP Server Includes

- MCP protocol handler
- Database client (Postgres connection)
- Job scheduler for reminder checks (implementation detail - standard Python framework)
- macOS notification integration

### Data Persistence

- PostgreSQL data volume mounted
- Survives container restarts
- Postgres is single source of truth - no server state outside database

### Configuration

- Database connection string
- User timezone (from onboarding)
- Work week definition (from onboarding)
- Notification settings

## User Flows

### Daily Work Logging

1. User tells Claude Code: "Working on auth module for 3 hours, fixed token refresh bug"
2. Claude Code calls log_work_session tool
3. System stores individual work session with timestamp
4. User can query later: "What did I work on today?"
5. End of week: "Generate timecard for Launch" - aggregates daily by project

### Meeting Logging

1. User: "Just finished client meeting about Project X, discussed timeline with Sarah"
2. Claude Code calls log_meeting tool with project association
3. System creates meeting record and auto-generates work session for Project X
4. Meeting duration becomes billable time on Project X timecard

### New Person Encountered

1. User mentions "Bob" for first time
2. System prompts: "I don't have Bob in my records, tell me about him"
3. User provides: full name, company, role, email, stakeholder status
4. System creates person entity with initial employment relationship
5. Notes can be added over time as user learns more

### Reminder Flow

1. User: "Remind me Friday at 2pm to follow up with Sarah about the spec"
2. Claude Code calls add_reminder tool
3. MCP server scheduler tracks due time
4. Friday at 2pm: server triggers macOS notification
5. User sees notification, can complete or snooze via Claude Code

### Privacy-Aware Querying

1. User: "Summarize my work this week for my manager"
2. Claude Code queries work sessions for the week
3. System includes public and internal items, excludes private
4. Claude generates summary appropriate for manager audience
5. Or Claude asks: "Should I exclude private items from this summary?"

### Retrospective Logging

1. User (11pm): "Oh, I forgot to log - I worked on the dashboard yesterday afternoon from 2-4pm"
2. Claude Code logs with explicit date (yesterday) and time range
3. System correctly attributes to previous day
4. Timecard for that week includes the retrospective entry

---

**End of Specification**

This document captures all design decisions and is ready for implementation.
