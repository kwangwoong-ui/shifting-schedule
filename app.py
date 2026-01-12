import streamlit as st
import pandas as pd

# 모바일 최적화 및 페이지 설정
st.set_page_config(page_title="자동 교대 시스템", layout="centered")

# --- 1. 글로벌 상태 관리 (핵심 로직용) ---
if 'staff_db' not in st.session_state:
    # 초기 직원 리스트 (사용자 취향에 맞게 수정 가능)
    initial_names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "주간2", "기동"]
    # rest_score: 쉰 지 얼마나 됐는지 (높을수록 근무 중, 0이면 방금 쉼)
    st.session_state.staff_db = {name: {"last_pos": None, "rest_score": i} for i, name in enumerate(initial_names)}
if 'booth_list' not in st.session_state:
    st.session_state.booth_list = ["감독/자동", "1번", "2번", "19/22번"]

# --- 2. 사이드바: 실시간 인원/부스 관리 ---
with st.sidebar:
    st.header("⚙️ 실시간 현장 설정")
    
    # 인원 추가/삭제 (지각, 조퇴 반영)
    st.subheader("👥 인원 관리")
    all_names = list(st.session_state.staff_db.keys())
    active_staff = st.multiselect("현재 투입 가능 인원", all_names, default=all_names)
    
    new_name = st.text_input("신규 인원 추가")
    if st.button("인원 추가") and new_name:
        st.session_state.staff_db[new_name] = {"last_pos": None, "rest_score": 0}
        st.rerun()

    st.divider()
    
    # 부스 추가/삭제 (근무지 변경 반영)
    st.subheader("🏢 부스 관리")
    current_booths = st.text_area("운영 부스 목록 (줄바꿈으로 구분)", "\n".join(st.session_state.booth_list))
    st.session_state.booth_list = current_booths.strip().split('\n')

# --- 3. 핵심 자동 배치 로직 ---
def generate_auto_schedule():
    # 1. 쉬어야 할 인원수 계산
    n_staff = len(active_staff)
    n_booth = len(st.session_state.booth_list)
    rest_needed = max(0, n_staff - n_booth)
    
    # 2. 가장 오래 일한 사람(rest_score 높은 순) 정렬
    sorted_staff = sorted(active_staff, key=lambda x: st.session_state.staff_db[x]['rest_score'], reverse=True)
    
    # 3. 휴식자 선정
    resters = sorted_staff[:rest_needed]
    workers = sorted_staff[rest_needed:]
    
    # 4. 부스 배치 (이전 위치 보존 로직)
    final_mapping = {}
    remaining_booths = st.session_state.booth_list.copy()
    unassigned_workers = workers.copy()
    
    # 원래 자리에 있던 사람 먼저 고정
    for person in workers:
        last_pos = st.session_state.staff_db[person]["last_pos"]
        if last_pos in remaining_booths:
            final_mapping[last_pos] = person
            remaining_booths.remove(last_pos)
            unassigned_workers.remove(person)
            
    # 빈 자리에 나머지 인원(복귀자 등) 순차 배치
    for booth in remaining_booths:
        if unassigned_workers:
            p = unassigned_workers.pop(0)
            final_mapping[booth] = p
            st.session_state.staff_db[p]["last_pos"] = booth

    return final_mapping, resters

# --- 4. 메인 화면 출력 ---
st.title("🤖 자동 교대 관리")

if st.button("🔄 다음 교대로 갱신 (자동 계산)", use_container_width=True):
    # 점수 업데이트 (일한 사람은 점수 올리고, 쉰 사람은 0으로)
    # 실제 배치 로직은 위 함수에서 처리
    st.session_state.last_result, st.session_state.last_resters = generate_auto_schedule()
    
    # 점수 갱신
    for name in active_staff:
        if name in st.session_state.last_resters:
            st.session_state.staff_db[name]['rest_score'] = 0
        else:
            st.session_state.staff_db[name]['rest_score'] += 1

# 결과 표시
if 'last_result' in st.session_state:
    st.subheader("📍 현재 부스별 배치")
    for booth, worker in st.session_state.last_result.items():
        st.markdown(f"""
            <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid #ff4b4b;">
                <span style="font-weight:bold; color:#555;">{booth}</span> : 
                <span style="font-size:18px; color:#222;">{worker}</span>
            </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    st.write(f"☕ **현재 휴식 보장:** {', '.join(st.session_state.last_resters) if st.session_state.last_resters else '없음'}")
else:
    st.info("상단 버튼을 눌러 첫 교대를 생성하세요.")
