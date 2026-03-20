from __future__ import annotations

from adapters.reddit.post_generator import _parse_post


class TestParsePost:
    def test_standard_format(self) -> None:
        raw = """TITLE: I grew my side project to 1,500 users using only Reddit

BODY:
I've been building a side project for the last 6 months. Here's what worked.

No ads. No Twitter. Just Reddit posts."""
        title, body = _parse_post(raw)
        assert title == "I grew my side project to 1,500 users using only Reddit"
        assert "6 months" in body
        assert "Just Reddit posts." in body

    def test_title_only_no_body_marker(self) -> None:
        raw = """TITLE: Quick update on the project

We shipped dark mode this week. Pretty happy with how it turned out."""
        title, _body = _parse_post(raw)
        assert title == "Quick update on the project"

    def test_no_markers_at_all(self) -> None:
        raw = """Some random LLM output
that doesn't follow the format
at all."""
        title, body = _parse_post(raw)
        assert title == "Some random LLM output"
        assert "doesn't follow the format" in body

    def test_empty_input(self) -> None:
        title, body = _parse_post("")
        assert title == "Update"
        assert body == ""

    def test_multiline_body(self) -> None:
        raw = """TITLE: Milestone: 500 users

BODY:
Line one of the body.

Line two with a blank line above.

**Bold markdown** and *italic* too."""
        title, body = _parse_post(raw)
        assert title == "Milestone: 500 users"
        assert "Line one" in body
        assert "Line two" in body
        assert "**Bold markdown**" in body

    def test_body_preserves_reddit_markdown(self) -> None:
        raw = """TITLE: Test

BODY:
Here's a list:
- Item 1
- Item 2

And some **bold text**."""
        _, body = _parse_post(raw)
        assert "- Item 1" in body
        assert "**bold text**" in body
