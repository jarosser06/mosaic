# Mosaic Project Overview

## Purpose
Mosaic is a personal work memory and time tracking MCP (Model Context Protocol) server. It provides LLMs with tools to:
- Track work sessions with half-hour rounding (0:01-0:30 → 0.5h, 0:31-1:00 → 1.0h)
- Log meetings with automatic billable time generation
- Manage people, clients, projects, employers
- Create notes and reminders
- Generate timecards with privacy filtering
- Search historical context

## Key Business Rules
- **Half-hour rounding**: Work duration rounded to nearest 0.5 hours
- **Privacy levels**: PRIVATE (default), INTERNAL, PUBLIC
- **Meeting-to-work auto-generation**: Project-associated meetings create billable work sessions
- **Single-user system**: Designed for personal use

## Data Model
11 main entities: User, Employer, Client, Project, Person, EmploymentHistory, WorkSession, Meeting, MeetingAttendee, Note, Reminder

## MCP Server
- 19 tools for work tracking operations
- Resources for documentation (5 static docs)
- Prompts for interactive guidance (8 dynamic prompts)
- FastMCP-based server with async SQLAlchemy 2.0
