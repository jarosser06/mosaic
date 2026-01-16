# Workflow Patterns

Common workflows and multi-tool interaction patterns for Mosaic MCP server.

## Overview

Mosaic supports complex workflows that span multiple MCP tools. This guide documents common patterns and best practices for composing tools to accomplish real-world tasks.

## Core Workflows

### 1. Client Onboarding

**Goal:** Set up a new client with first project

**Steps:**
1. Create client entity
2. Add contact person
3. Create initial project
4. Set up reminders for key milestones

**Tool Sequence:**
```
1. create_client
   Input: {
     "name": "Acme Corp",
     "type": "company",
     "status": "active"
   }
   Output: { "id": 123, ... }

2. create_person
   Input: {
     "full_name": "Alice Smith",
     "email": "alice@acme.com",
     "company": "Acme Corp",
     "title": "Engineering Manager",
     "is_stakeholder": true
   }
   Output: { "id": 456, ... }

3. update_client
   Input: {
     "client_id": 123,
     "updates": { "contact_person_id": 456 }
   }

4. create_project
   Input: {
     "name": "Website Redesign",
     "client_id": 123,
     "description": "Modernize company website",
     "status": "active"
   }
   Output: { "id": 789, ... }

5. create_reminder
   Input: {
     "reminder_time": "2026-01-20T09:00:00Z",
     "message": "Check in on Website Redesign kickoff",
     "related_entity_type": "project",
     "related_entity_id": 789
   }
```

**Expected Outcome:**
- New client with contact person
- Active project ready for time tracking
- Reminder set for follow-up

---

### 2. Daily Work Logging

**Goal:** Log a day's work across multiple projects

**Steps:**
1. Log work sessions for each project
2. Add contextual notes
3. Set reminders for follow-ups

**Tool Sequence:**
```
1. log_work_session (Project A)
   Input: {
     "project_id": 10,
     "start_time": "2026-01-15T09:00:00Z",
     "end_time": "2026-01-15T11:30:00Z",
     "summary": "Frontend component development",
     "privacy_level": "public"
   }

2. create_note (Project A context)
   Input: {
     "text": "Completed authentication flow, needs QA review",
     "entity_type": "project",
     "entity_id": 10,
     "privacy_level": "internal"
   }

3. log_work_session (Project B)
   Input: {
     "project_id": 11,
     "start_time": "2026-01-15T13:00:00Z",
     "end_time": "2026-01-15T16:00:00Z",
     "summary": "API integration testing",
     "privacy_level": "public"
   }

4. create_reminder (Follow-up)
   Input: {
     "reminder_time": "2026-01-16T10:00:00Z",
     "message": "Follow up on QA review for auth flow",
     "related_entity_type": "project",
     "related_entity_id": 10
   }
```

**Expected Outcome:**
- Work logged for multiple projects
- Contextual notes captured
- Follow-up reminders set

---

### 3. Meeting Capture with Auto Work Session

**Goal:** Log a client meeting that auto-generates billable time

**Steps:**
1. Create meeting with project association
2. Add attendees
3. System auto-generates work session
4. Add meeting notes

**Tool Sequence:**
```
1. log_meeting
   Input: {
     "title": "Website Redesign Kickoff",
     "start_time": "2026-01-15T10:00:00Z",
     "duration_minutes": 90,
     "project_id": 789,  // PROJECT ASSOCIATION KEY
     "privacy_level": "public",
     "attendee_ids": [456, 457]  // Alice + Bob
   }
   Output: {
     "id": 234,
     "auto_work_session_id": 567  // AUTO-GENERATED
   }

2. create_note (Meeting summary)
   Input: {
     "text": "Agreed on timeline: 6 weeks. Alice to provide brand assets.",
     "entity_type": "meeting",
     "entity_id": 234,
     "privacy_level": "internal"
   }

3. query (Verify work session created)
   Input: { "query": "Work sessions on Website Redesign today" }
   Output: {
     "results": [
       {
         "type": "work_session",
         "items": [
           {
             "id": 567,
             "duration_hours": "1.5",  // 90 min → 1.5 hours
             "summary": "Website Redesign Kickoff"
           }
         ]
       }
     ]
   }
```

**Expected Outcome:**
- Meeting logged with attendees
- Work session auto-created (90 min → 1.5 billable hours)
- Meeting notes captured for reference

**Key Rule:** Meeting → WorkSession only happens when `project_id` is set.

---

### 4. Timecard Generation

