# Time Tracking Rules

Business rules for work session duration calculation and half-hour rounding in Mosaic.

## Overview

Mosaic uses half-hour precision for all time tracking. This matches common billing and timecard practices where work is rounded to 0.5 hour increments.

## Half-Hour Rounding Rules

### Core Rule

All duration calculations are rounded to the nearest half-hour following these specific rules:

```
0:01 to 0:30 minutes → 0.5 hours
0:31 to 1:00 minutes → 1.0 hours
```

This pattern continues for all hour boundaries:
- 1:01 to 1:30 → 1.5 hours
- 1:31 to 2:00 → 2.0 hours
- 2:01 to 2:30 → 2.5 hours
- 2:31 to 3:00 → 3.0 hours

### Examples

| Actual Duration | Rounded Duration | Calculation |
|----------------|------------------|-------------|
| 15 minutes | 0.5 hours | 0:15 → round to 0:30 → 0.5 |
| 30 minutes | 0.5 hours | 0:30 → exactly 0.5 |
| 31 minutes | 1.0 hours | 0:31 → round to 1:00 → 1.0 |
| 45 minutes | 1.0 hours | 0:45 → round to 1:00 → 1.0 |
| 60 minutes | 1.0 hours | 1:00 → exactly 1.0 |
| 2:15 (135 min) | 2.5 hours | 2:15 → round to 2:30 → 2.5 |
| 2:30 (150 min) | 2.5 hours | 2:30 → exactly 2.5 |
| 2:31 (151 min) | 3.0 hours | 2:31 → round to 3:00 → 3.0 |
| 2:40 (160 min) | 3.0 hours | 2:40 → round to 3:00 → 3.0 |

### Boundary Behavior

**At exactly 30 minutes:** Rounds DOWN to 0.5 hours
**At exactly 60 minutes:** Uses exact 1.0 hours (no rounding needed)
**At 31 minutes:** Rounds UP to 1.0 hours

This is a "round up after 30" policy, not traditional rounding.

## Implementation

The rounding logic is implemented in `src/mosaic/services/time_utils.py`:

### Function: `round_to_half_hour(minutes: int) -> Decimal`

```python
def round_to_half_hour(minutes: int) -> Decimal:
    """
    Round duration to nearest 0.5 hours following spec rules.

    Args:
        minutes: Total duration in minutes

    Returns:
        Decimal: Rounded hours with 1 decimal place
    """
    if minutes <= 0:
        return Decimal("0.0")

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return Decimal(str(float(hours)))
    elif remaining_minutes <= 30:
        return Decimal(str(float(hours) + 0.5))
    else:
        return Decimal(str(float(hours) + 1.0))
```

### Function: `calculate_duration_rounded(start_time, end_time) -> Decimal`

```python
def calculate_duration_rounded(start_time: datetime, end_time: datetime) -> Decimal:
    """
    Calculate duration between times, rounded to half-hour precision.

    Args:
        start_time: Session start time
        end_time: Session end time

    Returns:
        Decimal: Rounded duration in hours

    Raises:
        ValueError: If end_time is before start_time
    """
    if end_time < start_time:
        raise ValueError("end_time must be after start_time")

    delta = end_time - start_time
    minutes = int(delta.total_seconds() / 60)
    return round_to_half_hour(minutes)
```

## Work Session Creation

When creating a work session, the duration is automatically calculated and rounded:

1. User provides `start_time` and `end_time`
2. System calculates duration in minutes
3. System applies half-hour rounding via `round_to_half_hour()`
4. Rounded duration stored in `duration_hours` field

**Database Field:**
```python
duration_hours: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
```

The `Numeric(4, 1)` type allows:
- Up to 999.9 hours
- Exactly 1 decimal place (0.5 precision)

## Meeting-to-WorkSession Auto-Generation

When a meeting has a project association, a work session is automatically created:

1. Meeting duration (in minutes) is extracted
2. Half-hour rounding is applied
3. WorkSession created with:
   - `project_id` from meeting
   - `start_time` = meeting start_time
   - `end_time` = meeting start_time + duration_minutes
   - `duration_hours` = rounded duration
   - `summary` = meeting title
   - Inherits `on_behalf_of` from project

