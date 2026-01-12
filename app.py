import streamlit as st

# 모바일 최적화 설정
st.set_page_config(page_title="현장 자동 교대 시스템", layout="centered")

# --- 1. 데이터 저장 및 초기화 ---
if 'staff_db' not in st.session_state:
    # 고정 (A~O), 지원 (지원1~10)
    db = {}
    for name in [chr(i) for i in range(ord('A'), ord('P'))]:
        db[name] = {"type": "고정", "current_group": None, "work_units": 0}
    for name in [f"지원{i}" for i in range(1, 11)]:
        db[name] = {"type": "지원", "current_group": None, "work_units": 0}
    st.session_state.staff_db = db

# 부스 리스트
ALL_BOOTHS = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# --- 2. 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 실시간 현장 설정")
    
    # [인원 및 부스 선택]
    selected_staff = []
    st.subheader("👥 인원 선택")
    c1 = st.columns(3)
    for i, name in enumerate(st.session_state.staff_db.keys()):
        with c1[i % 3 if i < 15 else (i-15) % 3]:
            if st.checkbox(name, value=(i < 12), key=f"s_{name}"):
                selected_staff.append(name)

    st.subheader("🏢 부스 선택")
    chosen_booths = []
    c2 = st.columns(3)
    for i, b_name in enumerate(ALL_BOOTHS):
        with c2[i % 3]:
            if st.checkbox(b_name, value=(i < 9), key=f"b_{b_name}"):
                chosen_booths.append(b_name)

    st.divider()
    
    # [핵심 규칙 설정]
    st.subheader("📏 그룹화 규칙")
    booth_n = st.radio("부스 묶음 단위 선택", [2, 3, 5], index=1, help="2개 묶음 시 3명, 3개 묶음 시 4명 배정")
    
    # 전부 투입 모드 체크
    all_in_mode = st.toggle("전부 투입 (인원 = 부스)", value=(len(selected_staff) == len(chosen_booths)))

# --- 3. 로직 함수 ---
def generate_optimized_schedule():
    if not selected_staff or not chosen_booths: return None, None
    
    # 1. 부스 그룹화 (선택한 단위 N개씩)
    station_groups = []
    for i in range(0, len(chosen_booths), booth_n):
        station_groups.append(chosen_booths[i : i + booth_n])
    
    num_groups = len(station_groups)
    ppl_per_group = booth_n + 1 if not all_in_mode else booth_n
    
    # 2. 인원 배정 (이동 최소화: 기존 그룹 유지 우선)
    # 인원을 '고정 알파벳순 -> 지원 순'으로 정렬
    sorted_staff = sorted(selected_staff, key=lambda x: (0 if st.session_state.staff_db[x]['type'] == '고정' else 1, x))
    
    group_assignments = {i: [] for i in range(num_groups)}
    remaining_staff = sorted_staff.copy()
    
    # Step A: 기존에 이 그룹(번호)에 속했던 사람 먼저 채우기
    for idx in range(num_groups):
        prev_members = [p for p in remaining_staff if st.session_state.staff_db[p].get('current_group') == idx]
        fill_num = min(len(prev_members), ppl_per_group)
        group_assignments[idx].extend(prev_members[:fill_num])
        for p in prev_members[:fill_num]: remaining_staff.remove(p)
            
    # Step B: 남은 자리에 새 인원 채우기
    for idx in range(num_groups):
        while len(group_assignments[idx]) < ppl_per_group and remaining_staff:
            p = remaining_workers = remaining_staff.pop(0)
            group_assignments[idx].append(p)
            st.session_state.staff_db[p]['current_group'] = idx

    # 3. 그룹 내 휴식자 결정 (가장 오래 일한 사람)
    final_res = {}
    current_resters = []
    
    for idx, members in group_assignments.items():
        g_name = "/".join(station_groups[idx])
        if all_in_mode:
            final_res[g_name] = sorted(members)
        else:
            # 그룹 멤버 중 work_units(연속근무)가 가장 높은 1명이 휴식
            m_sorted = sorted(members, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
            rester = m_sorted[0]
            workers = [m for m in members if m != rester]
            final_res[g_name] = sorted(workers) # 근무자는 알파벳순 표기
            current_resters.append(rester)
            
    return final_res, current_resters

# --- 4. 메인 화면 ---
st.title("⚡ 그룹 순환형 자동 교대기")

if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
    res, rests = generate_optimized_schedule()
    if res:
        st.session_state.last_res = res
        st.session_state.last_rests = rests
        # 데이터 업데이트
        for p in selected_staff:
            if p in rests:
                st.session_state.staff_db[p]['work_units'] = 0
            else:
                st.session_state.staff_db[p]['work_units'] += 1
    else:
        st.error("인원과 부스 설정을 확인하세요.")

if 'last_res' in st.session_state:
    st.subheader("📍 현재 근무 배치")
    for group_name, workers in st.session_state.last_res.items():
        st.markdown(f"**{group_name}** &nbsp;&nbsp; `{' '.join(workers)}`")
    
    st.divider()
    st.markdown(f"☕ **현재 휴식:** <span style='color:#007bff; font-weight:bold; font-size:18px;'>{' '.join(st.session_state.last_rests) if st.session_state.last_rests else '없음'}</span>", unsafe_allow_html=True)
