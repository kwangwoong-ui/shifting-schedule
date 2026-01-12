import streamlit as st

# 1. 모바일 최적화 및 레이아웃 설정
st.set_page_config(page_title="근무 관리", layout="centered")
st.title("📋 근무 배치 현황")

# 2. 마스터 데이터 정의 (절대 섞이지 않는 순서)
# 고정 근무자 A~O (15명)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('P'))]
# 지원 부서 1~10 (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]
# 부스 번호 (감독, 자동, 1~28 순서 고정)
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 데이터 저장소 초기화
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "last_group": None, "work_units": 0}
    for name in SUP_NAMES: db[name] = {"type": "지원", "last_group": None, "work_units": 0}
    st.session_state.staff_db = db

# --- 4. 사이드바: 100% 정렬 보장 (컬럼 제거) ---
with st.sidebar:
    st.header("⚙️ 설정창")
    
    # [교대수 설정]
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2) #
    group_size = n_shift - 1 # N교대면 부스 묶음은 N-1개
    
    st.divider()

    # [인원 선택] - 모바일 가독성을 위해 한 줄씩 출력 (정렬 보장)
    selected_staff = []
    st.subheader("👥 고정 근무자 (A~O)")
    for name in REG_NAMES:
        if st.checkbox(name, value=True, key=f"r_{name}"):
            selected_staff.append(name)
            
    st.subheader("🏢 지원 부서 (1~10)")
    for name in SUP_NAMES:
        if st.checkbox(name, value=False, key=f"s_{name}"):
            selected_staff.append(name)

    st.divider()

    # [부스 선택] - 감독~28번 순서 고정
    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in ["감독", "자동", "1"]), key=f"b_{b_name}"):
            selected_booths.append(b_name)

# --- 5. 배정 로직: N+1 법칙 및 이동 최소화 ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 부스와 근무자를 선택해주세요.", None

    # 부스 정렬 및 그룹화
    sorted_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    # N-1개씩 부스를 묶음
    station_groups = [sorted_booths[i : i + group_size] for i in range(0, len(sorted_booths), group_size)]
    
    # 인원 우선순위 (고정 A~O -> 지원 1~10)
    def get_sort_key(name):
        if name in REG_NAMES: return (0, name)
        return (1, int(name.replace("지원", "")))
    
    pool = sorted(selected_staff, key=get_sort_key)
    
    # 그룹당 필요 인원 계산 (부스 개수 k + 1명)
    assignments = {i: [] for i in range(len(station_groups))}
    remaining = pool.copy()
    
    # [이동 최소화] 기존 그룹 유지
    for i in range(len(station_groups)):
        needed = len(station_groups[i]) + 1
        prev = [p for p in remaining if st.session_state.staff_db[p].get('last_group') == i]
        fill = min(len(prev), needed)
        assignments[i].extend(prev[:fill])
        for p in prev[:fill]: remaining.remove(p)
    
    # [나머지 채우기]
    for i in range(len(station_groups)):
        needed = len(station_groups[i]) + 1
        while len(assignments[i]) < needed and remaining:
            p = remaining.pop(0)
            assignments[i].append(p)
            st.session_state.staff_db[p]['last_group'] = i

    # [최종 출력 생성]
    result_lines = []
    resters = []
    for i, members in assignments.items():
        booth_label = "/".join(station_groups[i])
        # 그룹 내에서 가장 오래 일한 사람 한 명 추출 (휴식 개념)
        m_sorted = sorted(members, key=lambda x: st.session_state.staff_db[x].get('work_units', 0), reverse=True)
        rester = m_sorted[0]
        resters.append(rester)
        
        # 화면에는 N+1명 전원 표시 (알파벳 순)
        display_members = sorted(members, key=get_sort_key)
        result_lines.append(f"{booth_label} {' '.join(display_members)}")
        
    return None, (result_lines, resters)

# --- 6. 화면 출력 ---
if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
    error, result = generate_schedule()
    if error:
        st.error(error)
    else:
        st.session_state.final_res = result[0]
        # 점수 업데이트 (일하면 +1, 쉬면 0)
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'final_res' in st.session_state:
    st.subheader("📍 현재 근무 배치")
    # 감독/자동/1 A B C D 형식
    for line in st.session_state.final_res:
        st.markdown(f"#### `{line}`")
