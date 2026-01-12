import streamlit as st
import math

# 1. 초기 설정
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 인터리빙 지능형 순환 시스템")

# 마스터 ID 정의 (A~L 12명 기준 예시)
if 'main_queue' not in st.session_state:
    st.session_state.main_queue = [chr(i) for i in range(ord('A'), ord('M'))] # A~L
if 'name_map' not in st.session_state:
    st.session_state.name_map = {uid: uid for uid in st.session_state.main_queue}
if 'shift_offset' not in st.session_state:
    st.session_state.shift_offset = 0

# --- 2. 사이드바: 운영 설정 ---
with st.sidebar:
    st.header("⚙️ 운영 설정")
    mode = st.radio("🔄 운영 모드", ["정규 4교대 (N명당 1명 휴식)", "밀어내기 (전체 중 1명 휴식)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)
    
    st.divider()
    st.subheader("👤 이름 수정")
    for uid in st.session_state.main_queue:
        st.session_state.name_map[uid] = st.text_input(f"슬롯 {uid}", value=st.session_state.name_map[uid], key=f"edit_{uid}")

    st.divider()
    st.subheader("📍 부스 선택")
    BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 29)]
    selected_booths = []
    for b in BOOTHS_MASTER:
        if st.checkbox(b, value=(b in BOOTHS_MASTER[:10]), key=f"bth_{b}"):
            selected_booths.append(b)

# --- 3. 핵심 로직: 인터리빙 및 부스 매핑 ---
def get_processed_queue(is_push_mode):
    base_q = st.session_state.main_queue
    if not is_push_mode:
        return base_q # 4교대는 정방향
    
    # [핵심] 밀어내기 전환 시 세로로 엮기 (A E B F C G D H...)
    # 왼쪽 사람은 왼쪽, 오른쪽은 오른쪽에 있게 함
    rows = [base_q[i:i+4] for i in range(0, len(base_q), 4)]
    interleaved = []
    for col in range(4):
        for row in rows:
            if col < len(row):
                interleaved.append(row[col])
    return interleaved

# --- 4. 실시간 진단 문구 ---
st.subheader("📊 실시간 근무 진단")
total_people = len(st.session_state.main_queue)
n_shift = 4

if "밀어내기" in mode:
    # 밀어내기는 전체 중 1명만 휴식 (전부 투입 시 0명)
    n_rest = 0 if all_in_mode else 1
    rec_booths = total_people - n_rest
else:
    # 4교대는 조별로 1명씩 휴식
    num_groups = math.ceil(total_people / n_shift)
    n_rest = 0 if all_in_mode else num_groups
    rec_booths = total_people - n_rest

st.info(f"💡 **{mode} 적용:** 현재 {total_people}명 투입 중이며, **적정 부스 개수는 {rec_booths}개**입니다.")

# --- 5. 배치표 생성 및 실행 ---
if st.button("🔄 다음 교대 진행 (순서 및 부스 유지)", use_container_width=True):
    # 내부 큐 회전 (4교대 기준 1칸씩)
    q = st.session_state.main_queue
    st.session_state.main_queue = q[1:] + q[:1]
    st.rerun()

st.divider()
st.subheader("📍 현재 근무 배치표")

# 현재 모드에 따른 큐 가공
current_queue = get_processed_queue("밀어내기" in mode)
current_names = [st.session_state.name_map[u] for u in current_queue]
temp_booths = selected_booths.copy()

res_display = []

if "밀어내기" in mode:
    # 밀어내기: 맨 앞 한 명만 휴식, 나머지는 순서대로 부스 점유
    if all_in_mode:
        workers = current_names
        rester = "없음"
    else:
        rester = current_names[0]
        workers = current_names[1:]
    
    # 부스 매핑 (왼쪽 우선순위 유지)
    assigned_booths = temp_booths[:len(workers)]
    res_display.append(f"🔸 {'/'.join(assigned_booths)} | {' '.join(workers)}")
    st.markdown(f"#### {res_display[0]}")
    if not all_in_mode: st.success(f"☕ 휴식: {rester}")

else:
    # 4교대: 4명씩 조를 짜서 첫 번째 사람 휴식
    for i in range(0, len(current_names), n_shift):
        group = current_names[i:i+n_shift]
        if all_in_mode:
            workers = group
            rester = "없음"
            g_booths = temp_booths[:4]
            temp_booths = temp_booths[4:]
        else:
            rester = group[0]
            workers = group[1:]
            g_booths = temp_booths[:3]
            temp_booths = temp_booths[3:]
        
        while len(g_booths) < (4 if all_in_mode else 3): g_booths.append("X")
        
        line = f"🔸 {'/'.join(g_booths)} | {' '.join(workers)}"
        if not all_in_mode: line += f" (휴식: {rester})"
        res_display.append(line)
        st.markdown(f"#### {line}")

# --- 6. 카카오톡 보고용 ---
st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 현황]\n" + "\n".join(res_display)
st.text_area("내용 복사:", value=kakao_text, height=150)
