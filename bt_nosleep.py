import numpy as np
import sounddevice as sd
import threading
import time
import pystray
from PIL import Image, ImageDraw

# -----------------------------
# AYARLAR
# -----------------------------
SAMPLE_RATE = 44100
VOLUME = 0.002   # çok düşük ses (kritik)
BLOCK_SIZE = 1024

running = True


# -----------------------------
# WHITE NOISE ÜRETİCİ
# -----------------------------
def audio_callback(outdata, frames, time_info, status):
    if not running:
        outdata[:] = np.zeros((frames, 1))
        return

    noise = np.random.uniform(-1, 1, frames).astype(np.float32)
    outdata[:] = (noise * VOLUME).reshape(-1, 1)


# -----------------------------
# AUDIO STREAM
# -----------------------------
stream = sd.OutputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    callback=audio_callback,
    blocksize=BLOCK_SIZE
)


# -----------------------------
# START / STOP
# -----------------------------
def start_audio():
    stream.start()


def stop_audio():
    stream.stop()


# -----------------------------
# TRAY ICON
# -----------------------------
def create_image():
    image = Image.new('RGB', (64, 64), (30, 30, 30))
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill=(0, 200, 0))
    return image


def on_toggle(icon, item):
    global running
    running = not running


def on_exit(icon, item):
    stop_audio()
    icon.stop()
    stream.close()


# -----------------------------
# TRAY MENU
# -----------------------------
menu = pystray.Menu(
    pystray.MenuItem("Enable / Disable", on_toggle),
    pystray.MenuItem("Exit", on_exit)
)


icon = pystray.Icon("BTNoSleep", create_image(), "BT No Sleep", menu)


# -----------------------------
# BACKGROUND START
# -----------------------------
def run():
    start_audio()
    icon.run()


if __name__ == "__main__":
    run()
