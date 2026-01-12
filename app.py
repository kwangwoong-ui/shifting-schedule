import streamlit as st
import math

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="현장 근무 관리 시스템", layout="centered")
st.title("📋 근무 배정 현황")

# 2. 고정 리스트 정의 (순서 강제 고정)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('P'))] # A~O (15명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10 (10명)
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 데이터 저장소 초기화
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "last_group": None}
    for name in SUP_NAMES: db[name] = {"type": "지원", "last_group": None}
    st.session_state.staff_db = db

# --- 4. 사이드바 (순서대로 출력) ---
with st.sidebar:
    st.header("⚙️ 설정창")
    
    # [교대수 설정]
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    # 규칙: N교대 시 부스 그룹 크기는 N-1, 배정 인원은 N명
    group_size = n_shift - 1
    ppl_per_group = n_shift
    
    st.divider()

    # [인원 선택] - A~O 순서 고정
    selected_staff = []
    st.subheader("👥 고정 근무자 (A~O)")
    c1 = st.columns(3)
    for i, name in enumerate(REG_NAMES):
        with c1[i % 3]:
            if st.checkbox(name, value=(i < 12), key=f"reg_{name}"):
                selected_staff.append(name)
                
    # [지원부서 선택] - 지원1~10 순서 고정
    st.subheader("🏢 지원 부서 (1~10)")
    c2 = st.columns(2)
    for i, name in enumerate(SUP_NAMES):
        with c2[i % 2]:
            if st.checkbox(name, value=False, key=f"sup_{name}"):
                selected_staff.append(name)

    st.divider()

    # [부스 선택] - 감독~28번 순서 고정
    st.subheader("📍 부스 선택")
    selected_booths = []
    c3 = st.columns(3)
    for i, b_name in enumerate(BOOTHS_MASTER):
        with c3[i % 3]:
            if st.checkbox(b_name, value=(i < 6), key=f"bth_{b_name}"):
                selected_booths.append(b_name)

# --- 5. 배정 로직 ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 부스와 근무자를 선택해주세요.", None

    # 부스 그룹화 (선택된 부스들을 마스터 순서대로 정렬 후 N-1개씩 묶음)
    sorted_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    station_groups = [sorted_booths[i : i + group_size] for i in range(0, len(sorted_booths), group_size)]
    
    num_groups = len(station_groups)
    total_needed = num_groups * ppl_per_group
    
    # 인원 부족 체크
    if len(selected_staff) < total_needed:
        return f"⚠️ 인원 부족: {total_needed}명이 필요하지만 현재 {len(selected_staff)}명입니다.", None

    # 인원 우선순위 정렬 (고정 A~O -> 지원 1~10)
    # 지원부서는 숫자로 정렬되도록 처리
    def get_sort_key(name):
        if name in REG_NAMES: return (0, name)
        return (1, int(name.replace("지원", "")))
    
    pool = sorted(selected_staff, key=get_sort_key)
    
    # 그룹 배정
    assignments = {i: [] for i in range(num_groups)}
    remaining = pool.copy()
    
    # [이동 최소화] 기존에 이 그룹번호에 있던 사람 우선 배정
    for i in range(num_groups):
        prev = [p for p in remaining if st.session_state.staff_db[p].get('last_group') == i]
        fill = min(len(prev), ppl_per_group)
        assignments[i].extend(prev[:fill])
        for p in prev[:fill]: remaining.remove(p)
    
    # [나머지 채우기]
    for i in range(num_groups):
        while len(assignments[i]) < ppl_per_group and remaining:
            p = remaining.pop(0)
            assignments[i].append(p)
            st.session_state.staff_db[p]['last_group'] = i

    # 결과 텍스트 생성 (부스그룹 이름들 + 인원 N명)
    result_lines = []
    for i in range(num_groups):
        booth_path = "/".join(station_groups[i])
        # 그룹 내 인원도 보기 좋게 정렬 (고정 우선)
        group_members = sorted(assignments[i], key=get_sort_key)
        result_lines.append(f"{booth_path} {' '.join(group_members)}")
        
    return None, result_lines

# --- 6. 메인 화면 출력 ---
if st.button("🔄 근무 스케줄 갱신 / 생성", use_container_width=True):
    error, results = generate_schedule()
    if error:
        st.error(error)
    else:
        st.session_state.final_display = results

if 'final_display' in st.session_state:
    st.subheader("📍 현재 근무 배치")
    # 관리자님이 원하신 형식: 부스이름 근무자1 근무자2 근무자3 근무자4
    for line in st.session_state.final_display:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    st.caption("※ 이 화면에는 해당 그룹의 근무자와 휴식자가 모두 포함되어 있습니다.")
