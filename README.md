# macOS Chassis Gestures 🖱️💻

Control your Mac by physically tapping or slapping its chassis. This project uses the undocumented Apple Silicon IMU (accelerometer) to detect vibrations and trigger system actions.

## 🚀 Features
- **Double Tap:** Toggle Mute/Unmute.
- **Triple Tap:** Skip to the next track (Music/Spotify).
- **Chassis Slap:** Trigger a custom alert/sound.

## 📦 Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/macos-chassis-gestures.git
   cd macos-chassis-gestures
   ```

2. **Install dependencies:**
   ```bash
   pip install macimu
   ```

## 🎮 Usage
Since accessing the IMU requires low-level HID access, you must run the script with **sudo**:

```bash
sudo python3 main.py
```

## 🛠️ How it works
The script reads raw acceleration data at ~800Hz via IOKit. It uses a high-pass filter to isolate the sharp "spikes" caused by physical impacts on the laptop body while ignoring the slow movement of the laptop itself.

## ⚠️ Requirements
- MacBook with Apple Silicon (M1 Pro/Max, M2, M3, M4).
- macOS 13.0 or newer.
- Root privileges (sudo).

## License
MIT
