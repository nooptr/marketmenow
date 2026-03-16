from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PACKAGE_DIR = Path(__file__).resolve().parent


class InstagramSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Figma
    figma_api_token: str = ""

    # TTS
    tts_provider: str = "elevenlabs"

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # OpenAI TTS
    openai_api_key: str = ""
    openai_tts_voice: str = "alloy"
    openai_tts_model: str = "tts-1"

    # Vertex AI / Gemini
    google_application_credentials: Path = Path("credentials.json")
    vertex_ai_project: str = ""
    vertex_ai_location: str = "us-central1"

    # Instagram Graph API
    instagram_access_token: str = ""
    instagram_business_account_id: str = ""

    # Paths
    output_dir: Path = Path("output")
    remotion_project_dir: Path = _PACKAGE_DIR / "reels" / "remotion"
