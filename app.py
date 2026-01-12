import streamlit as st
import math

# 1. 초기 설정 및 페이지 구성
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 마스터 데이터 (A~J 고정 및 지원1~10)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 29)]

# 2. 데이터 저장소 (연속성 보장)
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES + SUP_NAMES:
        db[name] = {"work_units": 0}
    st.session_state.staff_db = db
if 'shift_offset' not in st.session_state:
    st.session_state.shift_offset = 0

# --- 3. 사이드바: 설정 및 수동 고정 ---
with st.sidebar:
    st.header("⚙️ 설정 및 수동 배정")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5], index=2) # 4교대 기본
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    st.divider()
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
    st.subheader("📌 주요 부스 인원 고정")
    manual_pins = {}
    for pb in ["감독", "자동", "1", "2"]:
        if pb in selected_booths:
            choice = st.selectbox(f"[{pb}] 고정", ["자동"] + selected_staff, key=f"pin_{pb}")
            if choice != "자동": manual_pins[pb] = choice

# --- 4. [신규] 실시간 현황 진단 가이드 ---
st.subheader("📊 실시간 근무 진단")
total_staff_count = len(selected_staff)
if total_staff_count > 0:
    # 적정 부스 계산: (전체 인원 // N) * (N-1)
    # 전부 투입 모드라면 (전체 인원 // N) * N
    num_groups = total_staff_count // n_shift
    if all_in_mode:
        recommended_booths = num_groups * n_shift
    else:
        recommended_booths = num_groups * (n_shift - 1)
    
    # 감독, 자동 포함 안내 문구 출력
    st.info(f"💡 현재 투입 인원: **{total_staff_count}명**")
    st.success(f"✅ **{n_shift}교대 적정 부스: {recommended_booths}개** (감독/자동 포함)")
    
    # 설정 불일치 경고
    if len(selected_booths) > recommended_booths:
        st.warning(f"⚠️ 선택된 부스가 {len(selected_booths) - recommended_booths}개 많습니다. 하단에 유령 부스(X)가 생성됩니다.")
    elif len(selected_booths) < recommended_booths:
        st.error(f"🚨 부스가 {recommended_booths - len(selected_booths)}개 부족합니다. 부스를 더 선택하거나 인원을 줄여주세요.")
else:
    st.write("사이드바에서 인원을 선택하면 적정 부스 개수를 계산해 드립니다.")

# --- 5. 배정 로직 ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 설정이 부족합니다.", None

    pinned_staff = list(manual_pins.values())
    pinned_booths = list(manual_pins.keys())
    
    # 이력 정렬 (왼쪽 우선순위)
    rem_staff = [s for s in selected_staff if s not in pinned_staff]
    sorted_queue = sorted(rem_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    # 휴식자 선정
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift)
    resters = sorted_queue[:num_rest]
    
    # 부스 롤링
    rem_booths = [b for b in selected_booths if b not in pinned_booths]
    offset = st.session_state.shift_offset % max(1, len(rem_booths)) if rem_booths else 0
    rolled_booths = rem_booths[offset:] + rem_booths[:offset]

    # 결과 조립
    res_display = []
    for b, s in manual_pins.items():
        res_display.append(f"📍 {b} {s} (고정)")
    
    temp_workers = [p for p in sorted_queue] 
    temp_booths = rolled_booths.copy()
    b_per_group = n_shift if all_in_mode else (n_shift - 1)
    
    group_idx = 0
    while (group_idx * n_shift) < len(temp_workers):
        g_staff = temp_workers[group_idx * n_shift : (group_idx + 1) * n_shift]
        g_booths = temp_booths[:b_per_group]
        temp_booths = temp_booths[b_per_group:]
        while len(g_booths) < b_per_group: g_booths.append("X")
        
        res_display.append(f"🔸 {'/'.join(g_booths)} | {' '.join(g_staff)}")
        group_idx += 1

    return None, (res_display, resters)

# --- 6. 실행 및 카톡 복사 ---
if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
    st.session_state.shift_offset += 1
    error, result = generate_schedule()
    if error: st.error(error)
    else:
        st.session_state.final_res = result[0]
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'final_res' in st.session_state:
    st.divider()
    st.subheader("📍 현재 근무 배치표")
    for line in st.session_state.final_res:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    st.subheader("📱 카카오톡 보고용 텍스트")
    kakao_text = f"📢 [{n_shift}교대 배치 현황]\n" + "\n".join(st.session_state.final_res)
    st.text_area("복사하여 사용하세요:", value=kakao_text, height=200)
