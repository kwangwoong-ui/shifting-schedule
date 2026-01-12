import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 2. 마스터 데이터 (순서 절대 고정)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 데이터 저장소 초기화
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "work_units": 0}
    for name in SUP_NAMES: db[name] = {"type": "지원", "work_units": 0}
    st.session_state.staff_db = db

if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0

# --- 4. 사이드바: 100% 정렬 보장 ---
with st.sidebar:
    st.header("⚙️ 설정창")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    group_size = n_shift - 1
    ppl_per_group = n_shift
    
    st.divider()
    selected_staff = []
    st.subheader("👥 고정 근무자 (A~J)")
    for name in REG_NAMES:
        if st.checkbox(name, value=True, key=f"r_{name}"): selected_staff.append(name)
    st.subheader("🏢 지원 부서 (1~10)")
    for name in SUP_NAMES:
        if st.checkbox(name, value=False, key=f"s_{name}"): selected_staff.append(name)

    st.divider()
    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"b_{b_name}"):
            selected_booths.append(b_name)

# --- 5. 배정 로직 (중요 부스 우선 + 왼쪽 우선 순환) ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 부스와 근무자를 선택해주세요.", None

    # [1] 휴식 순번: 가장 오래 일한 사람(왼쪽)부터
    staff_queue = sorted(selected_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift)
    resters = staff_queue[:num_rest]
    
    # [2] 부스 정렬 및 순환 (감독/자동은 순환에서 제외하거나 최우선 순위 부여)
    # '감독', '자동'이 선택되었다면 무조건 리스트의 맨 앞으로 고정
    important = [b for b in ["감독", "자동"] if b in selected_booths]
    others = [b for b in selected_booths if b not in ["감독", "자동"]]
    
    # 일반 부스들만 롤링 적용
    offset = st.session_state.shift_count % max(1, len(others)) if others else 0
    rolled_others = others[offset:] + others[:offset]
    
    # 최종 부스 리스트: [중요 부스] + [순환하는 일반 부스]
    final_booth_pool = important + rolled_others

    # [3] 그룹 배정 (인원 기준)
    num_groups = math.ceil(len(selected_staff) / ppl_per_group)
    res_lines = []
    
    for i in range(num_groups):
        g_staff = staff_queue[i * ppl_per_group : (i+1) * ppl_per_group]
        if not g_staff: continue
        
        # 부스 배정 (N-1개)
        b_count = ppl_per_group if all_in_mode else (len(g_staff) - 1)
        g_booths = final_booth_pool[i * group_size : i * group_size + b_count]
        
        # 유령 부스 처리
        while len(g_booths) < group_size:
            g_booths.append("X")
        
        booth_label = "/".join(g_booths)
        res_lines.append(f"{booth_label} {' '.join(g_staff)}")
        
    return None, (res_lines, resters)

# --- 6. 화면 출력 및 진단 ---
st.subheader("📊 인원 정합성 체크")
total_needed = math.ceil(len(selected_booths) / (n_shift-1)) * n_shift if not all_in_mode else len(selected_booths)
if len(selected_staff) < total_needed:
    st.error(f"⚠️ 인원이 부족합니다! 현재 {len(selected_staff)}명 / 최소 {total_needed}명 필요")
else:
    st.success(f"✅ 인원이 충분합니다. ({len(selected_staff)}명 투입 중)")

if st.button("🔄 근무 스케줄 갱신 (중요 부스 우선)", use_container_width=True):
    st.session_state.shift_count += 1
    error, result = generate_schedule()
    if error:
        st.error(error)
    else:
        st.session_state.last_display = result[0]
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'last_display' in st.session_state:
    st.subheader("📍 현재 근무 배치")
    for line in st.session_state.last_display:
        st.markdown(f"#### `{line}`")
