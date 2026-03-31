from __future__ import annotations

import hashlib
import os
import re

from pydantic import BaseModel

_SENTINEL = "Crafted with"

# fmt: off
WORDLIST: tuple[str, ...] = (
    "amber", "anchor", "apple", "arctic", "aspen", "atlas", "aurora", "autumn",
    "bamboo", "basil", "beacon", "birch", "bloom", "bluff", "bolt", "breeze",
    "bridge", "bright", "brook", "brush", "calm", "canopy", "canyon", "cape",
    "cedar", "chalk", "chime", "cliff", "cloud", "clover", "coast", "cobalt",
    "coral", "crest", "crisp", "crown", "crystal", "cypress", "dapple", "dawn",
    "delta", "dew", "drift", "dune", "dusk", "eagle", "echo", "edge",
    "elm", "ember", "fable", "fawn", "fern", "field", "finch", "flame",
    "flint", "flora", "forge", "frost", "gale", "garden", "garnet", "gentle",
    "glade", "gleam", "glen", "glow", "grain", "grove", "gust", "harbor",
    "haven", "hawk", "hazel", "heath", "heron", "hill", "holly", "honey",
    "horizon", "hue", "ice", "inlet", "iris", "isle", "ivory", "ivy",
    "jade", "jasper", "jewel", "juniper", "keen", "kelp", "kindle", "knoll",
    "lace", "lake", "lapis", "lark", "laurel", "lava", "leaf", "light",
    "lily", "linden", "lotus", "lunar", "maple", "marble", "marsh", "meadow",
    "mesa", "mist", "moon", "moss", "nectar", "nimbus", "north", "nova",
    "oak", "oasis", "ocean", "olive", "onyx", "opal", "orchid", "osprey",
    "palm", "path", "peak", "pearl", "pebble", "pine", "plain", "plume",
    "pond", "poplar", "prism", "pulse", "quartz", "quest", "quiet", "quill",
    "rain", "rapid", "raven", "ray", "reef", "ridge", "ripple", "river",
    "robin", "root", "rose", "ruby", "rush", "sage", "sand", "sapphire",
    "scarlet", "sea", "shade", "shell", "shore", "silk", "silver", "sky",
    "slate", "snow", "solar", "spark", "spire", "spruce", "star", "steel",
    "stone", "storm", "stream", "summit", "sun", "swift", "thorn", "tide",
    "timber", "trail", "tulip", "tundra", "vale", "valley", "velvet", "verdant",
    "vine", "violet", "vista", "vivid", "wander", "wave", "whisper", "wild",
    "willow", "wind", "winter", "wisteria", "wonder", "wood", "wren", "yarrow",
    "yew", "zenith", "zephyr", "agate", "blaze", "branch", "cinder", "copper",
    "dahlia", "dove", "driftwood", "emerald", "fennel", "glacier", "hemlock", "indigo",
    "jasmine", "kite", "lantern", "magnolia", "nutmeg", "obsidian", "peony", "plum",
    "quince", "rosemary", "sable", "tansy", "umber", "vervain", "walnut", "zinnia",
    "aster", "birdsong", "chamomile", "dogwood", "edelweiss", "foxglove", "goldenrod", "heather",
    "ironwood", "junco", "kingfisher", "lavender", "marigold", "nightshade", "oleander", "primrose",
)
# fmt: on

assert len(WORDLIST) == 256, f"WORDLIST must have exactly 256 entries, got {len(WORDLIST)}"

_WORD_TO_BYTE: dict[str, int] = {word: idx for idx, word in enumerate(WORDLIST)}


class ReelIdentifier(BaseModel, frozen=True):
    """Decoded reel and template type identifiers."""

    reel_id: str
    template_type_id: str


def generate_reel_id() -> bytes:
    """Generate a random 4-byte reel identifier."""
    return os.urandom(4)


def template_type_id_from_slug(slug: str) -> bytes:
    """Derive a 4-byte template type ID from a template slug via SHA-256."""
    return hashlib.sha256(slug.encode()).digest()[:4]


def encode_reel_id(reel_id: bytes, template_type_id: bytes) -> str:
    """Encode reel_id (4 bytes) and template_type_id (4 bytes) as a natural-looking word sequence.

    Returns a string like: "Crafted with bright coral dawn echo field gentle harbor iris"
    """
    if len(reel_id) != 4:
        raise ValueError(f"reel_id must be 4 bytes, got {len(reel_id)}")
    if len(template_type_id) != 4:
        raise ValueError(f"template_type_id must be 4 bytes, got {len(template_type_id)}")

    words = [WORDLIST[b] for b in reel_id] + [WORDLIST[b] for b in template_type_id]
    return f"{_SENTINEL} {' '.join(words)}"


def decode_reel_id(description: str) -> ReelIdentifier | None:
    """Extract a ReelIdentifier from a YouTube description, or None if not found."""
    pattern = re.escape(_SENTINEL) + r"\s+((?:\S+\s+){7}\S+)"
    match = re.search(pattern, description)
    if not match:
        return None

    words = match.group(1).strip().split()
    if len(words) != 8:
        return None

    try:
        reel_bytes = bytes(_WORD_TO_BYTE[w] for w in words[:4])
        template_bytes = bytes(_WORD_TO_BYTE[w] for w in words[4:])
    except KeyError:
        return None

    return ReelIdentifier(
        reel_id=reel_bytes.hex(),
        template_type_id=template_bytes.hex(),
    )
