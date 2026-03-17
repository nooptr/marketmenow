from __future__ import annotations

import logging

from marketmenow.registry import AdapterRegistry

logger = logging.getLogger(__name__)


def build_registry() -> AdapterRegistry:
    """Auto-register all available platform bundles.

    Each adapter is attempted independently; if credentials are missing or the
    adapter's settings fail validation the platform is silently skipped so that
    the remaining platforms still work.
    """
    registry = AdapterRegistry()

    _try_instagram(registry)
    _try_twitter(registry)
    _try_linkedin(registry)

    return registry


def _try_instagram(registry: AdapterRegistry) -> None:
    try:
        from adapters.instagram import create_instagram_bundle
        from adapters.instagram.settings import InstagramSettings

        settings = InstagramSettings()
        bundle = create_instagram_bundle(settings)
        registry.register(bundle)
        logger.debug("Registered instagram adapter")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Skipping instagram adapter: %s", exc)


def _try_twitter(registry: AdapterRegistry) -> None:
    try:
        from adapters.twitter import create_twitter_bundle
        from adapters.twitter.settings import TwitterSettings

        settings = TwitterSettings()
        bundle = create_twitter_bundle(settings)
        registry.register(bundle)
        logger.debug("Registered twitter adapter")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Skipping twitter adapter: %s", exc)


def _try_linkedin(registry: AdapterRegistry) -> None:
    try:
        from adapters.linkedin import create_linkedin_bundle
        from adapters.linkedin.settings import LinkedInSettings

        settings = LinkedInSettings()
        bundle = create_linkedin_bundle(settings)
        registry.register(bundle)
        logger.debug("Registered linkedin adapter")
    except Exception as exc:  # noqa: BLE001
        logger.debug("Skipping linkedin adapter: %s", exc)
