import os
import time
import datetime
from mss import mss
from PIL import Image
from flask import Flask, jsonify

app = Flask(__name__)

# Folder create karo agar nahi hai toh
SCREENSHOT_DIR = "screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

def take_screenshot():
    """
    Screen capture karke file mein save karta hai.
    Returns the filename.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    try:
        with mss() as sct:
            # Primary monitor grab karo (monitor 1 usually primary hota hai)
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            # Convert to RGB for PIL
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            
            # Save file
            img.save(filepath)
            print(f"[+] Screenshot saved: {filepath}")
            return filepath
    except Exception as e:
        print(f"[-] Error taking screenshot: {e}")
        return None

@app.route('/')
def home():
    return "Server is running! Screenshotting automatically..."

@app.route('/capture', methods=['GET'])
def capture_endpoint():
    """
    Yeh endpoint manually trigger karne ke liye hai.
    Browser ya phone se /capture pe jao toh screenshot lega.
    """
    file_path = take_screenshot()
    if file_path:
        return jsonify({"status": "success", "file": file_path})
    else:
        return jsonify({"status": "error"})

def auto_capture_loop():
    """
    Yeh function background mein chalta rahega aur har 5 second mein screenshot lega.
    """
    print("[*] Starting automatic capture loop...")
    while True:
        take_screenshot()
        time.sleep(5)  # Har 5 second mein naya screenshot

if __name__ == "__main__":
    import threading
    
    # Background thread start karo jo har 5 sec me screenshot lega
    t = threading.Thread(target=auto_capture_loop)
    t.daemon = True  # Jab main process band hoga, yeh bhi band ho jayega
    t.start()

    # Flask server start karo taaki tum manually bhi trigger kar sako
    # port 10000 use kar rahe hain Render ke liye compatible
    app.run(host='0.0.0.0', port=10000)
