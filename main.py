#!/usr/bin/env python3
"""
Chassis Gesture Control for MacBook
Detects "Double Tap" or "Slap" on the MacBook chassis using the IMU
and performs system actions (Mute / Notification).

Usage: sudo python3 chassis_gestures.py
"""

import time
import subprocess
import os
import sys
from macimu import IMU
from macimu.filters import GravityKalman, magnitude

# --- Configuration ---
TAP_THRESHOLD = 0.12      # g's above noise (lower for sensitivity, higher for stability)
SLAP_THRESHOLD = 0.8      # g's for a hard slap
TAP_WINDOW = (0.1, 0.5)   # max seconds between taps
TRIPLE_TAP_WAIT = 0.35    # how long to wait after 2nd tap to see if a 3rd is coming
DEBOUNCE_MS = 0.12        # ignore peaks within this time (prevents echo)
COOLDOWN = 0.6            # wait after full gesture completion

def trigger_action(action_name):
    """Perform system actions based on gestures."""
    if action_name == "double_tap":
        print("\n[GESTURE] Double Tap Detected! -> Toggling Mute")
        # AppleScript to toggle mute
        cmd = "osascript -e 'set volume output muted not (output muted of (get volume settings))'"
        subprocess.run(cmd, shell=True)
        # Visual notification
        subprocess.run('osascript -e \'display notification "Mute Toggled " with title "Mac Gesture"\'', shell=True)
        
    elif action_name == "slap":
        print("\n[GESTURE] Chassis Slap Detected! -> Sending Alert")
        # Play a system sound
        subprocess.run("afplay /System/Library/Sounds/Tink.aiff", shell=True)
        subprocess.run('osascript -e \'display notification "Stop hitting me! " with title "Mac Hardware Alert"\'', shell=True)
        
    elif action_name == "triple_tap":
        print("\n[GESTURE] Triple Tap Detected! -> Skipping Track")
        # Try Music first, then Spotify
        cmd = """
        osascript -e 'if application "Music" is running then tell application "Music" to next track' \
                  -e 'if application "Spotify" is running then tell application "Spotify" to next track'
        """
        subprocess.run(cmd, shell=True)
        subprocess.run('osascript -e \'display notification "Skipped Track " with title "Mac Gesture"\'', shell=True)

class StatefulBiquad:
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
        print("ERROR: This script needs root privileges for IMU access.")
        print("Please run: sudo python3 chassis_gestures.py")
        sys.exit(1)

    print("🚀 Starting Chassis Gesture Monitor...")
    print("---------------------------------------")
    print("Action 1: Double-tap to Mute/Unmute.")
    print("Action 2: Triple-tap to Skip Song (Music/Spotify).")
    print("Action 3: Slap for a surprise.")
    print("---------------------------------------")

    # Use maximum sample rate (decimation=1 -> ~800Hz) to capture impacts
    with IMU(accel=True, gyro=False, decimation=1) as imu:
        from macimu.filters import _biquad_coeffs_hp
        
        # Setup stateful high-pass filter at 15Hz
        hp_coeffs = _biquad_coeffs_hp(cutoff_hz=15, sample_rate=800)
        hp = StatefulBiquad(*hp_coeffs)
        
        last_tap_t = 0
        last_gesture_t = 0
        tap_count = 0
        
        print("Calibrating (keep Mac flat)...")
        # Priming the filter to avoid startup spike
        for _ in range(50):
            imu.read_accel()
            time.sleep(0.01)

        try:
            while True:
                # Read all new samples
                raw_samples = imu.read_accel()
                if not raw_samples:
                    time.sleep(0.002)
                    continue
                
                t_now = time.time()
                latest_filtered_mag = 0

                for s in raw_samples:
                    # Apply stateful high-pass
                    fx, fy, fz = hp.process_one(s.x, s.y, s.z)
                    mag = magnitude(fx, fy, fz)
                    latest_filtered_mag = mag

                    # Ignore all peaks if we just triggered a gesture
                    if t_now - last_gesture_t < COOLDOWN:
                        continue

                    # 1. Check for hard slap (high priority)
                    if mag > SLAP_THRESHOLD:
                        trigger_action("slap")
                        last_gesture_t = t_now
                        tap_count = 0
                        break # Skip rest of this batch

                    # 2. Check for Tap peak
                    if mag > TAP_THRESHOLD:
                        # Debounce check
                        if t_now - last_tap_t > DEBOUNCE_MS:
                            dt = t_now - last_tap_t
                            
                            if tap_count == 0:
                                # First tap!
                                sys.stdout.write("\n[TAP 1] Waiting...")
                                tap_count = 1
                            elif tap_count == 1 and dt < TAP_WINDOW[1]:
                                # Second tap!
                                sys.stdout.write("\r[TAP 2] Waiting for Triple or Timeout...  ")
                                tap_count = 2
                            elif tap_count == 2 and dt < TRIPLE_TAP_WAIT:
                                # Registered third tap!
                                trigger_action("triple_tap")
                                last_gesture_t = t_now
                                tap_count = 0
                            
                            sys.stdout.flush()
                            last_tap_t = t_now

                # Logic to "finalize" a double-tap if no third tap follows
                if tap_count == 2 and (t_now - last_tap_t) > TRIPLE_TAP_WAIT:
                    trigger_action("double_tap")
                    last_gesture_t = t_now
                    tap_count = 0

                # Logic to time out a single tap
                if tap_count == 1 and (t_now - last_tap_t) > TAP_WINDOW[1]:
                    tap_count = 0
                    sys.stdout.write("\r[TAP 1] Timed out.          \n")

                # Update UI periodically
                bar_len = int(min(1.0, latest_filtered_mag / (TAP_THRESHOLD * 2)) * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                status_txt = f"[TAP {tap_count}]" if tap_count > 0 else "Ready   "
                sys.stdout.write(f"\rRecoil: [{bar}] {latest_filtered_mag:.3f}g  {status_txt} ")
                sys.stdout.flush()
                
        except KeyboardInterrupt:
            print("\nStopping Gesture Monitor...")

if __name__ == "__main__":
    main()
