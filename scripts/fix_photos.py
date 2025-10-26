#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "plants.json"
OUT_DIR = ROOT / "static_photos"
OUT_DIR.mkdir(exist_ok=True)

def safe_open_and_save(src: Path, dst: Path):
    try:
        with Image.open(src) as im:
            # convert to RGB and resize large images
            max_dim = 1600
            w,h = im.size
            if max(w,h) > max_dim:
                ratio = max_dim / max(w,h)
                im = im.resize((int(w*ratio), int(h*ratio)), Image.LANCZOS)
            im = im.convert("RGB")
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "JPEG", quality=85, optimize=True)
            return True
    except UnidentifiedImageError:
        return False
    except Exception:
        return False

def main():
    if not DATA_FILE.exists():
        print("plants.json 없음:", DATA_FILE)
        return
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    changed = False
    for p in data:
        photo = p.get("photo") or ""
        if not photo:
            continue
        src = ROOT / photo
        if not src.exists():
            # try relative from repo root (in case photo paths are without folder)
            src = ROOT / "photo" / Path(photo).name
        if src.exists():
            dst = OUT_DIR / f"{p.get('id','plant')}.jpg"
            ok = safe_open_and_save(src, dst)
            if ok:
                new_path = str(Path("static_photos") / dst.name)
                if p.get("photo") != new_path:
                    p["photo"] = new_path
                    changed = True
                    print("재저장 및 경로 갱신:", src, "->", new_path)
            else:
                print("이미지 열기 실패(손상 가능):", src)
        else:
            print("파일 없음:", src)
    if changed:
        bak = DATA_FILE.with_suffix(".bak")
        shutil.copy2(DATA_FILE, bak)
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("plants.json 업데이트 및 백업 생성:", bak)
    else:
        print("변경 없음.")

if __name__ == "__main__":
    main()