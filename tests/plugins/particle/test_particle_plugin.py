"""Unit tests for ParticlePlugin in src/pedre/plugins/particle/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

from pedre.conf import settings
from pedre.plugins.particle.base import Particle
from pedre.plugins.particle.plugin import ParticlePlugin


class TestParticlePlugin(unittest.TestCase):
    """Test Suite for ParticlePlugin."""

    def setUp(self) -> None:
        """Set up the ParticlePlugin."""
        self.plugin = ParticlePlugin()
        self.mock_context = MagicMock()
        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "particle"
        assert self.plugin.particles == []
        assert self.plugin.enabled is True
        assert self.plugin.context == self.mock_context

    def test_emit_hearts(self) -> None:
        """Test emitting heart particles."""
        self.plugin.emit_hearts(100, 200, count=5)

        assert len(self.plugin.particles) == 5
        for p in self.plugin.particles:
            assert isinstance(p, Particle)
            # Hearts move generally upward (positive Y velocity)
            # Code uses trigonometry to calculate velocity based on angle and speed.
            assert p.fade is True
            # Color check (RGB + 255 alpha)
            r, g, b = settings.PARTICLE_COLOR_HEARTS
            assert p.color == (r, g, b, 255)

    def test_emit_sparkles(self) -> None:
        """Test emitting sparkle particles."""
        self.plugin.emit_sparkles(100, 200, count=10)

        assert len(self.plugin.particles) == 10
        p = self.plugin.particles[0]
        r, g, b = settings.PARTICLE_COLOR_SPARKLES
        assert p.color == (r, g, b, 255)

    def test_emit_disabled(self) -> None:
        """Test that nothing is emitted if disabled."""
        self.plugin.enabled = False
        self.plugin.emit_hearts(100, 200)
        assert len(self.plugin.particles) == 0

    def test_update_physics(self) -> None:
        """Test particle physics updates (velocity, gravity, aging)."""
        # Create a deterministic particle
        p = Particle(
            x=100.0, y=100.0, velocity_x=10.0, velocity_y=10.0, lifetime=1.0, size=5.0, color=(255, 255, 255, 255)
        )
        self.plugin.particles.append(p)

        delta_time = 0.1
        self.plugin.update(delta_time)

        # Check aging
        assert p.age == delta_time

        # Check position update: x + vx * dt => 100 + 10 * 0.1 = 101
        assert abs(p.x - 101.0) < 0.0001

        assert abs(p.y - 101.0) < 0.0001
        assert abs(p.velocity_y - 5.0) < 0.0001

    def test_update_removes_dead_particles(self) -> None:
        """Test that particles exceeding lifetime are removed."""
        p = Particle(x=0, y=0, velocity_x=0, velocity_y=0, lifetime=1.0, age=0.0)
        self.plugin.particles.append(p)

        # Update with small dt -> still alive
        self.plugin.update(0.5)
        assert len(self.plugin.particles) == 1

        # Update past lifetime -> dead
        self.plugin.update(0.6)  # total age 1.1 > 1.0
        assert len(self.plugin.particles) == 0

    @patch("arcade.draw_circle_filled")
    def test_draw(self, mock_draw: MagicMock) -> None:
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
        self.plugin.particles.append(p)

        self.plugin.draw()

        assert mock_draw.called
        # Check arguments roughly: x, y, radius, color
        args, _ = mock_draw.call_args
        assert args[0] == 10.0
        assert args[1] == 20.0
        assert args[2] == 5.0
        # Alpha should be calculated. At age 0, life_ratio=1.0, alpha=255
        assert args[3] == (255, 0, 0, 255)

    def test_draw_disabled(self) -> None:
        """Test draw does nothing if disabled."""
        self.plugin.enabled = False
        self.plugin.particles.append(Particle(0, 0, 0, 0, 1))

        with patch("arcade.draw_circle_filled") as mock_draw:
            self.plugin.draw()
            mock_draw.assert_not_called()

    def test_toggle_and_clear(self) -> None:
        """Test toggling enabled state and clearing particles."""
        self.plugin.particles.append(Particle(0, 0, 0, 0, 1))

        # Toggle OFF
        new_state = self.plugin.toggle()
        assert new_state is False
        assert self.plugin.enabled is False
        assert len(self.plugin.particles) == 0

        # Toggle ON
        new_state = self.plugin.toggle()
        assert new_state is True
        assert self.plugin.enabled is True

    def test_save_restore(self) -> None:
        """Test save state persistence."""
        self.plugin.enabled = False
        state = self.plugin.get_save_state()
        assert state["enabled"] is False

        # Restore
        self.plugin.enabled = True  # Reset to default
        self.plugin.restore_save_state(state)
        assert self.plugin.enabled is False


if __name__ == "__main__":
    unittest.main()
