# AudioManager

Manages background music and sound effects with caching.

## Location

`src/pedre/systems/audio.py`

## Initialization

```python
from pedre.systems.audio import AudioManager

audio_manager = AudioManager(
    music_volume=0.5,  # 0.0 to 1.0
    sfx_volume=0.7     # 0.0 to 1.0
)
```

## Key Methods

### `play_music(filename: str, loop: bool = True) -> None`

Play background music.

**Parameters:**

- `filename` - Music file path (relative to assets/audio/music/)
- `loop` - Whether to loop the music (default: True)

**Example:**

```python
audio_manager.play_music("village_theme.ogg", loop=True)
```

### `stop_music() -> None`

Stop the currently playing music.

**Example:**

```python
audio_manager.stop_music()
```

### `play_sound(filename: str) -> None`

Play a sound effect.

**Parameters:**

- `filename` - Sound file path (relative to assets/audio/sfx/)

**Example:**

```python
audio_manager.play_sound("door_open.wav")
audio_manager.play_sound("footstep.wav")
```

### `set_music_volume(volume: float) -> None`

Set the music volume level.

**Parameters:**

- `volume` - Volume from 0.0 (mute) to 1.0 (full)

**Example:**

```python
audio_manager.set_music_volume(0.3)  # 30% volume
```

### `set_sfx_volume(volume: float) -> None`

Set the sound effects volume level.

**Parameters:**

- `volume` - Volume from 0.0 (mute) to 1.0 (full)

**Example:**

```python
audio_manager.set_sfx_volume(0.8)  # 80% volume
```

## Supported Formats

- Music: `.mp3`, `.ogg`, `.wav`
- SFX: `.wav`, `.ogg`
