"""Tests for ValidationContext."""

import pytest

from pedre.validators.context import ValidationContext


class TestValidationContext:
    """Test ValidationContext class."""

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a fresh ValidationContext for each test."""
        return ValidationContext()

    def test_add_map_entity_single(self, context: ValidationContext) -> None:
        """Test adding a single entity to a map."""
        context.add_map_entity("village", "npcs", "merchant")

        assert "village" in context.map_entities
        assert "npcs" in context.map_entities["village"]
        assert "merchant" in context.map_entities["village"]["npcs"]

    def test_add_map_entity_multiple_same_type(self, context: ValidationContext) -> None:
        """Test adding multiple entities of the same type to a map."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("village", "npcs", "guard")
        context.add_map_entity("village", "npcs", "blacksmith")

        assert len(context.map_entities["village"]["npcs"]) == 3
        assert "merchant" in context.map_entities["village"]["npcs"]
        assert "guard" in context.map_entities["village"]["npcs"]
        assert "blacksmith" in context.map_entities["village"]["npcs"]

    def test_add_map_entity_different_types(self, context: ValidationContext) -> None:
        """Test adding different entity types to the same map."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("village", "waypoints", "spawn_point")
        context.add_map_entity("village", "portals", "exit_portal")

        assert len(context.map_entities["village"]) == 3
        assert "npcs" in context.map_entities["village"]
        assert "waypoints" in context.map_entities["village"]
        assert "portals" in context.map_entities["village"]

    def test_add_map_entity_multiple_maps(self, context: ValidationContext) -> None:
        """Test adding entities across multiple maps."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("forest", "npcs", "hermit")
        context.add_map_entity("castle", "npcs", "king")

        assert len(context.map_entities) == 3
        assert "village" in context.map_entities
        assert "forest" in context.map_entities
        assert "castle" in context.map_entities

    def test_add_map_entity_duplicate(self, context: ValidationContext) -> None:
        """Test adding the same entity twice (should be idempotent due to set)."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("village", "npcs", "merchant")

        # Should only have one instance due to set behavior
        assert len(context.map_entities["village"]["npcs"]) == 1
        assert "merchant" in context.map_entities["village"]["npcs"]

    def test_get_map_npcs_exists(self, context: ValidationContext) -> None:
        """Test retrieving NPCs from a specific map that exists."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("village", "npcs", "guard")

        npcs = context.get_map_npcs("village")

        assert len(npcs) == 2
        assert "merchant" in npcs
        assert "guard" in npcs

    def test_get_map_npcs_not_found(self, context: ValidationContext) -> None:
        """Test retrieving NPCs from a non-existent map returns empty set."""
        npcs = context.get_map_npcs("nonexistent_map")

        assert npcs == set()
        assert isinstance(npcs, set)

    def test_get_map_npcs_no_npcs_in_map(self, context: ValidationContext) -> None:
        """Test retrieving NPCs from a map that has no NPCs."""
        context.add_map_entity("village", "waypoints", "spawn_point")

        npcs = context.get_map_npcs("village")

        assert npcs == set()

    def test_get_map_waypoints_exists(self, context: ValidationContext) -> None:
        """Test retrieving waypoints from a specific map that exists."""
        context.add_map_entity("village", "waypoints", "spawn_point")
        context.add_map_entity("village", "waypoints", "exit_point")
        context.add_map_entity("village", "waypoints", "quest_marker")

        waypoints = context.get_map_waypoints("village")

        assert len(waypoints) == 3
        assert "spawn_point" in waypoints
        assert "exit_point" in waypoints
        assert "quest_marker" in waypoints

    def test_get_map_waypoints_not_found(self, context: ValidationContext) -> None:
        """Test retrieving waypoints from a non-existent map returns empty set."""
        waypoints = context.get_map_waypoints("nonexistent_map")

        assert waypoints == set()
        assert isinstance(waypoints, set)

    def test_get_map_waypoints_no_waypoints_in_map(self, context: ValidationContext) -> None:
        """Test retrieving waypoints from a map that has no waypoints."""
        context.add_map_entity("village", "npcs", "merchant")

        waypoints = context.get_map_waypoints("village")

        assert waypoints == set()

    def test_get_all_npcs_multiple_maps(self, context: ValidationContext) -> None:
        """Test aggregating NPCs across all maps."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("village", "npcs", "guard")
        context.add_map_entity("forest", "npcs", "hermit")
        context.add_map_entity("castle", "npcs", "king")
        context.add_map_entity("castle", "npcs", "queen")

        all_npcs = context.get_all_npcs()

        assert len(all_npcs) == 5
        assert "merchant" in all_npcs
        assert "guard" in all_npcs
        assert "hermit" in all_npcs
        assert "king" in all_npcs
        assert "queen" in all_npcs

    def test_get_all_npcs_empty(self, context: ValidationContext) -> None:
        """Test getting all NPCs when context is empty."""
        all_npcs = context.get_all_npcs()

        assert all_npcs == set()
        assert isinstance(all_npcs, set)

    def test_get_all_npcs_no_npcs(self, context: ValidationContext) -> None:
        """Test getting all NPCs when maps have no NPCs."""
        context.add_map_entity("village", "waypoints", "spawn_point")
        context.add_map_entity("forest", "portals", "exit_portal")

        all_npcs = context.get_all_npcs()

        assert all_npcs == set()

    def test_get_all_waypoints_multiple_maps(self, context: ValidationContext) -> None:
        """Test aggregating waypoints across all maps."""
        context.add_map_entity("village", "waypoints", "spawn_point")
        context.add_map_entity("village", "waypoints", "shop_entrance")
        context.add_map_entity("forest", "waypoints", "clearing")
        context.add_map_entity("castle", "waypoints", "throne_room")

        all_waypoints = context.get_all_waypoints()

        assert len(all_waypoints) == 4
        assert "spawn_point" in all_waypoints
        assert "shop_entrance" in all_waypoints
        assert "clearing" in all_waypoints
        assert "throne_room" in all_waypoints

    def test_get_all_waypoints_empty(self, context: ValidationContext) -> None:
        """Test getting all waypoints when context is empty."""
        all_waypoints = context.get_all_waypoints()

        assert all_waypoints == set()
        assert isinstance(all_waypoints, set)

    def test_get_all_waypoints_no_waypoints(self, context: ValidationContext) -> None:
        """Test getting all waypoints when maps have no waypoints."""
        context.add_map_entity("village", "npcs", "merchant")
        context.add_map_entity("forest", "portals", "exit_portal")

        all_waypoints = context.get_all_waypoints()

        assert all_waypoints == set()

    def test_overlapping_entity_names_different_maps(self, context: ValidationContext) -> None:
        """Test that the same entity name can exist in different maps."""
        context.add_map_entity("village", "npcs", "guard")
        context.add_map_entity("castle", "npcs", "guard")
        context.add_map_entity("forest", "npcs", "guard")

        # Each map should have its own guard
        assert "guard" in context.get_map_npcs("village")
        assert "guard" in context.get_map_npcs("castle")
        assert "guard" in context.get_map_npcs("forest")

        # get_all_npcs should return a set, so only one "guard"
        all_npcs = context.get_all_npcs()
        assert len(all_npcs) == 1
        assert "guard" in all_npcs

    def test_overlapping_entity_names_different_types(self, context: ValidationContext) -> None:
        """Test that the same name can be used for different entity types."""
        context.add_map_entity("village", "npcs", "entrance")
        context.add_map_entity("village", "waypoints", "entrance")
        context.add_map_entity("village", "portals", "entrance")

        assert "entrance" in context.map_entities["village"]["npcs"]
        assert "entrance" in context.map_entities["village"]["waypoints"]
        assert "entrance" in context.map_entities["village"]["portals"]

    def test_dialog_npcs_tracking(self, context: ValidationContext) -> None:
        """Test dialog NPC tracking."""
        context.dialog_npcs["village"] = {"merchant", "guard"}
        context.dialog_npcs["forest"] = {"hermit"}

        assert len(context.dialog_npcs) == 2
        assert "merchant" in context.dialog_npcs["village"]
        assert "guard" in context.dialog_npcs["village"]
        assert "hermit" in context.dialog_npcs["forest"]

    def test_script_references_tracking(self, context: ValidationContext) -> None:
        """Test script reference tracking."""
        context.script_references["quest_start"] = {
            "npcs": {"merchant", "guard"},
            "waypoints": {"spawn_point"},
        }
        context.script_references["quest_end"] = {
            "npcs": {"king"},
            "waypoints": {"throne_room", "exit"},
        }

        assert len(context.script_references) == 2
        assert "merchant" in context.script_references["quest_start"]["npcs"]
        assert "spawn_point" in context.script_references["quest_start"]["waypoints"]
        assert "king" in context.script_references["quest_end"]["npcs"]

    def test_default_factory_independence(self, context: ValidationContext) -> None:
        """Test that default factory creates independent instances."""
        context1 = ValidationContext()
        context2 = ValidationContext()

        context1.add_map_entity("village", "npcs", "merchant")
        context2.add_map_entity("forest", "npcs", "hermit")

        assert "forest" not in context1.map_entities

    def test_get_map_portals_exists(self, context: ValidationContext) -> None:
        """Test retrieving portals from a specific map that exists."""
        context.add_map_entity("village", "portals", "dungeon_entrance")
        context.add_map_entity("village", "portals", "shop_exit")

        portals = context.get_map_portals("village")

        assert len(portals) == 2
        assert "dungeon_entrance" in portals
        assert "shop_exit" in portals

    def test_get_map_portals_not_found(self, context: ValidationContext) -> None:
        """Test retrieving portals from a non-existent map returns empty set."""
        portals = context.get_map_portals("nonexistent_map")

        assert portals == set()
        assert isinstance(portals, set)

    def test_get_all_portals_multiple_maps(self, context: ValidationContext) -> None:
        """Test aggregating portals across all maps."""
        context.add_map_entity("village", "portals", "dungeon")
        context.add_map_entity("forest", "portals", "cave")

        all_portals = context.get_all_portals()

        assert len(all_portals) == 2
        assert "dungeon" in all_portals
        assert "cave" in all_portals
