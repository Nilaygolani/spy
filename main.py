import os

# --- Render & Virtual Screen Setup (इसे सबसे ऊपर रखना ज़रूरी है) ---
# Xlib की एरर रोकने के लिए होम डायरेक्टरी बदलना
os.environ['HOME'] = '/tmp'

try:
    from xvfbwrapper import Xvfb
    # वर्चुअल डिस्प्ले शुरू करना
    vdisplay = Xvfb(width=1280, height=725)
    vdisplay.start()
    # 'mss' और बाकी टूल्स को वर्चुअल डिस्प्ले का पता बताना
    os.environ['DISPLAY'] = vdisplay.new_display
    print(f"[+] Virtual display started on {os.environ['DISPLAY']}")
except Exception as e:
    print(f"[-] Could not start Xvfb (running locally?): {e}")

# --- बाकी इम्पोर्ट्स ---
import time
import datetime
from mss import MSS  # पुराने mss (small letters) की जगह कैपिटल MSS का इस्तेमाल
from PIL import Image

# --- Screenshot helper -------------------------------------------------------
def take_screenshot(save_dir: str = "screenshots") -> str:
    """
    Capture the entire primary monitor and save as PNG.
    Returns the full path to the saved file.
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # Python 3.14 के लिए utcnow() की जगह नया सही तरीका
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(save_dir, f"screenshot_{timestamp}.png")

    # नए तरीके से Capital MSS() का इस्तेमाल किया
    with MSS() as sct:
        # Grab the primary monitor
        monitor = sct.monitors[1]          # 1 = primary monitor
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        img.save(file_path)

    print(f"[+] Screenshot saved: {file_path}")
    return file_path

# --- Main loop ---------------------------------------------------------------
if __name__ == "__main__":
    # Example: take one screenshot every 10 seconds
    try:
        while True:
            take_screenshot()
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[!] Stopped by user.")
    finally:
        # स्क्रिप्ट बंद होने पर वर्चुअल डिस्प्ले को भी साफ-सफाई से बंद करना
        if 'vdisplay' in locals():
            vdisplay.stop()
            print("[+] Virtual display stopped.")
