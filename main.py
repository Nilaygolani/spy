import os
import time
import datetime
from mss import mss
from PIL import Image

# --- Screenshot helper -------------------------------------------------------
def take_screenshot(save_dir: str = "screenshots") -> str:
    """
    Capture the entire primary monitor and save as PNG.
    Returns the full path to the saved file.
    """
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(save_dir, f"screenshot_{timestamp}.png")

    with mss() as sct:
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
