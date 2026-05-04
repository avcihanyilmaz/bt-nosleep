import numpy as np
import sounddevice as sd
import pystray
from PIL import Image, ImageDraw
import sys

# -----------------------------
# AYARLAR
# -----------------------------
SAMPLE_RATE = 44100
VOLUME = 0.02   
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
try:
    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        callback=audio_callback,
        blocksize=BLOCK_SIZE
    )
except Exception as e:
    print(f"Ses aygıtı başlatılamadı: {e}")
    sys.exit(1)

# -----------------------------
# TRAY ICON OLUŞTURMA
# -----------------------------
def create_image(is_running):
    """Duruma göre yeşil veya kırmızı ikon oluşturur."""
    image = Image.new('RGB', (64, 64), (30, 30, 30))
    dc = ImageDraw.Draw(image)
    # Renk seçimi: Çalışıyorsa Yeşil (0, 200, 0), Durmuşsa Kırmızı (200, 0, 0)
    color = (0, 200, 0) if is_running else (200, 0, 0)
    dc.ellipse((16, 16, 48, 48), fill=color)
    return image

def on_toggle(icon, item):
    global running
    running = not running
    # İkonu ve menüyü dinamik olarak güncelle
    icon.icon = create_image(running)
    icon.title = f"BT No Sleep - {'Aktif' if running else 'Pasif'}"

def on_exit(icon, item):
    stream.stop()
    stream.close()
    icon.stop()

# -----------------------------
# TRAY MENU & ICON
# -----------------------------
menu = pystray.Menu(
    pystray.MenuItem(lambda text: "Duraklat" if running else "Başlat", on_toggle),
    pystray.MenuItem("Çıkış", on_exit)
)

icon = pystray.Icon("BTNoSleep", create_image(running), "BT No Sleep", menu)

# -----------------------------
# ÇALIŞTIR
# -----------------------------
if __name__ == "__main__":
    stream.start()
    icon.run()
