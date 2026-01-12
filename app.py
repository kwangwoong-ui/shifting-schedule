import streamlit as st

# 모바일 최적화 설정
st.set_page_config(page_title="현장 자동 교대 시스템", layout="centered")

# --- 1. 데이터 저장소 초기화 ---
if 'staff_db' not in st.session_state:
    # 고정 근무자 (알파벳 순)
    reg_names = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
    # 지원 근무자 (후순위 배치용)
    sup_names = ["주간1", "주간2", "기동", "보근", "조조", "의무", "야간"]
    
    db = {}
    for name in reg_names: db[name] = {"type": "고정", "last_pos": None, "work_units": 0}
    for name in sup_names: db[name] = {"type": "지원", "last_pos": None, "work_units": 0}
    st.session_state.staff_db = db

# 부스 마스터 리스트 (감독 ~ 28번)
ALL_BOOTHS = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# --- 2. 사이드바: 딸깍 설정창 ---
with st.sidebar:
    st.header("⚙️ 현장 설정 (딸깍)")
    
    # [인원 선택]
    st.subheader("👥 인원 선택")
    selected_reg = []
    selected_sup = []
    
    st.write("**고정 근무자**")
    c1 = st.columns(3)
    for i, (name, info) in enumerate(st.session_state.staff_db.items()):
        if info["type"] == "고정":
            with c1[len(selected_reg) % 3]:
                if st.checkbox(name, value=True, key=f"reg_{name}"): selected_reg.append(name)
    
    st.write("**지원 근무자**")
    c2 = st.columns(3)
    for i, (name, info) in enumerate(st.session_state.staff_db.items()):
        if info["type"] == "지원":
            with c2[len(selected_sup) % 3]:
                if st.checkbox(name, value=False, key=f"sup_{name}"): selected_sup.append(name)

    st.divider()
    
    # [부스 선택]
    st.subheader("🏢 운영 부스 선택")
    active_booths = []
    b_cols = st.columns(3)
    for i, b_name in enumerate(ALL_BOOTHS):
        with b_cols[i % 3]:
            if st.checkbox(b_name, value=(i < 6), key=f"b_{b_name}"): active_booths.append(b_name)

    st.divider()
    
    # [그룹핑 및 N교대]
    group_input = st.text_area("🔗 부스 묶기 (슬래시/구분)", 
                                value="감독/자동/1\n2/19/22\n24/22", 
                                help="부스명/부스명 형식으로 입력")
    n_shift = st.number_input("교대수 (N)", min_value=1, value=3)

# --- 3. 자동 배치 알고리즘 ---
def run_rotation():
    # 1. 부스 그룹화 (입력된 순서대로 정렬됨)
    groups = group_input.strip().split('\n')
    stations = []
    used = set()
    for g in groups:
        parts = [p.strip() for p in g.split('/') if p.strip() in active_booths]
        if parts:
            stations.append("/".join(parts))
            for p in parts: used.add(p)
    for b in active_booths:
        if b not in used: stations.append(b)

    # 2. 휴식자 선정 (형평성 기준: 누적 근무 많은 사람 우선)
    all_active = selected_reg + selected_sup
    num_rest = len(all_active) // n_shift if n_shift > 1 else 0
    
    # 일한 순서대로 정렬
    sorted_staff = sorted(all_active, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    resters = sorted_staff[:num_rest]
    workers = [p for p in all_active if p not in resters]

    # 3. 근무자 우선순위 정렬 (고정 알파벳순 -> 지원 알파벳순)
    w_reg = sorted([p for p in workers if st.session_state.staff_db[p]["type"] == "고정"])
    w_sup = sorted([p for p in workers if st.session_state.staff_db[p]["type"] == "지원"])
    priority_workers = w_reg + w_sup

    # 4. 배치 (이전 위치 유지 우선 + 빈자리 채우기)
    assignment = {s: [] for s in stations}
    assigned_staff = set()

    # Step A: 원래 자리 지키기
    for s in stations:
        for p in workers:
            if st.session_state.staff_db[p]["last_pos"] == s and len(assignment[s]) < 3:
                assignment[s].append(p)
                assigned_staff.add(p)

    # Step B: 빈자리 채우기 (고정 우선순위대로 앞 번호 부스부터)
    for s in stations:
        while len(assignment[s]) < 3:
            # 아직 배치 안 된 사람 중 우선순위 높은 사람 추출
            candidates = [p for p in priority_workers if p not in assigned_staff]
            if not candidates: break
            next_p = candidates[0]
            assignment[s].append(next_p)
            assigned_staff.add(next_p)
            st.session_state.staff_db[next_p]["last_pos"] = s

    return assignment, resters

# --- 4. 메인 화면 ---
st.title("⚡ 지능형 자동 교대기")

if st.button("🚀 근무표 자동 생성", use_container_width=True):
    if not (selected_reg + selected_sup) or not active_booths:
        st.error("인원과 부스를 선택해주세요.")
    else:
        res, rests = run_rotation()
        st.session_state.current_res = res
        st.session_state.current_rests = rests
        
        # 데이터 업데이트
        for p in (selected_reg + selected_sup):
            if p in rests:
                st.session_state.staff_db[p]['work_units'] = 0
                st.session_state.staff_db[p]['last_pos'] = "휴식"
            else:
                st.session_state.staff_db[p]['work_units'] += 1

if 'current_res' in st.session_state:
    st.subheader("📍 이번 타임 배치도")
    for station, staff_list in st.session_state.current_res.items():
        # 요청하신 형식: 부스이름 이름 이름 이름
        staff_str = " ".join(staff_list)
        st.markdown(f"**{station}** &nbsp;&nbsp; `{staff_str}`")
    
    st.divider()
    st.write(f"☕ **휴식:** {' '.join(st.session_state.current_rests) if st.session_state.current_rests else '없음'}")
