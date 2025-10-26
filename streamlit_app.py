import streamlit as st
from pathlib import Path
import json
import base64
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

# load plants json
try:
    plants = json.loads(DATA_FILE.read_text(encoding="utf-8"))
except Exception:
    plants = []

# build photo_map: id -> data URI or absolute URL
photo_map = {}
for p in plants:
    pid = p.get("id")
    photo = (p.get("photo") or "").strip()
    if not pid or not photo:
        continue
    if photo.startswith(("http://", "https://", "data:")):
        photo_map[pid] = photo
        continue
    src = ROOT / photo
    if not src.exists():
        alt = ROOT / "photo" / Path(photo).name
        if alt.exists():
            src = alt
    if not src.exists():
        alt2 = ROOT / "static_photos" / Path(photo).name
        if alt2.exists():
            src = alt2
    if src.exists():
        try:
            b = src.read_bytes()
            mime, _ = mimetypes.guess_type(str(src))
            if not mime:
                mime = "image/jpeg"
            photo_map[pid] = "data:{};base64,".format(mime) + base64.b64encode(b).decode("ascii")
        except Exception:
            pass

# prepare map data URI
map_data_url = None
if MAP_FILE.exists():
    try:
        b = MAP_FILE.read_bytes()
        mime, _ = mimetypes.guess_type(str(MAP_FILE))
        if not mime:
            mime = "image/jpeg"
        map_data_url = "data:{};base64,".format(mime) + base64.b64encode(b).decode("ascii")
    except Exception:
        map_data_url = None

# safe JSON strings
plants_json_js = json.dumps(plants, ensure_ascii=False)
photo_map_js = json.dumps(photo_map, ensure_ascii=False)
map_data_url_js = json.dumps(map_data_url)

# build HTML: info panel top, smaller markers, and select box
html = (
    "<!doctype html><html lang='ko'><head><meta charset='utf-8'/>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
    "<style>"
    "body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;margin:0}"
    ".map-wrap{position:relative;flex:1;overflow:auto;background:#f0f0f0;display:flex;align-items:center;justify-content:center;height:100vh}"
    ".map-img{max-width:100%;height:auto;display:block;position:relative;cursor:crosshair}"
    ".marker{position:absolute;transform:translate(-50%,-100%);width:20px;height:20px;border-radius:50%;background:rgba(34,139,34,0.95);border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.25);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:11px;cursor:pointer}"
    ".marker:after{content:'';position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);width:2px;height:6px;background:rgba(34,139,34,0.95)}"
    ".panel{position:absolute;top:12px;left:50%;transform:translateX(-50%);width:340px;background:rgba(255,255,255,0.98);padding:10px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.12);z-index:40}"
    ".panel h2{margin:0 0 8px 0;font-size:16px}"
    ".panel select{width:100%;padding:6px;margin-bottom:8px;border-radius:6px;border:1px solid #ddd;font-size:13px}"
    ".panel img{width:100%;height:auto;border-radius:6px;margin-top:8px}"
    ".hint{color:#666;font-size:13px}"
    "@media(max-width:700px){.panel{left:8px;transform:none;width:calc(100% - 16px)}}"
    "</style></head><body>"
    "<div class='map-wrap' id='mapWrap'>"
    "<img id='mapImg' class='map-img' src=" + map_data_url_js + " alt='학교 지도'/>"
    "<aside class='panel' id='panel'>"
    "<h2>식물 정보</h2>"
    "<select id='plantSelect'><option value=''>-- 식물 선택 --</option></select>"
    "<div id='details'><p class='hint'>마커를 클릭하거나 목록에서 선택하세요.</p></div>"
    "</aside>"
    "</div>"
    "<script>"
    "const plants = " + plants_json_js + "; const photoMap = " + photo_map_js + ";"
    "const mapWrap = document.getElementById('mapWrap'), mapImg = document.getElementById('mapImg'), details = document.getElementById('details'), sel = document.getElementById('plantSelect');"
    "function esc(s){return String(s||'').replace(/[&<>\"']/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[m];});}"
    "function createMarker(p){const m = document.createElement('button');m.className='marker';m.type='button';m.title=p.name; m.style.left = p.x + '%'; m.style.top = p.y + '%'; m.dataset.id = p.id; m.textContent = p.label || '●'; m.addEventListener('click', function(ev){ ev.stopPropagation(); toggleShow(p); }); mapWrap.appendChild(m); }"
    "function renderDetails(p){ const pm = photoMap[p.id] || p.photo || ''; const photoTag = (pm && pm.length>0) ? ('<img src=\"'+esc(pm)+'\" alt=\"'+esc(p.name)+' 사진\" onerror=\"this.style.display=\\\\\\'none\\\\\\'\">') : ''; return '<strong>'+esc(p.name)+'</strong><p>'+esc(p.description||'')+'</p>' + photoTag; }"
    "function clearDetails(){ details.innerHTML = '<p class=\\'hint\\'>마커를 클릭하거나 목록에서 선택하세요.</p>'; delete details.dataset.current; sel.value = ''; }"
    "function toggleShow(p){ if(details.dataset.current === p.id){ clearDetails(); } else { details.innerHTML = renderDetails(p); details.dataset.current = p.id; sel.value = p.id; } }"
    "if(mapImg.complete){ plants.forEach(createMarker); } else { mapImg.onload = () => plants.forEach(createMarker); mapImg.onerror = () => plants.forEach(createMarker); }"
    "plants.forEach(p=>{ const opt = document.createElement('option'); opt.value = p.id; opt.textContent = p.name; sel.appendChild(opt); });"
    "sel.addEventListener('change', function(){ const id = this.value; if(!id){ clearDetails(); return; } const p = plants.find(x=>x.id===id); if(p) toggleShow(p); });"
    "mapWrap.addEventListener('click', ()=>{ clearDetails(); });"
    "</script></body></html>"
)

st.components.v1.html(html, height=820, scrolling=True)

# Run the app
if __name__ == "__main__":
    import sys
    sys.exit("Please run this script with the command: pip3 install --user -r requirements.txt || pip3 install --user streamlit\nstreamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0\n\"$BROWSER\" http://localhost:8501")
