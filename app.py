import streamlit as st
import math

# 1. 초기 설정 및 페이지 구성
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 마스터 데이터 정의 (A~J 고정 및 지원1~10)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 2. 개인별 연속 근무 이력 저장 (연속성 보장)
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES + SUP_NAMES:
        db[name] = {"work_units": 0}
    st.session_state.staff_db = db
if 'shift_offset' not in st.session_state:
    st.session_state.shift_offset = 0

# --- 3. 사이드바: 설정 및 수동 배정 ---
with st.sidebar:
    st.header("⚙️ 설정 및 수동 고정")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    st.divider()
    selected_staff = []
    st.subheader("👥 인원 선택")
    for name in REG_NAMES + SUP_NAMES:
        # A~J는 기본 체크
        if st.checkbox(name, value=(name in REG_NAMES), key=f"sel_{name}"):
            selected_staff.append(name)

    st.divider()
    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"bth_{b_name}"):
            selected_booths.append(b_name)

    st.divider()
    # 주요 부스 수동 고정 기능
    st.subheader("📌 주요 부스 인원 고정")
    manual_pins = {}
    for pb in ["감독", "자동", "1", "2"]:
        if pb in selected_booths:
            choice = st.selectbox(f"[{pb}] 고정 인원", ["자동 배정"] + selected_staff, key=f"pin_{pb}")
            if choice != "자동 배정": manual_pins[pb] = choice

# --- 4. 배정 로직: 개인 이력 + 왼쪽 우선순위 ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 인원과 부스를 선택해주세요.", None

    pinned_staff = list(manual_pins.values())
    pinned_booths = list(manual_pins.keys())
    
    # [핵심] 개인의 연속 근무 이력 기반 정렬 (왼쪽이 다음 휴식 1순위)
    rem_staff = [s for s in selected_staff if s not in pinned_staff]
    sorted_queue = sorted(rem_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    # 휴식자 선정
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift)
    resters = sorted_queue[:num_rest]
    workers = [p for p in sorted_queue if p not in resters]
    
    # 일반 부스 롤링 (순환)
    rem_booths = [b for b in selected_booths if b not in pinned_booths]
    offset = st.session_state.shift_offset % max(1, len(rem_booths)) if rem_booths else 0
    rolled_booths = rem_booths[offset:] + rem_booths[:offset]

    # 결과 조립 (N+1 형식)
    res_display = []
    for b, s in manual_pins.items():
        res_display.append(f"📍{b} {s} (고정)")
    
    temp_workers = workers.copy()
    temp_booths = rolled_booths.copy()
    b_per_group = n_shift if all_in_mode else (n_shift - 1)
    
    while temp_workers:
        g_staff = temp_workers[:n_shift]
        temp_workers = temp_workers[n_shift:]
        
        g_booths = temp_booths[:b_per_group]
        temp_booths = temp_booths[b_per_group:]
        while len(g_booths) < b_per_group: g_booths.append("X")
        
        res_display.append(f"🔸 {'/'.join(g_booths)} | {' '.join(g_staff)}")

    return None, (res_display, resters)

# --- 5. 화면 출력 및 복사 기능 ---
st.subheader("📊 인원 정합성 분석")
total_needed = math.ceil(len(selected_booths) / (n_shift-1)) * n_shift if not all_in_mode else len(selected_booths)
if len(selected_staff) < total_needed:
    st.error(f"⚠️ 인원 부족: 현재 {len(selected_staff)}명 / 최소 {total_needed}명 필요")
else:
    st.success("✅ 인원과 부스 배치가 안정적입니다.")

if st.button("🔄 근무 스케줄 갱신 (개인 이력 반영)", use_container_width=True):
    st.session_state.shift_offset += 1
    error, result = generate_schedule()
    if error: st.error(error)
    else:
        st.session_state.final_res = result[0]
        # 이력 업데이트 (쉰 사람은 0으로 리셋)
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'final_res' in st.session_state:
    st.divider()
    st.subheader("📍 실시간 근무 배치표")
    
    # 텍스트 결과 조합 (카톡 복사용)
    kakao_text = "📢 [근무 배치 현황]\n\n" + "\n".join(st.session_state.final_res)
    
    # 결과 출력
    for line in st.session_state.final_res:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    
    # [새로운 기능] 원클릭 복사 영역
    st.subheader("📱 카카오톡 보고용 텍스트")
    st.text_area("아래 내용을 길게 눌러 복사하세요:", value=kakao_text, height=200)
    st.caption("💡 팁: 모바일에서는 위 박스를 길게 누르면 '전체 선택' 및 '복사'가 가능합니다.")
