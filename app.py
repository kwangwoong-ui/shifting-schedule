import streamlit as st
import math

# 모바일 최적화 설정
st.set_page_config(page_title="현장 근무 스마트 관리", layout="centered")

# --- 1. 데이터 저장 및 초기화 ---
if 'staff_db' not in st.session_state:
    # 고정 근무자 A~O (15명)
    reg_names = [chr(i) for i in range(ord('A'), ord('P'))]
    # 지원 부서 1~10 (10명)
    sup_names = [f"지원{i}" for i in range(1, 11)]
    
    db = {}
    for name in reg_names: db[name] = {"type": "고정", "last_group": None, "work_units": 0}
    for name in sup_names: db[name] = {"type": "지원", "last_group": None, "work_units": 0}
    st.session_state.staff_db = db

# 부스 마스터 순서 (감독, 자동, 1~28)
ALL_BOOTHS = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# --- 2. 사이드바: 설정창 ---
with st.sidebar:
    st.header("⚙️ 현장 실시간 설정")
    
    # [인원 선택]
    st.subheader("👥 인원 선택")
    selected_staff = []
    st.write("**고정 근무자 (A~O)**")
    c1 = st.columns(3)
    for i, name in enumerate([chr(i) for i in range(ord('A'), ord('P'))]):
        with c1[i % 3]:
            if st.checkbox(name, value=(i < 12), key=f"r_{name}"): selected_staff.append(name)
            
    st.write("**지원 부서 (1~10)**")
    c2 = st.columns(2)
    for i, name in enumerate([f"지원{i}" for i in range(1, 11)]):
        with c2[i % 2]:
            if st.checkbox(name, value=False, key=f"s_{name}"): selected_staff.append(name)

    st.divider()

    # [부스 선택]
    st.subheader("🏢 부스 선택")
    chosen_booths = []
    c3 = st.columns(3)
    for i, b_name in enumerate(ALL_BOOTHS):
        with c3[i % 3]:
            if st.checkbox(b_name, value=(i < 9), key=f"b_{b_name}"): chosen_booths.append(b_name)

    st.divider()
    
    # [그룹 규칙]
    st.subheader("📏 그룹화 규칙")
    booth_n = st.radio("부스 묶음 단위", [2, 3, 5], index=1)
    all_in_mode = st.toggle("전부 투입 (휴식 없음)", value=False)
    
    # 그룹당 필요한 인원 계산 (N+1 법칙)
    ppl_per_group = booth_n if all_in_mode else (booth_n + 1)

# --- 3. 에러 진단 및 배치 로직 ---
def run_rotation_with_diag():
    # 기본 체크
    if not chosen_booths:
        return "❌ 운영할 **부스**를 최소 하나 이상 선택해주세요.", None
    if not selected_staff:
        return "❌ 투입할 **근무자**를 최소 하나 이상 선택해주세요.", None

    # 필요한 그룹 수와 인원 계산
    num_groups = math.ceil(len(chosen_booths) / booth_n)
    total_needed = num_groups * ppl_per_group
    
    # [오류 진단 1] 인원 부족 체크
    if len(selected_staff) < total_needed:
        diff = total_needed - len(selected_staff)
        return f"⚠️ **인원 부족:** 현재 설정된 부스를 운영하려면 **{total_needed}명**이 필요합니다. (현재 {len(selected_staff)}명 / **{diff}명 부족**)", None

    # [오류 진단 2] 부스 배치 정합성 체크 (나머지 부스 발생 시)
    # 예: 3개씩 묶는데 부스가 4개면 2그룹이 생기고 총 8명이 필요함을 알림
    
    # 실제 배치 로직 시작
    station_groups = [chosen_booths[i:i + booth_n] for i in range(0, len(chosen_booths), booth_n)]
    workers_pool = sorted(selected_staff, key=lambda x: (0 if st.session_state.staff_db[x]['type'] == '고정' else 1, x if st.session_state.staff_db[x]['type'] == '고정' else int(x.replace("지원", ""))))
    
    group_assignments = {i: [] for i in range(num_groups)}
    remaining = workers_pool.copy()
    
    # 위치 유지 우선 배치
    for idx in range(num_groups):
        prev = [p for p in remaining if st.session_state.staff_db[p].get('last_group') == idx]
        fill = min(len(prev), ppl_per_group)
        group_assignments[idx].extend(prev[:fill])
        for p in prev[:fill]: remaining.remove(p)
            
    # 빈자리 우선순위 배치
    for idx in range(num_groups):
        while len(group_assignments[idx]) < ppl_per_group and remaining:
            p = remaining.pop(0)
            group_assignments[idx].append(p)
            st.session_state.staff_db[p]['last_group'] = idx

    final_res = []
    resters = []
    for idx, members in group_assignments.items():
        g_name = "/".join(station_groups[idx])
        if all_in_mode:
            final_res.append(f"{g_name} {' '.join(sorted(members))}")
        else:
            sorted_m = sorted(members, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
            rester = sorted_m[0]
            current_workers = sorted([m for m in members if m != rester])
            final_res.append(f"{g_name} {' '.join(current_workers)}")
            resters.append(rester)
            
    return None, (final_res, resters)

# --- 4. 메인 화면 ---
st.title("📋 현장 근무 통합 관리")

if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
    error_msg, result = run_rotation_with_diag()
    if error_msg:
        st.error(error_msg) # 정확한 이유를 빨간 박스로 출력
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
    
    if st.session_state.display_rests:
        st.divider()
        st.markdown(f"☕ **현재 휴식:** <span style='color:#007bff; font-weight:bold; font-size:18px;'>{' '.join(st.session_state.display_rests)}</span>", unsafe_allow_html=True)
