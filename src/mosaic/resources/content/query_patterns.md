# Query Patterns

Common query examples and expected outputs for the Mosaic MCP query tool.

## Overview

The `query` MCP tool accepts natural language queries and returns structured results grouped by entity type. This guide provides examples of effective query patterns and their expected outputs.

## Time-Based Queries

### Last Week
```
Query: "What did I work on last week?"

Expected Output:
{
  "summary": "Last week you worked on 3 projects totaling 28.5 hours",
  "results": [
    {
      "type": "work_session",
      "count": 12,
      "items": [
        {
          "id": 101,
          "project_name": "Website Redesign",
          "date": "2026-01-13",
          "duration_hours": "3.5",
          "summary": "Frontend development"
        },
        // ... more sessions
      ]
    }
  ]
}
```

### This Month
```
Query: "Show me all meetings this month"

Expected Output:
{
  "summary": "Found 8 meetings in January 2026",
  "results": [
    {
      "type": "meeting",
      "count": 8,
      "items": [
        {
          "id": 201,
          "title": "Client Demo",
          "start_time": "2026-01-15T10:00:00Z",
          "duration_minutes": 60,
          "attendees": ["Alice Smith", "Bob Jones"]
        },
        // ... more meetings
      ]
    }
  ]
}
```

### Specific Date Range
```
Query: "Work sessions between December 1 and December 15"

Expected Output:
{
  "summary": "Found 15 work sessions totaling 42.0 hours from Dec 1-15",
  "results": [
    {
      "type": "work_session",
      "count": 15,
      "items": [/* work sessions */]
    }
  ]
}
```

## Entity-Specific Queries

### Projects
```
Query: "Active projects for Acme Corp"

Expected Output:
{
  "summary": "Found 2 active projects for client Acme Corp",
  "results": [
    {
      "type": "project",
      "count": 2,
      "items": [
        {
          "id": 10,
          "name": "Website Redesign",
          "status": "active",
          "client_name": "Acme Corp",
          "start_date": "2026-01-01"
        },
        {
          "id": 11,
          "name": "API Integration",
          "status": "active",
          "client_name": "Acme Corp",
          "start_date": "2026-01-10"
        }
      ]
    }
  ]
}
```

### People
```
Query: "Who did I meet with last month?"

Expected Output:
{
  "summary": "You met with 12 people in December 2025",
  "results": [
    {
      "type": "person",
      "count": 12,
      "items": [
        {
          "id": 5,
          "full_name": "Alice Smith",
          "company": "Acme Corp",
          "title": "Engineering Manager",
          "meeting_count": 4
        },
        // ... more people
      ]
    }
  ]
}
```

### Clients
```
Query: "Show all active clients"

Expected Output:
{
  "summary": "Found 5 active clients",
  "results": [
    {
      "type": "client",
      "count": 5,
      "items": [
        {
          "id": 1,
          "name": "Acme Corp",
          "type": "company",
          "status": "active",
          "project_count": 2
        },
        // ... more clients
      ]
    }
  ]
}
```

## Relationship-Based Queries

### Work on Specific Project
```
Query: "All work sessions for Website Redesign project"

Expected Output:
{
  "summary": "Found 23 work sessions totaling 87.5 hours on Website Redesign",
  "results": [
    {
      "type": "work_session",
      "count": 23,
      "items": [
        {
          "id": 150,
          "project_name": "Website Redesign",
          "date": "2026-01-15",
          "duration_hours": "4.0",
          "summary": "Component refactoring"
        },
        // ... more sessions
      ]
    }
  ]
}
```

### Meetings with Specific Person
```
Query: "Meetings with Alice Smith"

Expected Output:
{
  "summary": "Found 6 meetings with Alice Smith",
  "results": [
    {
      "type": "meeting",
      "count": 6,
      "items": [
        {
          "id": 220,
          "title": "Sprint Planning",
          "start_time": "2026-01-15T09:00:00Z",
          "project_name": "Website Redesign",
          "other_attendees": ["Bob Jones"]
        },
        // ... more meetings
      ]
    }
  ]
}
```

### Employment History
```
Query: "Who works at Acme Corp?"

Expected Output:
{
  "summary": "Found 4 people currently employed at Acme Corp",
  "results": [
    {
      "type": "person",
      "count": 4,
      "items": [
        {
          "id": 5,
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
```

## Tag-Based Queries