**Goal:** Generate client-ready timecard for invoicing

**Steps:**
1. Query work sessions for project/date range
2. Filter by privacy level (PUBLIC for client visibility)
3. Generate timecard summary
4. Review and adjust privacy levels if needed

**Tool Sequence:**
```
1. generate_timecard
   Input: {
     "project_id": 789,
     "start_date": "2026-01-13",
     "end_date": "2026-01-17",
     "include_private": false  // CLIENT-FACING
   }
   Output: {
     "project_name": "Website Redesign",
     "total_hours": "28.5",
     "entries": [
       {
         "date": "2026-01-13",
         "hours": "4.0",
         "description": "Frontend development"
       },
       {
         "date": "2026-01-14",
         "hours": "6.5",
         "description": "API integration"
       },
       // ... more entries (PRIVATE entries excluded)
     ]
   }

2. query (Internal audit - all privacy levels)
   Input: {
     "query": "All work on Website Redesign this week"
   }
   Output: {
     // Includes PRIVATE entries for internal comparison
   }

3. update_work_session (Adjust privacy if needed)
   Input: {
     "work_session_id": 567,
     "updates": {
       "privacy_level": "internal"  // Change from private to internal
     }
   }
```

**Expected Outcome:**
- Client-ready timecard with PUBLIC entries only
- Internal audit shows full hours (all privacy levels)
- Privacy levels adjusted as needed

---

### 5. Project Status Summary

**Goal:** Generate comprehensive project summary for client

**Steps:**
1. Query all project-related entities
2. Aggregate totals
3. Filter by privacy for client view

**Tool Sequence:**
```
1. query (All project work)
   Input: {
     "query": "Everything related to Website Redesign project"
   }
   Output: {
     "results": [
       { "type": "work_session", "count": 23 },
       { "type": "meeting", "count": 8 },
       { "type": "note", "count": 12 },
       { "type": "reminder", "count": 2 }
     ]
   }

2. query (Public work only for client)
   Input: {
     "query": "Public work sessions on Website Redesign"
   }
   Output: {
     "summary": "Found 18 public work sessions totaling 67.5 hours",
     // ... details
   }

3. query (Stakeholder meetings)
   Input: {
     "query": "Meetings on Website Redesign with stakeholders"
   }
   Output: {
     // Meetings with is_stakeholder=true attendees
   }
```

**Expected Outcome:**
- Internal view: All project data (45 items)
- Client view: Public items only (18 work sessions, 5 meetings)
- Stakeholder engagement metrics

---

### 6. People Network Mapping

**Goal:** Understand who you've worked with and where

**Steps:**
1. Query people with employment history
2. Map person → client relationships
3. Identify key stakeholders

**Tool Sequence:**
```
1. query
   Input: { "query": "All people I've met with this year" }
   Output: {
     "results": [
       { "type": "person", "count": 45, "items": [...] }
     ]
   }

2. query (Employment at specific client)
   Input: { "query": "Who works at Acme Corp?" }
   Output: {
     "results": [
       {
         "type": "person",
         "items": [
           {
             "full_name": "Alice Smith",
             "role": "Engineering Manager",
             "start_date": "2024-03-01",
             "current": true
           },
           // ... more people
         ]
       }
     ]
   }

3. query (Stakeholders only)
   Input: { "query": "Show all stakeholders" }
   Output: {
     "results": [
       {
         "type": "person",
         "items": [
           {
             "full_name": "John Executive",
             "is_stakeholder": true,
             "company": "Acme Corp"
           }
         ]
       }
     ]
   }
```

**Expected Outcome:**
- Full people network (45 people)
- Current Acme Corp employees (4 people)
- Key stakeholders identified (6 people)

---

### 7. Reminder Management with Recurrence

**Goal:** Set up recurring reminders for weekly standup

**Steps:**
1. Create recurring reminder
2. Update reminder config
3. Complete and snooze reminders

**Tool Sequence:**
```
1. create_reminder
   Input: {
     "reminder_time": "2026-01-20T09:00:00Z",
     "message": "Weekly team standup",
     "recurrence_config": {
       "frequency": "weekly",
       "day_of_week": "monday",
       "time": "09:00"
     }
   }
   Output: { "id": 101, ... }

2. query (Upcoming reminders)
   Input: { "query": "Upcoming reminders next 7 days" }
   Output: {
     "results": [
       {
         "type": "reminder",
         "items": [
           {
             "id": 101,
             "reminder_time": "2026-01-20T09:00:00Z",
             "message": "Weekly team standup",
             "is_completed": false
           }
         ]
       }
     ]
   }

3. update_reminder (Complete)
   Input: {
     "reminder_id": 101,
     "updates": { "is_completed": true }
   }

4. update_reminder (Snooze)
   Input: {
     "reminder_id": 102,
     "updates": {
       "snoozed_until": "2026-01-20T14:00:00Z"
     }
   }
```

