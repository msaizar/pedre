"""Tests for ConditionLoader."""

import sys

import pytest

from pedre.conditions.loader import ConditionLoader
from pedre.conditions.registry import ConditionRegistry


def test_condition_loader_imports_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ConditionLoader imports configured modules."""
    # Note: We don't clear the registry here because in a full test run,
    # other tests may have already loaded these modules. Since Python caches
    # imports, the decorators won't re-execute on subsequent imports.
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_CONDITIONS",
        [
            "pedre.plugins.inventory.conditions",
        ],
    )

    loader = ConditionLoader()
    loader.load_modules()

    # Verify inventory conditions were registered (may already be registered from earlier tests)
    assert "inventory_accessed" in ConditionRegistry._checkers
    assert "item_acquired" in ConditionRegistry._checkers


def test_condition_loader_with_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ConditionLoader handles empty INSTALLED_CONDITIONS."""
    ConditionRegistry.clear()
    monkeypatch.setattr("pedre.conf.settings.INSTALLED_CONDITIONS", [])

    loader = ConditionLoader()
    loader.load_modules()  # Should not raise

    assert not ConditionRegistry._checkers


def test_condition_loader_raises_on_invalid_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ConditionLoader raises ImportError for invalid modules."""
    ConditionRegistry.clear()
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_CONDITIONS",
        [
            "nonexistent.module",
        ],
    )

    loader = ConditionLoader()
    with pytest.raises(ImportError):
        loader.load_modules()


def test_condition_loader_loads_multiple_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ConditionLoader can load multiple condition modules."""
    ConditionRegistry.clear()

    # Remove the module from sys.modules to force re-import and re-registration
    # This is necessary because Python caches imports and won't re-execute decorators
    module_name = "pedre.plugins.script.conditions"
    if module_name in sys.modules:
        del sys.modules[module_name]

    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_CONDITIONS",
        [
            module_name,
        ],
    )

    loader = ConditionLoader()
    loader.load_modules()

    # Verify script conditions were registered
    assert "script_completed" in ConditionRegistry._checkers
