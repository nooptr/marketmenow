from __future__ import annotations

from marketmenow.steps.registry import get_step_class, list_steps


class TestGetStepClass:
    def test_known_step(self) -> None:
        cls = get_step_class("generate-reel")
        assert cls is not None
        assert cls.__name__ == "GenerateReelStep"

    def test_all_registered_steps(self) -> None:
        expected = {
            "generate-reel",
            "generate-carousel",
            "generate-thread",
            "generate-reddit-posts",
            "generate-replies",
            "post-to-platform",
            "post-to-subreddits",
            "post-replies",
            "discover-posts",
            "linkedin-post",
            "send-emails",
            "youtube-upload",
        }
        for name in expected:
            cls = get_step_class(name)
            assert cls is not None, f"Step '{name}' not found"

    def test_unknown_raises(self) -> None:
        import pytest

        with pytest.raises(KeyError, match="Unknown step"):
            get_step_class("nonexistent-step")


class TestListSteps:
    def test_returns_list(self) -> None:
        steps = list_steps()
        assert isinstance(steps, list)
        assert len(steps) >= 10

    def test_step_info_fields(self) -> None:
        steps = list_steps()
        for info in steps:
            assert info.name
            assert info.description
            assert info.cls is not None

    def test_names_are_unique(self) -> None:
        steps = list_steps()
        names = [s.name for s in steps]
        assert len(names) == len(set(names))