**Expected Outcome:**
- Recurring weekly reminder set
- Completed reminders tracked
- Snoozed reminders delayed

---

### 8. Privacy Audit and Cleanup

**Goal:** Review privacy levels before sharing timecard

**Steps:**
1. Query all work on project
2. Identify PRIVATE entries
3. Review and reclassify as needed

**Tool Sequence:**
```
1. query (All work sessions)
   Input: {
     "query": "All work sessions on Website Redesign this month"
   }
   Output: {
     "results": [
       {
         "type": "work_session",
         "items": [
           { "id": 501, "privacy_level": "public", ... },
           { "id": 502, "privacy_level": "private", ... },
           { "id": 503, "privacy_level": "internal", ... }
         ]
       }
     ]
   }

2. query (Private entries only)
   Input: {
     "query": "Private work sessions on Website Redesign"
   }
   Output: {
     "summary": "Found 4 private work sessions (8.5 hours)",
     "results": [/* private entries */]
   }

3. update_work_session (Reclassify safe items)
   Input: {
     "work_session_id": 502,
     "updates": {
       "privacy_level": "public",
       "summary": "Client communication" // Generic description
     }
   }

4. generate_timecard (Verify billable hours)
   Input: {
     "project_id": 789,
     "start_date": "2026-01-01",
     "end_date": "2026-01-31",
     "include_private": false
   }
   Output: {
     "total_hours": "87.5"  // Increased after privacy changes
   }
```

**Expected Outcome:**
- Identified 4 PRIVATE entries (8.5 hours)
- Reclassified 1 entry to PUBLIC
- Timecard now shows 87.5 hours (was 79.0)

---

### 9. Project Closure

**Goal:** Close completed project and archive data

**Steps:**
1. Update project status
2. Generate final timecard
3. Create summary notes
4. Archive reminders

**Tool Sequence:**
```
1. update_project
   Input: {
     "project_id": 789,
     "updates": {
       "status": "completed",
       "end_date": "2026-01-31"
     }
   }

2. generate_timecard (Final billing)
   Input: {
     "project_id": 789,
     "start_date": "2026-01-01",
     "end_date": "2026-01-31",
     "include_private": false
   }
   Output: {
     "total_hours": "142.5"
   }

3. create_note (Project retrospective)
   Input: {
     "text": "Project completed on time. Client very satisfied. Potential for Phase 2.",
     "entity_type": "project",
     "entity_id": 789,
     "privacy_level": "internal"
   }

4. query (Archive related reminders)
   Input: {
     "query": "Reminders related to Website Redesign"
   }
   Output: {
     "results": [/* related reminders */]
   }

5. update_reminder (Complete all project reminders)
   Input: {
     "reminder_id": 101,
     "updates": { "is_completed": true }
   }
```

**Expected Outcome:**
- Project marked completed
- Final timecard generated (142.5 hours)
- Retrospective notes captured
- All project reminders completed

---

### 10. Multi-Project Reporting

**Goal:** Generate summary across all active projects

**Steps:**
1. Query all active projects
2. Aggregate hours by project
3. Identify projects needing attention

**Tool Sequence:**
```
1. query (Active projects)
   Input: { "query": "Active projects" }
   Output: {
     "results": [
       {
         "type": "project",
         "items": [
           { "id": 10, "name": "Website Redesign" },
           { "id": 11, "name": "API Integration" },
           { "id": 12, "name": "Mobile App" }
         ]
       }
     ]
   }

2. query (Hours by project this month)
   Input: { "query": "Total hours per project this month" }
   Output: {
     "results": [
       {
         "type": "project_summary",
         "items": [
           { "project_name": "Website Redesign", "total_hours": "42.5" },
           { "project_name": "API Integration", "total_hours": "31.0" },
           { "project_name": "Mobile App", "total_hours": "5.0" }  // LOW
         ]
       }
     ]
   }

3. query (Work sessions on low-activity project)
   Input: {
     "query": "Work sessions on Mobile App this month"
   }
   Output: {
     "summary": "Found 2 work sessions totaling 5.0 hours",
     // Identify why activity is low
   }

4. create_reminder (Follow-up)
   Input: {
     "reminder_time": "2026-02-01T09:00:00Z",
     "message": "Check status of Mobile App project (low activity)",
     "related_entity_type": "project",
     "related_entity_id": 12
   }
```

