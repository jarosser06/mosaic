---
name: prompt-writing
description: Write effective prompts for Claude following Anthropic's best practices. Use when designing system prompts, tool descriptions, or agent instructions.
allowed-tools: Read
user-invocable: true
---

# Prompt Writing Skill

Write effective prompts for Claude models (4.x series: Opus 4.5, Sonnet 4.5, Haiku 4.5) following Anthropic's 2026 best practices.

## Core Principles

### 1. Be Specific and Explicit

Claude 4.x models have been trained for precise instruction following.

**Good:**
```
Analyze the codebase for DRY violations. Specifically:
1. Search for duplicate function implementations
2. Identify repeated validation patterns
3. Look for copy-pasted business logic
4. Report findings with file paths and line numbers
5. Suggest consolidation strategies
```

**Bad:**
```
Check the code for problems.
```

### 2. Provide Context and Motivation

Explain WHY the behavior is important.

**Good:**
```
You are reviewing code for a financial application where accuracy
is critical. When checking calculations, be extremely thorough
because errors could result in incorrect billing. Verify:
- All decimal arithmetic uses Decimal type (not float)
- Rounding follows documented business rules
- Edge cases are handled (zero, negative, very large numbers)
```

**Bad:**
```
Check the calculations.
```

### 3. Use Examples Carefully

Claude 4.x pays close attention to details in examples. Ensure examples align with desired behavior.

**Good:**
```
Write docstrings following Google style:

Example:
def calculate_duration(start: datetime, end: datetime) -> Decimal:
    """
    Calculate duration between two times.

    Args:
        start: Start time
        end: End time

    Returns:
        Decimal: Duration in hours

    Raises:
        ValueError: If end is before start
    """
```

**Bad:**
```
Write good docstrings like this:

def foo(x):
    # does stuff
    pass
```
(Bad example shows poor practices that Claude will emulate)

### 4. Structured Prompts Work Best

A good Claude system prompt reads like a short contract.

**Structure:**
```markdown
# Role
You are a [specific role with expertise]

# Goals
Your primary objectives are:
1. [Goal 1]
2. [Goal 2]
3. [Goal 3]

# Constraints
- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

# Process
When given a task:
1. [Step 1]
2. [Step 2]
3. [Step 3]

# Success Criteria
Output is successful when:
- [Criterion 1]
- [Criterion 2]

# Error Handling
If you encounter [situation], [action]
```

**Example for App Architect Agent:**
```markdown
# Role
You are an Application Architect specializing in Python async applications
with SQLAlchemy 2.0, focusing on clean architecture and DRY principles.

# Goals
1. Design code components that are maintainable and testable
2. Ensure DRY (Don't Repeat Yourself) principles throughout
3. Apply SOLID principles and appropriate design patterns
4. Create detailed implementation specifications for developers

# Constraints
- Must use Serena MCP for all codebase searches
- Must use Context7 MCP for documentation lookup
- Must check for existing implementations before designing new code
- Must follow project's established patterns

# Process
When designing a component:
1. Use Serena to search for similar existing implementations
2. Use Context7 to research best practices for required libraries
3. Design component following repository/service/tool layers
4. Document all design decisions and patterns used
5. Create detailed specification with type hints and examples
6. Delegate implementation to Python Developer agent

# Success Criteria
Design is successful when:
- No code duplication (verified via Serena search)
- Follows SOLID principles
- Uses dependency injection
- Includes comprehensive type hints
- Matches existing project patterns

# Error Handling
If existing pattern is found, reuse it instead of creating new
If uncertain about library usage, research with Context7
If design violates DRY, refactor to eliminate duplication
```

### 5. Use Thinking Capabilities

Claude 4.x models have extended thinking that can help with complex reasoning.

**Enable thinking:**
```xml
<claude_thinking_mode>interleaved</claude_thinking_mode>
```

**Guide thinking:**
```
Before implementing, think through:
- What existing patterns can I reuse?
- What edge cases exist?
- How will this interact with other components?
- What tests are needed?
```

### 6. Think Step by Step

Claude performs better with explicit step-by-step instructions.

**Good:**
```
To implement the repository:
1. First, use Serena to find BaseRepository
2. Read BaseRepository to understand the pattern
3. Design WorkSessionRepository inheriting from base
4. Add specific methods: get_by_date_range, aggregate_by_project
5. Ensure all methods use async/await
6. Add type hints to all methods
7. Write docstrings for public methods
```

**Bad:**
```
Implement the repository using best practices.
```

### 7. Prompt Chaining for Complex Tasks

Break complex tasks into multiple prompts.

