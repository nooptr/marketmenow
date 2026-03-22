from __future__ import annotations

from web.cli_runner import (
    BUILDERS,
    PLATFORM_META,
    _build_carousel_generate,
    _build_carousel_publish,
    _build_email_generate,
    _build_email_publish,
    _build_linkedin_generate,
    _build_linkedin_publish,
    _build_reddit_engage_generate,
    _build_reddit_engage_publish,
    _build_reddit_launch_generate,
    _build_reddit_launch_publish,
    _build_reel_generate,
    _build_reel_publish,
    _build_twitter_all_generate,
    _build_twitter_all_publish,
    _build_twitter_engage_generate,
    _build_twitter_engage_publish,
    _build_twitter_thread_generate,
    _build_twitter_thread_publish,
    _parse_progress,
    get_builders,
    get_meta,
)

# ---------------------------------------------------------------------------
# PLATFORM_META / BUILDERS consistency
# ---------------------------------------------------------------------------


class TestMetaBuilderConsistency:
    def test_every_meta_entry_has_builders(self) -> None:
        for platform, commands in PLATFORM_META.items():
            for cmd_type in commands:
                assert get_builders(platform, cmd_type) is not None, (
                    f"PLATFORM_META has {platform}/{cmd_type} but BUILDERS does not"
                )

    def test_every_builder_has_meta(self) -> None:
        for platform, commands in BUILDERS.items():
            for cmd_type in commands:
                assert get_meta(platform, cmd_type) is not None, (
                    f"BUILDERS has {platform}/{cmd_type} but PLATFORM_META does not"
                )

    def test_get_builders_unknown_returns_none(self) -> None:
        assert get_builders("ghost", "nope") is None

    def test_get_meta_unknown_returns_none(self) -> None:
        assert get_meta("ghost", "nope") is None


# ---------------------------------------------------------------------------
# Instagram builders
# ---------------------------------------------------------------------------


class TestReelBuilders:
    def test_generate_default(self) -> None:
        cmd = _build_reel_generate({}, "/tmp/out")
        assert cmd[:3] == ["mmn", "reel", "create"]
        assert "--output-dir" in cmd
        assert "/tmp/out" in cmd

    def test_generate_with_params(self) -> None:
        params = {"template": "demo", "tts": "kokoro", "caption": "test"}
        cmd = _build_reel_generate(params, "/tmp/out")
        assert "--template" in cmd
        assert "demo" in cmd
        assert "--tts" in cmd
        assert "kokoro" in cmd
        assert "--caption" in cmd

    def test_publish_extends_generate(self) -> None:
        cmd = _build_reel_publish({}, "/tmp/out")
        assert "--publish" in cmd
        assert "mmn" in cmd


class TestCarouselBuilders:
    def test_generate(self) -> None:
        cmd = _build_carousel_generate({}, "/tmp/out")
        assert cmd[:3] == ["mmn", "carousel", "generate"]
        assert "--output-dir" in cmd

    def test_publish_has_publish_flag(self) -> None:
        cmd = _build_carousel_publish({}, "/tmp/out")
        assert "--publish" in cmd


# ---------------------------------------------------------------------------
# LinkedIn builders
# ---------------------------------------------------------------------------


class TestLinkedInBuilders:
    def test_generate_dry_run(self) -> None:
        cmd = _build_linkedin_generate({}, "/tmp/out")
        assert "linkedin" in cmd
        assert "--dry-run" in cmd

    def test_publish_with_text(self) -> None:
        cmd = _build_linkedin_publish({"text": "Hello world"}, "/tmp/out")
        assert "--text" in cmd
        assert "Hello world" in cmd

    def test_publish_without_text_uses_all(self) -> None:
        cmd = _build_linkedin_publish({}, "/tmp/out")
        assert "all" in cmd
        assert "--count" in cmd


# ---------------------------------------------------------------------------
# Twitter builders
# ---------------------------------------------------------------------------


class TestTwitterBuilders:
    def test_thread_generate(self) -> None:
        cmd = _build_twitter_thread_generate({"topic": "AI"}, "/tmp/out")
        assert "thread" in cmd
        assert "--topic" in cmd
        assert "AI" in cmd

    def test_thread_publish_has_post(self) -> None:
        cmd = _build_twitter_thread_publish({"topic": "AI"}, "/tmp/out")
        assert "--post" in cmd

    def test_all_generate_headless(self) -> None:
        cmd = _build_twitter_all_generate({}, "/tmp/out")
        assert "--headless" in cmd
        assert any("replies.csv" in arg for arg in cmd)

    def test_all_publish(self) -> None:
        cmd = _build_twitter_all_publish({"max_replies": 5}, "/tmp/out")
        assert "all" in cmd
        assert "--max-replies" in cmd
        assert "5" in cmd

    def test_engage_generate(self) -> None:
        cmd = _build_twitter_engage_generate({}, "/tmp/out")
        assert "engage" in cmd
        assert "replies.csv" in cmd[-1]

    def test_engage_publish(self) -> None:
        cmd = _build_twitter_engage_publish({}, "/tmp/out")
        assert "reply" in cmd
        assert "replies.csv" in cmd[-1]


