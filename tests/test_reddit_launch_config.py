from __future__ import annotations

import pytest

from marketmenow.core.workflow import WorkflowError
from marketmenow.steps.generate_reddit_post import (
    _load_campaign_config,
    _read_brief,
)


class TestLoadCampaignConfig:
    def test_loads_valid_yaml(self, tmp_path: object) -> None:
        from pathlib import Path

        p = Path(str(tmp_path)) / "campaign.yaml"
        p.write_text(
            "product:\n"
            "  name: TestApp\n"
            "  url: https://test.app\n"
            "  description: A test app\n"
            "subreddits:\n"
            "  - buildinpublic\n"
            "  - microsaas\n"
            "post_type: launch\n"
        )
        cfg = _load_campaign_config(str(p))
        assert cfg["product"]["name"] == "TestApp"  # type: ignore[index]
        assert cfg["subreddits"] == ["buildinpublic", "microsaas"]
        assert cfg["post_type"] == "launch"

    def test_missing_file_raises(self) -> None:
        with pytest.raises(WorkflowError, match="Config file not found"):
            _load_campaign_config("/nonexistent/campaign.yaml")

    def test_empty_yaml_returns_empty_dict(self, tmp_path: object) -> None:
        from pathlib import Path

        p = Path(str(tmp_path)) / "empty.yaml"
        p.write_text("")
        cfg = _load_campaign_config(str(p))
        assert cfg == {}

    def test_posting_section(self, tmp_path: object) -> None:
        from pathlib import Path

        p = Path(str(tmp_path)) / "campaign.yaml"
        p.write_text(
            "product:\n"
            "  name: X\n"
            "  description: Y\n"
            "subreddits: [a]\n"
            "posting:\n"
            "  min_delay: 60\n"
            "  max_delay: 180\n"
        )
        cfg = _load_campaign_config(str(p))
        assert cfg["posting"]["min_delay"] == 60  # type: ignore[index]
        assert cfg["posting"]["max_delay"] == 180  # type: ignore[index]


class TestReadBrief:
    def test_inline_text_returned_as_is(self) -> None:
        result = _read_brief("We just shipped dark mode and 500 users loved it")
        assert result == "We just shipped dark mode and 500 users loved it"

    def test_file_path_reads_contents(self, tmp_path: object) -> None:
        from pathlib import Path

        p = Path(str(tmp_path)) / "notes.md"
        p.write_text("# Release Notes\n\nWe added dark mode.\n")
        result = _read_brief(str(p))
        assert "Release Notes" in result
        assert "dark mode" in result

    def test_nonexistent_path_treated_as_text(self) -> None:
        result = _read_brief("/this/file/does/not/exist.md")
        assert result == "/this/file/does/not/exist.md"

    def test_empty_string(self) -> None:
        result = _read_brief("")
        assert result == ""
