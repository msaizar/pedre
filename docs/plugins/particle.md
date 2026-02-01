# ParticlePlugin

Manages particle effects and visual polish.

## Location

- Implementation: [src/pedre/plugins/particle/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/particle/plugin.py)
- Base class: [src/pedre/plugins/particle/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/particle/base.py)
- Actions: [src/pedre/plugins/particle/actions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/particle/actions.py)

## Configuration

The ParticlePlugin uses the following settings from `pedre.conf.settings`:

### Particle Plugin Settings

- `PARTICLE_ENABLED` - Whether particle effects are enabled by default (default: True)
- `PARTICLE_COLOR_HEARTS` - Default color for heart particles (default: (255, 105, 180) - hot pink)
- `PARTICLE_COLOR_SPARKLES` - Default color for sparkle particles (default: (255, 255, 100) - yellow)
- `PARTICLE_COLOR_TRAIL` - Default color for trail particles (default: (200, 200, 255) - light blue)
- `PARTICLE_COLOR_BURST` - Default color for burst particles (default: (255, 200, 0) - orange)

These can be overridden in your project's `settings.py`:

```python
# Custom particle settings
PARTICLE_ENABLED = True
PARTICLE_COLOR_HEARTS = (255, 20, 147)  # Deep pink
PARTICLE_COLOR_SPARKLES = (255, 215, 0)  # Gold
PARTICLE_COLOR_TRAIL = (173, 216, 230)  # Light blue
PARTICLE_COLOR_BURST = (255, 140, 0)  # Dark orange
```

## Public API

### Particle Emission

#### emit_hearts

`emit_hearts(x: float, y: float, count: int = 10, *, color: tuple[int, int, int] = settings.PARTICLE_COLOR_HEARTS) -> None`

Emit heart particles for romantic or affectionate moments.

**Parameters:**

- `x` - X position to emit from (world coordinates)
- `y` - Y position to emit from (world coordinates)
- `count` - Number of particles to emit (default: 10)
- `color` - RGB color tuple (defaults to `settings.PARTICLE_COLOR_HEARTS`)

**Example:**

```python
# Use default color
particle_plugin.emit_hearts(player_x, player_y)

# Custom color (red hearts)
particle_plugin.emit_hearts(npc_x, npc_y, count=15, color=(255, 0, 0))
```

**Notes:**

- Creates particles that float upward with slight outward spread
- Typically used during romantic dialogues or when NPCs show affection
- Particles are larger than other types and use a gentle upward trajectory
- Each particle has random position offsets, velocities, and lifetimes
- Particles fade out as they age and are affected by gravity

#### emit_sparkles

`emit_sparkles(x: float, y: float, count: int = 15, *, color: tuple[int, int, int] = settings.PARTICLE_COLOR_SPARKLES) -> None`

Emit sparkle particles for interactions and discoveries.

**Parameters:**

- `x` - X position to emit from (world coordinates)
- `y` - Y position to emit from (world coordinates)
- `count` - Number of particles to emit (default: 15)
- `color` - RGB color tuple (defaults to `settings.PARTICLE_COLOR_SPARKLES`)

**Example:**

```python
# Use default color
particle_plugin.emit_sparkles(chest_x, chest_y)

# Custom color (blue sparkles)
particle_plugin.emit_sparkles(item_x, item_y, count=20, color=(0, 191, 255))
```

**Notes:**

- Creates small, fast-moving particles that burst outward in all directions
- Typically used when the player interacts with objects or discovers items
- Shorter lifetimes than hearts and move more dynamically
- The outward burst pattern creates a satisfying "pop" effect

**Common uses:**

- Object interactions (chests, doors, switches)
- Item pickups and discoveries
- General interaction feedback

#### emit_trail

`emit_trail(x: float, y: float, count: int = 3, *, color: tuple[int, int, int] = settings.PARTICLE_COLOR_TRAIL) -> None`

