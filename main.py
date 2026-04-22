#!/usr/bin/env python3
"""
mac-gestures: Professional Chassis Gesture Controller
Detects physical impacts on the MacBook body to trigger system actions.
"""

import time
import subprocess
import os
import sys
from macimu import IMU
from macimu.filters import magnitude

# --- Global Configuration ---
class Config:
    TAP_THRESHOLD = 0.12      # g's above noise
    SLAP_THRESHOLD = 0.8      # g's for a hard slap
    TAP_WINDOW = (0.1, 0.5)   # Seconds between taps
    TRIPLE_TAP_WAIT = 0.35    # Wait for 3rd tap
    DEBOUNCE_MS = 0.12        # Ignore echo peaks
    COOLDOWN = 0.6            # Wait after gesture
    HP_CUTOFF = 15            # High-pass filter frequency (Hz)
    SAMPLE_RATE = 800         # SPU native rate

class SystemActions:
    """Encapsulates system-level reactions to gestures."""
    
    @staticmethod
    def toggle_mute():
        cmd = "osascript -e 'set volume output muted not (output muted of (get volume settings))'"
        subprocess.run(cmd, shell=True)
        subprocess.run('osascript -e \'display notification "Mute Toggled" with title "mac-gestures"\'', shell=True)

    @staticmethod
    def next_track():
        cmd = """
        osascript -e 'if application "Music" is running then tell application "Music" to next track' \
                  -e 'if application "Spotify" is running then tell application "Spotify" to next track'
        """
        subprocess.run(cmd, shell=True)
        subprocess.run('osascript -e \'display notification "Skipped Track" with title "mac-gestures"\'', shell=True)

    @staticmethod
    def slap_alert():
        subprocess.run("afplay /System/Library/Sounds/Tink.aiff", shell=True)
        subprocess.run('osascript -e \'display notification "Chassis impact detected!" with title "mac-gestures"\'', shell=True)

class StatefulBiquad:
    """Stateful filter implementation for real-time signal processing."""
    def __init__(self, b0, b1, b2, a1, a2):
        self.coeffs = (b0, b1, b2, a1, a2)
        self.dx1, self.dx2 = 0.0, 0.0
        self.dy1, self.dy2 = 0.0, 0.0
        self.dz1, self.dz2 = 0.0, 0.0

    def process_one(self, x, y, z):
        b0, b1, b2, a1, a2 = self.coeffs
        ox = b0 * x + self.dx1
        self.dx1 = b1 * x - a1 * ox + self.dx2
        self.dx2 = b2 * x - a2 * ox
        oy = b0 * y + self.dy1
        self.dy1 = b1 * y - a1 * oy + self.dy2
        self.dy2 = b2 * y - a2 * oy
        oz = b0 * z + self.dz1
        self.dz1 = b1 * z - a1 * oz + self.dz2
        self.dz2 = b2 * z - a2 * oz
        return ox, oy, oz

def main():
    if os.geteuid() != 0:
        print("Error: Root privileges required for HID access. Run with sudo.")
        sys.exit(1)

    print("mac-gestures: Monitoring hardware impacts...")
    print("------------------------------------------")
    print("Double-tap: Toggle Mute")
    print("Triple-tap: Next Track")
    print("Hard Slap: System Alert")
    print("------------------------------------------")

    with IMU(accel=True, gyro=False, decimation=1) as imu:
        from macimu.filters import _biquad_coeffs_hp
        
        hp_coeffs = _biquad_coeffs_hp(cutoff_hz=Config.HP_CUTOFF, sample_rate=Config.SAMPLE_RATE)
        hp = StatefulBiquad(*hp_coeffs)
        
        last_tap_t = 0
        last_gesture_t = 0
        tap_count = 0
        
        try:
            while True:
                raw_samples = imu.read_accel()
                if not raw_samples:
                    time.sleep(0.002)
                    continue
                
                t_now = time.time()

                for s in raw_samples:
                    fx, fy, fz = hp.process_one(s.x, s.y, s.z)
                    mag = magnitude(fx, fy, fz)

                    if t_now - last_gesture_t < Config.COOLDOWN:
                        continue

                    # Hard Slap
                    if mag > Config.SLAP_THRESHOLD:
                        SystemActions.slap_alert()
                        last_gesture_t = t_now
                        tap_count = 0
                        break

                    # Tap Detection
                    if mag > Config.TAP_THRESHOLD:
                        if t_now - last_tap_t > Config.DEBOUNCE_MS:
                            dt = t_now - last_tap_t
                            
                            if tap_count == 0:
                                tap_count = 1
                            elif tap_count == 1 and dt < Config.TAP_WINDOW[1]:
                                tap_count = 2
                            elif tap_count == 2 and dt < Config.TRIPLE_TAP_WAIT:
                                SystemActions.next_track()
                                last_gesture_t = t_now
                                tap_count = 0
                            
                            last_tap_t = t_now

                # Finalize Double Tap
                if tap_count == 2 and (t_now - last_tap_t) > Config.TRIPLE_TAP_WAIT:
                    SystemActions.toggle_mute()
                    last_gesture_t = t_now
                    tap_count = 0

                # Reset single tap timeout
                if tap_count == 1 and (t_now - last_tap_t) > Config.TAP_WINDOW[1]:
                    tap_count = 0

        except KeyboardInterrupt:
            print("\nShutting down monitor.")

if __name__ == "__main__":
    main()