**Example chain:**
```
Prompt 1 (Research):
"Use Serena to find all repository implementations. List their patterns."

Prompt 2 (Design):
"Based on these patterns, design WorkSessionRepository with these methods: [list]"

Prompt 3 (Implementation):
"Implement the repository following this design: [design]"

Prompt 4 (Testing):
"Write tests for the repository ensuring 90%+ coverage"
```

## Tool Description Best Practices

MCP tool descriptions are prompts that Claude reads.

**Good tool description:**
```python
@server.tool()
async def log_work_session(input: LogWorkSessionInput) -> WorkSessionResult:
    """
    Log a work session with automatic half-hour rounding.

    This tool records time spent on a project. Duration is calculated from
    start_time to end_time and automatically rounded following business rules:
    - 0:01 to 0:30 minutes → 0.5 hours
    - 0:31 to 1:00 minutes → 1.0 hours

    The work session is stored with PRIVATE privacy by default for security.

    Required fields:
    - project_id: Must be a valid, active project
    - start_time: ISO 8601 datetime when work started
    - end_time: ISO 8601 datetime when work ended (must be after start_time)

    Optional fields:
    - summary: Brief description of work performed (max 500 chars)
    - privacy_level: "public", "internal", or "private" (default: "private")

    Returns structured result with:
    - Generated session ID
    - Project name for confirmation
    - Rounded hours calculated
    - Timestamps in ISO format

    Example usage:
    Input: start=9:00, end=10:15 → Result: 1.5 hours
    Input: start=9:00, end=9:20 → Result: 0.5 hours
    """
```

**Bad tool description:**
```python
@server.tool()
async def log_work_session(data: dict):
    """Log work session."""
```

## System Prompt Template

Use this template for agent system prompts:

```markdown
# [Agent Name] Agent

## Role
You are a [specific expertise] specializing in [domain knowledge].
You have access to [specific tools/resources].

## Responsibilities
1. [Primary responsibility]
2. [Secondary responsibility]
3. [Tertiary responsibility]

## Mandatory Tools
- **Serena MCP**: Use for [specific Serena use cases]
- **Context7 MCP**: Use for [specific Context7 use cases]
- **[Other tools]**: Use for [specific purposes]

## Process
When assigned a task:
1. [First step - usually research/understanding]
2. [Second step - usually planning]
3. [Third step - usually implementation/execution]
4. [Fourth step - usually validation]
5. [Fifth step - usually reporting/delegation]

## Code Quality Standards
- [ ] [Standard 1]
- [ ] [Standard 2]
- [ ] [Standard 3]

## Delegation Rules
- Delegate [task type] to [agent name]
- Report results to [parent agent]
- Never [prohibited action]

## Success Criteria
Task is complete when:
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]

## Error Handling
- If [situation], [action]
- If [situation], [action]

## Output Format
Provide [specific output format with examples]
```

## Common Pitfalls

### ❌ Vague Instructions
```
"Make the code better"
```

### ✅ Specific Instructions
```
"Refactor to eliminate duplicate validation logic. Specifically:
1. Find all email validation code
2. Create shared email_validator() function
3. Update all call sites to use shared function"
```

### ❌ Too Many Examples
```
Here are 20 examples of how to write functions...
(Claude may overfit to examples)
```

### ✅ Right Amount of Examples
```
Here are 2 examples showing good and bad patterns:

Good:
async def get_user(session: AsyncSession, id: int) -> User | None:
    ...

Bad:
def get_user(session, id):  # Missing async, type hints
    ...
```

### ❌ Contradictory Instructions
```
"Be concise but also very thorough and detailed"
```

### ✅ Clear Priorities
```
"Prioritize correctness over brevity. Provide thorough
explanations, but use structured format (headings, bullets)
for readability."
```

## Checklist for Good Prompts

- [ ] Clear, specific instructions (not vague)
- [ ] Context provided (why is this important?)
- [ ] Examples align with desired behavior
- [ ] Structured format (role, goals, constraints, process)
- [ ] Success criteria defined
- [ ] Error handling specified
- [ ] Step-by-step process when needed
- [ ] No contradictions

## When to Use

- Writing agent system prompts
- Designing MCP tool descriptions
- Creating skill instructions
- Writing task delegation prompts
- Reviewing existing prompts for clarity

## Resources

Based on research from:
- [Claude 4 Best Practices - Anthropic Docs](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Claude Prompt Engineering Best Practices 2026](https://promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026)
- [Prompt Engineering Techniques - AWS Blog](https://aws.amazon.com/blogs/machine-learning/prompt-engineering-techniques-and-best-practices-learn-by-doing-with-anthropics-claude-3-on-amazon-bedrock/)
- [Claude Code Best Practices - Anthropic Engineering](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Interactive Prompt Engineering Tutorial - Anthropic](https://github.com/anthropics/prompt-eng-interactive-tutorial)
