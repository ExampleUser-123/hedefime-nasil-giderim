# -*- coding: utf-8 -*-
"""Ikon + splash kaynaklarini Android tum yogunluklarina isler."""
import os
from PIL import Image, ImageDraw, ImageOps

RES = r"C:\Users\Ömer Faruk\Desktop\HEDEFİME NASIL GİDİCEM\frontend\android\app\src\main\res"
BRAND = r"C:\Users\Ömer Faruk\Desktop\HEDEFİME NASIL GİDİCEM\frontend\resources\branding"
ICON_SRC = os.path.join(BRAND, "icon.png")
SPLASH_SRC = os.path.join(BRAND, "splash.png")

os.makedirs(BRAND, exist_ok=True)

icon = Image.open(ICON_SRC).convert("RGBA")
splash_src = Image.open(SPLASH_SRC).convert("RGBA")

# Arka plan rengini ikonun sol ust kosesinden ornekle
bg_rgb = icon.getpixel((30, 30))[:3]
bg_hex = "#%02X%02X%02X" % bg_rgb
print("adaptive background:", bg_hex)

# values/ic_launcher_background.xml guncelle
val_dir = os.path.join(RES, "values")
os.makedirs(val_dir, exist_ok=True)
with open(os.path.join(val_dir, "ic_launcher_background.xml"), "w") as f:
    f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
            '    <color name="ic_launcher_background">%s</color>\n</resources>\n' % bg_hex)

# --- 1) launcher ikonlari ---
DENSITIES = {"ldpi": 36, "mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FG_DENSITIES = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}

def rounded(img, size):
    im = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], radius=int(size * 4 * 0.18), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out

def circular(img, size):
    im = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out

for dpi, size in DENSITIES.items():
    folder = os.path.join(RES, "mipmap-" + dpi)
    os.makedirs(folder, exist_ok=True)
    rounded(icon, size).save(os.path.join(folder, "ic_launcher.png"))
    circular(icon, size).save(os.path.join(folder, "ic_launcher_round.png"))

# adaptive foreground: icerik guvenli bolgeye (%60) yerlestirilir
for dpi, size in FG_DENSITIES.items():
    folder = os.path.join(RES, "mipmap-" + dpi)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * 0.60)
    fg = icon.resize((inner, inner), Image.LANCZOS)
    canvas.paste(fg, ((size - inner) // 2, (size - inner) // 2), fg)
    canvas.save(os.path.join(folder, "ic_launcher_foreground.png"))

# --- 2) splash ekranlari: mevcut dosya boyutlarini koru, logo ortala ---
count = 0
for name in os.listdir(RES):
    if not name.startswith("drawable"):
        continue
    folder = os.path.join(RES, name)
    splash_path = os.path.join(folder, "splash.png")
    if not os.path.isfile(splash_path):
        continue
    w, h = Image.open(splash_path).size
    canvas = Image.new("RGBA", (w, h), bg_rgb + (255,))
    logo_w = int(min(w, h) * 0.72)
    logo_h = int(logo_w * splash_src.height / splash_src.width)
    if logo_h > h * 0.9:
        logo_h = int(h * 0.9)
        logo_w = int(logo_h * splash_src.width / splash_src.height)
    logo = splash_src.resize((logo_w, logo_h), Image.LANCZOS)
    canvas.paste(logo, ((w - logo_w) // 2, (h - logo_h) // 2), logo)
    canvas.convert("RGB").save(splash_path)
    count += 1
    print("splash:", name, w, "x", h)

print("bitti:", count, "splash |", len(DENSITIES), "ikon boyutu |", len(FG_DENSITIES), "foreground")
