from __future__ import annotations

from pathlib import Path

import pytest

from web.credentials import (
    PLATFORM_CREDENTIAL_KEYS,
    delete_credential_set,
    get_all_platforms,
    get_env_overrides,
    get_keys_for_platform,
    get_platform_credential_sets,
    load_credential_sets,
    save_credential_set,
)


@pytest.fixture(autouse=True)
def _use_tmp_creds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the credentials module at a temp file."""
    import web.credentials as mod

    monkeypatch.setattr(mod, "_CREDENTIALS_PATH", tmp_path / "credentials.yaml")


class TestLoadEmpty:
    def test_no_file_returns_empty(self) -> None:
        result = load_credential_sets()
        assert result == {}


class TestSaveAndLoad:
    def test_save_then_load(self) -> None:
        save_credential_set(
            "reddit-main", "reddit", {"REDDIT_SESSION": "abc", "REDDIT_USERNAME": "user1"}
        )
        sets = load_credential_sets()
        assert "reddit-main" in sets
        assert sets["reddit-main"].platform == "reddit"
        assert sets["reddit-main"].env["REDDIT_SESSION"] == "abc"

    def test_save_multiple(self) -> None:
        save_credential_set("reddit-main", "reddit", {"REDDIT_SESSION": "a"})
        save_credential_set("reddit-alt", "reddit", {"REDDIT_SESSION": "b"})
        save_credential_set("twitter-brand", "twitter", {"TWITTER_AUTH_TOKEN": "t"})
        sets = load_credential_sets()
        assert len(sets) == 3

    def test_upsert_overwrites(self) -> None:
        save_credential_set("test", "reddit", {"REDDIT_SESSION": "old"})
        save_credential_set("test", "reddit", {"REDDIT_SESSION": "new"})
        sets = load_credential_sets()
        assert sets["test"].env["REDDIT_SESSION"] == "new"


class TestDelete:
    def test_delete_existing(self) -> None:
        save_credential_set("temp", "reddit", {"REDDIT_SESSION": "x"})
        assert delete_credential_set("temp") is True
        sets = load_credential_sets()
        assert "temp" not in sets

    def test_delete_nonexistent(self) -> None:
        assert delete_credential_set("ghost") is False


class TestGetPlatformSets:
    def test_filter_by_platform(self) -> None:
        save_credential_set("r1", "reddit", {"REDDIT_SESSION": "a"})
        save_credential_set("r2", "reddit", {"REDDIT_SESSION": "b"})
        save_credential_set("t1", "twitter", {"TWITTER_AUTH_TOKEN": "c"})
        assert set(get_platform_credential_sets("reddit")) == {"r1", "r2"}
        assert get_platform_credential_sets("twitter") == ["t1"]
        assert get_platform_credential_sets("youtube") == []


class TestGetEnvOverrides:
    def test_returns_env_dict(self) -> None:
        save_credential_set("test", "reddit", {"REDDIT_SESSION": "cookie", "REDDIT_USERNAME": "me"})
        overrides = get_env_overrides("test")
        assert overrides == {"REDDIT_SESSION": "cookie", "REDDIT_USERNAME": "me"}

    def test_unknown_returns_empty(self) -> None:
        assert get_env_overrides("nonexistent") == {}


class TestPlatformKeys:
    def test_all_platforms_have_keys(self) -> None:
        for platform in get_all_platforms():
            keys = get_keys_for_platform(platform)
            assert "required" in keys
            assert "optional" in keys

    def test_known_platforms(self) -> None:
        assert "reddit" in PLATFORM_CREDENTIAL_KEYS
        assert "twitter" in PLATFORM_CREDENTIAL_KEYS
        assert "instagram" in PLATFORM_CREDENTIAL_KEYS

    def test_unknown_platform(self) -> None:
        keys = get_keys_for_platform("nonexistent")
        assert keys == {"required": [], "optional": []}
