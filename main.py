import os
import time
import datetime
import threading
import asyncio

# --- 1. Render & Virtual Screen Setup ---
os.environ['HOME'] = '/tmp'

try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1280, height=725)
    vdisplay.start()
    os.environ['DISPLAY'] = vdisplay.new_display
    print(f"[+] Virtual display started on {os.environ['DISPLAY']}")
except Exception as e:
    print(f"[-] Could not start Xvfb: {e}")

# --- बाकी इम्पोर्ट्स ---
from mss import MSS
from PIL import Image
from flask import Flask, jsonify
from telethon import TelegramClient

app = Flask(__name__)

# =================================================================
# ⚠️ यहाँ अपनी टेलीग्राम API डिटेल्स डालें (my.telegram.org वाली)
API_ID = 3882991     # यहाँ अपनी API ID डालें (बिना Quotes के, सिर्फ नंबर)
API_HASH = "ec5f3ec29625714ba93a77cb4df24eb1"
# =================================================================

# Telethon क्लाइंट सेटअप (यह आपके Saved Messages में 'me' पर भेजेगा)
client = TelegramClient('/tmp/session_name', API_ID, API_HASH)

# Folder create karo agar nahi hai toh
SCREENSHOT_DIR = "screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

async def send_to_telegram_async(file_path: str):
    """Telethon के ज़रिए स्क्रीनशॉट को आपके Saved Messages में भेजता है"""
    try:
        # अगर क्लाइंट कनेक्टेड नहीं है तो कनेक्ट करें
        if not client.is_connected():
            await client.connect()
        
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 'me' का मतलब है आपके खुद के Saved Messages
        await client.send_file('me', file_path, caption=f"📸 Captured at: {timestamp}")
        print("[+] Successfully sent to Saved Messages via Telethon!")
    except Exception as e:
        print(f"[-] Telethon upload error: {e}")

def take_screenshot():
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)

    try:
        with MSS() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            img.save(filepath)
            print(f"[+] Screenshot saved locally: {filepath}")
            
            # Async फंक्शन को सिंक्रोनस कोड से चलाने का तरीका
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_to_telegram_async(filepath))
            loop.close()
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
            return filepath
    except Exception as e:
        print(f"[-] Error taking screenshot: {e}")
        return None

@app.route('/')
def home():
    return "Server is running with Telethon Userbot!"

def auto_capture_loop():
    print("[*] Starting automatic capture loop...")
    while True:
        take_screenshot()
        time.sleep(5)

if __name__ == "__main__":
    # पहली बार चलने पर यह आपसे टर्मिनल में आपका फ़ोन नंबर और OTP मांगेगा लॉगिन के लिए
    client.loop.run_until_complete(client.connect())
    if not client.loop.run_until_complete(client.is_user_authorized()):
        print("[-] कृपया ध्यान दें: पहली बार लॉगिन के लिए आपको इसे लोकल कंप्यूटर पर रन करना होगा ताकि आप OTP डाल सकें।")
    
    t = threading.Thread(target=auto_capture_loop)
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', port=10000)
