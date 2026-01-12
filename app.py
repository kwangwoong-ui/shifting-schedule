import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="centered")
st.title("📋 고정 배정 및 지능형 순환 시스템")

# 2. 마스터 데이터 정의
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 데이터 저장소 초기화
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES + SUP_NAMES:
        db[name] = {"work_units": 0}
    st.session_state.staff_db = db
if 'shift_offset' not in st.session_state:
    st.session_state.shift_offset = 0

# --- 4. 사이드바: 설정 및 수동 고정 배정 ---
with st.sidebar:
    st.header("⚙️ 설정 및 수동 배정")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    st.divider()
    # 인원 및 부스 선택
    selected_staff = []
    st.subheader("👥 인원 선택")
    for name in REG_NAMES + SUP_NAMES:
        if st.checkbox(name, value=(name in REG_NAMES), key=f"sel_{name}"):
            selected_staff.append(name)

    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"bth_{b_name}"):
            selected_booths.append(b_name)

    st.divider()
    # [핵심] 수동 고정 배정 설정
    st.subheader("📌 주요 부스 수동 고정")
    manual_pins = {}
    priority_booths = ["감독", "자동", "1", "2"]
    for pb in priority_booths:
        if pb in selected_booths:
            # 선택된 인원 중에서 해당 부스에 고정할 사람 선택
            choice = st.selectbox(f"[{pb}] 고정 인원", ["자동 배정"] + selected_staff, key=f"pin_{pb}")
            if choice != "자동 배정":
                manual_pins[pb] = choice

# --- 5. 배정 로직 (수동 고정 제외 후 순환) ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 설정이 부족합니다.", None

    # 1. 수동 고정 인원 및 부스 제외
    pinned_staff = list(manual_pins.values())
    pinned_booths = list(manual_pins.keys())
    
    remaining_staff = [s for s in selected_staff if s not in pinned_staff]
    remaining_booths = [b for b in selected_booths if b not in pinned_booths]

    # 2. 남은 인원 이력 기반 정렬 (왼쪽 우선순위)
    def sort_key(name):
        return (-st.session_state.staff_db[name]['work_units'], 
                0 if name in REG_NAMES else 1, 
                name if name in REG_NAMES else int(name.replace("지원", "")))
    
    # 남은 인원들을 줄 세움
    unified_queue = sorted(remaining_staff, key=sort_key)
    
    # 3. 휴식자 선정 (수동 고정 인원은 휴식에서 제외/강제 근무)
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift)
    # 수동 고정 인원을 뺀 나머지에서 휴식자를 뽑음
    resters = unified_queue[:num_rest]
    workers = [p for p in unified_queue if p not in resters]
    
    # 4. 일반 부스 롤링
    offset = st.session_state.shift_offset % max(1, len(remaining_booths)) if remaining_booths else 0
    rolled_booths = remaining_booths[offset:] + remaining_booths[:offset]

    # 5. 최종 결과 조립
    # 수동 고정 부스를 첫 번째 줄에 배치
    final_lines = []
    if manual_pins:
        for b, s in manual_pins.items():
            final_lines.append(f"📍 {b} {s} (수동 고정)")

    # 나머지 자동 배정 (N-1 규칙 적용)
    group_size = n_shift - 1
    num_groups = math.ceil(len(workers) / group_size) if group_size > 0 else 0
    
    for i in range(num_groups):
        g_booths = rolled_booths[i * group_size : (i+1) * group_size]
        while len(g_booths) < group_size: g_booths.append("X")
        
        # 각 조 인원은 N명씩 끊어서 표시 (왼쪽 우선)
        # 이미 workers는 이력 순으로 정렬됨
        g_staff = workers[i * n_shift : (i+1) * n_shift] # 실제로는 workers를 다시 쪼개야 함
        # (간편한 표시를 위해 남은 인원들을 순차적으로 배치)
        
    # [참고] 관리자님의 "부스/부스 + 인원들" 형식을 위해 로직 정교화
    # 실제 조 편성은 순서대로 묶음
    res_display = []
    # 고정 배정 라인 추가
    for b, s in manual_pins.items():
        res_display.append(f"{b} {s}")
    
    # 자동 순환 라인 추가
    auto_workers = workers.copy()
    auto_booths = rolled_booths.copy()
    
    while auto_workers:
        current_g_staff = auto_workers[:n_shift]
        auto_workers = auto_workers[n_shift:]
        
        current_g_booths = auto_booths[:n_shift-1]
        auto_booths = auto_booths[n_shift-1:]
        while len(current_g_booths) < (n_shift-1): current_g_booths.append("X")
        
        res_display.append(f"{'/'.join(current_g_booths)} {' '.join(current_g_staff)}")

    return None, (res_display, resters, pinned_staff)

# --- 6. 실행 및 관리 ---
if st.button("🔄 근무 스케줄 갱신 (수동 고정 반영)", use_container_width=True):
    st.session_state.shift_offset += 1
    error, result = generate_schedule()
    if error:
        st.error(error)
    else:
        st.session_state.final_display = result[0]
        # 이력 업데이트
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0 # 쉰 사람
            else: st.session_state.staff_db[p]['work_units'] += 1 # 일한 사람 (고정 인원 포함)

if 'final_display' in st.session_state:
    st.subheader("📍 현재 근무 배치 현황")
    for line in st.session_state.final_display:
        st.markdown(f"#### `{line}`")
