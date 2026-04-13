#!/usr/bin/env python3
"""
Music Light Show - Real-Time Audio-Reactive Light Controller

Captures system audio on macOS (from AirPlay/Spotify) via a loopback
audio device (e.g. BlackHole), analyzes it in real-time, and drives
light show effects based on beats and frequency bands.

Setup:
  1. Install BlackHole (https://existential.audio/blackhole/)
  2. Create a Multi-Output Device in Audio MIDI Setup that combines
     your speakers + BlackHole so you hear the music AND this script
     can capture it.
  3. pip install sounddevice numpy
  4. Play music via AirPlay to your Mac or directly from Spotify.
  5. Run: python music_light_show.py
"""

import argparse
import sys
import time
import threading
from collections import deque

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Install with: pip install numpy", file=sys.stderr)
    sys.exit(1)

try:
    import sounddevice as sd
except ImportError:
    print("Error: sounddevice is required. Install with: pip install sounddevice", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Frequency band definitions (Hz)
# ---------------------------------------------------------------------------
BANDS = {
    "sub_bass":  (20, 60),
    "bass":      (60, 250),
    "low_mid":   (250, 500),
    "mid":       (500, 2000),
    "high_mid":  (2000, 6000),
    "highs":     (6000, 20000),
}

# Default color mapping per band (RGB tuples)
BAND_COLORS = {
    "sub_bass":  (128, 0, 255),   # deep purple
    "bass":      (255, 0, 0),     # red
    "low_mid":   (255, 128, 0),   # orange
    "mid":       (0, 255, 0),     # green
    "high_mid":  (0, 128, 255),   # sky blue
    "highs":     (255, 255, 255), # white
}


class BeatDetector:
    """Simple energy-based beat detector."""

    def __init__(self, history_seconds=1.0, sample_rate=44100, hop_size=1024):
        history_length = int(history_seconds * sample_rate / hop_size)
        self.energy_history = deque(maxlen=max(history_length, 1))
        self.threshold_multiplier = 1.4
        self.last_beat_time = 0.0
        self.min_beat_interval = 0.15  # ignore beats closer than 150ms

    def detect(self, energy):
        """Return True if the current frame is a beat."""
        self.energy_history.append(energy)
        if len(self.energy_history) < self.energy_history.maxlen:
            return False

        avg_energy = np.mean(self.energy_history)
        now = time.time()
        if energy > avg_energy * self.threshold_multiplier:
            if now - self.last_beat_time > self.min_beat_interval:
                self.last_beat_time = now
                return True
        return False


class AudioAnalyzer:
    """Real-time FFT analysis split into frequency bands."""

    def __init__(self, sample_rate=44100, block_size=1024):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.freqs = np.fft.rfftfreq(block_size, d=1.0 / sample_rate)

    def analyze(self, audio_block):
        """Return a dict of {band_name: energy} for the given audio block."""
        mono = audio_block.mean(axis=1) if audio_block.ndim > 1 else audio_block
        windowed = mono * np.hanning(len(mono))
        spectrum = np.abs(np.fft.rfft(windowed))

        band_energies = {}
        for band_name, (lo, hi) in BANDS.items():
            mask = (self.freqs >= lo) & (self.freqs < hi)
            band_energies[band_name] = float(np.mean(spectrum[mask])) if mask.any() else 0.0

        return band_energies


class LightController:
    """
    Translates audio analysis into light commands.

    This base implementation prints to the console. Subclass and override
    `send_lights` to talk to real hardware (DMX, WLED, Hue, etc.).
    """

    def __init__(self, num_zones=6):
        self.num_zones = num_zones
        self.band_names = list(BANDS.keys())

    def compute_colors(self, band_energies, is_beat):
        """Map band energies to RGB colors for each zone."""
        colors = []
        for band_name in self.band_names[:self.num_zones]:
            energy = band_energies.get(band_name, 0.0)
            brightness = min(energy / 50.0, 1.0)  # normalize
            if is_beat and band_name in ("bass", "sub_bass"):
                brightness = min(brightness * 1.8, 1.0)  # flash on beat

            base_r, base_g, base_b = BAND_COLORS.get(band_name, (255, 255, 255))
            r = int(base_r * brightness)
            g = int(base_g * brightness)
            b = int(base_b * brightness)
            colors.append((r, g, b))
        return colors

    def send_lights(self, colors, is_beat):
        """Send colors to lights. Override for real hardware."""
        pass


class ConsoleLightController(LightController):
    """Prints a colorized bar visualization to the terminal."""

    RESET = "\033[0m"

    @staticmethod
    def rgb_bg(r, g, b):
        return f"\033[48;2;{r};{g};{b}m"

    def send_lights(self, colors, is_beat):
        beat_indicator = " ** BEAT ** " if is_beat else "            "
        blocks = ""
        for r, g, b in colors:
            blocks += self.rgb_bg(r, g, b) + "      " + self.RESET
        sys.stdout.write(f"\r{blocks} {beat_indicator}")
        sys.stdout.flush()


class MusicLightShow:
    """Main coordinator: captures audio, analyzes, and drives lights."""

    def __init__(self, device=None, sample_rate=44100, block_size=1024,
                 light_controller=None):
        self.device = device
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.analyzer = AudioAnalyzer(sample_rate, block_size)
        self.beat_detector = BeatDetector(sample_rate=sample_rate,
                                          hop_size=block_size)
        self.light_controller = light_controller or ConsoleLightController()
        self._running = False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"\n[audio warning] {status}", file=sys.stderr)
        band_energies = self.analyzer.analyze(indata)
        total_energy = sum(band_energies.values())
        is_beat = self.beat_detector.detect(total_energy)
        colors = self.light_controller.compute_colors(band_energies, is_beat)
        self.light_controller.send_lights(colors, is_beat)

    def list_devices(self):
        """Print available audio input devices."""
        print("Available audio input devices:\n")
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                marker = " <-- (default)" if i == sd.default.device[0] else ""
                print(f"  [{i}] {dev['name']} "
                      f"({dev['max_input_channels']} ch, "
                      f"{int(dev['default_samplerate'])} Hz){marker}")
        print()
        print("Tip: Look for 'BlackHole' or your Multi-Output Device.")

    def run(self):
        """Start capturing audio and driving lights."""
        device_name = self.device if self.device is not None else "default"
        print(f"Starting Music Light Show")
        print(f"  Audio device : {device_name}")
        print(f"  Sample rate  : {self.sample_rate} Hz")
        print(f"  Block size   : {self.block_size} samples")
        print()
        print("Play music via AirPlay or Spotify on your Mac.")
        print("Press Ctrl+C to stop.\n")

        self._running = True
        try:
            with sd.InputStream(device=self.device,
                                channels=2,
                                samplerate=self.sample_rate,
                                blocksize=self.block_size,
                                callback=self._audio_callback):
                while self._running:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nStopped.")
        except sd.PortAudioError as e:
            print(f"\nAudio device error: {e}", file=sys.stderr)
            print("Run with --list-devices to see available inputs.",
                  file=sys.stderr)
            sys.exit(1)

    def stop(self):
        self._running = False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Real-time music-reactive light show. "
                    "Captures system audio on macOS (AirPlay / Spotify) "
                    "via a loopback device and drives light effects.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Quick-start:
  1. Install BlackHole:  brew install blackhole-2ch
  2. Open Audio MIDI Setup on your Mac.
  3. Create a Multi-Output Device combining your speakers + BlackHole 2ch.
  4. Set that Multi-Output Device as your system sound output.
  5. pip install sounddevice numpy
  6. python music_light_show.py --list-devices   # find BlackHole index
  7. python music_light_show.py --device <index>  # start the show
  8. Play music from Spotify or AirPlay from your iPhone.
""",
    )

    parser.add_argument(
        "--list-devices", action="store_true",
        help="List available audio input devices and exit",
    )
    parser.add_argument(
        "--device", type=int, default=None,
        help="Audio input device index (use --list-devices to find it)",
    )
    parser.add_argument(
        "--sample-rate", type=int, default=44100,
        help="Audio sample rate in Hz (default: 44100)",
    )
    parser.add_argument(
        "--block-size", type=int, default=1024,
        help="Audio block size in samples (default: 1024)",
    )

    args = parser.parse_args()

    show = MusicLightShow(
        device=args.device,
        sample_rate=args.sample_rate,
        block_size=args.block_size,
    )

    if args.list_devices:
        show.list_devices()
        return

    show.run()


if __name__ == "__main__":
    main()
