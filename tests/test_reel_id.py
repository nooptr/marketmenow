from __future__ import annotations

from marketmenow.core.reel_id import (
    WORDLIST,
    decode_reel_id,
    encode_reel_id,
    generate_reel_id,
    template_type_id_from_slug,
)


def test_wordlist_has_256_entries() -> None:
    assert len(WORDLIST) == 256


def test_wordlist_entries_are_unique() -> None:
    assert len(set(WORDLIST)) == 256


def test_round_trip_encode_decode() -> None:
    reel_id = b"\x00\x01\x02\x03"
    tmpl_id = b"\xff\xfe\xfd\xfc"
    encoded = encode_reel_id(reel_id, tmpl_id)
    result = decode_reel_id(encoded)
    assert result is not None
    assert result.reel_id == reel_id.hex()
    assert result.template_type_id == tmpl_id.hex()


def test_round_trip_random() -> None:
    reel_id = generate_reel_id()
    tmpl_id = template_type_id_from_slug("can_ai_grade_this")
    encoded = encode_reel_id(reel_id, tmpl_id)
    result = decode_reel_id(encoded)
    assert result is not None
    assert result.reel_id == reel_id.hex()
    assert result.template_type_id == tmpl_id.hex()


def test_encode_starts_with_sentinel() -> None:
    encoded = encode_reel_id(b"\x00\x00\x00\x00", b"\x00\x00\x00\x00")
    assert encoded.startswith("Crafted with ")


def test_decode_returns_none_when_no_sentinel() -> None:
    assert decode_reel_id("Just a regular description with no ID") is None


def test_decode_returns_none_on_partial_words() -> None:
    assert decode_reel_id("Crafted with amber anchor apple") is None


def test_decode_returns_none_on_unknown_words() -> None:
    assert decode_reel_id("Crafted with zzzzz amber anchor apple arctic aspen atlas aurora") is None


def test_decode_in_longer_description() -> None:
    reel_id = b"\x0a\x0b\x0c\x0d"
    tmpl_id = b"\x10\x11\x12\x13"
    id_str = encode_reel_id(reel_id, tmpl_id)
    description = f"Great video about AI!\n\nhttps://gradeasy.ai\n\n#shorts #ai\n\n{id_str}"
    result = decode_reel_id(description)
    assert result is not None
    assert result.reel_id == reel_id.hex()
    assert result.template_type_id == tmpl_id.hex()


def test_template_type_id_deterministic() -> None:
    a = template_type_id_from_slug("reddit_aita_story")
    b = template_type_id_from_slug("reddit_aita_story")
    assert a == b
    assert len(a) == 4


def test_template_type_id_different_for_different_slugs() -> None:
    a = template_type_id_from_slug("reddit_aita_story")
    b = template_type_id_from_slug("can_ai_grade_this")
    assert a != b


def test_generate_reel_id_is_4_bytes() -> None:
    assert len(generate_reel_id()) == 4


def test_generate_reel_id_is_random() -> None:
    ids = {generate_reel_id() for _ in range(100)}
    assert len(ids) > 90  # extremely unlikely to have collisions
