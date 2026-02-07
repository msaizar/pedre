"""Tests for pedre.conf settings module."""

from unittest import mock

import pytest

from pedre.conf import LazySettings, Settings, __all__, global_settings, settings


class TestSettings:
    """Tests for the Settings class."""

    def test_settings_loads_global_defaults(self) -> None:
        """Test that Settings loads all uppercase attributes from global_settings."""
        s = Settings()
        # Check a few known global settings
        assert hasattr(s, "SCREEN_WIDTH")
        assert hasattr(s, "SCREEN_HEIGHT")
        assert s.SCREEN_WIDTH == global_settings.SCREEN_WIDTH
        assert s.SCREEN_HEIGHT == global_settings.SCREEN_HEIGHT

    def test_settings_only_loads_uppercase(self) -> None:
        """Test that Settings only loads uppercase attributes."""
        s = Settings()
        # Should not load lowercase or dunder attributes
        assert not hasattr(s, "__name__")
        assert not hasattr(s, "__file__")


class TestLazySettings:
    """Tests for the LazySettings class."""

    def test_lazy_settings_initialization(self) -> None:
        """Test that LazySettings initializes without loading."""
        lazy = LazySettings()
        assert lazy._wrapped is None

    def test_lazy_settings_loads_on_first_access(self) -> None:
        """Test that settings are loaded on first attribute access."""
        lazy = LazySettings()
        assert lazy._wrapped is None
        _ = lazy.SCREEN_WIDTH  # Trigger loading
        assert lazy._wrapped is not None

    def test_lazy_settings_uses_default_module_name(self) -> None:
        """Test that LazySettings uses 'settings' as default module name."""
        lazy = LazySettings()
        with (
            mock.patch.dict("os.environ", {}, clear=True),
            mock.patch("importlib.import_module") as mock_import,
        ):
            mock_import.side_effect = ImportError()
            _ = lazy.SCREEN_WIDTH  # Trigger loading
            mock_import.assert_called_once_with("settings")

    def test_lazy_settings_uses_env_variable(self) -> None:
        """Test that LazySettings uses PEDRE_SETTINGS_MODULE env variable."""
        lazy = LazySettings()
        with (
            mock.patch.dict("os.environ", {"PEDRE_SETTINGS_MODULE": "custom.settings"}),
            mock.patch("importlib.import_module") as mock_import,
        ):
            mock_import.side_effect = ImportError()
            _ = lazy.SCREEN_WIDTH  # Trigger loading
            mock_import.assert_called_once_with("custom.settings")

    def test_lazy_settings_loads_user_settings(self) -> None:
        """Test that LazySettings loads and applies user settings."""
        # Create a mock module with custom settings
        mock_module = type("MockModule", (), {"CUSTOM_SETTING": "test_value", "SCREEN_WIDTH": 1234})()

        lazy = LazySettings()
        with mock.patch("importlib.import_module", return_value=mock_module):
            value = lazy.CUSTOM_SETTING
            assert value == "test_value"
            assert lazy.SCREEN_WIDTH == 1234

    def test_lazy_settings_only_loads_uppercase(self) -> None:
        """Test that LazySettings only loads uppercase attributes from user settings."""
        # Create a mock module with both uppercase and lowercase settings
        mock_module = type(
            "MockModule",
            (),
            {
                "UPPERCASE_SETTING": "should_load",
                "lowercase_setting": "should_not_load",
                "_private": "should_not_load",
            },
        )()

        lazy = LazySettings()
        with mock.patch("importlib.import_module", return_value=mock_module):
            assert lazy.UPPERCASE_SETTING == "should_load"
            # lowercase_setting should not be loaded
            with pytest.raises(AttributeError):
                _ = lazy.lowercase_setting

    def test_lazy_settings_handles_import_error(self) -> None:
        """Test that LazySettings gracefully handles missing user settings module."""
        lazy = LazySettings()
        with mock.patch("importlib.import_module", side_effect=ImportError()):
            # Should still work with global defaults
            value = lazy.SCREEN_WIDTH
            assert value == global_settings.SCREEN_WIDTH

    def test_lazy_settings_loads_multiple_uppercase_from_user_module(self) -> None:
        """Test that all uppercase attributes are loaded from user module."""
        # Create a mock module with multiple uppercase settings
        mock_module = type(
            "MockModule",
            (),
            {
                "SETTING_ONE": "value1",
                "SETTING_TWO": "value2",
                "SETTING_THREE": "value3",
                "lowercase": "ignored",
            },
        )()

        lazy = LazySettings()
        with mock.patch("importlib.import_module", return_value=mock_module):
            # Access to trigger loading
            _ = lazy.SETTING_ONE
            # Verify all uppercase settings were loaded
            assert lazy.SETTING_ONE == "value1"
            assert lazy.SETTING_TWO == "value2"
            assert lazy.SETTING_THREE == "value3"

    def test_lazy_settings_setattr_for_wrapped(self) -> None:
        """Test that __setattr__ handles _wrapped specially."""
        lazy = LazySettings()
        test_settings = Settings()
        lazy._wrapped = test_settings
        assert lazy._wrapped is test_settings

    def test_lazy_settings_setattr_creates_settings_if_needed(self) -> None:
        """Test that __setattr__ triggers setup if not yet configured."""
        lazy = LazySettings()
        assert lazy._wrapped is None
        lazy.CUSTOM_SETTING = "test_value"
        assert lazy._wrapped is not None
        assert lazy.CUSTOM_SETTING == "test_value"

    def test_lazy_settings_setattr_on_already_configured(self) -> None:
        """Test that __setattr__ works when settings are already configured."""
        lazy = LazySettings()
        # First configure it
        lazy.configure(INITIAL="value")
        assert lazy._wrapped is not None
        # Now set a new attribute - this should hit line 78 (the else branch)
        # since _wrapped is not None
        lazy.NEW_SETTING = "new_value"
        assert lazy.NEW_SETTING == "new_value"

    def test_lazy_settings_configure(self) -> None:
        """Test that configure() manually sets settings."""
        lazy = LazySettings()
        lazy.configure(CUSTOM_SETTING="test", ANOTHER_SETTING=123)
        assert lazy.CUSTOM_SETTING == "test"
        assert lazy.ANOTHER_SETTING == 123

    def test_lazy_settings_configure_creates_settings_if_needed(self) -> None:
        """Test that configure() creates Settings if not yet initialized."""
        lazy = LazySettings()
        assert lazy._wrapped is None
        lazy.configure(TEST_SETTING="value")
        assert lazy._wrapped is not None
        assert lazy.TEST_SETTING == "value"

    def test_lazy_settings_configure_updates_existing_settings(self) -> None:
        """Test that configure() updates existing settings."""
        lazy = LazySettings()
        lazy.configure(SETTING_ONE="first")
        assert lazy.SETTING_ONE == "first"
        lazy.configure(SETTING_TWO="second")
        assert lazy.SETTING_ONE == "first"  # Should still exist
        assert lazy.SETTING_TWO == "second"

    def test_is_configured_false_initially(self) -> None:
        """Test that is_configured() returns False initially."""
        lazy = LazySettings()
        assert not lazy.is_configured()

    def test_is_configured_true_after_access(self) -> None:
        """Test that is_configured() returns True after settings are loaded."""
        lazy = LazySettings()
        _ = lazy.SCREEN_WIDTH  # Trigger loading
        assert lazy.is_configured()

    def test_is_configured_true_after_configure(self) -> None:
        """Test that is_configured() returns True after configure()."""
        lazy = LazySettings()
        lazy.configure(TEST="value")
        assert lazy.is_configured()


class TestGlobalSettingsInstance:
    """Tests for the global settings instance."""

    def test_global_settings_instance_exists(self) -> None:
        """Test that the global settings instance exists."""
        assert settings is not None
        assert isinstance(settings, LazySettings)

    def test_can_access_global_settings_directly(self) -> None:
        """Test that we can access settings through the global instance."""
        # This should work without errors
        value = settings.SCREEN_WIDTH
        assert isinstance(value, int)


class TestExports:
    """Tests for module exports."""

    def test_all_exports(self) -> None:
        """Test that __all__ contains expected exports."""
        assert "LazySettings" in __all__
        assert "Settings" in __all__
        assert "global_settings" in __all__
        assert "settings" in __all__
