import streamlit as st
import math

# 모바일 최적화 및 레이아웃 설정
st.set_page_config(page_title="현장 근무 스마트 관리", layout="centered")

# --- 1. 데이터 초기화 및 순서 강제 정의 ---
# 고정 근무자 A~O (15명)
REG_LIST = [chr(i) for i in range(ord('A'), ord('P'))] 
# 지원 부서 1~10 (정렬을 위해 리스트 직접 생성)
SUP_LIST = [f"지원{i}" for i in range(1, 11)]
# 부스 마스터 순서 (감독 -> 자동 -> 1~28)
ALL_BOOTHS = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_LIST: db[name] = {"type": "고정", "last_group": None, "work_units": 0}
    for name in SUP_LIST: db[name] = {"type": "지원", "last_group": None, "work_units": 0}
    st.session_state.staff_db = db

# --- 2. 사이드바: 정렬된 레이아웃 ---
with st.sidebar:
    st.header("⚙️ 실시간 현장 설정")
    
    selected_staff = []
    
    # [인원 선택] - A~O 순서 고정
    st.subheader("👥 고정 근무자 (A~O)")
    reg_cols = st.columns(3)
    for i, name in enumerate(REG_LIST):
        with reg_cols[i % 3]:
            if st.checkbox(name, value=(i < 12), key=f"r_{name}"):
                selected_staff.append(name)
            
    # [지원 부서] - 1~10 순서 고정
    st.subheader("🏢 지원 부서 (1~10)")
    sup_cols = st.columns(2)
    for i, name in enumerate(SUP_LIST):
        with sup_cols[i % 2]:
            if st.checkbox(name, value=False, key=f"s_{name}"):
                selected_staff.append(name)

    st.divider()

    # [부스 선택] - 감독~28번 순서 고정
    st.subheader("📍 운영 부스 선택")
    chosen_booths = []
    booth_cols = st.columns(3)
    for i, b_name in enumerate(ALL_BOOTHS):
        with booth_cols[i % 3]:
            if st.checkbox(b_name, value=(i < 6), key=f"b_{b_name}"):
                chosen_booths.append(b_name)

    st.divider()
    
    # [교대 방식]
    st.subheader("📏 교대수 설정")
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    # 교대 규칙: N교대는 (N-1)개 부스에 N명을 배정함
    booth_n = n_shift - 1
    ppl_per_group = n_shift
    st.info(f"💡 {n_shift}교대: 부스 {booth_n}개당 {ppl_per_group}명 배정")

# --- 3. 로직 함수: 진단 및 배치 ---
def run_rotation():
    if not chosen_booths: return "❌ 부스를 선택해주세요.", None
    if not selected_staff: return "❌ 근무자를 선택해주세요.", None

    num_groups = math.ceil(len(chosen_booths) / booth_n)
    total_needed = num_groups * ppl_per_group
    
    if len(selected_staff) < total_needed:
        return f"⚠️ **인원 부족:** {total_needed}명이 필요합니다. (현재 {len(selected_staff)}명)", None

    # 1. 부스 그룹화 (선택된 순서가 아닌 마스터 리스트 순서로 정렬)
    sorted_chosen_booths = [b for b in ALL_BOOTHS if b in chosen_booths]
    station_groups = [sorted_chosen_booths[i:i + booth_n] for i in range(0, len(sorted_chosen_booths), booth_n)]
    
    # 2. 인원 정렬 (고정 A-O 순 -> 지원 1-10 순)
    workers_pool = sorted(selected_staff, key=lambda x: (
        0 if st.session_state.staff_db[x]['type'] == '고정' else 1, 
        x if st.session_state.staff_db[x]['type'] == '고정' else int(x.replace("지원", ""))
    ))
    
    group_assignments = {i: [] for i in range(len(station_groups))}
    remaining = workers_pool.copy()
    
    # 3. 그룹 배정 (이동 최소화)
    for idx in range(len(station_groups)):
        prev = [p for p in remaining if st.session_state.staff_db[p].get('last_group') == idx]
        fill = min(len(prev), ppl_per_group)
        group_assignments[idx].extend(prev[:fill])
        for p in prev[:fill]: remaining.remove(p)
            
    for idx in range(len(station_groups)):
        while len(group_assignments[idx]) < ppl_per_group and remaining:
            p = remaining.pop(0)
            group_assignments[idx].append(p)
            st.session_state.staff_db[p]['last_group'] = idx

    # 4. 결과 생성 (내부 정렬 포함)
    final_res = []
    all_resters = []
    for idx, members in group_assignments.items():
        g_name = "/".join(station_groups[idx])
        # 그룹 내 휴식자 선정
        sorted_m = sorted(members, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
        rester = sorted_m[0]
        # 근무자 알파벳/숫자 순 정렬 출력
        current_workers = sorted([m for m in members if m != rester], key=lambda x: (
            0 if st.session_state.staff_db[x]['type'] == '고정' else 1,
            x if st.session_state.staff_db[x]['type'] == '고정' else int(x.replace("지원", ""))
        ))
        final_res.append(f"{g_name} {' '.join(current_workers)}")
        all_resters.append(rester)
            
    return None, (final_res, all_resters)

# --- 4. 메인 화면 ---
st.title("📋 현장 근무 통합 관리")

if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
    err, result = run_rotation()
    if err:
        st.error(err)
    else:
        st.session_state.display_res = result[0]
        st.session_state.display_rests = result[1]
        for p in selected_staff:
            if p in result[1]: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

if 'display_res' in st.session_state:
    st.subheader("📍 현재 근무 배치")
    for line in st.session_state.display_res:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    st.caption(f"현재 휴식 중: {', '.join(st.session_state.display_rests)}")
