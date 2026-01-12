import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 2. 마스터 데이터 (순서 절대 고정)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10 (10명)
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 세션 상태 (근무 이력 저장)
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "work_units": 0}
    for name in SUP_NAMES: db[name] = {"type": "지원", "work_units": 0}
    st.session_state.staff_db = db

if 'last_display' not in st.session_state:
    st.session_state.last_display = []

# --- 4. 사이드바: 100% 세로 정렬 (A-J, 지원1-10) ---
with st.sidebar:
    st.header("⚙️ 설정 및 인원 선택")
    
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2) #
    all_in_mode = st.toggle("전부 투입 (휴식 없음)", value=False) #
    
    # N교대 규칙: 부스 그룹 크기는 N-1, 배정 인원은 N명
    group_size = n_shift - 1
    ppl_per_group = n_shift
    
    st.divider()

    # 인원 선택 (모바일 꼬임 방지를 위해 컬럼 없이 한 줄씩 출력)
    selected_staff = []
    st.subheader("👥 고정 근무자 (A~J)")
    for name in REG_NAMES:
        if st.checkbox(name, value=True, key=f"sb_r_{name}"):
            selected_staff.append(name)
            
    st.subheader("🏢 지원 부서 (1~10)")
    for name in SUP_NAMES:
        if st.checkbox(name, value=False, key=f"sb_s_{name}"):
            selected_staff.append(name)

    st.divider()

    # 부스 선택
    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"sb_b_{b_name}"):
            selected_booths.append(b_name)

# --- 5. 배정 로직 (이력 기반 휴식 선정 및 경력순 배치) ---
def generate_rotation():
    if not selected_booths or not selected_staff:
        return "❌ 설정이 부족합니다.", None

    # [중요: 휴식 순번 보장]
    # 연속 근무 시간(work_units)이 가장 높은 사람부터 줄을 세웁니다.
    # 방금 쉰 사람은 0점이 되어 줄의 맨 뒤로 갑니다.
    staff_sorted_by_history = sorted(selected_staff, 
                                     key=lambda x: st.session_state.staff_db[x]['work_units'], 
                                     reverse=True)
    
    # [인원 정렬 가이드 (A-J 우선)]
    def priority_key(name):
        if name in REG_NAMES: return (0, name) # 고정은 알파벳순
        return (1, int(name.replace("지원", ""))) # 지원은 숫자순

    # 그룹 만들기
    num_groups = math.ceil(len(selected_staff) / ppl_per_group)
    sorted_active_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    
    res_lines = []
    current_resters = []
    
    # 전체 인원을 N명씩 묶음 (이미 휴식 이력에 따라 줄이 세워져 있음)
    # 하지만 배치는 경력자가 상위 부스로 가야 하므로, 각 그룹 내에서 재정렬합니다.
    for i in range(num_groups):
        g_staff = staff_sorted_by_history[i * ppl_per_group : (i+1) * ppl_per_group]
        if not g_staff: continue
        
        # 그룹 내 휴식자 선정 (가장 오래 일한 1명)
        if not all_in_mode and len(g_staff) >= ppl_per_group:
            rester = sorted(g_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)[0]
            current_resters.append(rester)
        
        # 부스 배정 (N-1개)
        b_count = (len(g_staff) if all_in_mode else len(g_staff) - 1)
        g_booths = sorted_active_booths[i * group_size : i * group_size + b_count]
        while len(g_booths) < group_size:
            g_booths.append("X") # 부족하면 유령 부스 표시
        
        # 출력 생성 (부스이름 근무자1 근무자2 근무자3...)
        # 이름은 경력순(A-J)으로 정렬하여 표시
        booth_label = "/".join(g_booths)
        display_names = sorted(g_staff, key=priority_key)
        res_lines.append(f"{booth_label} {' '.join(display_names)}")
        
    return None, (res_lines, current_resters)

# --- 6. 화면 출력 및 진단 ---
st.subheader("📊 현재 투입 현황 및 기록")
# 누가 얼마나 연속 근무했는지 시각적으로 보여줌 (관리자 확인용)
with st.expander("👁️ 근무 이력(연속 근무 타임) 확인"):
    for name in selected_staff:
        units = st.session_state.staff_db[name]['work_units']
        st.text(f"{name}: {units}타임 연속 근무 중 {'(다음 휴식 유력)' if units >= 3 else ''}")

if st.button("🔄 근무 스케줄 갱신 (이전 근무 반영)", use_container_width=True):
    error, result = generate_rotation()
    if error:
        st.error(error)
    else:
        st.session_state.last_display = result[0]
        # 이력 업데이트
        for p in selected_staff:
            if p in result[1]: # 쉰 사람은 0으로 리셋
                st.session_state.staff_db[p]['work_units'] = 0
            else: # 일한 사람은 +1
                st.session_state.staff_db[p]['work_units'] += 1

if st.session_state.last_display:
    st.subheader("📍 이번 타임 배치표")
    # 관리자님이 원하신 형식 그대로 출력
    for line in st.session_state.last_display:
        st.markdown(f"#### `{line}`")
    
    st.divider()
    # 수동 수정을 위해 텍스트 박스 제공
    st.subheader("✍️ 결과 복사 및 수동 수정")
    st.text_area("결과를 복사하거나 직접 수정하세요:", value="\n".join(st.session_state.last_display), height=200)