**Example:**
```
Meeting:
  title: "Client Kickoff"
  start_time: 2026-01-15 10:00:00
  duration_minutes: 45
  project_id: 123

Generated WorkSession:
  project_id: 123
  start_time: 2026-01-15 10:00:00
  end_time: 2026-01-15 10:45:00
  duration_hours: 1.0 (45 minutes → rounded to 1.0)
  summary: "Client Kickoff"
```

## Timecard Generation

When generating timecards, work sessions are aggregated by project and date:

```python
# For each project on each date:
total_hours = sum(work_session.duration_hours)
```

**Important:** Individual work sessions are already rounded. The timecard simply sums the pre-rounded values. No additional rounding is applied at the timecard level.

## Edge Cases

### Zero or Negative Duration

If `end_time <= start_time`, raises `ValueError`:
```python
ValueError: "end_time must be after start_time"
```

### Very Short Sessions

Even 1 minute of work rounds to 0.5 hours:
```
1 minute → 0.5 hours
5 minutes → 0.5 hours
29 minutes → 0.5 hours
30 minutes → 0.5 hours
```

### Multi-Day Sessions

For sessions spanning multiple days:
```
start_time: 2026-01-15 23:30:00
end_time:   2026-01-16 01:15:00
duration:   105 minutes (1:45)
rounded:    2.0 hours
```

The `date` field on WorkSession uses the start_time date (2026-01-15).

### Decimal Precision

All durations use Python `Decimal` type to avoid floating-point errors:
```python
from decimal import Decimal

# Good
duration = Decimal("2.5")

# Bad (floating point issues)
duration = 2.5
```

## Testing Requirements

All rounding logic must have comprehensive unit tests covering:

**Parametrized boundary tests:**
- Exactly 0 minutes
- 1-29 minutes (should all → 0.5)
- Exactly 30 minutes (should → 0.5)
- 31-59 minutes (should all → 1.0)
- Exactly 60 minutes (should → 1.0)
- Multi-hour boundaries (2:15 → 2.5, 2:31 → 3.0, etc.)

**Error cases:**
- Negative duration
- end_time before start_time

See `tests/unit/test_time_utils.py` for full test suite.

## Business Justification

**Why half-hour precision?**

1. **Industry Standard:** Most professional services bill in 0.5 hour increments
2. **Simplicity:** Easier to mentally track than 15-minute (0.25 hour) increments
3. **Fairness:** Rounds in favor of work done (31 minutes = 1 hour billable)
4. **Timecard Compatibility:** Matches common timecard systems

**Why "round up after 30" instead of standard rounding?**

Standard rounding would round 30 minutes to 0.0 or 1.0 depending on banker's rounding. The spec explicitly states 30 minutes = 0.5 hours, ensuring predictable behavior.

## API Usage

### MCP Tool: `log_work_session`

When using the MCP tool to log work:
```json
{
  "project_id": 123,
  "start_time": "2026-01-15T14:00:00Z",
  "end_time": "2026-01-15T15:45:00Z",
  "summary": "Refactored authentication module"
}
```

Response includes rounded duration:
```json
{
  "id": 456,
  "project_id": 123,
  "date": "2026-01-15",
  "start_time": "2026-01-15T14:00:00Z",
  "end_time": "2026-01-15T15:45:00Z",
  "duration_hours": "2.0",  // 105 minutes → 2.0 hours
  "summary": "Refactored authentication module"
}
```

### Query: Timecard Total

When querying total hours for a project:
```
Query: "Total hours on Project Apollo this week"

Result: 15.5 hours
(sum of all work sessions' pre-rounded duration_hours)
```

## Future Considerations

**Alternate Rounding Policies:**

The system could support configurable rounding policies:
- 15-minute increments (0.25 hours)
- 6-minute increments (0.1 hours, "decimal hours")
- No rounding (track exact minutes)

This would require:
- User preference in User model
- Conditional logic in `time_utils.py`
- Migration of existing duration_hours values

Currently NOT implemented. All durations use half-hour rounding.