Emit subtle trail particles for player movement.

**Parameters:**

- `x` - X position to emit from (world coordinates, typically player position)
- `y` - Y position to emit from (world coordinates, typically player position)
- `count` - Number of particles to emit per call (default: 3, kept low for continuous use)
- `color` - RGB color tuple (defaults to `settings.PARTICLE_COLOR_TRAIL`)

**Example:**

```python
# Use default color
particle_plugin.emit_trail(player_x, player_y)

# Custom color (green trail)
particle_plugin.emit_trail(player_x, player_y, count=5, color=(0, 255, 100))
```

**Notes:**

- Creates small, semi-transparent particles with low velocities and short lifetimes
- Designed to leave a subtle visual trail behind the player as they move
- Effect is intentionally understated to add visual interest without being distracting
- Trail particles start semi-transparent and fade quickly
- Emitted with small random offsets and low velocities
- Typically called continuously during player movement

#### emit_burst

`emit_burst(x: float, y: float, count: int = 20, *, color: tuple[int, int, int] = settings.PARTICLE_COLOR_BURST) -> None`

Emit burst particles for dramatic events and reveals.

**Parameters:**

- `x` - X position to emit from (world coordinates)
- `y` - Y position to emit from (world coordinates)
- `count` - Number of particles to emit (default: 20 for dramatic effect)
- `color` - RGB color tuple (defaults to `settings.PARTICLE_COLOR_BURST`)

**Example:**

```python
# Use default color
particle_plugin.emit_burst(event_x, event_y)

# Custom color (gold burst for NPC reveals)
particle_plugin.emit_burst(npc_x, npc_y, count=25, color=(255, 215, 0))
```

**Notes:**

- Creates a large number of particles that explode outward at high speeds
- Designed for dramatic moments like NPC reveals, quest completions, or significant game events
- Particles are larger and faster than sparkles, creating a more pronounced explosion effect
- High-speed radial burst creates maximum visual impact
- Particles are larger and live longer than sparkles

**Common uses:**

- NPC reveals (RevealNPCsAction uses gold burst)
- Quest completion moments
- Major event triggers
- Dramatic reveals and discoveries

### Plugin Control

#### toggle

`toggle() -> bool`

Toggle particle effects on/off.

**Returns:**

- New enabled state (True if now enabled, False if now disabled)

**Example:**

```python
# Toggle particles
is_enabled = particle_plugin.toggle()
print(f"Particles {'enabled' if is_enabled else 'disabled'}")
```

**Notes:**

- Switches the particle plugin between enabled and disabled states
- When disabling, all active particles are immediately cleared
- When disabled, no new particles are created (emit methods return immediately)
- When disabled, no particles are rendered (draw returns immediately)
- Useful for performance optimization, player preference settings, or debugging

#### clear

`clear() -> None`

Clear all active particles.

**Example:**

```python
# Remove all particles
particle_plugin.clear()
```

**Notes:**

- Immediately removes all particles from the plugin
- Useful for scene transitions where particles should not carry over
- Called automatically by `toggle()` when disabling particle effects

### Update and Rendering

#### update

`update(delta_time: float) -> None`

Update all active particles.

**Parameters:**

- `delta_time` - Time elapsed since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.particle_plugin.update(delta_time)
```

**Notes:**

- Called automatically by PluginLoader each frame
- Updates particle ages, positions, and velocities
- Removes particles that have exceeded their lifetime
- Applies downward gravity acceleration to all particles
- Gravity simulation (50 pixels/second² downward) makes particles follow realistic arcs

#### draw

`draw() -> None`

Draw all active particles.

**Example:**

```python
def on_draw(self):
    self.particle_plugin.draw()
