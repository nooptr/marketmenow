from __future__ import annotations

import logging

from marketmenow.core.workflow import Workflow, WorkflowError

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Holds registered workflows keyed by name."""

    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}

    def register(self, workflow: Workflow) -> None:
        if workflow.name in self._workflows:
            raise WorkflowError(f"Workflow already registered: {workflow.name}")
        self._workflows[workflow.name] = workflow
        logger.debug("Registered workflow: %s", workflow.name)

    def get(self, name: str) -> Workflow:
        if name not in self._workflows:
            raise WorkflowError(f"Unknown workflow: {name}")
        return self._workflows[name]

    def list_all(self) -> list[Workflow]:
        return list(self._workflows.values())


def build_workflow_registry() -> WorkflowRegistry:
    """Auto-register all built-in workflows.

    Each workflow is attempted independently; import or config errors
    cause that workflow to be silently skipped.
    """
    registry = WorkflowRegistry()

    _try_register(registry, "marketmenow.workflows.instagram_reel", "workflow")
    _try_register(registry, "marketmenow.workflows.instagram_carousel", "workflow")
    _try_register(registry, "marketmenow.workflows.twitter_thread", "workflow")
    _try_register(registry, "marketmenow.workflows.twitter_engage", "workflow")
    _try_register(registry, "marketmenow.workflows.reddit_engage", "workflow")
    _try_register(registry, "marketmenow.workflows.linkedin_post", "workflow")
    _try_register(registry, "marketmenow.workflows.email_outreach", "workflow")
    _try_register(registry, "marketmenow.workflows.youtube_short", "workflow")
    _try_register(registry, "marketmenow.workflows.reddit_launch", "workflow")

    return registry


def _try_register(
    registry: WorkflowRegistry,
    module_path: str,
    attr_name: str,
) -> None:
    """Import *module_path*, grab the ``attr_name`` attribute, and register it."""
    import importlib

    try:
        mod = importlib.import_module(module_path)
        workflow = getattr(mod, attr_name)
        registry.register(workflow)
    except Exception as exc:
        logger.debug("Skipping workflow from %s: %s", module_path, exc)
