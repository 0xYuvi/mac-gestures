# mac-gestures

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-000000.svg)](https://www.apple.com/macos/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**mac-gestures** turns your MacBook's physical body into a touch-sensitive interface. By leveraging the undocumented Apple Silicon IMU (Inertial Measurement Unit), it detects high-frequency vibrations from taps and slaps on the chassis to trigger system-wide actions.

---

## Features

- **Double Tap:** Toggle System Mute/Unmute.
- **Triple Tap:** Skip to the next track in Apple Music or Spotify.
- **Chassis Slap:** Triggers a system alert.
- **High Sensitivity:** Tuned to distinguish between typing and intentional taps.

## Quick Start

### Prerequisites
- A MacBook with Apple Silicon (M1, M2, M3, M4 series).
- Root privileges (Required for low-level HID sensor access).

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/0xYuvi/mac-gestures.git
   cd mac-gestures
   ```

2. **Install the core driver:**
   ```bash
   pip install macimu
   ```

3. **Run the monitor:**
   ```bash
   sudo python3 main.py
   ```

---

## How It Works

This project utilizes the AppleSPU (Sensor Processing Unit) HID interface. Modern MacBooks contain a Bosch-based IMU used for internal telemetry.

**mac-gestures** works by:
1. Reading raw 3-axis acceleration data at 800Hz.
2. Passing the signal through a Biquad High-Pass Filter (cutoff at 15Hz) to remove gravity and slow device movement.
3. Analyzing the Euclidean Magnitude of the filtered signal to detect spikes that represent physical impacts.
4. Using a time-windowed state machine to distinguish between single, double, and triple taps.

---

## Configuration

You can tune the sensitivity in `main.py`:
- `TAP_THRESHOLD`: Increase if the script is too sensitive.
- `SLAP_THRESHOLD`: Increase to require a harder slap.
- `DEBOUNCE_MS`: Time to ignore echo vibrations after a hit.

---

## Future Scope

The goal is to transition this script into a full-featured macOS application with the following roadmap:

- **Menu Bar Integration:** A native Swift-based menu bar app to manage the background process.
- **Custom Mapping UI:** A GUI to allow users to map specific gestures (single/double/triple taps) to custom shell scripts or AppleScript.
- **Machine Learning Integration:** Moving beyond simple magnitude thresholds to ML-based gesture classification (e.g., distinguishing between a "knock" on the lid vs. the palm rest).
- **Sensitivity Profiles:** Presets for different MacBook models (Air vs. Pro) to account for chassis density and dampening.

---

## Credits and Prior Art

This project is built upon the reverse-engineering work found in the [apple-silicon-accelerometer](https://github.com/olvvier/apple-silicon-accelerometer) repository.

Special thanks to **[@olvvier](https://github.com/olvvier)** for developing the `macimu` library and documenting the AppleSPU HID path.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  <i>Developed for the Mac community.</i>
</p>