```

**Notes:**

- Called automatically by PluginLoader during the draw loop
- Renders each particle as a filled circle with appropriate color and alpha
- Particles with fade=True have their alpha calculated based on remaining lifetime
- When the particle plugin is disabled, returns immediately without rendering
- Should be called after drawing the game world but before UI elements

#### on_draw

`on_draw() -> None`

Draw all active particles (BasePlugin interface).

**Notes:**

- Wrapper for `draw()` method to satisfy BasePlugin interface
- Called automatically by PluginLoader

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing enabled state

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "particle": particle_plugin.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Particle state is not persisted - particles are transient effects
- Only saves the enabled/disabled state

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore state from save data.

**Parameters:**

- `state` - Previously saved state dictionary

**Example:**

```python
particle_plugin.restore_save_state(save_data["particle"])
```

**Notes:**

- Restores enabled/disabled state
- Active particles are not restored (they're temporary visual effects)

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the particle plugin with game context and settings.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up particle resources when the scene unloads.

**Notes:**

- Clears all active particles
- Called automatically by PluginLoader

#### reset

`reset() -> None`

Reset plugin state for a new game session.

**Notes:**

- Clears all active particles
- Called when starting a new game

## Particle Plugin

### How It Works

The particle plugin consists of:

1. **Particle** - Individual particle data including position, velocity, and visual properties
2. **ParticlePlugin** - Plugin for creating, updating, and rendering particles

The plugin provides several pre-configured particle effects:

- **Hearts** - Romantic/affection effects that float upward
- **Sparkles** - Quick bursts for interactions and discoveries
- **Trail** - Subtle movement trails for the player
- **Burst** - Dramatic explosions for reveals and events

Particles automatically fade out over their lifetime and are removed when expired. The plugin uses simple physics including gravity simulation for realistic movement.

### Particle Properties

Each particle has the following properties:

- `x`, `y` - Position in world coordinates
- `velocity_x`, `velocity_y` - Movement speed and direction
- `lifetime` - Maximum age in seconds before removal
- `age` - Current age in seconds
- `color` - RGBA color tuple
- `size` - Radius in pixels
- `fade` - Whether to fade out over lifetime

### Physics Simulation

Particles use simple physics:

1. Position updated based on velocity each frame
2. Downward gravity applied (50 pixels/second²)
3. Alpha calculated based on remaining lifetime (if fading enabled)
4. Particles removed when age exceeds lifetime

This creates realistic arcing motion and smooth fade-out effects.

## Actions

### EmitParticlesAction

Emit particle effects at specific locations or following entities.

**Type:** `emit_particles`

**Parameters:**

- `particle_type` (string) - Type of particles: "hearts", "sparkles", "burst", or "trail"
- **Exactly one of:**
  - `npc` (string) - NPC name to emit particles at
  - `player` (boolean) - If true, emit at player location
  - `interactive_object` (string) - Interactive object name to emit at
- `color` (array[int, int, int], optional) - RGB color tuple to override default color

**Example - Hearts at NPC:**

```json
{
  "type": "emit_particles",
  "particle_type": "hearts",
  "npc": "yema"
}
```

**Example - Sparkles at player with custom color:**

```json
{
  "type": "emit_particles",
  "particle_type": "sparkles",
  "player": true,
  "color": [0, 191, 255]
}
```

**Example - Burst at interactive object:**

```json
{
  "type": "emit_particles",
  "particle_type": "burst",
  "interactive_object": "treasure_chest",
  "color": [255, 215, 0]
}
```

**Notes:**

- Exactly one location parameter must be provided (npc, player, or interactive_object)
- If color is not specified, uses the default color from settings
- Color should be an array of 3 integers [R, G, B] in the range 0-255

## Usage Examples

### Basic Particle Emission

```python
# Emit hearts at player position
player_sprite = context.player_plugin.get_player_sprite()
particle_plugin.emit_hearts(player_sprite.center_x, player_sprite.center_y)

# Emit sparkles at NPC position
npc = context.npc_plugin.get_npc_by_name("merchant")
if npc:
    particle_plugin.emit_sparkles(npc.sprite.center_x, npc.sprite.center_y)

