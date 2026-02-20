"""Unit tests for ParticlePlugin in src/pedre/plugins/particle/plugin.py."""

from unittest.mock import MagicMock, patch

import pytest

from pedre.conf import settings
from pedre.plugins.particle.base import Particle
from pedre.plugins.particle.plugin import ParticlePlugin


class TestParticlePlugin:
    """Test Suite for ParticlePlugin."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context."""
        return MagicMock()

    @pytest.fixture
    def plugin(self, mock_context: MagicMock) -> ParticlePlugin:
        """Fixture for ParticlePlugin."""
        p = ParticlePlugin()
        p.setup(mock_context)
        return p

    def test_initialization(self, plugin: ParticlePlugin, mock_context: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "particle"
        assert plugin.particles == []
        assert plugin.enabled is True
        assert plugin.context == mock_context

    def test_emit_hearts(self, plugin: ParticlePlugin) -> None:
        """Test emitting heart particles."""
        plugin.emit_hearts(100, 200, count=5)

        assert len(plugin.particles) == 5
        for p in plugin.particles:
            assert isinstance(p, Particle)
            # Hearts move generally upward (positive Y velocity)
            # Code uses trigonometry to calculate velocity based on angle and speed.
            assert p.fade is True
            # Color check (RGB + 255 alpha)
            r, g, b = settings.PARTICLE_COLOR_HEARTS
            assert p.color == (r, g, b, 255)

    def test_emit_sparkles(self, plugin: ParticlePlugin) -> None:
        """Test emitting sparkle particles."""
        plugin.emit_sparkles(100, 200, count=10)

        assert len(plugin.particles) == 10
        p = plugin.particles[0]
        r, g, b = settings.PARTICLE_COLOR_SPARKLES
        assert p.color == (r, g, b, 255)

    def test_emit_disabled(self, plugin: ParticlePlugin) -> None:
        """Test that nothing is emitted if disabled."""
        plugin.enabled = False
        plugin.emit_hearts(100, 200)
        assert len(plugin.particles) == 0

    def test_update_physics(self, plugin: ParticlePlugin) -> None:
        """Test particle physics updates (velocity, gravity, aging)."""
        # Create a deterministic particle
        p = Particle(
            x=100.0, y=100.0, velocity_x=10.0, velocity_y=10.0, lifetime=1.0, size=5.0, color=(255, 255, 255, 255)
        )
        plugin.particles.append(p)

        delta_time = 0.1
        plugin.update(delta_time)

        # Check aging
        assert p.age == delta_time

        # Check position update: x + vx * dt => 100 + 10 * 0.1 = 101
        assert abs(p.x - 101.0) < 0.0001

        assert abs(p.y - 101.0) < 0.0001
        assert abs(p.velocity_y - 5.0) < 0.0001

    def test_update_removes_dead_particles(self, plugin: ParticlePlugin) -> None:
        """Test that particles exceeding lifetime are removed."""
        p = Particle(x=0, y=0, velocity_x=0, velocity_y=0, lifetime=1.0, age=0.0)
        plugin.particles.append(p)

        # Update with small dt -> still alive
        plugin.update(0.5)
        assert len(plugin.particles) == 1

        # Update past lifetime -> dead
        plugin.update(0.6)  # total age 1.1 > 1.0
        assert len(plugin.particles) == 0

    @patch("arcade.draw_circle_filled")
    def test_draw(self, mock_draw: MagicMock, plugin: ParticlePlugin) -> None:
        """Test drawing particles."""
        p = Particle(
            x=10.0,
            y=20.0,
            velocity_x=0,
            velocity_y=0,
            lifetime=1.0,
            age=0.0,
            color=(255, 0, 0, 255),
            size=5.0,
            fade=True,
        )
        plugin.particles.append(p)

        plugin.draw()

        assert mock_draw.called
        # Check arguments roughly: x, y, radius, color
        args, _ = mock_draw.call_args
        assert args[0] == 10.0
        assert args[1] == 20.0
        assert args[2] == 5.0
        # Alpha should be calculated. At age 0, life_ratio=1.0, alpha=255
        assert args[3] == (255, 0, 0, 255)

    def test_draw_disabled(self, plugin: ParticlePlugin) -> None:
        """Test draw does nothing if disabled."""
        plugin.enabled = False
        plugin.particles.append(Particle(0, 0, 0, 0, 1))

        with patch("arcade.draw_circle_filled") as mock_draw:
            plugin.draw()
            mock_draw.assert_not_called()

    def test_toggle_and_clear(self, plugin: ParticlePlugin) -> None:
        """Test toggling enabled state and clearing particles."""
        plugin.particles.append(Particle(0, 0, 0, 0, 1))

        # Toggle OFF
        new_state = plugin.toggle()
        assert new_state is False
        assert plugin.enabled is False
        assert len(plugin.particles) == 0

        # Toggle ON
        new_state = plugin.toggle()
        assert new_state is True
        assert plugin.enabled is True

    def test_save_restore(self, plugin: ParticlePlugin) -> None:
        """Test save state persistence."""
        plugin.enabled = False
        state = plugin.get_save_state()
        assert state["enabled"] is False

        # Restore
        plugin.enabled = True  # Reset to default
        plugin.restore_save_state(state)
        assert plugin.enabled is False

    def test_cleanup(self, plugin: ParticlePlugin) -> None:
        """Test cleanup clears particles."""
        plugin.particles.append(Particle(0, 0, 0, 0, 1))
        assert len(plugin.particles) == 1

        plugin.cleanup()
        assert len(plugin.particles) == 0

    def test_emit_trail(self, plugin: ParticlePlugin) -> None:
        """Test emitting trail particles."""
        plugin.emit_trail(100, 200, count=3)

        assert len(plugin.particles) == 3
        for p in plugin.particles:
            assert isinstance(p, Particle)
            assert p.fade is True
            # Trail particles start semi-transparent (alpha=128)
            r, g, b = settings.PARTICLE_COLOR_TRAIL
            assert p.color == (r, g, b, 128)
            # Small size for trail particles
            assert 2.0 <= p.size <= 3.0

    def test_emit_trail_disabled(self, plugin: ParticlePlugin) -> None:
        """Test that trail particles are not emitted when disabled."""
        plugin.enabled = False
        plugin.emit_trail(100, 200)
        assert len(plugin.particles) == 0

    def test_emit_burst(self, plugin: ParticlePlugin) -> None:
        """Test emitting burst particles."""
        plugin.emit_burst(100, 200, count=20)

        assert len(plugin.particles) == 20
        for p in plugin.particles:
            assert isinstance(p, Particle)
            assert p.fade is True
            r, g, b = settings.PARTICLE_COLOR_BURST
            assert p.color == (r, g, b, 255)
            # Burst particles are larger
            assert 4.0 <= p.size <= 8.0

    def test_emit_burst_disabled(self, plugin: ParticlePlugin) -> None:
        """Test that burst particles are not emitted when disabled."""
        plugin.enabled = False
        plugin.emit_burst(100, 200)
        assert len(plugin.particles) == 0

    def test_on_draw(self, plugin: ParticlePlugin) -> None:
        """Test on_draw calls draw."""
        with patch.object(plugin, "draw") as mock_draw:
            plugin.on_draw()
            mock_draw.assert_called_once()

    @patch("arcade.draw_circle_filled")
    def test_draw_non_fading_particle(self, mock_draw: MagicMock, plugin: ParticlePlugin) -> None:
        """Test drawing particles without fade."""
        p = Particle(
            x=10.0,
            y=20.0,
            velocity_x=0,
            velocity_y=0,
            lifetime=1.0,
            age=0.0,
            color=(255, 0, 0, 200),
            size=5.0,
            fade=False,  # Non-fading particle
        )
        plugin.particles.append(p)

        plugin.draw()

        assert mock_draw.called
        args, _ = mock_draw.call_args
        # Alpha should remain constant at 200
        assert args[3] == (255, 0, 0, 200)

    def test_reset(self, plugin: ParticlePlugin) -> None:
        """Test reset clears particles."""
        plugin.particles.append(Particle(0, 0, 0, 0, 1))
        assert len(plugin.particles) == 1

        plugin.reset()
        assert len(plugin.particles) == 0

    def test_emit_sparkles_disabled(self, plugin: ParticlePlugin) -> None:
        """Test sparkles emission when plugin is disabled."""
        plugin.enabled = False
        plugin.emit_sparkles(100, 200, count=10)
        assert len(plugin.particles) == 0

    def test_emit_hearts_disabled(self, plugin: ParticlePlugin) -> None:
        """Test hearts emission when plugin is disabled."""
        plugin.enabled = False
        plugin.emit_hearts(100, 200, count=5)
        assert len(plugin.particles) == 0
