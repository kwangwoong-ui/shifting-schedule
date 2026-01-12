import streamlit as st

# 모바일 최적화 설정
st.set_page_config(page_title="현장 근무 스마트 관리", layout="centered")

# --- 1. 데이터 저장 및 초기화 ---
if 'staff_db' not in st.session_state:
    # 고정 근무자 (A~O)
    reg_names = [chr(i) for i in range(ord('A'), ord('P'))] 
    # 지원 근무자 (지원1 ~ 지원10)
    sup_names = [f"지원{i}" for i in range(1, 11)]
    
    db = {}
    for name in reg_names: db[name] = {"type": "고정", "last_pos": None, "work_units": 0}
    for name in sup_names: db[name] = {"type": "지원", "last_pos": None, "work_units": 0}
    st.session_state.staff_db = db

# 전체 부스 마스터 순서
ALL_BOOTHS = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# --- 2. 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 실시간 현장 설정")
    
    # [인원 선택]
    st.subheader("👥 인원 선택 (딸깍)")
    selected_staff = []
    st.write("**고정 근무자 (A~O)**")
    c1 = st.columns(3)
    regs = [n for n, idx in st.session_state.staff_db.items() if idx["type"] == "고정"]
    for i, name in enumerate(regs):
        with c1[i % 3]:
            if st.checkbox(name, value=(i < 9), key=f"r_{name}"): selected_staff.append(name)
            
    st.write("**지원 부서 (지원1~10)**")
    c2 = st.columns(2)
    sups = [n for n, idx in st.session_state.staff_db.items() if idx["type"] == "지원"]
    for i, name in enumerate(sups):
        with c2[i % 2]:
            if st.checkbox(name, value=False, key=f"s_{name}"): selected_staff.append(name)

    st.divider()

    # [부스 선택]
    st.subheader("🏢 부스 선택")
    chosen_booths = []
    b_cols = st.columns(3)
    for i, b_name in enumerate(ALL_BOOTHS):
        with b_cols[i % 3]:
            if st.checkbox(b_name, value=(i < 9), key=f"b_{b_name}"): chosen_booths.append(b_name)

    st.divider()
    n_shift = st.number_input("교대수 (N)", min_value=1, value=4)
    ppl_per_group = st.slider("한 그룹당 근무 인원", 1, 4, 3)

# --- 3. 로직 함수 ---
def run_rotation():
    if not selected_staff or not chosen_booths: return None, None

    # 1. 부스 그룹화
    stations = []
    for i in range(0, len(chosen_booths), ppl_per_group):
        group = chosen_booths[i : i + ppl_per_group]
        stations.append("/".join(group))

    # 2. 휴식 순번 계산 (오래 일한 순서 = 포인트 높은 순서)
    # 이 정렬 방식이 관리자님이 말씀하신 '순번 유지'를 보장합니다.
    sorted_by_work = sorted(selected_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    
    num_rest = len(selected_staff) // n_shift if n_shift > 1 else 0
    resters = sorted_by_work[:num_rest] # 가장 오래 일한 사람이 우선 휴식
    workers = [p for p in selected_staff if p not in resters]

    # 3. 배치 우선순위 (고정 A-O 순 -> 지원부서 순)
    w_reg = sorted([p for p in workers if st.session_state.staff_db[p]["type"] == "고정"])
    w_sup = sorted([p for p in workers if st.session_state.staff_db[p]["type"] == "지원"], 
                   key=lambda x: int(x.replace("지원", "")))
    priority_workers = w_reg + w_sup

    # 4. 배치 실행
    assignment = {s: [] for s in stations}
    assigned_set = set()

    for s in stations:
        for p in workers:
            if st.session_state.staff_db[p]["last_pos"] == s and len(assignment[s]) < ppl_per_group:
                assignment[s].append(p)
                assigned_set.add(p)

    for s in stations:
        while len(assignment[s]) < ppl_per_group:
            candidates = [p for p in priority_workers if p not in assigned_set]
            if not candidates: break
            next_p = candidates[0]
            assignment[s].append(next_p)
            assigned_set.add(next_p)
            st.session_state.staff_db[next_p]["last_pos"] = s

    return assignment, resters

# --- 4. 메인 화면 ---
st.title("⚡ 안정적 휴식 보장 시스템")

# [핵심: 휴식 대기열 시각화]
st.info("💡 아래 명단에서 **앞에 있는 사람**이 다음 타임 휴식 1순위입니다.")
wait_list = sorted(selected_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
st.write(f"**휴식 대기 순번:** {' → '.join(wait_list)}")

if st.button("🚀 이번 타임 근무표 생성", use_container_width=True):
    res, rests = run_rotation()
    if res:
        st.session_state.current_res = res
        st.session_state.current_rests = rests
        for p in selected_staff:
            if p in rests:
                st.session_state.staff_db[p]['work_units'] = 0 # 쉰 사람은 0점으로 맨 뒤로 이동
            else:
                st.session_state.staff_db[p]['work_units'] += 1 # 일한 사람은 점수 증가
    else:
        st.error("설정을 확인하세요.")

if 'current_res' in st.session_state:
    st.subheader("📍 현재 배치 결과")
    for station, staff_list in st.session_state.current_res.items():
        st.markdown(f"**{station}** &nbsp;&nbsp; `{' '.join(staff_list)}`")
    
    st.divider()
    st.markdown(f"☕ **현재 휴식:** <span style='color:#007bff; font-weight:bold; font-size:18px;'>{' '.join(st.session_state.current_rests) if st.session_state.current_rests else '없음'}</span>", unsafe_allow_html=True)
