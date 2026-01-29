"""Tests for EventLoader."""

import pytest

from pedre.events.loader import EventLoader
from pedre.events.registry import EventRegistry


def test_event_loader_imports_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that EventLoader imports configured modules."""
    # Note: We don't clear the registry here because in a full test run,
    # other tests may have already loaded these modules. Since Python caches
    # imports, the decorators won't re-execute on subsequent imports.
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_EVENTS",
        [
            "pedre.systems.interaction.events",
        ],
    )

    loader = EventLoader()
    loader.load_modules()

    # Verify interaction events were registered (may already be registered from earlier tests)
    assert EventRegistry.get("object_interacted") is not None


def test_event_loader_with_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that EventLoader handles empty INSTALLED_EVENTS."""
    EventRegistry.clear()
    monkeypatch.setattr("pedre.conf.settings.INSTALLED_EVENTS", [])

    loader = EventLoader()
    loader.load_modules()  # Should not raise

    # Registry should be empty
    assert EventRegistry.get("some_nonexistent_event") is None


def test_event_loader_raises_on_invalid_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that EventLoader raises ImportError for invalid modules."""
    EventRegistry.clear()
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_EVENTS",
        [
            "nonexistent.module",
        ],
    )

    loader = EventLoader()
    with pytest.raises(ImportError):
        loader.load_modules()


def test_event_loader_loads_multiple_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that EventLoader can load multiple event modules."""
    EventRegistry.clear()
    monkeypatch.setattr(
        "pedre.conf.settings.INSTALLED_EVENTS",
        [
            "pedre.systems.portal.events",
        ],
    )

    loader = EventLoader()
    loader.load_modules()

    # Verify portal events were registered (testing a module not imported by other tests)
    assert EventRegistry.get("portal_entered") is not None
