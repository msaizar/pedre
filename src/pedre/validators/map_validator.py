"""Map validator for Tiled TMX map files."""

from pathlib import Path

import arcade

from pedre.conf import settings
from pedre.constants import asset_path
from pedre.validators.base import ValidationResult, Validator


class MapValidator(Validator):
    """Validates Tiled TMX map files for structural correctness."""

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Maps"

    def validate(self) -> ValidationResult:
        """Validate all TMX map files in the configured directory.

        Returns:
            ValidationResult with errors and metadata
        """
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Maps directory not found: {self.path}"],
                item_count=0,
                metadata={},
            )

        # Find all TMX files
        map_files = list(self.path.glob("*.tmx"))

        if not map_files:
            return ValidationResult(
                errors=[],
                item_count=0,
                metadata={},
            )

        errors: list[str] = []
        total_npcs = 0
        total_waypoints = 0
        total_portals = 0
        total_interactive = 0

        for map_file in map_files:
            map_name = map_file.stem  # Filename without extension

            try:
                # Load the tilemap
                tile_map = arcade.load_tilemap(str(map_file))

                # Validate Waypoints layer
                waypoint_errors = self._validate_waypoint_layer(tile_map, map_name)
                errors.extend(waypoint_errors)

                # Validate NPCs layer
                npc_errors = self._validate_npc_layer(tile_map, map_name)
                errors.extend(npc_errors)

                # Validate Portals layer
                portal_errors = self._validate_portal_layer(tile_map, map_name)
                errors.extend(portal_errors)

                # Validate Interactive layer
                interactive_errors = self._validate_interactive_layer(tile_map, map_name)
                errors.extend(interactive_errors)

                # Validate Player layer
                player_errors = self._validate_player_layer(tile_map, map_name)
                errors.extend(player_errors)

                # Validate map properties
                map_prop_errors = self._validate_map_properties(tile_map, map_name)
                errors.extend(map_prop_errors)

                # Count entities for metadata
                if "Waypoints" in tile_map.object_lists:
                    total_waypoints += len(tile_map.object_lists["Waypoints"])
                if "NPCs" in tile_map.object_lists:
                    total_npcs += len(tile_map.object_lists["NPCs"])
                if "Portals" in tile_map.object_lists:
                    total_portals += len(tile_map.object_lists["Portals"])
                if "Interactive" in tile_map.object_lists:
                    total_interactive += len(tile_map.object_lists["Interactive"])

            except (OSError, ValueError, RuntimeError) as e:
                errors.append(f"Failed to load map '{map_file.name}': {e}")

        return ValidationResult(
            errors=errors,
            item_count=len(map_files),
            metadata={
                "Total NPCs": total_npcs,
                "Total Waypoints": total_waypoints,
                "Total Portals": total_portals,
                "Total Interactive Objects": total_interactive,
            },
        )

    def _validate_waypoint_layer(self, tile_map: arcade.TileMap, map_name: str) -> list[str]:
        """Validate Waypoints object layer.

        Args:
            tile_map: Loaded tilemap
            map_name: Name of the map for error messages

        Returns:
            List of error messages
        """
        errors = []

        if "Waypoints" not in tile_map.object_lists:
            return errors  # Waypoints are optional

        for waypoint in tile_map.object_lists["Waypoints"]:
            # Validate required 'name' property
            name = waypoint.name
            if not name:
                errors.append(f"Map '{map_name}': Waypoints layer: waypoint missing required 'name' property")
                continue

            # Validate shape coordinates
            if not hasattr(waypoint, "shape") or not waypoint.shape:
                errors.append(f"Map '{map_name}': Waypoints layer: '{name}': missing shape coordinates")
                continue

            # Shape should be a list/tuple with at least 2 numeric elements [x, y]
            try:
                if len(waypoint.shape) < 2:
                    errors.append(
                        f"Map '{map_name}': Waypoints layer: '{name}': "
                        f"shape must have at least 2 coordinates, got {len(waypoint.shape)}"
                    )
                    continue
                # Validate coordinates are numeric
                float(waypoint.shape[0])
                float(waypoint.shape[1])
            except (TypeError, ValueError) as e:
                errors.append(f"Map '{map_name}': Waypoints layer: '{name}': invalid shape coordinates: {e}")
                continue

            # Register waypoint in context
            self.context.add_map_entity(map_name, "waypoints", name)

        return errors

    def _validate_npc_layer(self, tile_map: arcade.TileMap, map_name: str) -> list[str]:
        """Validate NPCs object layer.

        Args:
            tile_map: Loaded tilemap
            map_name: Name of the map for error messages

        Returns:
            List of error messages
        """
        errors = []

        if "NPCs" not in tile_map.object_lists:
            return errors  # NPCs are optional

        for npc in tile_map.object_lists["NPCs"]:
            # Validate required 'name' property
            name = npc.name
            if not name:
                errors.append(f"Map '{map_name}': NPCs layer: NPC missing required 'name' property")
                continue

            # Validate required 'sprite_sheet' property
            if not hasattr(npc, "properties") or npc.properties is None or "sprite_sheet" not in npc.properties:
                errors.append(f"Map '{map_name}': NPCs layer: '{name}': missing required 'sprite_sheet' property")
                continue

            # Validate optional properties have correct types
            if "tile_size" in npc.properties:
                error = self._validate_property_type(npc.properties["tile_size"], int, "tile_size", f"NPC '{name}'")
                if error:
                    errors.append(f"Map '{map_name}': NPCs layer: {error}")

            if "scale" in npc.properties:
                error = self._validate_property_type(npc.properties["scale"], (int, float), "scale", f"NPC '{name}'")
                if error:
                    errors.append(f"Map '{map_name}': NPCs layer: {error}")

            if "initially_hidden" in npc.properties:
                error = self._validate_property_type(
                    npc.properties["initially_hidden"], bool, "initially_hidden", f"NPC '{name}'"
                )
                if error:
                    errors.append(f"Map '{map_name}': NPCs layer: {error}")

            # Validate animation properties (if present, must be ints)
            animation_props = [
                "appear_duration",
                "appear_complete",
                "disappear_duration",
                "disappear_complete",
                "interact_duration",
                "interact_complete",
                "walk_frame_count",
                "walk_duration",
                "idle_duration",
            ]
            for prop in animation_props:
                if prop in npc.properties:
                    error = self._validate_property_type(npc.properties[prop], int, prop, f"NPC '{name}'")
                    if error:
                        errors.append(f"Map '{map_name}': NPCs layer: {error}")

            # Register NPC in context
            self.context.add_map_entity(map_name, "npcs", name)

        return errors

    def _validate_portal_layer(self, tile_map: arcade.TileMap, map_name: str) -> list[str]:
        """Validate Portals object layer.

        Args:
            tile_map: Loaded tilemap
            map_name: Name of the map for error messages

        Returns:
            List of error messages
        """
        errors = []

        if "Portals" not in tile_map.object_lists:
            return errors  # Portals are optional

        for portal in tile_map.object_lists["Portals"]:
            # Validate required 'name' property
            name = portal.name
            if not name:
                errors.append(f"Map '{map_name}': Portals layer: portal missing required 'name' property")
                continue

            # Validate required 'properties'
            if not hasattr(portal, "properties") or not portal.properties:
                errors.append(f"Map '{map_name}': Portals layer: '{name}': missing required properties")

            # Validate shape exists
            if not hasattr(portal, "shape") or not portal.shape:
                errors.append(f"Map '{map_name}': Portals layer: '{name}': missing shape")
                continue

            # Register portal in context
            self.context.add_map_entity(map_name, "portals", name)

        return errors

    def _validate_interactive_layer(self, tile_map: arcade.TileMap, map_name: str) -> list[str]:
        """Validate Interactive object layer.

        Args:
            tile_map: Loaded tilemap
            map_name: Name of the map for error messages

        Returns:
            List of error messages
        """
        errors = []

        if "Interactive" not in tile_map.object_lists:
            return errors  # Interactive objects are optional

        for obj in tile_map.object_lists["Interactive"]:
            # Validate required 'name' property
            name = obj.name
            if not name:
                errors.append(f"Map '{map_name}': Interactive layer: object missing required 'name' property")
                continue

            # Validate shape exists
            if not hasattr(obj, "shape") or not obj.shape:
                errors.append(f"Map '{map_name}': Interactive layer: '{name}': missing shape")

        return errors

    def _validate_player_layer(self, tile_map: arcade.TileMap, map_name: str) -> list[str]:
        """Validate Player object layer.

        Args:
            tile_map: Loaded tilemap
            map_name: Name of the map for error messages

        Returns:
            List of error messages
        """
        errors = []

        if "Player" not in tile_map.object_lists:
            return errors  # Player is optional

        for player in tile_map.object_lists["Player"]:
            # Validate required 'sprite_sheet' property
            if (
                not hasattr(player, "properties")
                or player.properties is None
                or "sprite_sheet" not in player.properties
            ):
                errors.append(f"Map '{map_name}': Player layer: missing required 'sprite_sheet' property")
                continue

            # Validate sprite_sheet file exists
            sprite_sheet = player.properties["sprite_sheet"]
            if not isinstance(sprite_sheet, str):
                errors.append(f"Map '{map_name}': Player layer: 'sprite_sheet' must be string")
            elif not self._asset_exists(sprite_sheet):
                errors.append(f"Map '{map_name}': Player layer: sprite_sheet '{sprite_sheet}' not found")

            # Validate optional properties have correct types
            if "tile_size" in player.properties:
                error = self._validate_property_type(player.properties["tile_size"], int, "tile_size", "Player")
                if error:
                    errors.append(f"Map '{map_name}': Player layer: {error}")

            if "scale" in player.properties:
                error = self._validate_property_type(player.properties["scale"], (int, float), "scale", "Player")
                if error:
                    errors.append(f"Map '{map_name}': Player layer: {error}")

            if "spawn_at_portal" in player.properties:
                error = self._validate_property_type(
                    player.properties["spawn_at_portal"], bool, "spawn_at_portal", "Player"
                )
                if error:
                    errors.append(f"Map '{map_name}': Player layer: {error}")

        return errors

    def _validate_map_properties(self, tile_map: arcade.TileMap, map_name: str) -> list[str]:
        """Validate map-level properties.

        Args:
            tile_map: Loaded tilemap
            map_name: Name of the map for error messages

        Returns:
            List of error messages
        """
        errors = []

        if not hasattr(tile_map, "properties") or not tile_map.properties:
            return errors  # Map properties are optional

        # Validate optional map properties
        if "music" in tile_map.properties:
            error = self._validate_property_type(tile_map.properties["music"], str, "music", "Map")
            if error:
                errors.append(f"Map '{map_name}': {error}")
            else:
                # Validate music file exists
                music_file = tile_map.properties["music"]
                if not self._asset_exists(music_file):
                    errors.append(f"Map '{map_name}': music file '{music_file}' not found")

        if "camera_follow" in tile_map.properties:
            error = self._validate_property_type(tile_map.properties["camera_follow"], str, "camera_follow", "Map")
            if error:
                errors.append(f"Map '{map_name}': {error}")

        if "camera_smooth" in tile_map.properties:
            error = self._validate_property_type(tile_map.properties["camera_smooth"], bool, "camera_smooth", "Map")
            if error:
                errors.append(f"Map '{map_name}': {error}")

        return errors

    def _validate_property_type(
        self, value: object, expected_type: type | tuple[type, ...], property_name: str, entity_name: str
    ) -> str | None:
        """Validate that a property has the expected type.

        Args:
            value: Property value to check
            expected_type: Expected type or tuple of types
            property_name: Name of the property for error messages
            entity_name: Name of the entity for error messages

        Returns:
            Error message if validation fails, None otherwise
        """
        if not isinstance(value, expected_type):
            if isinstance(expected_type, tuple):
                type_names = " or ".join(t.__name__ for t in expected_type)
                return f"{entity_name}: '{property_name}' must be {type_names}, got {type(value).__name__}"
            return f"{entity_name}: '{property_name}' must be {expected_type.__name__}, got {type(value).__name__}"
        return None

    def _asset_exists(self, asset_path_str: str) -> bool:
        """Check if an asset exists relative to the assets directory.

        Args:
            asset_path_str: Path string from Tiled property

        Returns:
            True if file exists, False otherwise
        """
        try:
            path_str = asset_path(asset_path_str, settings.ASSETS_HANDLE)
            path = Path(path_str)
            return path.exists() and path.is_file()
        except (OSError, ValueError, TypeError):
            return False

    def validate_cross_references(self) -> ValidationResult:
        """Validate cross-references (no cross-validation needed for maps).

        Maps are the source of truth for NPCs and waypoints, so they don't
        need to validate references to other assets.

        Returns:
            Empty ValidationResult
        """
        return ValidationResult(errors=[], item_count=0, metadata={})
