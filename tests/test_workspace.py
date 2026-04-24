"""Tests for core/workspace.py"""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from corbell.core.workspace import (
    WorkspaceConfig,
    find_workspace_root,
    init_workspace_yaml,
    load_workspace,
)


def test_load_workspace_basic(sample_workspace_yaml, sample_repo):
    cfg = load_workspace(sample_workspace_yaml)
    assert cfg.workspace.name == "test-platform"
    assert len(cfg.services) == 1
    assert cfg.services[0].id == "sample-service"
    assert cfg.services[0].resolved_path == sample_repo


def test_load_workspace_from_dir(sample_workspace_yaml):
    cfg = load_workspace(sample_workspace_yaml.parent)
    assert cfg.workspace.name == "test-platform"


def test_load_workspace_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_workspace(tmp_path / "nonexistent" / "workspace.yaml")


def test_init_workspace_yaml(tmp_path):
    out = init_workspace_yaml(tmp_path)
    assert out.exists()
    raw = yaml.safe_load(out.read_text())
    assert "services" in raw
    assert raw["workspace"]["name"] == "my-platform"
    assert raw["llm"]["api_key"] is None
    assert raw["integrations"]["jira"]["url"] is None


def test_init_workspace_yaml_overwrite(tmp_path):
    out1 = init_workspace_yaml(tmp_path)
    out2 = init_workspace_yaml(tmp_path)
    assert out1 == out2


def test_cli_init_creates_workspace_under_corbell_data(tmp_path):
    from corbell.cli.main import app

    runner = CliRunner()
    target = tmp_path / "workspace-root"
    target.mkdir()

    result = runner.invoke(app, ["init", "--dir", str(target)])

    ws_file = target / "corbell-data" / "workspace.yaml"
    assert result.exit_code == 0, result.output
    assert ws_file.exists()


def test_cli_init_respects_existing_workspace_without_force(tmp_path):
    from corbell.cli.main import app

    runner = CliRunner()
    target = tmp_path / "workspace-root"
    ws_dir = target / "corbell-data"
    ws_dir.mkdir(parents=True)
    ws_file = ws_dir / "workspace.yaml"
    original = 'version: "1"\nworkspace:\n  name: custom-platform\n'
    ws_file.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["init", "--dir", str(target)])

    assert result.exit_code == 0, result.output
    assert "already exists" in result.output
    assert ws_file.read_text(encoding="utf-8") == original


def test_find_workspace_root(tmp_path, sample_workspace_yaml):
    # Should find from inside the workspace dir
    root = find_workspace_root(sample_workspace_yaml.parent)
    assert root is not None


def test_find_workspace_root_not_found(tmp_path):
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    assert find_workspace_root(isolated) is None


def test_llm_config_resolved_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    config_dir = tmp_path / "corbell"
    config_dir.mkdir()
    ws = config_dir / "workspace.yaml"
    ws.write_text("""
version: "1"
workspace:
  name: test
services: []
llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
""")
    cfg = load_workspace(ws)
    assert cfg.llm.resolved_api_key() == "sk-test-123"


def test_db_path_creates_parent(sample_workspace_yaml, tmp_path):
    cfg = load_workspace(sample_workspace_yaml)
    db = cfg.db_path(sample_workspace_yaml.parent)
    assert db.parent.exists()


def test_detect_language(tmp_path):
    from corbell.core.workspace import _detect_language

    # Test typescript
    ts_dir = tmp_path / "ts-proj"
    ts_dir.mkdir()
    (ts_dir / "package.json").touch()
    assert _detect_language(ts_dir) == "typescript"

    # Test python
    py_dir = tmp_path / "py-proj"
    py_dir.mkdir()
    (py_dir / "requirements.txt").touch()
    assert _detect_language(py_dir) == "python"

    # Test java
    java_dir = tmp_path / "java-proj"
    java_dir.mkdir()
    (java_dir / "pom.xml").touch()
    assert _detect_language(java_dir) == "java"

    # Test unknown fallback
    unk_dir = tmp_path / "unknown-proj"
    unk_dir.mkdir()
    assert _detect_language(unk_dir) == "python"


def test_detect_services_monorepo(tmp_path):
    from corbell.core.workspace import _detect_services

    target_dir = tmp_path / "monorepo"
    target_dir.mkdir()
    
    # Not a service dir, just node_modules
    (target_dir / "node_modules").mkdir()
    
    # Service 1
    s1 = target_dir / "service1"
    s1.mkdir()
    (s1 / "package.json").touch()

    # Service 2
    s2 = target_dir / "api"
    s2.mkdir()
    (s2 / "requirements.txt").touch()

    services = _detect_services(target_dir)
    assert len(services) == 2
    
    # Sort them to verify properties predictably
    services.sort(key=lambda s: s["id"])
    
    assert services[0]["id"] == "api"
    assert services[0]["language"] == "python"
    assert services[0]["repo"] == "../api"

    assert services[1]["id"] == "service1"
    assert services[1]["language"] == "typescript"
    assert services[1]["repo"] == "../service1"


def test_detect_services_single_repo(tmp_path):
    from corbell.core.workspace import _detect_services

    target_dir = tmp_path / "my-api"
    target_dir.mkdir()
    (target_dir / "go.mod").touch()
    (target_dir / ".git").mkdir()

    services = _detect_services(target_dir)
    assert len(services) == 1
    assert services[0]["id"] == "my-api"
    assert services[0]["language"] == "go"
    assert services[0]["repo"] == ".."
