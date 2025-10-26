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

# build HTML: two-column layout (map left, info sidebar right)
css = (
    "html,body{height:100%;margin:0;font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Noto Sans KR',sans-serif}"
    ".container{display:flex;gap:12px;height:100vh;padding:12px;box-sizing:border-box;background:#f6f7f8}"
    ".map-area{flex:1;position:relative;display:flex;align-items:center;justify-content:center;overflow:auto;background:#e9eef0;border-radius:6px;padding:8px}"
    ".map-img{max-width:100%;height:auto;display:block;position:relative;cursor:crosshair}"
    ".marker{position:absolute;transform:translate(-50%,-100%);width:18px;height:18px;border-radius:50%;background:rgba(34,139,34,0.95);border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.25);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:10px;cursor:pointer}"
    ".marker:after{content:'';position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);width:2px;height:6px;background:rgba(34,139,34,0.95)}"
    ".sidebar{width:360px;min-width:260px;background:#fff;border-radius:6px;padding:12px;box-shadow:0 6px 18px rgba(0,0,0,0.08);overflow:auto}"
    ".sidebar h2{margin:0 0 8px 0;font-size:18px}"
    ".sidebar select{width:100%;padding:8px;margin-bottom:8px;border-radius:6px;border:1px solid #ddd;font-size:14px}"
    ".sidebar img{width:100%;height:auto;border-radius:6px;margin-top:8px}"
    ".controls{display:flex;gap:8px;margin-top:10px}"
    ".btn{flex:1;padding:8px;border-radius:6px;border:1px solid #ccc;background:#f8f8f8;cursor:pointer;font-size:13px}"
    ".btn:disabled{opacity:0.5;cursor:not-allowed}"
    ".hint{color:#666;font-size:13px}"
    "@media(max-width:900px){.container{flex-direction:column}.sidebar{width:100%;min-width:auto}}"
)

html = (
    "<!doctype html><html lang='ko'><head><meta charset='utf-8'/>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
    "<style>" + css + "</style></head><body>"
    "<div class='container'>"
    "<div class='map-area' id='mapWrap'>"
    "<img id='mapImg' class='map-img' src=" + map_data_url_js + " alt='학교 지도'/>"
    "</div>"
    "<aside class='sidebar' id='panel'>"
    "<h2>식물 정보</h2>"
    "<select id='plantSelect'><option value=''>-- 식물 선택 --</option></select>"
    "<div id='details'><p class='hint'>마커를 클릭하거나 목록에서 선택하세요.</p></div>"
    "<div class='controls'><button id='backBtn' class='btn' disabled>돌아가기</button><button id='clearBtn' class='btn'>닫기</button></div>"
    "</aside>"
    "</div>"
    "<script>"
    "const plants = " + plants_json_js + "; const photoMap = " + photo_map_js + ";"
    "const mapWrap = document.getElementById('mapWrap'), mapImg = document.getElementById('mapImg'), details = document.getElementById('details'), sel = document.getElementById('plantSelect'), backBtn = document.getElementById('backBtn'), clearBtn = document.getElementById('clearBtn');"
    "let history = [];"
    "function esc(s){return String(s||'').replace(/[&<>\"']/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}[m];});}"
    "function createMarker(p){const m = document.createElement('button');m.className='marker';m.type='button';m.title=p.name; m.style.left = p.x + '%'; m.style.top = p.y + '%'; m.dataset.id = p.id; m.textContent = p.label || '●'; m.addEventListener('click', function(ev){ ev.stopPropagation(); showPlant(p, true); }); mapWrap.appendChild(m); }"
    "function renderDetails(p){ const pm = photoMap[p.id] || p.photo || ''; const photoTag = (pm && pm.length>0) ? ('<img src=\"'+esc(pm)+'\" alt=\"'+esc(p.name)+' 사진\" onerror=\"this.style.display=\\\\\\'none\\\\\\'\">') : ''; return '<strong>'+esc(p.name)+'</strong><p>'+esc(p.description||'')+'</p>' + photoTag; }"
    "function updateBackState(){ backBtn.disabled = history.length === 0; }"
    "function showPlant(p, pushHistory){ const cur = details.dataset.current || ''; if(cur && cur !== p.id && pushHistory){ history.push(cur); } details.innerHTML = renderDetails(p); details.dataset.current = p.id; sel.value = p.id; updateBackState(); }"
    "function clearDetails(){ details.innerHTML = '<p class=\\'hint\\'>마커를 클릭하거나 목록에서 선택하세요.</p>'; delete details.dataset.current; sel.value = ''; updateBackState(); }"
    "function goBack(){ if(history.length === 0) return; const id = history.pop(); const p = plants.find(x=>x.id===id); if(p) showPlant(p, false); updateBackState(); }"
    "if(mapImg.complete){ plants.forEach(createMarker); } else { mapImg.onload = () => plants.forEach(createMarker); mapImg.onerror = () => plants.forEach(createMarker); }"
    "plants.forEach(p=>{ const opt = document.createElement('option'); opt.value = p.id; opt.textContent = p.name; sel.appendChild(opt); });"
    "sel.addEventListener('change', function(){ const id = this.value; if(!id){ clearDetails(); return; } const p = plants.find(x=>x.id===id); if(p) showPlant(p, true); });"
    "backBtn.addEventListener('click', function(e){ e.stopPropagation(); goBack(); });"
    "clearBtn.addEventListener('click', function(e){ e.stopPropagation(); clearDetails(); });"
    "mapWrap.addEventListener('click', ()=>{ clearDetails(); });"
    "</script></body></html>"
)

st.components.v1.html(html, height=820, scrolling=True)

# Run the app
if __name__ == "__main__":
    import sys
    sys.exit("Please run this script with the command: pip3 install --user -r requirements.txt || pip3 install --user streamlit\nstreamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0\n\"$BROWSER\" http://localhost:8501")
