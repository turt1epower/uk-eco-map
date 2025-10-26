import streamlit as st
from pathlib import Path
import json
import base64

st.set_page_config(page_title="학교 생태지도", layout="wide")

ROOT = Path(__file__).resolve().parents[0]
DATA_FILE = ROOT / "data" / "plants.json"
MAP_DIR = ROOT / "map"

# choose map image: pick largest image file in map/ if any, else fallback to school-map.jpg
def choose_map_file():
    exts = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    if MAP_DIR.exists():
        imgs = [p for p in MAP_DIR.iterdir() if p.suffix.lower() in exts and p.is_file()]
        if imgs:
            # pick largest (prefer real upload over tiny sample)
            imgs_sorted = sorted(imgs, key=lambda p: p.stat().st_size, reverse=True)
            return imgs_sorted[0]
    # fallback
    return MAP_DIR / "school-map.jpg"

MAP_FILE = choose_map_file()

# load plants
try:
    plants = json.loads(DATA_FILE.read_text(encoding="utf-8"))
except Exception:
    plants = []

# prepare map image data url if available
map_data_url = None
if MAP_FILE.exists():
    try:
        b = MAP_FILE.read_bytes()
        mime = "image/jpeg"
        if MAP_FILE.suffix.lower() == ".png":
            mime = "image/png"
        elif MAP_FILE.suffix.lower() == ".svg":
            mime = "image/svg+xml"
        map_data_url = f"data:{mime};base64," + base64.b64encode(b).decode("ascii")
    except Exception:
        map_data_url = None

# 안전하게 JS에 주입할 JSON 문자열 생성
plants_json_js = json.dumps(plants, ensure_ascii=False)
map_data_url_js = json.dumps(map_data_url)  # "null" or quoted string

html = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>학교 생태지도 (embedded)</title>
<style>
  body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans KR", "Apple SD Gothic Neo", sans-serif; margin:0; }
  .app { display:flex; height:100vh; }
  .map-wrap { position:relative; flex:1; overflow:auto; background:#f0f0f0; display:flex; align-items:center; justify-content:center; padding:12px; }
  .map-img { max-width:100%; height:auto; display:block; position:relative; cursor:crosshair; }
  .marker {
    position:absolute; transform:translate(-50%,-100%);
    width:28px; height:28px; border-radius:50%;
    background:rgba(34,139,34,0.95); border:2px solid #fff;
    box-shadow:0 2px 6px rgba(0,0,0,0.3);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-weight:700; cursor:pointer;
  }
  .marker:after { content:""; position:absolute; left:50%; bottom:-8px; transform:translateX(-50%); width:2px; height:8px; background:rgba(34,139,34,0.95); }
  .panel { width:320px; max-width:40%; background:#fff; border-left:1px solid #e0e0e0; padding:16px; box-sizing:border-box; overflow:auto; }
  .panel h2 { margin:0 0 8px 0; font-size:18px; }
  .panel img { width:100%; height:auto; border-radius:6px; margin-bottom:8px; }
  .hint { color:#666; font-size:14px; }
  @media(max-width:700px){ .panel{ position:fixed; right:0; top:0; bottom:0; z-index:30; width:90%; } }
</style>
</head>
<body>
<div style="display:flex; height:100vh;">
  <div class="map-wrap" id="mapWrap">
    <img id="mapImg" class="map-img" src=""" + map_data_url_js + """ alt="학교 지도" />
  </div>
  <aside class="panel" id="panel">
    <h2>식물 정보</h2>
    <div id="details"><p class="hint">지도에서 식물 마커를 클릭하세요.</p></div>
  </aside>
</div>

<script>
(function(){
  const plants = """ + plants_json_js + """;
  const mapWrap = document.getElementById('mapWrap');
  const mapImg = document.getElementById('mapImg');
  const details = document.getElementById('details');

  function escapeHtml(s){ return String(s||'').replace(/[&<>"']/g, function(m){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]; }); }

  function createMarker(p){
    const m = document.createElement('button');
    m.className = 'marker';
    m.type = 'button';
    m.title = p.name;
    m.style.left = p.x + '%';
    m.style.top = p.y + '%';
    m.dataset.id = p.id;
    m.textContent = p.label || '●';
    m.addEventListener('click', (ev)=>{
      ev.stopPropagation();
      showPlant(p);
    });
    mapWrap.appendChild(m);
  }

  function showPlant(p){
    // 사진이 로컬 경로로 깨지면 안내 문구만 표시
    const photoTag = (p.photo && p.photo.length>0) ? ('<img src="'+escapeHtml(p.photo)+'" alt="'+escapeHtml(p.name)+' 사진" style="max-width:100%;margin-bottom:8px" onerror="this.style.display=\\'none\\';document.getElementById(\\'photoWarn\\').style.display=\\'block\\';"/>') : '';
    details.innerHTML = '<h3>'+escapeHtml(p.name)+'</h3>'
      + photoTag
      + '<div id="photoWarn" style="display:none;color:#c33;font-size:13px;margin-bottom:6px;">사진을 불러오지 못했습니다. (사진 파일이 누락되었거나 경로가 잘못되었습니다)</div>'
      + '<p>'+escapeHtml(p.description || '설명이 없습니다.')+'</p>';
  }

  if (mapImg.complete) {
    plants.forEach(createMarker);
  } else {
    mapImg.onload = ()=> plants.forEach(createMarker);
    mapImg.onerror = ()=> plants.forEach(createMarker);
  }

  mapWrap.addEventListener('click', ()=> {
    details.innerHTML = '<p class="hint">지도에서 식물 마커를 클릭하세요.</p>';
  });

})();
</script>
</body>
</html>
"""
# render in Streamlit
st.components.v1.html(html, height=800, scrolling=True)