# Emit burst with custom color
particle_plugin.emit_burst(x, y, count=30, color=(255, 0, 255))
```

### Script-Based Particle Effects

```json
{
  "treasure_opened": {
    "scene": "dungeon",
    "trigger": {
      "event": "object_interacted",
      "object_name": "treasure_chest"
    },
    "actions": [
      {
        "type": "emit_particles",
        "particle_type": "burst",
        "interactive_object": "treasure_chest",
        "color": [255, 215, 0]
      },
      {
        "type": "play_sfx",
        "file": "chest_open.wav"
      },
      {
        "type": "acquire_item",
        "item_id": "golden_key"
      }
    ]
  }
}
```

### NPC Affection Effect

```json
{
  "npc_happy": {
    "scene": "village",
    "trigger": {
      "event": "dialog_closed",
      "npc": "yema"
    },
    "conditions": [
      {"check": "inventory_has_item", "item_id": "flowers"}
    ],
    "actions": [
      {
        "type": "emit_particles",
        "particle_type": "hearts",
        "npc": "yema"
      },
      {
        "type": "dialog",
        "speaker": "Yema",
        "text": ["These flowers are beautiful! Thank you!"]
      }
    ]
  }
}
```

### Performance Optimization

```python
# Disable particles on low-end devices
if is_low_end_device():
    particle_plugin.toggle()  # Disables particles

# Or configure in settings.py
PARTICLE_ENABLED = False  # Start with particles disabled
```

## Custom Particle Implementation

If you need to replace the particle plugin with a custom implementation, you can extend the `ParticleBasePlugin` abstract base class.

### ParticleBasePlugin

**Location:** [src/pedre/plugins/particle/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/particle/base.py)

The `ParticleBasePlugin` class defines the minimum interface that any particle plugin must implement.

#### Required Methods

Your custom particle plugin must implement these abstract methods:

```python
from pedre.plugins.particle.base import ParticleBasePlugin
from pedre.conf import settings

class CustomParticlePlugin(ParticleBasePlugin):
    """Custom particle implementation."""

    name = "particle"
    dependencies = ["scene"]

    def emit_hearts(
        self,
        x: float,
        y: float,
        count: int = 10,
        *,
        color: tuple[int, int, int] = settings.PARTICLE_COLOR_HEARTS,
    ) -> None:
        """Emit heart particles."""
        ...

    def emit_sparkles(
        self,
        x: float,
        y: float,
        count: int = 15,
        *,
        color: tuple[int, int, int] = settings.PARTICLE_COLOR_SPARKLES,
    ) -> None:
        """Emit sparkle particles."""
        ...

    def emit_trail(
        self,
        x: float,
        y: float,
        count: int = 3,
        *,
        color: tuple[int, int, int] = settings.PARTICLE_COLOR_TRAIL,
    ) -> None:
        """Emit trail particles."""
        ...

    def emit_burst(
        self,
        x: float,
        y: float,
        count: int = 20,
        *,
        color: tuple[int, int, int] = settings.PARTICLE_COLOR_BURST,
    ) -> None:
        """Emit burst particles."""
        ...

    def toggle(self) -> bool:
        """Toggle particle effects on/off."""
        ...

    def clear(self) -> None:
        """Clear all active particles."""
        ...

    def draw(self) -> None:
        """Draw all active particles."""
        ...
```

#### Registration

Register your custom particle plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.particle.base import ParticleBasePlugin

@PluginRegistry.register
class CustomParticlePlugin(ParticleBasePlugin):
    name = "particle"
    dependencies = ["scene"]

    # ... implement all abstract methods ...
```

Then in your project's `settings.py`, load your custom module:

```python
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_particle",  # Load custom particle first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.particle") ...
]
```

## See Also

- [ScriptPlugin](script.md) - Event-driven scripting
- [Configuration Guide](../guides/configuration.md)
- [Scripting Actions](../scripting/actions.md)