### Work Sessions by Tag
```
Query: "Work sessions tagged with 'frontend'"

Expected Output:
{
  "summary": "Found 15 work sessions tagged 'frontend' totaling 52.5 hours",
  "results": [
    {
      "type": "work_session",
      "count": 15,
      "items": [/* sessions with 'frontend' tag */]
    }
  ]
}
```

### Projects by Tag
```
Query: "Show projects tagged 'urgent'"

Expected Output:
{
  "summary": "Found 2 projects tagged 'urgent'",
  "results": [
    {
      "type": "project",
      "count": 2,
      "items": [
        {
          "id": 10,
          "name": "Security Patch Deployment",
          "tags": ["urgent", "security"]
        },
        // ... more projects
      ]
    }
  ]
}
```

## Privacy-Aware Queries

### Public Work Only
```
Query: "Public work sessions this week"

Expected Output:
{
  "summary": "Found 8 public work sessions totaling 28.0 hours this week",
  "results": [
    {
      "type": "work_session",
      "count": 8,
      "items": [
        {
          "id": 180,
          "privacy_level": "public",
          "summary": "Frontend development",
          // ... more details
        }
      ]
    }
  ]
}
```

### Private Notes Only
```
Query: "Show my private notes"

Expected Output:
{
  "summary": "Found 24 private notes",
  "results": [
    {
      "type": "note",
      "count": 24,
      "items": [
        {
          "id": 50,
          "text": "Need to follow up on pricing discussion",
          "privacy_level": "private",
          "created_at": "2026-01-15T14:30:00Z"
        },
        // ... more notes
      ]
    }
  ]
}
```

## Aggregation Queries

### Total Hours by Project
```
Query: "Total hours per project this month"

Expected Output:
{
  "summary": "Worked on 4 projects totaling 98.5 hours in January",
  "results": [
    {
      "type": "project_summary",
      "items": [
        {
          "project_name": "Website Redesign",
          "total_hours": "42.5",
          "session_count": 18
        },
        {
          "project_name": "API Integration",
          "total_hours": "31.0",
          "session_count": 12
        },
        // ... more projects
      ]
    }
  ]
}
```

### Total Hours by Client
```
Query: "Billable hours by client this quarter"

Expected Output:
{
  "summary": "Worked for 5 clients totaling 287.5 hours Q1 2026",
  "results": [
    {
      "type": "client_summary",
      "items": [
        {
          "client_name": "Acme Corp",
          "total_hours": "156.5",
          "project_count": 3
        },
        // ... more clients
      ]
    }
  ]
}
```

## Text Search Queries

### Search Work Session Summaries
```
Query: "Work sessions mentioning 'authentication'"

Expected Output:
{
  "summary": "Found 7 work sessions mentioning 'authentication'",
  "results": [
    {
      "type": "work_session",
      "count": 7,
      "items": [
        {
          "id": 190,
          "summary": "Refactored authentication module",
          "date": "2026-01-14",
          "duration_hours": "3.5"
        },
        // ... more sessions
      ]
    }
  ]
}
```

### Search Notes
```
Query: "Notes containing 'budget constraints'"

Expected Output:
{
  "summary": "Found 3 notes mentioning 'budget constraints'",
  "results": [
    {
      "type": "note",
      "count": 3,
      "items": [
        {
          "id": 55,
          "text": "Client mentioned budget constraints for Q2",
          "entity_type": "meeting",
          "entity_id": 225
        },
        // ... more notes
      ]
    }
  ]
}
```

## Status-Based Queries

### Active vs Completed Projects
```
Query: "Completed projects"

Expected Output:
{
  "summary": "Found 8 completed projects",
  "results": [
    {
      "type": "project",
      "count": 8,
      "items": [
        {
          "id": 7,
          "name": "Mobile App v1.0",
          "status": "completed",
          "end_date": "2025-12-15"
        },
        // ... more projects
      ]
    }
  ]
}
```

### Pending Reminders
```
Query: "Upcoming reminders"

Expected Output:
{
  "summary": "Found 5 pending reminders in the next 7 days",
  "results": [
    {
      "type": "reminder",
      "count": 5,
      "items": [
        {
          "id": 30,
          "reminder_time": "2026-01-16T09:00:00Z",
          "message": "Follow up on proposal",
          "is_completed": false
        },
        // ... more reminders
      ]
    }
  ]
}
```

## Multi-Entity Queries

### Stakeholders
```
Query: "Show all stakeholders"

Expected Output:
{
  "summary": "Found 6 stakeholders across 4 clients",
  "results": [
    {
      "type": "person",
      "count": 6,
      "items": [
        {
          "id": 12,
          "full_name": "John Executive",
          "is_stakeholder": true,
          "company": "Acme Corp",
          "title": "VP of Engineering"
        },
        // ... more stakeholders
      ]
    }
  ]
}
```

