import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="centered")
st.title("📋 지능형 근무 배정 현황")

# 2. 마스터 데이터 정의 (순서 절대 고정)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10 (10명)
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 데이터 저장소 초기화 (휴식 순번 추적용 포인트)
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "work_units": 0, "last_group": None}
    for name in SUP_NAMES: db[name] = {"type": "지원", "work_units": 0, "last_group": None}
    st.session_state.staff_db = db

# --- 4. 사이드바: 완벽 정렬 (모바일 꼬임 방지) ---
with st.sidebar:
    st.header("⚙️ 설정 및 인원 선택")
    
    # [교대수 설정]
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2)
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    # N교대 규칙: 부스 그룹 크기는 N-1, 배정 인원은 N명
    group_size = n_shift - 1
    ppl_per_group = n_shift
    
    st.divider()

    # [인원 선택] - A~J 순서 강제 고정
    selected_staff = []
    st.subheader("👥 고정 근무자 (A~J)")
    for name in REG_NAMES:
        if st.checkbox(name, value=True, key=f"sidebar_r_{name}"):
            selected_staff.append(name)
            
    st.subheader("🏢 지원 부서 (1~10)")
    for name in SUP_NAMES:
        if st.checkbox(name, value=False, key=f"sidebar_s_{name}"):
            selected_staff.append(name)

    st.divider()

    # [부스 선택] - 번호 순서 강제 고정
    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"sidebar_b_{b_name}"):
            selected_booths.append(b_name)

# --- 5. 배정 로직 (N+1 전원 표시 및 휴식 순번 보장) ---
def generate_schedule():
    if not selected_booths or not selected_staff:
        return "❌ 부스와 근무자를 선택해주세요.", None

    # 1. 인원 정렬 (고정 A~J -> 지원 1~10)
    def get_priority_key(name):
        if name in REG_NAMES: return (0, name)
        return (1, int(name.replace("지원", "")))
    
    # 전체 선택된 인원을 우선순위대로 정렬
    pool = sorted(selected_staff, key=get_priority_key)
    
    # 2. 그룹 나누기 (N명씩 한 그룹)
    num_groups = math.ceil(len(pool) / ppl_per_group)
    sorted_active_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    
    final_lines = []
    current_resters = []
    
    for i in range(num_groups):
        # 이번 그룹 인원 (N명)
        g_staff = pool[i * ppl_per_group : (i+1) * ppl_per_group]
        actual_count = len(g_staff)
        
        # [휴식자 선정] 그룹 내에서 가장 오래 일한(work_units가 높은) 사람 1명
        # 전부 투입 모드가 아닐 때만 휴식자 선정
        rester = None
        if not all_in_mode and actual_count > 0:
            rester = sorted(g_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)[0]
            current_resters.append(rester)

        # [부스 배정]
        # N교대면 부스는 N-1개가 필요함 (전부 투입 시는 N개 필요)
        needed_b_count = actual_count if all_in_mode else (actual_count - 1)
        needed_b_count = max(0, needed_b_count)
        
        g_booths = sorted_active_booths[i * group_size : i * group_size + needed_b_count]
        
        # [유령 부스(X) 처리] 부스가 부족하면 X로 채움
        while len(g_booths) < (ppl_per_group - 1 if not all_in_mode else ppl_per_group):
            g_booths.append("X")
            
        # [출력 형식 생성] 부스/부스/부스 + 그룹 전원(N명) 이름
        booth_label = "/".join(g_booths)
        # 이름은 항상 경력순(알파벳순) 정렬 표시
        sorted_g_staff = sorted(g_staff, key=get_priority_key)
        worker_str = " ".join(sorted_g_staff)
        
        final_lines.append(f"{booth_label} {worker_str}")
        
    return None, (final_lines, current_resters)

# --- 6. 화면 출력 및 진단 ---
st.divider()
col_btn, col_diag = st.columns([1, 1])

with col_btn:
    if st.button("🔄 근무 스케줄 갱신", use_container_width=True):
        error, result = generate_schedule()
        if error:
            st.error(error)
        else:
            st.session_state.last_display = result[0]
            # 휴식 데이터 업데이트
            for p in selected_staff:
                if p in result[1]: 
                    st.session_state.staff_db[p]['work_units'] = 0 # 쉰 사람 리셋
                else: 
                    st.session_state.staff_db[p]['work_units'] += 1 # 일한 사람 누적

with col_diag:
    # 인원 부족/남음 실시간 진단 문구
    total_needed = math.ceil(len(selected_booths) / (n_shift-1)) * n_shift if not all_in_mode else len(selected_booths)
    if len(selected_staff) < total_needed:
        st.warning(f"⚠️ 인원 부족 (필요:{total_needed}/현재:{len(selected_staff)})")
    elif len(selected_staff) > total_needed:
        st.info(f"💡 인원 남음 ({len(selected_staff) - total_needed}명 여유)")

if 'last_display' in st.session_state:
    st.subheader("📍 현재 근무 배치")
    for line in st.session_state.last_display:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    # 수동 조작을 위한 텍스트 영역 (실수 방지 및 되돌리기용)
    st.subheader("✍️ 수동 수정 및 복사")
    edited_text = st.text_area("배치표를 직접 수정하거나 복사하세요:", 
                               value="\n".join(st.session_state.last_display), 
                               height=200)
