"""Tests for ContentLoader."""

import logging
import sys
from typing import TYPE_CHECKING

import pytest

from pedre.content.loader import ContentLoader
from pedre.content.registry import ContentTypeRegistry

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear ContentTypeRegistry before and after each test."""
    ContentTypeRegistry.clear()
    yield
    ContentTypeRegistry.clear()


def test_load_modules_imports_configured_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_modules() imports each module in INSTALLED_CONTENT."""
    module_name = "pedre.content.registries.npc"
    if module_name in sys.modules:
        del sys.modules[module_name]

    monkeypatch.setattr("pedre.conf.settings.INSTALLED_CONTENT", [module_name])

    loader = ContentLoader()
    loader.load_modules()

    assert ContentTypeRegistry.is_registered("npcs")


def test_load_modules_with_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_modules() handles an empty INSTALLED_CONTENT without raising."""
    monkeypatch.setattr("pedre.conf.settings.INSTALLED_CONTENT", [])

    loader = ContentLoader()
    loader.load_modules()

    assert ContentTypeRegistry.get_all_names() == []


def test_load_modules_raises_on_invalid_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_modules() raises ImportError for a non-existent module."""
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_CONTENT",
        ["nonexistent.content.module"],
    )

    loader = ContentLoader()
    with pytest.raises(ImportError):
        loader.load_modules()


def test_load_modules_loads_multiple_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_modules() imports all modules in INSTALLED_CONTENT."""
    npc_module = "pedre.content.registries.npc"
    sprite_module = "pedre.content.registries.sprite"
    for module_name in (npc_module, sprite_module):
        if module_name in sys.modules:
            del sys.modules[module_name]

    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_CONTENT",
        [npc_module, sprite_module],
    )

    loader = ContentLoader()
    loader.load_modules()

    assert ContentTypeRegistry.is_registered("npcs")
    assert ContentTypeRegistry.is_registered("sprites")


def test_load_modules_logs_debug_on_success(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """Test that load_modules() emits a debug log for each successfully loaded module."""
    module_name = "pedre.content.registries.item"
    if module_name in sys.modules:
        del sys.modules[module_name]

    monkeypatch.setattr("pedre.conf.settings.INSTALLED_CONTENT", [module_name])

    loader = ContentLoader()
    with caplog.at_level(logging.DEBUG, logger="pedre.content.loader"):
        loader.load_modules()

    assert any(module_name in record.message for record in caplog.records)
