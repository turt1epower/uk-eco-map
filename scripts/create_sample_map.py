#!/usr/bin/env python3
# 샘플 지도 이미지(map/school-map.jpg)를 생성합니다 (테스트용).
# Pillow가 없으면 먼저 설치하세요: pip3 install --user pillow
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUT = Path("map")
OUT.mkdir(exist_ok=True)
outf = OUT / "school-map.jpg"

w, h = 1400, 900
im = Image.new("RGB", (w, h), (245, 250, 240))
draw = ImageDraw.Draw(im)
draw.rectangle([(40,40),(w-40,h-40)], outline=(200,200,200), width=3)
draw.text((60,60), "학교 생태지도 (샘플)", fill=(20,80,20))
# 간단한 나무/건물 아이콘(원/사각)
draw.ellipse([(200,200),(260,260)], fill=(34,139,34))
draw.rectangle([(400,300),(520,420)], fill=(180,120,80))
im.save(outf, "JPEG", quality=85)
print("샘플 지도 생성됨:", outf)