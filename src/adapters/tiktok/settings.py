from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class TikTokSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OAuth API credentials
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_access_token: str = ""
    tiktok_refresh_token: str = ""
    tiktok_default_privacy: str = "SELF_ONLY"

    # Cookie login -- grab sessionid from DevTools > Application > Cookies > tiktok.com
    tiktok_session_id: str = ""

    # Browser / session persistence
    tiktok_session_path: Path = Path(".tiktok_session.json")
    tiktok_user_data_dir: Path = Path(".tiktok_browser_profile")
    headless: bool = True
    slow_mo_ms: int = 50
    proxy_url: str = ""
    viewport_width: int = 1280
    viewport_height: int = 900
