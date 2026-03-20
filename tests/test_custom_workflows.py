from __future__ import annotations

from pathlib import Path

import pytest

from marketmenow.core.workflow_registry import WorkflowRegistry


@pytest.fixture
def custom_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point _load_custom_workflows at a temp directory."""
    custom = tmp_path / "workflows" / "custom"
    custom.mkdir(parents=True)

    import marketmenow.core.workflow_registry as mod

    def patched(registry: WorkflowRegistry) -> None:
        import yaml

        from marketmenow.core.workflow import ParamDef, ParamType, Workflow
        from marketmenow.steps.registry import get_step_class

        for yaml_path in sorted(custom.glob("*.yaml")):
            try:
                with yaml_path.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                name = data.get("name", yaml_path.stem)
                description = data.get("description", "")
                step_names = data.get("steps", [])
                param_defs_raw = data.get("params", [])

                steps = []
                for sname in step_names:
                    cls = get_step_class(sname)
                    steps.append(cls())

                params = []
                for pdef in param_defs_raw:
                    params.append(
                        ParamDef(
                            name=str(pdef.get("name", "")),
                            type=ParamType(str(pdef.get("type", "string"))),
                            required=bool(pdef.get("required", False)),
                            default=pdef.get("default"),
                            help=str(pdef.get("help", "")),
                        )
                    )

                wf = Workflow(
                    name=name,
                    description=description,
                    steps=tuple(steps),
                    params=tuple(params),
                )
                registry.register(wf)
            except Exception:
                pass

    monkeypatch.setattr(mod, "_load_custom_workflows", patched)
    return custom


class TestCustomWorkflowLoading:
    def test_loads_yaml_workflow(self, custom_dir: Path) -> None:
        (custom_dir / "test-flow.yaml").write_text(
            "name: test-flow\n"
            "description: A test workflow\n"
            "steps:\n"
            "  - generate-thread\n"
            "params:\n"
            "  - name: topic\n"
            "    type: string\n"
            "    required: true\n"
            "    help: Thread topic\n"
        )

        from marketmenow.core.workflow_registry import build_workflow_registry

        registry = build_workflow_registry()
        wf = registry.get("test-flow")
        assert wf.name == "test-flow"
        assert wf.description == "A test workflow"
        assert len(wf.steps) == 1
        assert wf.steps[0].name == "generate-thread"
        assert len(wf.params) == 1
        assert wf.params[0].name == "topic"
        assert wf.params[0].required is True

    def test_empty_dir_no_error(self, custom_dir: Path) -> None:
        from marketmenow.core.workflow_registry import build_workflow_registry

        registry = build_workflow_registry()
        assert registry.list_all()

    def test_invalid_yaml_skipped(self, custom_dir: Path) -> None:
        (custom_dir / "bad.yaml").write_text("{{invalid yaml")

        from marketmenow.core.workflow_registry import build_workflow_registry

        registry = build_workflow_registry()
        assert registry.list_all()

    def test_unknown_step_skipped(self, custom_dir: Path) -> None:
        (custom_dir / "bad-steps.yaml").write_text(
            "name: bad-steps\nsteps:\n  - nonexistent-step\n"
        )

        from marketmenow.core.workflow_registry import build_workflow_registry

        registry = build_workflow_registry()
        names = {w.name for w in registry.list_all()}
        assert "bad-steps" not in names
