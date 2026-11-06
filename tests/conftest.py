import os  # noqa: F401
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def mock_os_name(monkeypatch):
    """Hide the real OS from sgpt.app.

    Upstream patched ``os.name`` globally, which crashes pytest on Windows:
    pathlib picks its path flavour from ``os.name`` and cannot build a PosixPath
    there. Only ``sgpt.app`` reads ``os.name``, so patch it there instead.
    """
    import sgpt.app as app

    monkeypatch.setattr(app, "os", SimpleNamespace(name="test"))


@pytest.fixture(autouse=True)
def isolated_providers(tmp_path, monkeypatch):
    """Never let a developer's real providers.json leak into a test run."""
    monkeypatch.setenv("SGPT_PROVIDERS_PATH", str(tmp_path / "providers.json"))
    monkeypatch.delenv("SGPT_PROVIDER", raising=False)
