import os
import time
import datetime
import threading
import requests  # टेलीग्राम पर भेजने के लिए

# --- 1. Render & Virtual Screen Setup (इसे सबसे ऊपर रखना जरूरी है) ---
os.environ['HOME'] = '/tmp'

try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1280, height=725)
    vdisplay.start()
    os.environ['DISPLAY'] = vdisplay.new_display
    print(f"[+] Virtual display started on {os.environ['DISPLAY']}")
except Exception as e:
    print(f"[-] Could not start Xvfb (running locally?): {e}")

# --- बाकी इम्पोर्ट्स ---
from mss import MSS  # वॉर्निंग से बचने के लिए कैपिटल MSS का उपयोग
from PIL import Image
from flask import Flask, jsonify

app = Flask(__name__)

# =================================================================
# ⚠️ यहाँ अपनी टेलीग्राम डिटेल्स डालें
TELEGRAM_TOKEN ="ec5f3ec29625714ba93a77cb4df24eb1"
TELEGRAM_CHAT_ID = 38829911 
# =================================================================

# Folder create karo agar nahi hai toh
SCREENSHOT_DIR = "screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# --- Telegram Helper ---
def send_to_telegram(file_path: str):
    """स्क्रीनशॉट को सीधे टेलीग्राम पर भेजता है"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        with open(file_path, 'rb') as photo:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID, 
                'caption': f"📸 Screenshot captured at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            files = {'photo': photo}
            response = requests.post(url, data=payload, files=files)
            if response.status_code == 200:
                print("[+] Successfully sent to Telegram!")
            else:
                print(f"[-] Telegram error: {response.text}")
    except Exception as e:
        print(f"[-] Failed to send Telegram message: {e}")

# --- Screenshot helper ---
def take_screenshot():
    """
    Screen capture karke file mein save karta hai aur Telegram par bhejta hai.
    """
    # Python 3.14 compatible timezone-aware timestamp
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    try:
        with MSS() as sct:
            # Primary monitor grab karo
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            # Convert to RGB for PIL
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            
            # Save file locally
            img.save(filepath)
            print(f"[+] Screenshot saved locally: {filepath}")
            
            # Telegram par bhejen
            send_to_telegram(filepath)
            
            # Render की मेमोरी भरने से रोकने के लिए भेजने के बाद फाइल डिलीट कर देते हैं
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return filepath
    except Exception as e:
        print(f"[-] Error taking screenshot: {e}")
        return None

@app.route('/')
def home():
    return "Server is running! Screenshotting automatically and sending to Telegram..."

@app.route('/capture', methods=['GET'])
def capture_endpoint():
    """
    Browser ya phone se /capture pe jao toh manual screenshot lega.
    """
    file_path = take_screenshot()
    if file_path:
        return jsonify({"status": "success", "msg": "Screenshot taken and sent to Telegram!"})
    else:
        return jsonify({"status": "error"})

def auto_capture_loop():
    """
    Background mein har 5 second mein screenshot leta rahega.
    """
    print("[*] Starting automatic capture loop...")
    while True:
        take_screenshot()
        time.sleep(5)  # Har 5 second mein naya screenshot

if __name__ == "__main__":
    # Background thread start karo jo har 5 sec me screenshot lega
    t = threading.Thread(target=auto_capture_loop)
    t.daemon = True  # Main process band hone par yeh bhi band ho jayega
    t.start()

    # Flask server start karo port 10000 par Render ke liye
    try:
        app.run(host='0.0.0.0', port=10000)
    finally:
        # क्लीनअप ताकि वर्चुअल डिस्प्ले बंद हो सके
        if 'vdisplay' in locals():
            vdisplay.stop()
            print("[+] Virtual display stopped.")
