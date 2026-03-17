from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class LinkedInSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Cookie login -- grab li_at from DevTools > Application > Cookies > linkedin.com
    linkedin_li_at: str = ""

    # Organization page URL slug or numeric ID (for posting as an org)
    linkedin_organization_id: str = ""

    # Session / browser paths
    linkedin_session_path: Path = Path(".linkedin_session.json")
    linkedin_user_data_dir: Path = Path(".linkedin_browser_profile")

    # Browser
    headless: bool = False
    slow_mo_ms: int = 50
    proxy_url: str = ""
    viewport_width: int = 1280
    viewport_height: int = 900
