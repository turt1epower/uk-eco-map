import streamlit as st

st.title("학교 생태지도 — 배포 테스트")
st.write("이 메시지가 보이면 Streamlit 실행은 정상입니다.")
try:
    st.image("map/school-map.jpg", caption="map/school-map.jpg", use_column_width=True)
except Exception as e:
    st.write("map 이미지 로드 실패:", e)
