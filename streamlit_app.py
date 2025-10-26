import streamlit as st
from pathlib import Path
import json
import requests
import mimetypes

st.set_page_config(page_title="학교 생태지도", layout="wide")

ROOT = Path(__file__).resolve().parents[0]
DATA_FILE = ROOT / "data" / "plants.json"
MAP_DIR = ROOT / "map"

def choose_map_file():
    exts = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    if MAP_DIR.exists():
        imgs = [p for p in MAP_DIR.iterdir() if p.suffix.lower() in exts and p.is_file()]
        if imgs:
            return sorted(imgs, key=lambda p: p.stat().st_size, reverse=True)[0]
    return MAP_DIR / "school-map.jpg"

MAP_FILE = choose_map_file()

# load plants
try:
    plants = json.loads(DATA_FILE.read_text(encoding="utf-8"))
except Exception:
    plants = []

st.title("학교 생태지도")

# helper: resolve photo path and return info
def resolve_photo_paths(photo_field):
    tried = []
    if not photo_field:
        return None, tried, "empty"
    if photo_field.startswith("http://") or photo_field.startswith("https://") or photo_field.startswith("data:"):
        return photo_field, tried, "url_or_data"
    p1 = ROOT / photo_field
    tried.append(str(p1))
    if p1.exists():
        return p1, tried, "file"
    p2 = ROOT / "photo" / Path(photo_field).name
    tried.append(str(p2))
    if p2.exists():
        return p2, tried, "file"
    p3 = ROOT / "static_photos" / Path(photo_field).name
    tried.append(str(p3))
    if p3.exists():
        return p3, tried, "file"
    return None, tried, "not_found"

# layout
col_map, col_panel = st.columns([3,1])

with col_map:
    if MAP_FILE.exists():
        try:
            st.image(str(MAP_FILE), use_container_width=True)
        except Exception as e:
            st.error("지도 이미지 표시 실패: " + str(e))
    else:
        st.warning("map 폴더에 지도 이미지가 없습니다.")

with col_panel:
    st.header("식물 목록")
    names = [f"{p.get('name','(이름없음)')} ({p.get('id')})" for p in plants]
    if names:
        idx = st.selectbox("식물 선택", list(range(len(names))), format_func=lambda i: names[i])
        p = plants[idx]
        st.subheader(p.get("name",""))
        photo_field = p.get("photo","") or ""
        resolved, tried, kind = resolve_photo_paths(photo_field)

        st.markdown("**디버그 정보**")
        st.text(f"photo field: {photo_field}")
        st.text(f"resolved type: {kind}")
        st.text("tried paths:")
        for t in tried:
            st.text("  " + t)

        img_displayed = False
        if kind == "url_or_data":
            try:
                if photo_field.startswith("http"):
                    r = requests.get(photo_field, timeout=5)
                    if r.status_code == 200 and len(r.content) > 0:
                        st.image(r.content, use_container_width=True)
                        img_displayed = True
                    else:
                        st.info(f"원격 이미지 요청 실패: HTTP {r.status_code}")
                else:
                    header, b64 = photo_field.split(",",1)
                    import base64
                    data = base64.b64decode(b64)
                    st.image(data, use_container_width=True)
                    img_displayed = True
            except Exception as e:
                st.info("원격/data 이미지 로드 실패: " + str(e))
        elif kind == "file" and isinstance(resolved, Path):
            try:
                size = resolved.stat().st_size
                st.text(f"파일 존재: {resolved} ({size//1024} KB)")
                b = resolved.read_bytes()
                st.image(b, use_container_width=True)
                img_displayed = True
            except Exception as e:
                st.info("로컬 파일 읽기 실패: " + str(e))
        else:
            st.info("사진 파일이 누락되었거나 경로가 잘못되었습니다.")

        st.write(p.get("description","설명이 없습니다."))

        if not img_displayed:
            st.markdown("**다음 확인사항**")
            st.markdown("- repo에 사진이 커밋되어 있는지: `git ls-files | grep -E \"photo|static_photos\"`")
            st.markdown("- 파일명 대소문자 일치 여부(리눅스는 구분)")
            st.markdown("- 필요하면 `scripts/fix_photos.py`로 재인코딩 후 `static_photos/`에 넣기")
            st.markdown("- 외부 URL을 사용하려면 plants.json의 photo에 절대 URL 넣기")
    else:
        st.info("등록된 식물이 없습니다.")

# 서버의 폴더 내용 간단 노출 (디버그)
st.markdown("---")
st.markdown("**서버에 존재하는 관련 폴더(최대 몇 항목)**")
def list_some(p):
    if not p.exists():
        return f"{p} (없음)"
    try:
        items = list(p.iterdir())[:20]
        return "\n".join([f"{it.name}  ({it.stat().st_size//1024} KB)" for it in items]) or "(비어있음)"
    except Exception as e:
        return f"읽기 실패: {e}"

st.text("map/:")
st.text(list_some(MAP_DIR))
st.text("photo/:")
st.text(list_some(ROOT / "photo"))
st.text("static_photos/:")
st.text(list_some(ROOT / "static_photos"))
