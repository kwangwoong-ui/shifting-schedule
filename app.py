import streamlit as st
import pandas as pd
from datetime import datetime

# 모바일 브라우저 최적화 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="centered")

# --- 데이터 초기화 및 상태 보존 ---
if 'staff_db' not in st.session_state:
    # 예시 인원 데이터 (경력순 정렬)
    names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "주간2", "기동", "조조", "의무"]
    st.session_state.staff_db = {name: {"last_booth": None, "rest_score": 0, "active": True} for name in names}

# --- 상단: 실시간 인원 현황 (모바일용 체크박스) ---
st.title("📱 실시간 근무 관리")
st.subheader("👥 인원 이탈/지각/조회 체크")

cols = st.columns(3) # 모바일 3열 배치
for i, name in enumerate(st.session_state.staff_db.keys()):
    with cols[i % 3]:
        # 체크박스로 인원 활성/비활성 결정
        is_active = st.checkbox(name, value=st.session_state.staff_db[name]["active"], key=f"active_{name}")
        st.session_state.staff_db[name]["active"] = is_active

st.divider()

# --- 중단: 부스 설정 및 교대수 ---
st.subheader("🏢 부스 운영 설정")
booth_input = st.text_input("운영할 부스 번호 (슬래시/로 구분)", "감독/자동/1/2/19/22")
active_booths = [b.strip() for b in booth_input.split('/')]

# --- 핵심 로직: 배치 계산 ---
# 1. 현재 투입 가능 인원 필터링
current_staff = [name for name, info in st.session_state.staff_db.items() if info["active"]]
n_staff = len(current_staff)
n_booth = len(active_booths)

# 2. 휴식자 선정 (형평성 기준: 누적 근무가 많은 사람부터 쉼)
sorted_staff = sorted(current_staff, key=lambda x: st.session_state.staff_db[x]['rest_score'], reverse=True)
rest_count = max(0, n_staff - n_booth)
resters = sorted_staff[:rest_count]
workers = sorted_staff[rest_count:]

# --- 하단: 실시간 배치 결과 및 관리자 조치 ---
st.subheader("📋 배치 가이드 (연속성 우선)")

assignment = {}
unassigned_workers = workers.copy()
remaining_booths = active_booths.copy()

# [연속성] 직전 부스 위치 유지 시도
for person in workers:
    last_pos = st.session_state.staff_db[person]["last_booth"]
    if last_pos in remaining_booths:
        assignment[last_pos] = person
        remaining_booths.remove(last_pos)
        unassigned_workers.remove(person)

# [빈자리 채우기] 경력순 배치
for booth in remaining_booths:
    if unassigned_workers:
        person = unassigned_workers.pop(0)
        assignment[booth] = person
        st.session_state.staff_db[person]["last_booth"] = booth # 위치 기록 업데이트

# 결과 출력 (모바일 가독성 중심)
for booth in active_booths:
    worker = assignment.get(booth, "⚠️ 공석 (관리자 확인)")
    
    with st.container():
        c1, c2 = st.columns([1, 2])
        c1.write(f"**부스 {booth}**")
        if "공석" in worker:
            c2.error(worker)
        else:
            c2.success(f"👤 {worker}")

st.divider()
st.write(f"☕ **현재 휴식 보장:** {', '.join(resters) if resters else '없음'}")

# --- 관리자 업데이트 버튼 ---
if st.button("🔄 다음 교대로 업데이트", use_container_width=True):
    for p in workers: st.session_state.staff_db[p]['rest_score'] += 1
    for p in resters: st.session_state.staff_db[p]['rest_score'] = 0
    st.rerun()