### Cross-Entity Search
```
Query: "Everything related to Website Redesign project"

Expected Output:
{
  "summary": "Found 45 items related to Website Redesign",
  "results": [
    {
      "type": "work_session",
      "count": 23,
      "items": [/* work sessions */]
    },
    {
      "type": "meeting",
      "count": 8,
      "items": [/* meetings */]
    },
    {
      "type": "note",
      "count": 12,
      "items": [/* notes */]
    },
    {
      "type": "reminder",
      "count": 2,
      "items": [/* reminders */]
    }
  ]
}
```

## Complex Filters

### Combining Filters
```
Query: "Public work sessions on Website Redesign last month"

Expected Output:
{
  "summary": "Found 12 public work sessions on Website Redesign in December",
  "results": [
    {
      "type": "work_session",
      "count": 12,
      "items": [
        {
          "project_name": "Website Redesign",
          "privacy_level": "public",
          "date": "2025-12-15",
          // ... more details
        }
      ]
    }
  ]
}
```

### Multiple Entity Types
```
Query: "Meetings and notes from last week"

Expected Output:
{
  "summary": "Found 5 meetings and 8 notes from last week",
  "results": [
    {
      "type": "meeting",
      "count": 5,
      "items": [/* meetings */]
    },
    {
      "type": "note",
      "count": 8,
      "items": [/* notes */]
    }
  ]
}
```

## Edge Cases

### No Results
```
Query: "Work sessions tagged 'nonexistent'"

Expected Output:
{
  "summary": "No work sessions found with tag 'nonexistent'",
  "results": []
}
```

### Ambiguous Query
```
Query: "Show me recent stuff"

Expected Output:
{
  "summary": "Found 47 recent items from last 7 days",
  "results": [
    {
      "type": "work_session",
      "count": 18,
      "items": [/* sessions */]
    },
    {
      "type": "meeting",
      "count": 12,
      "items": [/* meetings */]
    },
    {
      "type": "note",
      "count": 15,
      "items": [/* notes */]
    },
    {
      "type": "reminder",
      "count": 2,
      "items": [/* reminders */]
    }
  ]
}
```

## Query Optimization Tips

### Be Specific with Time Ranges
✅ **Good:** "Work sessions from January 1 to January 15"
❌ **Vague:** "Recent work sessions"

### Use Entity Names
✅ **Good:** "Meetings with Alice Smith on Website Redesign"
❌ **Vague:** "Recent meetings"

### Specify Privacy When Needed
✅ **Good:** "Public work for client timecard"
❌ **Ambiguous:** "Work this week" (returns all privacy levels)

### Combine Filters Logically
✅ **Good:** "Active projects for Acme Corp with work last month"
❌ **Confusing:** "Projects and work and clients last month"

## Response Format

All query responses follow this structure:

```typescript
{
  "summary": string,           // Natural language summary
  "results": [
    {
      "type": string,          // Entity type (work_session, meeting, etc.)
      "count": number,         // Number of items
      "items": Array<object>   // Discriminated union of entity types
    }
  ]
}
```

**Discriminated Union Types:**
- `work_session`: WorkSessionOutput
- `meeting`: MeetingOutput
- `person`: PersonOutput
- `client`: ClientOutput
- `project`: ProjectOutput
- `employer`: EmployerOutput
- `note`: NoteOutput
- `reminder`: ReminderOutput

## Testing Query Patterns

Comprehensive integration tests should cover:

**Time Ranges:**
- Last week, this week, next week
- Last month, this month
- Specific date ranges
- Year-to-date, quarter-to-date

**Entity Filters:**
- Single entity type
- Multiple entity types
- All entity types (broad query)

**Relationship Filters:**
- Project → work sessions
- Project → meetings
- Person → meetings
- Client → projects

**Aggregations:**
- Total hours by project
- Total hours by client
- Meeting count by person

**Privacy Filters:**
- Public only
- Public + Internal
- All levels

See `tests/integration/test_query_tool.py` for full test suite.

---

# Structured Query Language (New)

For precise, type-safe queries with complex filtering and aggregations, use the structured query DSL instead of natural language.

## Overview

The structured query DSL provides:
- 15 filter operators (eq, ne, gt, contains, has_tag, etc.)
- 6 aggregation functions (count, sum, avg, min, max, count_distinct)
- Relationship path traversal (e.g., "project.client.name")
- Time shortcuts (today, this_week, this_month, etc.)

