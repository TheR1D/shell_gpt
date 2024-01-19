import os

import pytest


@pytest.fixture(autouse=True)
def mock_os_name(monkeypatch):
    monkeypatch.setattr(os, "name", "test")
