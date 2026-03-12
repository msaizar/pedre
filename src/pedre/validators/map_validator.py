"""Map validator for Tiled TMX map files."""

import json

import arcade

from pedre.conf import settings
from pedre.content.registries.map import MapRegistry
from pedre.content.registry import InvalidDefinitionError
from pedre.helpers import asset_exists
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

                # Register this map in context (even if it has no entities)
                if map_name not in self.context.map_entities:
                    self.context.map_entities[map_name] = {}
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
            if len(waypoint.shape) < 2:
                errors.append(
                    f"Map '{map_name}': Waypoints layer: '{name}': "
                    f"shape must have at least 2 coordinates, got {len(waypoint.shape)}"
                )
                continue
            # Validate coordinates are numeric (shape[0] and shape[1] must be scalars)
            coord_x = waypoint.shape[0]
            coord_y = waypoint.shape[1]
            if not isinstance(coord_x, (int, float)) or not isinstance(coord_y, (int, float)):
                errors.append(
                    f"Map '{map_name}': Waypoints layer: '{name}': invalid shape coordinates: "
                    f"expected numeric, got {type(coord_x)}, {type(coord_y)}"
                )
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

            # Register interactive object in context
            self.context.add_map_entity(map_name, "interactive_objects", name)

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

    def validate_cross_references(self) -> ValidationResult:
        """Validate that maps.json entries reference scene names with existing TMX files.

        Loads maps.json from the content directory and checks that each map ID
        matches a TMX file in the maps directory. Also validates structural
        correctness of each maps.json entry via MapRegistry.validate().

        Returns:
            ValidationResult with cross-reference errors
        """
        content_dir = self.path.parent / settings.CONTENT_DIRECTORY
        maps_file = content_dir / "maps.json"

        if not maps_file.exists():
            return ValidationResult(errors=[], item_count=0, metadata={})

        try:
            with maps_file.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(errors=[f"Failed to parse {maps_file.name}: {e}"], item_count=0, metadata={})
        except OSError as e:
            return ValidationResult(errors=[f"Failed to load {maps_file.name}: {e}"], item_count=0, metadata={})

        if not isinstance(data, dict):
            return ValidationResult(errors=[], item_count=0, metadata={})

        known_maps = self.context.get_all_maps()
        registry = MapRegistry()
        errors: list[str] = []

        for map_id, map_data in data.items():
            if not isinstance(map_data, dict):
                errors.append(f"Map entry '{map_id}': must be a dictionary")
                continue

            try:
                registry.validate(map_id, map_data)
            except InvalidDefinitionError as e:
                errors.append(str(e))
                continue

            if map_id not in known_maps:
                errors.append(f"Map entry '{map_id}' in maps.json has no corresponding TMX file in the maps directory.")

            if "music" in map_data:
                music_file = map_data["music"]
                if not asset_exists(f"{settings.AUDIO_MUSIC_DIRECTORY}/{music_file}"):
                    errors.append(
                        f"Map '{map_id}': music file '{settings.AUDIO_MUSIC_DIRECTORY}/{music_file}' not found."
                    )

            if "camera_follow" in map_data:
                camera_follow = map_data["camera_follow"].strip().lower()
                if camera_follow not in ("player", "none") and not (
                    camera_follow.startswith("npc:") and camera_follow[4:].strip()
                ):
                    errors.append(
                        f"Map '{map_id}': 'camera_follow' must be 'player', 'none', or 'npc:<name>', "
                        f"got '{map_data['camera_follow']}'."
                    )

        return ValidationResult(errors=errors, item_count=0, metadata={})