**Expected Outcome:**
- 3 active projects identified
- Hours aggregated: 42.5, 31.0, 5.0
- Low-activity project flagged
- Follow-up reminder set

---

## Best Practices

### 1. Privacy-First Logging

**Always consider privacy level when logging work:**

✅ **Good:**
```
log_work_session({
  ...,
  "summary": "Frontend development",
  "privacy_level": "public"  // EXPLICIT
})
```

❌ **Risky:**
```
log_work_session({
  ...,
  "summary": "Fixed security vulnerability in auth system"
  // Defaults to PRIVATE, may miss billable hours
})
```

### 2. Meeting-to-Work-Session Auto-Generation

**Use project association to auto-bill meeting time:**

✅ **Good (auto-generates work session):**
```
log_meeting({
  "title": "Client Demo",
  "duration_minutes": 60,
  "project_id": 789  // AUTO-GENERATES WORK SESSION
})
```

❌ **Missed Opportunity:**
```
log_meeting({
  "title": "Client Demo",
  "duration_minutes": 60
  // No project_id, no auto work session
})
```

### 3. Tag Consistently

**Use consistent tags for queryability:**

✅ **Good:**
```
Tags: ["frontend", "react", "ui"]
```

❌ **Inconsistent:**
```
Tags: ["frontend", "Front-End", "FE", "ui-work"]
```

### 4. Link Entities

**Use entity relationships for rich context:**

✅ **Good:**
```
create_note({
  "text": "Client wants feature X prioritized",
  "entity_type": "meeting",
  "entity_id": 234  // LINKED TO MEETING
})
```

❌ **Lost Context:**
```
create_note({
  "text": "Client wants feature X prioritized"
  // No entity link, context lost
})
```

### 5. Query Before Update

**Verify current state before making changes:**

✅ **Good:**
```
1. query({ "query": "Show project Website Redesign" })
2. update_project({ ... })  // Based on current state
```

❌ **Risky:**
```
update_project({ ... })  // Blind update, may overwrite data
```

---

## Error Handling Patterns

### Handling Missing Entities

```
1. create_project (Requires client_id)
   Error: "Client ID 999 not found"

2. Create client first:
   create_client({ "name": "New Client" })
   Output: { "id": 123 }

3. Retry project creation:
   create_project({ "client_id": 123, ... })
   Success
```

### Handling Validation Errors

```
1. log_work_session
   Input: {
     "start_time": "2026-01-15T14:00:00Z",
     "end_time": "2026-01-15T12:00:00Z"  // BEFORE start
   }
   Error: "end_time must be after start_time"

2. Correct and retry:
   Input: {
     "start_time": "2026-01-15T12:00:00Z",
     "end_time": "2026-01-15T14:00:00Z"
   }
   Success
```

---

## Performance Considerations

### Batch Queries

**Use broad queries instead of multiple specific queries:**

✅ **Efficient:**
```
query({ "query": "Everything related to Website Redesign" })
// Single query returns all entity types
```

❌ **Inefficient:**
```
query({ "query": "Work sessions on Website Redesign" })
query({ "query": "Meetings on Website Redesign" })
query({ "query": "Notes on Website Redesign" })
// Three separate queries
```

### Date Range Limits

**Be specific with date ranges to avoid large result sets:**

✅ **Efficient:**
```
query({ "query": "Work sessions from Jan 1 to Jan 15" })
```

❌ **Inefficient:**
```
query({ "query": "All work sessions" })
// Unbounded query, may return thousands of results
```

---

## Testing Workflows

Integration tests should cover complete workflows end-to-end:

**Example: Meeting → WorkSession Auto-Generation**
```python
async def test_meeting_creates_work_session():
    # 1. Create project
    project = await create_project(...)

    # 2. Log meeting with project
    meeting = await log_meeting(project_id=project.id, ...)

    # 3. Verify work session auto-created
    work_sessions = await query_work_sessions(project_id=project.id)
    assert len(work_sessions) == 1
    assert work_sessions[0].duration_hours == calculate_rounded(meeting.duration_minutes)
```

See `tests/integration/test_workflows.py` for full workflow test suite.
