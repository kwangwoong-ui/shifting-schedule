import streamlit as st
import math

# 1. 초기 설정 및 페이지 구성
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 성함 지정형 근무 배정 시스템")

# 마스터 ID 정의 (내부 로직용)
REG_IDS = [chr(i) for i in range(ord('A'), ord('K'))] # A~J
SUP_IDS = [f"S{i}" for i in range(1, 11)]             # S1~S10

# 2. 데이터 저장소 초기화 (성함 매핑 및 이력 보존)
if 'name_map' not in st.session_state:
    # 초기값은 A, B, C... 및 지원1, 지원2...
    st.session_state.name_map = {rid: rid for rid in REG_IDS}
    for sid in SUP_IDS:
        st.session_state.name_map[sid] = f"지원{sid[1:]}"

if 'staff_db' not in st.session_state:
    db = {}
    for uid in REG_IDS + SUP_IDS:
        db[uid] = {"work_units": 0}
    st.session_state.staff_db = db

if 'shift_offset' not in st.session_state:
    st.session_state.shift_offset = 0

# --- 3. 사이드바: 인원 성함 관리 및 설정 ---
with st.sidebar:
    st.header("👤 근무자 명단 관리")
    st.caption("성함을 수정하면 배치표에 즉시 반영됩니다.")
    
    # 성함 수정 필드 (고정 대원)
    with st.expander("고정 대원 성함 수정 (A~J)"):
        for rid in REG_IDS:
            st.session_state.name_map[rid] = st.text_input(f"슬롯 {rid} 성함", value=st.session_state.name_map[rid], key=f"edit_{rid}")

    # 성함 수정 필드 (지원 부서)
    with st.expander("지원 부서 성함 수정 (1~10)"):
        for sid in SUP_IDS:
            st.session_state.name_map[sid] = st.text_input(f"지원 {sid[1:]} 성함", value=st.session_state.name_map[sid], key=f"edit_{sid}")

    st.divider()
    st.header("⚙️ 배정 설정")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5], index=2)
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    st.divider()
    # 인원 선택 (수정된 이름으로 표시)
    selected_uids = []
    st.subheader("👥 투입 인원 선택")
    for uid in REG_IDS + SUP_IDS:
        display_name = st.session_state.name_map[uid]
        if st.checkbox(display_name, value=(uid in REG_IDS), key=f"sel_{uid}"):
            selected_uids.append(uid)

    st.divider()
    selected_booths = []
    st.subheader("📍 부스 선택")
    BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 29)]
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"bth_{b_name}"):
            selected_booths.append(b_name)

    # 수동 고정 (수정된 이름 반영)
    st.divider()
    st.subheader("📌 주요 부스 인원 고정")
    manual_pins = {}
    for pb in ["감독", "자동", "1", "2"]:
        if pb in selected_booths:
            options = {st.session_state.name_map[u]: u for u in selected_uids}
            choice = st.selectbox(f"[{pb}] 고정", ["자동"] + list(options.keys()), key=f"pin_{pb}")
            if choice != "자동": manual_pins[pb] = options[choice]

# --- 4. 실시간 현황 진단 가이드 ---
st.subheader("📊 실시간 근무 진단")
total_staff_count = len(selected_uids)
if total_staff_count > 0:
    num_groups = total_staff_count // n_shift
    recommended_booths = num_groups * n_shift if all_in_mode else num_groups * (n_shift - 1)
    
    st.info(f"💡 투입 인원: **{total_staff_count}명** | **{n_shift}교대 적정 부스: {recommended_booths}개** (감독/자동 포함)")
    if len(selected_booths) > recommended_booths:
        st.warning(f"⚠️ 부스가 {len(selected_booths) - recommended_booths}개 더 선택되었습니다. (X 표시 생성)")
    elif len(selected_booths) < recommended_booths:
        st.error(f"🚨 부스가 {recommended_booths - len(selected_booths)}개 부족합니다.")

# --- 5. 배정 로직 (이력 기반) ---
def generate_schedule():
    if not selected_booths or not selected_uids:
        return "❌ 설정 부족", None

    pinned_uids = list(manual_pins.values())
    pinned_booths = list(manual_pins.keys())
    
    # 이력 정렬 (왼쪽 우선순위)
    rem_uids = [u for u in selected_uids if u not in pinned_uids]
    sorted_queue = sorted(rem_uids, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    num_rest = 0 if all_in_mode else (len(selected_uids) // n_shift)
    resters = sorted_queue[:num_rest]
    
    rem_booths = [b for b in selected_booths if b not in pinned_booths]
    offset = st.session_state.shift_offset % max(1, len(rem_booths)) if rem_booths else 0
    rolled_booths = rem_booths[offset:] + rem_booths[:offset]

    res_display = []
    # 고정 배정 (성함 매핑)
    for b, u in manual_pins.items():
        res_display.append(f"📍 {b} {st.session_state.name_map[u]} (고정)")
    
    temp_workers = [u for u in sorted_queue] 
    temp_booths = rolled_booths.copy()
    b_per_group = n_shift if all_in_mode else (n_shift - 1)
    
    group_idx = 0
    while (group_idx * n_shift) < len(temp_workers):
        g_uids = temp_workers[group_idx * n_shift : (group_idx + 1) * n_shift]
        g_names = [st.session_state.name_map[u] for u in g_uids] # 실제 이름으로 변환
        
        g_booths = temp_booths[:b_per_group]
        temp_booths = temp_booths[b_per_group:]
        while len(g_booths) < b_per_group: g_booths.append("X")
        
        res_display.append(f"🔸 {'/'.join(g_booths)} | {' '.join(g_names)}")
        group_idx += 1

    return None, (res_display, resters)

# --- 6. 실행 및 카톡 복사 ---
if st.button("🔄 근무 스케줄 갱신 (이력 반영)", use_container_width=True):
    st.session_state.shift_offset += 1
    error, result = generate_schedule()
    if error: st.error(error)
    else:
        st.session_state.final_res = result[0]
        for u in selected_uids:
            if u in result[1]: st.session_state.staff_db[u]['work_units'] = 0
            else: st.session_state.staff_db[u]['work_units'] += 1

if 'final_res' in st.session_state:
    st.divider()
    st.subheader("📍 현재 근무 배치표")
    for line in st.session_state.final_res:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    st.subheader("📱 카카오톡 보고용 텍스트")
    kakao_text = f"📢 [{n_shift}교대 배치 현황]\n" + "\n".join(st.session_state.final_res)
    st.text_area("복사하여 사용하세요:", value=kakao_text, height=200)
