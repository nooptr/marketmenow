from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_CREDENTIALS_PATH = Path("credentials.yaml")

PLATFORM_CREDENTIAL_KEYS: dict[str, dict[str, list[str]]] = {
    "instagram": {
        "required": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"],
        "optional": [
            "INSTAGRAM_APP_ID",
            "INSTAGRAM_APP_SECRET",
            "FIGMA_API_TOKEN",
            "VERTEX_AI_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "AWS_S3_BUCKET",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ],
    },
    "twitter": {
        "required": ["TWITTER_AUTH_TOKEN", "TWITTER_CT0"],
        "optional": [
            "TWITTER_USERNAME",
            "VERTEX_AI_PROJECT",
            "VERTEX_AI_LOCATION",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
    },
    "linkedin": {
        "required": [],
        "optional": [
            "LINKEDIN_ACCESS_TOKEN",
            "LINKEDIN_PERSON_URN",
            "LINKEDIN_LI_AT",
            "LINKEDIN_ORGANIZATION_ID",
            "LINKEDIN_CLIENT_ID",
            "LINKEDIN_CLIENT_SECRET",
            "VERTEX_AI_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
    },
    "reddit": {
        "required": ["REDDIT_SESSION", "REDDIT_USERNAME"],
        "optional": [
            "VERTEX_AI_PROJECT",
            "VERTEX_AI_LOCATION",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
    },
    "youtube": {
        "required": [
            "YOUTUBE_CLIENT_ID",
            "YOUTUBE_CLIENT_SECRET",
            "YOUTUBE_REFRESH_TOKEN",
        ],
        "optional": ["YOUTUBE_DEFAULT_PRIVACY", "YOUTUBE_DEFAULT_CATEGORY_ID"],
    },
    "email": {
        "required": ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD"],
        "optional": [
            "SMTP_FROM",
            "SMTP_FROM_NAME",
            "SMTP_USE_TLS",
            "SMTP_USE_SSL",
            "VERTEX_AI_PROJECT",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ],
    },
    "facebook": {
        "required": ["FACEBOOK_C_USER", "FACEBOOK_XS"],
        "optional": ["FACEBOOK_GROUP_IDS"],
    },
}


@dataclass
class CredentialSet:
    name: str
    platform: str
    env: dict[str, str] = field(default_factory=dict)


def _read_yaml() -> dict[str, object]:
    if not _CREDENTIALS_PATH.exists():
        return {}
    with _CREDENTIALS_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_yaml(data: dict[str, object]) -> None:
    with _CREDENTIALS_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_credential_sets() -> dict[str, CredentialSet]:
    data = _read_yaml()
    sets_raw: dict[str, dict[str, object]] = data.get("sets", {})  # type: ignore[assignment]
    result: dict[str, CredentialSet] = {}
    for name, spec in sets_raw.items():
        if not isinstance(spec, dict):
            continue
        result[name] = CredentialSet(
            name=name,
            platform=str(spec.get("platform", "")),
            env={str(k): str(v) for k, v in spec.get("env", {}).items()},  # type: ignore[union-attr]
        )
    return result


def save_credential_set(name: str, platform: str, env_vars: dict[str, str]) -> None:
    data = _read_yaml()
    sets_raw: dict[str, object] = data.get("sets", {})  # type: ignore[assignment]
    if not isinstance(sets_raw, dict):
        sets_raw = {}
    sets_raw[name] = {"platform": platform, "env": env_vars}
    data["sets"] = sets_raw
    _write_yaml(data)


def delete_credential_set(name: str) -> bool:
    data = _read_yaml()
    sets_raw: dict[str, object] = data.get("sets", {})  # type: ignore[assignment]
    if not isinstance(sets_raw, dict) or name not in sets_raw:
        return False
    del sets_raw[name]
    data["sets"] = sets_raw
    _write_yaml(data)
    return True


def get_platform_credential_sets(platform: str) -> list[str]:
    all_sets = load_credential_sets()
    return [name for name, cs in all_sets.items() if cs.platform == platform]


def get_env_overrides(set_name: str) -> dict[str, str]:
    all_sets = load_credential_sets()
    cs = all_sets.get(set_name)
    if cs is None:
        return {}
    return dict(cs.env)


def get_all_platforms() -> list[str]:
    return sorted(PLATFORM_CREDENTIAL_KEYS.keys())


def get_keys_for_platform(platform: str) -> dict[str, list[str]]:
    return PLATFORM_CREDENTIAL_KEYS.get(platform, {"required": [], "optional": []})
