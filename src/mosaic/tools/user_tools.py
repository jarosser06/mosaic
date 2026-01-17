"""User profile management tools."""

from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import Context

from ..models.base import WeekBoundary
from ..repositories.user_repository import UserRepository
from ..schemas.user import GetUserOutput, UpdateUserInput, UpdateUserOutput
from ..server import AppContext, mcp


@mcp.tool()
async def get_user_profile(ctx: Context[Any, AppContext, Any]) -> GetUserOutput:
    """
    Get the current user profile.

    Returns user information including name, timezone, work preferences, etc.
    This is a single-user system, so there's only one user profile.
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_current_user()

        if not user:
            # Return empty profile if not initialized
            return GetUserOutput(
                id=None,
                full_name="",
                email=None,
                phone=None,
                timezone="UTC",
                week_boundary="monday_friday",
                working_hours_start=None,
                working_hours_end=None,
                communication_style=None,
                work_approach=None,
                profile_last_updated=None,
                created_at=None,
                updated_at=None,
            )

        return GetUserOutput(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            timezone=user.timezone,
            week_boundary=user.week_boundary.value,
            working_hours_start=user.working_hours_start,
            working_hours_end=user.working_hours_end,
            communication_style=user.communication_style,
            work_approach=user.work_approach,
            profile_last_updated=user.profile_last_updated,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


@mcp.tool()
async def update_user_profile(
    input: UpdateUserInput, ctx: Context[Any, AppContext, Any]
) -> UpdateUserOutput:
    """
    Create or update the user profile.

    This is used during initial onboarding and for periodic profile updates.

    Args:
        input: User profile information including:
            - full_name: User's full name (required for initial creation)
            - email: Email address (optional)
            - phone: Phone number (optional)
            - timezone: IANA timezone (e.g., "America/Los_Angeles", default: "UTC")
            - week_boundary: Work week definition (monday_friday, sunday_saturday, etc.)
            - working_hours_start: Start hour in 24h format (e.g., 9 for 9am)
            - working_hours_end: End hour in 24h format (e.g., 17 for 5pm)
            - communication_style: Preferred communication style and preferences
            - work_approach: Work approach and values

    Returns:
        Updated user profile
    """
    app_ctx = ctx.request_context.lifespan_context

    async with app_ctx.session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_current_user()

        # Build update data
        update_data: dict[str, Any] = {}

        if input.full_name is not None:
            update_data["full_name"] = input.full_name
        if input.email is not None:
            update_data["email"] = input.email
        if input.phone is not None:
            update_data["phone"] = input.phone
        if input.timezone is not None:
            update_data["timezone"] = input.timezone
        if input.week_boundary is not None:
            update_data["week_boundary"] = WeekBoundary(input.week_boundary)
        if input.working_hours_start is not None:
            update_data["working_hours_start"] = input.working_hours_start
        if input.working_hours_end is not None:
            update_data["working_hours_end"] = input.working_hours_end
        if input.communication_style is not None:
            update_data["communication_style"] = input.communication_style
        if input.work_approach is not None:
            update_data["work_approach"] = input.work_approach

        # Always update profile_last_updated timestamp
        update_data["profile_last_updated"] = datetime.now(timezone.utc)

        if user:
            # Update existing user
            updated_user = await repo.update(user.id, **update_data)
            if not updated_user:
                raise ValueError("Failed to update user profile")
            user = updated_user
        else:
            # Create new user (initial onboarding)
            if "full_name" not in update_data:
                raise ValueError("full_name is required for initial user creation")
            user = await repo.create(**update_data)

        await session.commit()

        return UpdateUserOutput(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            timezone=user.timezone,
            week_boundary=user.week_boundary.value,
            working_hours_start=user.working_hours_start,
            working_hours_end=user.working_hours_end,
            communication_style=user.communication_style,
            work_approach=user.work_approach,
            profile_last_updated=user.profile_last_updated,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
