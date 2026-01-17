"""Configuration management using Pydantic Settings."""

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    All settings can be configured via .env file or environment variables.
    """

    database_url: PostgresDsn = Field(
        description="PostgreSQL connection URL with asyncpg driver",
        examples=["postgresql+asyncpg://mosaic:changeme@localhost:5433/mosaic"],
    )

    scheduler_timezone: str = Field(
        default="UTC",
        description="Timezone for scheduler operations",
        examples=["UTC", "America/New_York", "Europe/London"],
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level for application",
        examples=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    reminder_notification_cooldown_minutes: int = Field(
        default=60,
        description="Minimum minutes between notifications for same reminder (prevents spam)",
        ge=1,
        le=1440,  # Max 24 hours
    )

    reminder_auto_complete_non_recurring: bool = Field(
        default=True,
        description=(
            "Automatically mark non-recurring reminders as completed " "after first notification"
        ),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
