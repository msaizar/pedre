"""Tests for ActionLoader."""

import pytest

from pedre.actions.loader import ActionLoader
from pedre.actions.registry import ActionRegistry


def test_action_loader_imports_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ActionLoader imports configured modules."""
    # Note: We don't clear the registry here because in a full test run,
    # other tests may have already loaded these modules. Since Python caches
    # imports, the decorators won't re-execute on subsequent imports.
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_ACTIONS",
        [
            "pedre.systems.dialog.actions",
        ],
    )

    loader = ActionLoader()
    loader.load_modules()

    # Verify dialog actions were registered (may already be registered from earlier tests)
    assert ActionRegistry.is_registered("dialog")
    assert ActionRegistry.is_registered("wait_for_dialog_close")


def test_action_loader_with_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ActionLoader handles empty INSTALLED_ACTIONS."""
    ActionRegistry.clear()
    monkeypatch.setattr("pedre.conf.settings.INSTALLED_ACTIONS", [])

    loader = ActionLoader()
    loader.load_modules()  # Should not raise

    assert not ActionRegistry.get_all_types()


def test_action_loader_raises_on_invalid_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ActionLoader raises ImportError for invalid modules."""
    ActionRegistry.clear()
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_ACTIONS",
        [
            "nonexistent.module",
        ],
    )

    loader = ActionLoader()
    with pytest.raises(ImportError):
        loader.load_modules()


def test_action_loader_loads_multiple_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ActionLoader can load multiple action modules."""
    ActionRegistry.clear()
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_ACTIONS",
        [
            "pedre.systems.npc.actions",
        ],
    )

    loader = ActionLoader()
    loader.load_modules()

    # Verify NPC actions were registered (testing a module not imported by other tests)
    assert ActionRegistry.is_registered("move_npc")
    assert ActionRegistry.is_registered("advance_dialog")
    assert ActionRegistry.is_registered("set_dialog_level")
