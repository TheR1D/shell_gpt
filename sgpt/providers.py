"""Provider presets and the ``providers.json`` profile store.

A profile never holds a secret: ``api_key_env`` is the *name* of an environment
variable, and the key is read at request time.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from click import UsageError

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
DEFAULT_PATH = Path(os.path.expanduser("~/.config/shell_gpt/providers.json"))

_replace = os.replace  # patchable seam for the atomic-write test


@dataclass(frozen=True)
class Preset:
    base_url: str
    model: str
    api_key_env: str | None


# Every preset below speaks OpenAI-compatible Chat Completions, which is why no
# provider-specific client or litellm route is needed.
PRESETS: dict[str, Preset] = {
    # Verified against each vendor's docs on 2026-11-05. Model names move; the
    # wizard lets the user type a different one without touching this table.
    "openai": Preset("https://api.openai.com/v1", "gpt-6-luna", "OPENAI_API_KEY"),
    "anthropic": Preset(
        "https://api.anthropic.com/v1/", "claude-sonnet-5-5", "ANTHROPIC_API_KEY"
    ),
    "gemini": Preset(
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini-3.8-flash",
        "GEMINI_API_KEY",
    ),
    "deepseek": Preset(
        "https://api.deepseek.com", "deepseek-flash", "DEEPSEEK_API_KEY"
    ),
    "openrouter": Preset(
        "https://openrouter.ai/api/v1",
        "anthropic/claude-sonnet-5.5",
        "OPENROUTER_API_KEY",
    ),
    "groq": Preset(
        "https://api.groq.com/openai/v1", "openai/gpt-oss-120b", "GROQ_API_KEY"
    ),
    "mistral": Preset(
        "https://api.mistral.ai/v1", "mistral-large-4", "MISTRAL_API_KEY"
    ),
    "ollama": Preset("http://localhost:11434/v1", "qwen3:8b", None),
}


@dataclass(frozen=True)
class Provider:
    name: str
    preset: str
    base_url: str
    model: str
    api_key_env: str | None = None
    # Set only when a key was pasted into the wizard instead of a variable name.
    # Upstream already stores OPENAI_API_KEY in .sgptrc the same way.
    api_key_value: str | None = None

    def api_key(self) -> str | None:
        if self.api_key_env and os.getenv(self.api_key_env):
            return os.getenv(self.api_key_env)
        if self.api_key_value:
            return self.api_key_value
        if self.api_key_env:
            return None
        return _legacy("OPENAI_API_KEY") or (
            "ollama" if self.preset == "ollama" else None
        )

    @property
    def key_present(self) -> bool:
        return bool(self.api_key()) or not self.api_key_env

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "preset": self.preset,
            "base_url": self.base_url,
            "model": self.model,
            "api_key_env": self.api_key_env,
        }
        if self.api_key_value:
            data["api_key"] = self.api_key_value
        return data


def path() -> Path:
    """Location of the profile store (overridable for tests)."""
    override = os.getenv("SGPT_PROVIDERS_PATH")
    return Path(override) if override else DEFAULT_PATH


def _legacy(key: str) -> Any:
    from .config import cfg

    try:
        return cfg.get(key)
    except UsageError:
        return None


def _read() -> dict[str, Any]:
    file = path()
    if not file.exists():
        return {}
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        with suppress(OSError):
            file.replace(file.with_name(file.name + ".bak"))
        return {}
    return data if isinstance(data, dict) else {}


def _write(data: dict[str, Any]) -> None:
    file = path()
    file.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(
        dir=str(file.parent), prefix=".providers-", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        if os.name == "posix":
            os.chmod(tmp, 0o600)
        _replace(tmp, file)
    except BaseException:
        with suppress(OSError):
            os.unlink(tmp)
        raise


def profiles() -> dict[str, Provider]:
    """All saved profiles, skipping any entry that cannot be read."""
    found: dict[str, Provider] = {}
    for name, item in (_read().get("providers") or {}).items():
        if not isinstance(item, dict):
            continue
        if not all(item.get(field) for field in ("base_url", "model")):
            continue
        found[name] = Provider(
            name=name,
            preset=str(item.get("preset") or "custom"),
            base_url=item["base_url"],
            model=item["model"],
            api_key_env=item.get("api_key_env") or None,
            api_key_value=item.get("api_key") or None,
        )
    return found


def active_name() -> str | None:
    name = _read().get("active")
    return name if name in profiles() else None


def save(provider: Provider, *, activate: bool = True) -> None:
    data = _read()
    stored = data.get("providers")
    data["providers"] = stored if isinstance(stored, dict) else {}
    data["version"] = 1
    data["providers"][provider.name] = provider.to_dict()
    if activate or not data.get("active"):
        data["active"] = provider.name
    _write(data)


def set_active(name: str) -> None:
    if name not in profiles():
        raise UsageError(f"No such provider: {name}. Known: {known_names()}")
    data = _read()
    data["active"] = name
    _write(data)


def remove(name: str) -> None:
    data = _read()
    stored = data.get("providers")
    if not isinstance(stored, dict) or name not in stored:
        raise UsageError(f"No such provider: {name}. Known: {known_names()}")
    del stored[name]
    if data.get("active") == name:
        data["active"] = next(iter(stored), None)
    _write(data)


def known_names() -> str:
    return ", ".join(sorted(profiles())) or "none"


def _legacy_base_url() -> str | None:
    value = _legacy("API_BASE_URL")
    return None if not value or value == "default" else value


def resolve(name: str | None = None) -> Provider:
    """CLI flag > SGPT_PROVIDER > active profile > legacy ``.sgptrc`` values."""
    saved = profiles()
    chosen = name or os.getenv("SGPT_PROVIDER") or active_name()
    if chosen and chosen not in saved:
        raise UsageError(f"No such provider: {chosen}. Known: {known_names()}")

    provider = saved[chosen] if chosen else None
    if provider is None:
        provider = Provider(
            name="default",
            preset="custom",
            base_url=_legacy_base_url() or "",
            model=_legacy("DEFAULT_MODEL") or "gpt-5.4-mini",
            api_key_env=None,
        )

    override = _legacy_base_url()
    if override and override != provider.base_url:
        provider = Provider(
            name=provider.name,
            preset=provider.preset,
            base_url=override,
            model=provider.model,
            api_key_env=provider.api_key_env,
            api_key_value=provider.api_key_value,
        )
    return provider


def rows() -> list[tuple[str, str, str, str, str, str, str]]:
    """Display rows: name, preset, model, base URL, key var, key state, active."""
    active = active_name()
    return [
        (
            provider.name,
            provider.preset,
            provider.model,
            provider.base_url,
            provider.api_key_env or "-",
            _key_label(provider),
            "yes" if provider.name == active else "",
        )
        for provider in sorted(profiles().values(), key=lambda item: item.name)
    ]


def _key_label(provider: Provider) -> str:
    if provider.api_key_value:
        return "stored"
    if not provider.api_key_env:
        return "none"
    return "ok" if provider.key_present else "missing"
