import streamlit as st
import math

# 1. 초기 설정
st.set_page_config(page_title="현장 근무 관리 도구", layout="centered")
st.title("📋 부스 이름 순환 배정 시스템")

# 2. 세션 상태 (명단 및 성함 고정)
if 'main_queue' not in st.session_state:
    st.session_state.main_queue = [chr(i) for i in range(ord('A'), ord('L'))] # A~K
if 'name_map' not in st.session_state:
    st.session_state.name_map = {uid: uid for uid in st.session_state.main_queue}
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0

# --- 3. 사이드바: 설정 및 성함 수정 ---
with st.sidebar:
    st.header("⚙️ 운영 설정")
    mode = st.radio("🔄 운영 모드", ["정규 4교대", "밀어내기 (1명 휴식)"])
    
    st.divider()
    st.subheader("👤 근무자 성함 (순서 고정)")
    for uid in st.session_state.main_queue:
        st.session_state.name_map[uid] = st.text_input(f"슬롯 {uid}", value=st.session_state.name_map[uid], key=f"nm_{uid}")

    st.divider()
    st.subheader("📍 운영 부스 선택")
    BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 29)]
    selected_booths = []
    for b in BOOTHS_MASTER:
        if st.checkbox(b, value=(b in BOOTHS_MASTER[:10]), key=f"bth_{b}"):
            selected_booths.append(b)

# --- 4. 배정 로직: 이름 고정, 부스 라벨 순환 ---
def get_display_lines(current_mode, count):
    all_uids = st.session_state.main_queue
    all_names = [st.session_state.name_map[u] for u in all_uids]
    booth_pool = selected_booths.copy()
    
    lines = []
    
    if "4교대" in current_mode:
        # 4명씩 조를 짜되, 이름(ABCD)은 고정하고 부스 이름표를 돌림
        for i in range(0, len(all_names), 4):
            group = all_names[i:i+4]
            # 이 조에서 누가 쉴지 결정 (count에 따라 0, 1, 2, 3번째 인덱스)
            rest_idx = count % 4
            
            # 사용할 부스 3개 추출 및 순환 (감독/자동/1 -> 자동/1/감독 -> 1/감독/자동)
            g_booths_base = booth_pool[:3]
            booth_pool = booth_pool[3:]
            while len(g_booths_base) < 3: g_booths_base.append("X")
            
            # 부스 이름표 돌리기 로직
            b_offset = count % 3
            rolled_booths = g_booths_base[b_offset:] + g_booths_base[:b_offset]
            
            # 실제 배치 (휴식자는 건너뛰고 부스 이름표 붙이기)
            mapping = []
            b_idx = 0
            for j in range(4):
                if j == rest_idx:
                    continue # 휴식자는 부스 이름표를 붙이지 않음 (미표기)
                if b_idx < len(rolled_booths):
                    mapping.append(rolled_booths[b_idx])
                    b_idx += 1
            
            lines.append(f"🔸 {'/'.join(mapping)} | {' '.join(group)}")
            
    else:
        # 밀어내기: 전체 인원에서 1명만 휴식, 나머지 부스 순환
        rest_idx = count % len(all_names)
        
        # 부스 이름표 돌리기
        b_offset = count % len(booth_pool) if booth_pool else 0
        rolled_booths = booth_pool[b_offset:] + booth_pool[:b_offset]
        
        mapping = []
        b_idx = 0
        for i in range(len(all_names)):
            if i == rest_idx: continue
            if b_idx < len(rolled_booths):
                mapping.append(rolled_booths[b_idx])
                b_idx += 1
        
        lines.append(f"🔸 {'/'.join(mapping)} | {' '.join(all_names)}")
        
    return lines

# --- 5. 실시간 진단 및 출력 ---
st.subheader("📊 근무 진단")
num_p = len(st.session_state.main_queue)
if "4교대" in mode:
    rec_b = (num_p // 4) * 3 + (num_p % 4 if num_p % 4 > 0 else 0)
else:
    rec_b = num_p - 1

st.info(f"💡 **{mode} 적용:** 적정 부스 개수는 **{rec_b}개**입니다. (현재 선택: {len(selected_booths)}개)")

if st.button("🔄 다음 교대 (부스 이름표 갱신)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader("📍 현재 근무 배치 (이름 고정)")
display_results = get_display_lines(mode, st.session_state.shift_count)
for res in display_results:
    st.markdown(f"#### `{res}`")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 현황]\n" + "\n".join(display_results)
st.text_area("복사하기:", value=kakao_text, height=150)
