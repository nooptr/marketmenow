from __future__ import annotations

from typer.testing import CliRunner

from marketmenow.cli import app

runner = CliRunner()


class TestBanner:
    def test_bare_invocation_shows_banner(self) -> None:
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "mmn --help" in result.output
        assert "mmn workflows" in result.output

    def test_help_shows_workflows_panel(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Workflows" in result.output
        assert "run" in result.output
        assert "workflows" in result.output


class TestVersion:
    def test_version_output(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "marketmenow" in result.output


class TestPlatforms:
    def test_platforms_lists_entries(self) -> None:
        result = runner.invoke(app, ["platforms"])
        assert result.exit_code == 0
        assert "Instagram" in result.output
        assert "Twitter" in result.output or "X / Twitter" in result.output
        assert "LinkedIn" in result.output
        assert "Reddit" in result.output


class TestWorkflowsList:
    def test_workflows_shows_table(self) -> None:
        result = runner.invoke(app, ["workflows"])
        assert result.exit_code == 0
        assert "instagram-reel" in result.output
        assert "twitter-thread" in result.output
        assert "reddit-engage" in result.output
        assert "reddit-launch" in result.output


class TestRunWorkflow:
    def test_run_help(self) -> None:
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "Workflow name" in result.output

    def test_run_unknown_workflow(self) -> None:
        result = runner.invoke(app, ["run", "nonexistent-flow"])
        assert result.exit_code == 1
        assert "Unknown workflow" in result.output

    def test_run_info_flag(self) -> None:
        result = runner.invoke(app, ["run", "instagram-reel", "--info"])
        assert result.exit_code == 0
        assert "instagram-reel" in result.output
        assert "Pipeline steps" in result.output
        assert "generate-reel" in result.output
        assert "Parameters" in result.output
        assert "--template" in result.output

    def test_run_info_twitter_engage(self) -> None:
        result = runner.invoke(app, ["run", "twitter-engage", "--info"])
        assert result.exit_code == 0
        assert "discover-twitter" in result.output
        assert "generate-replies" in result.output
        assert "post-replies" in result.output

    def test_run_missing_required_param(self) -> None:
        result = runner.invoke(app, ["run", "email-outreach"])
        assert result.exit_code == 1
        assert "Missing required parameter" in result.output
        assert "--template" in result.output

    def test_run_reddit_launch_info(self) -> None:
        result = runner.invoke(app, ["run", "reddit-launch", "--info"])
        assert result.exit_code == 0
        assert "generate-reddit-posts" in result.output
        assert "post-to-subreddits" in result.output
        assert "--config" in result.output
        assert "--brief" in result.output
        assert "--product-name" in result.output


class TestAuthHelp:
    def test_auth_help(self) -> None:
        result = runner.invoke(app, ["auth", "--help"])
        assert result.exit_code == 0
        assert "twitter" in result.output
        assert "linkedin" in result.output
        assert "youtube" in result.output

    def test_auth_twitter_help(self) -> None:
        result = runner.invoke(app, ["auth", "twitter", "--help"])
        assert result.exit_code == 0
        assert "--cookies" in result.output
        assert "--force" in result.output

    def test_auth_linkedin_help(self) -> None:
        result = runner.invoke(app, ["auth", "linkedin", "--help"])
        assert result.exit_code == 0
        assert "--oauth" in result.output
        assert "--cookies" in result.output


class TestHiddenAdapterCommands:
    """Adapter CLIs are mounted as hidden groups for the web frontend.

    They should be callable but NOT visible in ``mmn --help``.
    """

    def test_hidden_from_top_level_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for name in (
            "instagram",
            "twitter",
            "linkedin",
            "reddit",
            "email",
            "youtube",
            "reel",
            "carousel",
        ):
            assert (
                name not in result.output.lower().split()
            ), f"'{name}' should be hidden from --help but was found"

    def test_reel_help_works(self) -> None:
        result = runner.invoke(app, ["reel", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output

    def test_carousel_help_works(self) -> None:
        result = runner.invoke(app, ["carousel", "--help"])
        assert result.exit_code == 0
        assert "generate" in result.output

    def test_instagram_help_works(self) -> None:
        result = runner.invoke(app, ["instagram", "--help"])
        assert result.exit_code == 0

    def test_twitter_help_works(self) -> None:
        result = runner.invoke(app, ["twitter", "--help"])
        assert result.exit_code == 0
        assert "engage" in result.output
        assert "thread" in result.output

    def test_linkedin_help_works(self) -> None:
        result = runner.invoke(app, ["linkedin", "--help"])
        assert result.exit_code == 0
        assert "post" in result.output

    def test_reddit_help_works(self) -> None:
        result = runner.invoke(app, ["reddit", "--help"])
        assert result.exit_code == 0
        assert "engage" in result.output

    def test_email_help_works(self) -> None:
        result = runner.invoke(app, ["email", "--help"])
        assert result.exit_code == 0
        assert "send" in result.output

    def test_youtube_help_works(self) -> None:
        result = runner.invoke(app, ["youtube", "--help"])
        assert result.exit_code == 0
        assert "upload" in result.output

    def test_x_alias_works(self) -> None:
        result = runner.invoke(app, ["x", "--help"])
        assert result.exit_code == 0
        assert "engage" in result.output