## Filter Operators

### Comparison Operators
- **eq** - Equal to
- **ne** - Not equal to
- **gt** - Greater than
- **gte** - Greater than or equal
- **lt** - Less than
- **lte** - Less than or equal

### Set Operators
- **in** - Value in list
- **not_in** - Value not in list

### String Operators
- **contains** - Case-insensitive substring match
- **starts_with** - Case-insensitive starts with
- **ends_with** - Case-insensitive ends with

### Null Operators
- **is_null** - Field is NULL
- **is_not_null** - Field is NOT NULL

### Array Operators (PostgreSQL)
- **has_tag** - Array contains single value
- **has_any_tag** - Array overlaps with list

## Aggregation Functions

- **count** - Count rows
- **sum** - Sum values
- **avg** - Average values
- **min** - Minimum value
- **max** - Maximum value
- **count_distinct** - Count distinct values

## Relationship Paths

### Work Session
- `project.name` - Project name
- `project.client.name` - Client name
- `project.client.contact_person.email` - Contact email
- `project.employer.name` - Employer name

### Meeting
- `project.name` - Project name
- `project.client.name` - Client name
- `attendees.person.full_name` - Attendee names
- `attendees.person.email` - Attendee emails

### Project
- `client.name` - Client name
- `client.contact_person.full_name` - Contact person name
- `employer.name` - Employer name

## Example Structured Queries

**Field Naming:** Use API/schema field names in queries (e.g., `on_behalf_of`), not database field names (e.g., `on_behalf_of_id`). The query system automatically handles field name mapping.

### Simple Filter
```json
{
  "entity_type": "work_session",
  "filters": [
    {"field": "date", "operator": "gte", "value": "this_month"}
  ],
  "limit": 100
}
```

### Relationship Traversal
```json
{
  "entity_type": "work_session",
  "filters": [
    {"field": "project.client.name", "operator": "eq", "value": "Acme Corp"}
  ]
}
```

### Aggregation with GROUP BY
```json
{
  "entity_type": "work_session",
  "filters": [
    {"field": "date", "operator": "gte", "value": "this_week"}
  ],
  "aggregation": {
    "function": "sum",
    "field": "duration_hours",
    "group_by": ["project.name"]
  }
}
```

### Multiple Filters
```json
{
  "entity_type": "meeting",
  "filters": [
    {"field": "tags", "operator": "has_any_tag", "value": ["urgent", "client"]},
    {"field": "start_time", "operator": "gte", "value": "this_week"}
  ]
}
```

### Complex Query
```json
{
  "entity_type": "project",
  "filters": [
    {"field": "status", "operator": "eq", "value": "active"},
    {"field": "client.contact_person.email", "operator": "ends_with", "value": "@acme.com"}
  ],
  "limit": 50
}
```

### Null Checks
```json
{
  "entity_type": "project",
  "filters": [
    {"field": "on_behalf_of", "operator": "is_null", "value": null}
  ]
}
```

**Note:** Use `on_behalf_of` (not `on_behalf_of_id`) when querying. The system automatically maps API field names to database field names.

```json
{
  "entity_type": "project",
  "filters": [
    {"field": "on_behalf_of", "operator": "is_not_null", "value": null}
  ]
}
```

## Time Shortcuts

- **today** - Current date
- **this_week** - Start of current week (Monday)
- **this_month** - Start of current month
- **this_year** - Start of current year
- **now** - Current datetime

## Response Formats

### Entity Query Response
```json
{
  "entity_type": "work_session",
  "results": [...],
  "total_count": 15
}
```

### Aggregation Response (Global)
```json
{
  "entity_type": "work_session",
  "aggregation": {
    "function": "sum",
    "field": "duration_hours",
    "result": 42.5
  }
}
```

### Aggregation Response (Grouped)
```json
{
  "entity_type": "work_session",
  "aggregation": {
    "function": "sum",
    "field": "duration_hours",
    "groups": [
      {"group_values": ["Project Alpha"], "result": 24.5},
      {"group_values": ["Project Beta"], "result": 18.0}
    ]
  },
  "total_groups": 2
}
```

## Migration from Natural Language

The natural language `query` tool still works for simple queries. Use structured queries for:
- Precise filtering with specific operators
- Relationship traversal (multi-level joins)
- Aggregations with GROUP BY
- Complex queries with multiple conditions

Both query methods coexist - use whichever fits your needs.
