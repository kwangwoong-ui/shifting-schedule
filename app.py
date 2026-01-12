import streamlit as st
import math

# 1. 초기 설정 및 페이지 구성
st.set_page_config(page_title="현장 근무 관리 도구", layout="centered")
st.title("📋 근무 순환 관리 (밀어내기/4교대)")

# 2. 세션 상태 (명단 순서 유지)
if 'main_queue' not in st.session_state:
    # 최초 명단 (알파벳으로 시작하지만 이름 수정 시 반영됨)
    st.session_state.main_queue = [chr(i) for i in range(ord('A'), ord('L'))] # A~K (11명 예시)
if 'name_map' not in st.session_state:
    st.session_state.name_map = {c: c for c in st.session_state.main_queue}

# --- 3. 사이드바: 모드 전환 및 이름 수정 ---
with st.sidebar:
    st.header("⚙️ 모드 및 인원 설정")
    
    # [핵심] 모드 선택 (밀어내기 vs 4교대)
    mode = st.radio("🔄 운영 모드 선택", ["밀어내기 (1명 휴식)", "정규 4교대 (N/4 휴식)"])
    
    st.divider()
    st.subheader("👤 이름 수정")
    for uid in st.session_state.main_queue:
        st.session_state.name_map[uid] = st.text_input(f"슬롯 {uid}", value=st.session_state.name_map[uid], key=f"edit_{uid}")

# --- 4. 순환 로직 (단순 밀어내기) ---
def push_queue(n_rest):
    # 명단 리스트에서 왼쪽 n_rest명 만큼을 떼어서 맨 뒤로 보냄
    q = st.session_state.main_queue
    st.session_state.main_queue = q[n_rest:] + q[:n_rest]

# --- 5. 화면 표시 및 실행 ---
# 선택된 부스 (고정 예시: 1~9번)
BOOTHS = ["감독", "자동", "1", "2", "3", "4", "5", "6", "7"]

st.subheader("📊 현재 투입 순번")
display_names = [st.session_state.name_map[u] for u in st.session_state.main_queue]
st.info(" → ".join(display_names))
st.caption("💡 맨 왼쪽 인원이 다음 휴식 1순위입니다.")

# 휴식 인원 계산
if "밀어내기" in mode:
    n_rest = 1
else:
    n_rest = len(st.session_state.main_queue) // 4

if st.button(f"🔄 {mode} - 다음 교대 진행", use_container_width=True):
    push_queue(n_rest)
    st.rerun()

# 배치표 생성
st.divider()
st.subheader("📍 현재 근무 배치표")

# 현재 상태의 이름을 가져옴
current_names = [st.session_state.name_map[u] for u in st.session_state.main_queue]

if "밀어내기" in mode:
    # 전체 부스 하나로 묶음
    booth_label = "/".join(BOOTHS)
    st.markdown(f"#### `{booth_label} | {' '.join(current_names)}`")
else:
    # 4교대: 4명씩 조를 짜서 표시
    group_size = 4
    for i in range(0, len(current_names), group_size):
        g_staff = current_names[i:i+group_size]
        g_booths = BOOTHS[i//group_size * 3 : (i//group_size + 1) * 3] # 3개씩 매칭
        while len(g_booths) < 3: g_booths.append("X")
        
        booth_label = "/".join(g_booths)
        st.markdown(f"#### `{booth_label} | {' '.join(g_staff)}`")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 배치 현황]\n" + " ".join(current_names)
st.text_area("복사해서 사용하세요:", value=kakao_text, height=100)
