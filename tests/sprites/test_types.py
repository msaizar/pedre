"""Tests for AnimationStateConfig."""

from pedre.sprites.types import AnimationStateConfig


class TestAnimationStateConfigFromDict:
    """Tests for AnimationStateConfig.from_dict."""

    def test_from_dict_non_directional(self) -> None:
        """Test parsing a non-directional state."""
        cfg = AnimationStateConfig.from_dict(
            "appear",
            {"directional": False, "loop": False, "priority": 3, "frames": 5, "row": 8},
        )
        assert cfg.name == "appear"
        assert not cfg.directional
        assert not cfg.loop
        assert cfg.priority == 3
        assert cfg.frames == 5
        assert cfg.row == 8
        assert cfg.directions is None

    def test_from_dict_directional_with_directions(self) -> None:
        """Test parsing a directional state with explicit directions data."""
        cfg = AnimationStateConfig.from_dict(
            "idle",
            {
                "directional": True,
                "loop": True,
                "priority": 0,
                "directions": {"down": {"frames": 4, "row": 0}, "up": {"frames": 4, "row": 1}},
            },
        )
        assert cfg.directional
        assert cfg.directions == {"down": {"frames": 4, "row": 0}, "up": {"frames": 4, "row": 1}}

    def test_from_dict_directional_without_directions_key(self) -> None:
        """Test that directional=True with no directions key produces empty dict (branch 54->58)."""
        cfg = AnimationStateConfig.from_dict(
            "walk",
            {"directional": True, "loop": True, "priority": 1},
        )
        assert cfg.directional
        assert cfg.directions == {}

    def test_from_dict_optional_fields_default(self) -> None:
        """Test that optional fields default correctly when absent."""
        cfg = AnimationStateConfig.from_dict(
            "idle",
            {"directional": False, "loop": True, "priority": 0},
        )
        assert cfg.on_complete is None
        assert cfg.reverse_load is False
        assert cfg.auto_from is None
        assert cfg.frames is None
        assert cfg.row is None

    def test_from_dict_optional_fields_set(self) -> None:
        """Test parsing with all optional fields present."""
        cfg = AnimationStateConfig.from_dict(
            "disappear",
            {
                "directional": False,
                "loop": False,
                "priority": 4,
                "on_complete": "hide",
                "reverse_load": True,
                "auto_from": "appear",
            },
        )
        assert cfg.on_complete == "hide"
        assert cfg.reverse_load is True
        assert cfg.auto_from == "appear"