# ---------------------------------------------------------------------------
# Reddit builders
# ---------------------------------------------------------------------------


class TestRedditBuilders:
    def test_engage_generate(self) -> None:
        cmd = _build_reddit_engage_generate({}, "/tmp/out")
        assert "engage" in cmd
        assert "comments.csv" in cmd[-1]

    def test_engage_generate_with_max(self) -> None:
        cmd = _build_reddit_engage_generate({"max_comments": 10}, "/tmp/out")
        assert "--max-comments" in cmd
        assert "10" in cmd

    def test_engage_publish(self) -> None:
        cmd = _build_reddit_engage_publish({}, "/tmp/out")
        assert "reply" in cmd
        assert "comments.csv" in cmd[-1]

    def test_launch_generate_dry_run(self) -> None:
        cmd = _build_reddit_launch_generate(
            {"product_name": "TestApp", "subreddits": "buildinpublic,microsaas"},
            "/tmp/out",
        )
        assert cmd[:3] == ["mmn", "run", "reddit-launch"]
        assert "--dry-run" in cmd
        assert "--product-name" in cmd
        assert "TestApp" in cmd
        assert "--subreddits" in cmd

    def test_launch_publish(self) -> None:
        cmd = _build_reddit_launch_publish(
            {"config": "campaigns/test.yaml", "post_type": "milestone"},
            "/tmp/out",
        )
        assert cmd[:3] == ["mmn", "run", "reddit-launch"]
        assert "--dry-run" not in cmd
        assert "--config" in cmd
        assert "--post-type" in cmd
        assert "milestone" in cmd

    def test_launch_generate_with_brief(self) -> None:
        cmd = _build_reddit_launch_generate({"brief": "We shipped dark mode"}, "/tmp/out")
        assert "--brief" in cmd
        assert "We shipped dark mode" in cmd


# ---------------------------------------------------------------------------
# Email builders
# ---------------------------------------------------------------------------


class TestEmailBuilders:
    def test_generate_dry_run(self) -> None:
        cmd = _build_email_generate(
            {"template": "invite.html", "file": "contacts.csv", "subject": "Hello"},
            "/tmp/out",
        )
        assert "--dry-run" in cmd
        assert "-t" in cmd
        assert "-f" in cmd
        assert "-s" in cmd

    def test_publish_no_dry_run(self) -> None:
        cmd = _build_email_publish(
            {"template": "invite.html", "file": "contacts.csv", "subject": "Hello"},
            "/tmp/out",
        )
        assert "--dry-run" not in cmd
        assert "-t" in cmd


# ---------------------------------------------------------------------------
# Progress parser
# ---------------------------------------------------------------------------


class TestProgressParser:
    def test_waiting_line(self) -> None:
        evt = _parse_progress("Waiting 300s before next reply...")
        assert evt is not None
        assert evt.event_type == "wait"
        assert evt.wait_seconds == 300

    def test_generating_reply_progress(self) -> None:
        evt = _parse_progress("Generating reply 3/10")
        assert evt is not None
        assert evt.event_type == "progress"
        assert evt.current == 3
        assert evt.total == 10

    def test_generic_generating(self) -> None:
        evt = _parse_progress("Generating thread for topic...")
        assert evt is not None
        assert evt.event_type == "phase"
        assert evt.phase == "generation"

    def test_posted_reply(self) -> None:
        evt = _parse_progress("Posted reply 2/5 successfully")
        assert evt is not None
        assert evt.event_type == "progress"
        assert evt.phase == "posting"

    def test_discovery(self) -> None:
        evt = _parse_progress("Discovered 15 posts from handles")
        assert evt is not None
        assert evt.phase == "discovery"
        assert evt.total == 15

    def test_discovering_phase(self) -> None:
        evt = _parse_progress("Discovering relevant posts...")
        assert evt is not None
        assert evt.phase == "discovery"

    def test_error_detection(self) -> None:
        evt = _parse_progress("ERROR: something went wrong")
        assert evt is not None
        assert evt.event_type == "error"

    def test_traceback_detection(self) -> None:
        evt = _parse_progress("Traceback (most recent call last):")
        assert evt is not None
        assert evt.event_type == "error"

    def test_saved_replies(self) -> None:
        evt = _parse_progress("Saved 12 replies to output/replies.csv")
        assert evt is not None
        assert evt.event_type == "done"
        assert evt.total == 12

    def test_unrecognized_line_returns_none(self) -> None:
        evt = _parse_progress("Just a normal log line")
        assert evt is None

    def test_empty_line_returns_none(self) -> None:
        evt = _parse_progress("")
        assert evt is None

    def test_handles_hashtags_progress(self) -> None:
        evt = _parse_progress("Handles 3/5  Hashtags 2/4  Posts 12")
        assert evt is not None
        assert evt.event_type == "progress"
        assert evt.phase == "discovery"
        assert evt.current == 5
        assert evt.total == 9

    def test_engagement_complete(self) -> None:
        evt = _parse_progress("Engagement complete")
        assert evt is not None
        assert evt.event_type == "done"
