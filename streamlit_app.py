import streamlit as st
from pathlib import Path
import json
import base64
import mimetypes

st.set_page_config(page_title="운광초등학교 생태지도", layout="wide")

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

# build photo map
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

plants_json_js = json.dumps(plants, ensure_ascii=False)
photo_map_js = json.dumps(photo_map, ensure_ascii=False)
map_data_url_js = json.dumps(map_data_url)

# HTML template
html_template = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
html,body{height:100%;margin:0;font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Noto Sans KR',sans-serif}
.container{display:flex;gap:12px;height:100vh;padding:12px;box-sizing:border-box;background:#f6f7f8}
.map-area{flex:1;position:relative;display:flex;align-items:flex-start;justify-content:center;overflow:hidden;background:#e9eef0;border-radius:6px;padding:8px 8px 20px 8px} /* 상단으로 올리도록 align-items:flex-start 및 하단 여유 */
.viewport{position:relative;touch-action:none;cursor:grab;display:inline-block}
.map-img{display:block;width:100%;height:auto;user-select:none;pointer-events:none}
.marker{position:absolute;transform:translate(-50%,-100%);width:18px;height:18px;border-radius:50%;background:rgba(34,139,34,0.95);border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.25);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:10px;cursor:pointer;pointer-events:auto}
.marker:after{content:'';position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);width:2px;height:6px;background:rgba(34,139,34,0.95)}
.sidebar{width:360px;min-width:260px;background:#fff;border-radius:6px;padding:12px;box-shadow:0 6px 18px rgba(0,0,0,0.08);overflow:auto}
.sidebar h2{margin:0 0 8px 0;font-size:18px}
.sidebar select{width:100%;padding:8px;margin-bottom:8px;border-radius:6px;border:1px solid #ddd;font-size:14px}
.sidebar img{width:100%;height:auto;border-radius:6px;margin-top:8px}
.controls{display:flex;gap:8px;margin-top:10px;align-items:center}
.btn{padding:8px;border-radius:6px;border:1px solid #ccc;background:#f8f8f8;cursor:pointer;font-size:13px}
.zoom-controls{display:flex;gap:6px;margin-left:auto}
.zoom-controls button{width:36px;height:36px;border-radius:6px;border:1px solid #ccc;background:#fff;cursor:pointer}
.hint{color:#666;font-size:13px}
@media(max-width:900px){.container{flex-direction:column}.sidebar{width:100%;min-width:auto}}
</style>
</head>
<body>
<div class="container">
  <div class="map-area" id="mapArea">
    <div id="viewport" class="viewport" style="transform-origin:0 0;transform:translate(0px,0px) scale(1);">
      <img id="mapImg" class="map-img" src={{MAPDATA}} alt="학교 지도"/>
    </div>
  </div>
  <aside class="sidebar" id="panel">
    <h2>식물 정보</h2>
    <select id="plantSelect"><option value="">-- 식물 선택 --</option></select>
    <div id="details"><p class="hint">마커를 클릭하거나 목록에서 선택하세요.</p></div>
    <div class="controls">
      <div class="zoom-controls"><button id="zoomOut">-</button><button id="zoomIn">+</button><button id="zoomReset">◯</button></div>
      <div style="flex:1"></div>
    </div>
    <div style="height:8px"></div>
    <div class="controls"><button id="backBtn" class="btn" disabled>돌아가기</button><button id="clearBtn" class="btn">닫기</button></div>
  </aside>
</div>

<script>
const plants = {{PLANTS}};
const photoMap = {{PHOTOMAP}};
const viewport = document.getElementById('viewport'), mapImg = document.getElementById('mapImg'), mapArea = document.getElementById('mapArea');
const details = document.getElementById('details'), sel = document.getElementById('plantSelect'), backBtn = document.getElementById('backBtn'), clearBtn = document.getElementById('clearBtn');
const zoomInBtn = document.getElementById('zoomIn'), zoomOutBtn = document.getElementById('zoomOut'), zoomResetBtn = document.getElementById('zoomReset');
let zoom = 1, tx = 0, ty = 0, isDragging = false, dragStart = null, history = [];

function esc(s){return String(s||'').replace(/[&<>"']/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m];});}

// clamp pan so image cannot be dragged completely out of view
function clampPan(){
  const area = mapArea.getBoundingClientRect();
  const imgW = mapImg.clientWidth * zoom;
  const imgH = mapImg.clientHeight * zoom;
  if(imgW <= area.width){
    tx = Math.round((area.width - imgW)/2);
  } else {
    const minTx = area.width - imgW;
    tx = Math.min(0, Math.max(minTx, tx));
  }
  if(imgH <= area.height){
    ty = Math.round((area.height - imgH)/2);
  } else {
    const minTy = area.height - imgH;
    ty = Math.min(0, Math.max(minTy, ty));
  }
}

function setTransform(){ clampPan(); viewport.style.transform = 'translate('+tx+'px,'+ty+'px) scale('+zoom+')'; }

function zoomTo(factor, cx=null, cy=null){
  const old = zoom;
  let newZoom = zoom * factor;
  newZoom = Math.max(0.5, Math.min(4, newZoom));
  const f = newZoom / old;
  zoom = newZoom;
  const area = mapArea.getBoundingClientRect();
  if(cx===null||cy===null){cx = area.width/2; cy = area.height/2;}
  const localX = cx - tx;
  const localY = cy - ty;
  tx = cx - localX * f;
  ty = cy - localY * f;
  clampPan(); setTransform();
}

zoomInBtn.addEventListener('click', ()=>{ const a = mapArea.getBoundingClientRect(); zoomTo(1.25,a.width/2,a.height/2); });
zoomOutBtn.addEventListener('click', ()=>{ const a = mapArea.getBoundingClientRect(); zoomTo(0.8,a.width/2,a.height/2); });
zoomResetBtn.addEventListener('click', ()=>{ zoom=1; tx=0; ty=0; setTransform(); });

function populateSelect(){
  sel.innerHTML = '<option value="">-- 식물 선택 --</option>';
  plants.forEach(p=>{ const opt = document.createElement('option'); opt.value = p.id; opt.textContent = p.name || p.id; sel.appendChild(opt); });
}

function createMarker(p){
  const m = document.createElement('button');
  m.className = 'marker';
  m.type = 'button';
  m.title = p.name;
  m.dataset.id = p.id;
  m.style.left = p.x + '%';
  m.style.top = p.y + '%';
  m.textContent = p.label || '●';
  m.addEventListener('click', e => { e.stopPropagation(); toggleShow(p); });
  viewport.appendChild(m);
}

function toggleShow(p){
  const cur = details.dataset.current || '';
  if(cur === p.id){
    // same marker clicked again -> hide
    clearDetails();
  } else {
    showPlant(p, true);
  }
}

mapImg.onload = function(){
  populateSelect();
  Array.from(viewport.querySelectorAll('.marker')).forEach(n=>n.remove());
  plants.forEach(p=>createMarker(p));
  if(viewport.firstChild !== mapImg) viewport.insertBefore(mapImg, viewport.firstChild);
  clampPan(); setTransform();
};
if(mapImg.complete) mapImg.onload();

function renderDetails(p){
  const pm = photoMap[p.id] || p.photo || '';
  const photoTag = (pm && pm.length>0) ? ('<img src="'+esc(pm)+'" alt="'+esc(p.name)+' 사진" onerror="this.style.display=\\'none\\'">') : '';
  return '<strong>'+esc(p.name)+'</strong><p>'+esc(p.description||'')+'</p>' + photoTag;
}
function updateBackState(){ backBtn.disabled = history.length === 0; }

function showPlant(p, pushHistory){
  const cur = details.dataset.current || '';
  if(cur && cur !== p.id && pushHistory) history.push(cur);
  details.innerHTML = renderDetails(p);
  details.dataset.current = p.id;
  sel.value = p.id;
  updateBackState();
  const marker = viewport.querySelector(".marker[data-id='"+p.id+"']");
  if(marker){
    const mr = marker.getBoundingClientRect();
    const area = mapArea.getBoundingClientRect();
    const centerX = mr.left + mr.width/2 - area.left;
    const centerY = mr.top + mr.height/2 - area.top;
    tx += area.width/2 - centerX;
    ty += area.height/2 - centerY;
    clampPan(); setTransform();
  }
}

function clearDetails(){ details.innerHTML = '<p class=\\'hint\\'>마커를 클릭하거나 목록에서 선택하세요.</p>'; delete details.dataset.current; sel.value = ''; updateBackState(); }
function goBack(){ if(history.length === 0) return; const id = history.pop(); const p = plants.find(x=>x.id===id); if(p) showPlant(p,false); updateBackState(); }

sel.addEventListener('change', function(){ const id = this.value; if(!id){ clearDetails(); return; } const p = plants.find(x=>x.id===id); if(p) showPlant(p,true); });
backBtn.addEventListener('click', function(e){ e.stopPropagation(); goBack(); });
clearBtn.addEventListener('click', function(e){ e.stopPropagation(); clearDetails(); });

// dragging (pan)
viewport.addEventListener('mousedown', function(e){ if(e.button!==0) return; isDragging=true; viewport.style.cursor='grabbing'; dragStart = {x:e.clientX, y:e.clientY, tx:tx, ty:ty}; e.preventDefault(); });
window.addEventListener('mousemove', function(e){ if(!isDragging || !dragStart) return; const dx = e.clientX - dragStart.x; const dy = e.clientY - dragStart.y; tx = dragStart.tx + dx; ty = dragStart.ty + dy; setTransform(); });
window.addEventListener('mouseup', function(e){ if(isDragging){ isDragging=false; viewport.style.cursor='grab'; dragStart=null; clampPan(); setTransform(); } });

// touch pan
viewport.addEventListener('touchstart', function(e){ if(e.touches.length===1){ const t=e.touches[0]; isDragging=true; dragStart={x:t.clientX,y:t.clientY,tx:tx,ty:ty}; } }, {passive:false});
viewport.addEventListener('touchmove', function(e){ if(!isDragging||!dragStart) return; const t=e.touches[0]; const dx=t.clientX-dragStart.x; const dy=t.clientY-dragStart.y; tx=dragStart.tx+dx; ty=dragStart.ty+dy; setTransform(); e.preventDefault(); }, {passive:false});
viewport.addEventListener('touchend', function(e){ isDragging=false; dragStart=null; clampPan(); setTransform(); });

// wheel zoom with modifier
mapArea.addEventListener('wheel', function(e){ if(e.ctrlKey || e.metaKey || e.shiftKey){ e.preventDefault(); const rect = mapArea.getBoundingClientRect(); zoomTo(e.deltaY<0?1.15:0.85, e.clientX-rect.left, e.clientY-rect.top); } }, {passive:false});

// clicking empty map clears details
mapArea.addEventListener('click', function(){ clearDetails(); });
</script>
</body>
</html>
"""

html = html_template.replace("{{PLANTS}}", plants_json_js).replace("{{PHOTOMAP}}", photo_map_js).replace("{{MAPDATA}}", map_data_url_js)

st.components.v1.html(html, height=820, scrolling=True)

# Run the app
if __name__ == "__main__":
    import sys
    sys.exit("Please run this script with the command: pip3 install --user -r requirements.txt || pip3 install --user streamlit\nstreamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0\n\"$BROWSER\" http://localhost:8501")
