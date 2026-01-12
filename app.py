import streamlit as st
import math

# 1. 페이지 및 데이터 초기화
st.set_page_config(page_title="현장 근무 스마트 관리", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 마스터 데이터 정의
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10 (10명)
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "work_units": 0}
    for name in SUP_NAMES: db[name] = {"type": "지원", "work_units": 0}
    st.session_state.staff_db = db

# --- 2. 사이드바 설정 (정렬 보장) ---
with st.sidebar:
    st.header("⚙️ 설정창")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    all_in_mode = st.toggle("전부 투입 (휴식 인원 없음)", value=False)
    
    # N+1 법칙: N교대 시 한 그룹당 인원은 N명, 부스는 N-1개
    group_booth_count = n_shift - 1
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

# --- 3. 핵심 배정 알고리즘 ---
def generate_rotation():
    if not selected_booths or not selected_staff:
        return "❌ 부스와 근무자를 선택해주세요.", None

    # [휴식 순번 로직] 근무 포인트가 높은 순서(오래 일한 순)로 정렬
    sorted_by_work = sorted(selected_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    # 휴식 인원 결정 (전부 투입 시 0명)
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift if n_shift > 1 else 0)
    resters = sorted_by_work[:num_rest]
    
    # 근무 투입 인원 (전부 투입 시 전원 포함)
    workers = [p for p in selected_staff if p not in resters]
    
    # [우선순위 배치] 고정(A-J) 알파벳순 -> 지원부서 숫자순
    def get_priority(name):
        if name in REG_NAMES: return (0, name)
        return (1, int(name.replace("지원", "")))
    
    sorted_workers = sorted(workers, key=get_priority)
    
    # 전부 투입 시, 휴식 예정자들을 명단 마지막에 추가 (유령 부스 X에 배치하기 위함)
    if all_in_mode:
        sorted_resters = sorted(sorted_by_work[:len(selected_staff) // n_shift], key=get_priority)
        # 이미 workers에 포함되어 있으므로 추가 정렬만 보장
        sorted_workers = sorted(selected_staff, key=get_priority)

    # 부스 그룹화 및 유령 부스(X) 처리
    sorted_active_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    num_groups = math.ceil(len(sorted_workers) / ppl_per_group)
    
    final_lines = []
    for i in range(num_groups):
        # 이번 그룹 부스 (N-1개)
        g_booths = sorted_active_booths[i * group_booth_count : (i+1) * group_booth_count]
        while len(g_booths) < group_booth_count:
            g_booths.append("X") # 부족한 자리는 유령 부스 X 표시
            
        # 이번 그룹 인원 (N명)
        g_workers = sorted_workers[i * ppl_per_group : (i+1) * ppl_per_group]
        
        # 출력 형식: 부스/부스/부스 이름1 이름2 이름3 이름4
        booth_label = "/".join(g_booths)
        worker_str = " ".join(sorted(g_workers, key=get_priority))
        final_lines.append(f"{booth_label} {worker_str}")
        
    return None, (final_lines, resters)

# --- 4. 화면 출력 및 데이터 갱신 ---
if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
    error, result = generate_rotation()
    if error:
        st.error(error)
    else:
        st.session_state.display_lines = result[0]
        # 포인트 업데이트: 쉰 사람은 0으로 초기화(다음 휴식 순번의 마지막이 됨)
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'display_lines' in st.session_state:
    st.subheader("📍 현재 근무 배치 현황")
    for line in st.session_state.display_lines:
        st.markdown(f"#### `{line}`")
