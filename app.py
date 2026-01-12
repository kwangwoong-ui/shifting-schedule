import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 스마트 관리", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 2. 마스터 데이터 (A~J 고정, 지원1~10)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] 
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 세션 상태 초기화 (연속 근무 시간 및 부스 순환 카운트)
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "work_units": 0}
    for name in SUP_NAMES: db[name] = {"type": "지원", "work_units": 0}
    st.session_state.staff_db = db
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0

# --- 4. 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 설정창")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    # N교대 규칙: 부스 N-1개, 인원 N명
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

# --- 5. 배정 로직 (왼쪽 우선순위 정렬 및 부스 롤링) ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 설정이 부족합니다.", None

    # [중요] 연속 근무가 긴 사람(휴식 1순위)부터 줄 세우기
    # 이 순서가 배치표의 '왼쪽'부터 채워지게 됩니다.
    staff_queue = sorted(selected_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    # 휴식자 선정 (가장 왼쪽 인원들)
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift)
    resters = staff_queue[:num_rest]
    
    # 부스 롤링 로직 (1/2 -> 2/1)
    sorted_active_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    offset = st.session_state.shift_count % max(1, len(sorted_active_booths))
    rolled_booths = sorted_active_booths[offset:] + sorted_active_booths[:offset]

    num_groups = math.ceil(len(selected_staff) / ppl_per_group)
    res_lines = []
    
    for i in range(num_groups):
        # 이번 그룹 인원 선정 (휴식 예정자 포함 N명)
        g_staff = staff_queue[i * ppl_per_group : (i+1) * ppl_per_group]
        if not g_staff: continue
        
        # 부스 배정 (N-1개)
        b_count = ppl_per_group if all_in_mode else (len(g_staff) - 1)
        g_booths = rolled_booths[i * group_size : i * group_size + b_count]
        while len(g_booths) < group_size: g_booths.append("X") # 유령 부스 처리
        
        # [출력 형식] 부스이름 근무자1 근무자2 근무자3...
        # g_staff 자체가 이미 '가장 오래 일한 사람' 순서(왼쪽 우선)로 정렬되어 있습니다.
        booth_label = "/".join(g_booths)
        res_lines.append(f"{booth_label} {' '.join(g_staff)}")
        
    return None, (res_lines, resters)

# --- 6. 실행 및 출력 ---
if st.button("🔄 근무 스케줄 갱신 (왼쪽 우선순위 적용)", use_container_width=True):
    st.session_state.shift_count += 1
    error, result = generate_schedule()
    if error:
        st.error(error)
    else:
        st.session_state.last_display = result[0]
        # 포인트 업데이트 (쉰 사람은 초기화하여 줄의 맨 오른쪽으로 보냄)
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'last_display' in st.session_state:
    st.subheader("📍 현재 근무 배치 (왼쪽 이름이 다음 휴식 1순위)")
    for line in st.session_state.last_display:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    st.caption("💡 갱신 버튼을 누를 때마다 각 조의 가장 왼쪽 인원이 휴식에 들어갑니다.")
