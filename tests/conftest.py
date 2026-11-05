import os  # noqa: F401
from types import SimpleNamespace

import pytest


@pytest.fixture(autouse=True)
def mock_os_name(monkeypatch):
    """Hide the real OS from sgpt.app.

    Patching ``os.name`` globally breaks pytest on Windows: pathlib picks its
    path flavour from ``os.name`` and cannot build a PosixPath there. Only
    ``sgpt.app`` reads ``os.name``, so patch it on that module instead.
    """
    import sgpt.app as app

    monkeypatch.setattr(app, "os", SimpleNamespace(name="test"))
