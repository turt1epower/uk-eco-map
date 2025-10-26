#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRS = [ROOT / "map", ROOT / "photo"]

# 최대 너비/높이와 JPEG 품질 설정
MAX_DIM = 1600
JPEG_QUALITY = 80

def compress_image(p: Path):
    try:
        with Image.open(p) as im:
            orig_size = p.stat().st_size
            w,h = im.size
            scale = min(1.0, MAX_DIM / max(w,h))
            if scale < 1:
                new_size = (int(w*scale), int(h*scale))
                im = im.resize(new_size, Image.LANCZOS)
            # PNG은 RGBA 처리, JPG로 변환 가능하지만 확장자 유지
            if p.suffix.lower() in [".jpg", ".jpeg"]:
                im = im.convert("RGB")
                im.save(p, "JPEG", quality=JPEG_QUALITY, optimize=True)
            elif p.suffix.lower() == ".png":
                im = im.convert("RGBA")
                im.save(p, "PNG", optimize=True)
            else:
                return
            new_size = p.stat().st_size
            print(f"{p}: {orig_size//1024}KB -> {new_size//1024}KB")
    except Exception as e:
        print("실패:", p, e)

def main():
    for d in TARGET_DIRS:
        if not d.exists(): continue
        for p in d.rglob("*"):
            if p.suffix.lower() in [".jpg",".jpeg",".png"]:
                compress_image(p)

if __name__ == "__main__":
    main()