#!/usr/bin/env python3
# 이미지 열기/검사하고 재저장(재인코딩)으로 복구 시도
import sys
import pathlib

try:
    from PIL import Image, UnidentifiedImageError
except Exception:
    print("Pillow가 설치되어 있지 않습니다. 설치: pip3 install --user pillow")
    sys.exit(2)

def usage():
    print("사용법: check_and_fix_image.py <map/파일명>")
    sys.exit(2)

def main():
    if len(sys.argv) != 2:
        usage()
    p = pathlib.Path(sys.argv[1])
    if not p.exists():
        print("파일이 없습니다:", p)
        sys.exit(1)
    try:
        # 간단 검사
        with Image.open(p) as im:
            im.verify()
        # 재열기 후 재저장 (원본 포맷 유지 시도)
        with Image.open(p) as im:
            fmt = im.format or "JPEG"
            out = p.with_name(p.name + ".fixed")
            im = im.convert("RGB") if fmt.upper() in ("JPEG", "JPG") else im.convert("RGBA" if fmt.upper()=="PNG" else "RGB")
            im.save(out, format=fmt)
        print("이미지 열림 및 재저장 완료:", out)
        sys.exit(0)
    except UnidentifiedImageError:
        print("이미지로 인식되지 않습니다(손상 가능):", p)
        sys.exit(1)
    except Exception as e:
        print("오류 발생:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()