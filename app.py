import streamlit as st
import math

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="현장 근무 스마트 관리", layout="centered")
st.title("📋 지능형 근무 배정 시스템")

# 2. 마스터 데이터 정의 (순서 절대 고정)
REG_NAMES = [chr(i) for i in range(ord('A'), ord('K'))] # A~J (10명)
SUP_NAMES = [f"지원{i}" for i in range(1, 11)]         # 지원1~10 (10명)
BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 11)] + [str(i) for i in range(15, 29)]

# 3. 데이터 저장소 및 수동 조작용 세션 초기화
if 'staff_db' not in st.session_state:
    db = {}
    for name in REG_NAMES: db[name] = {"type": "고정", "work_units": 0}
    for name in SUP_NAMES: db[name] = {"type": "지원", "work_units": 0}
    st.session_state.staff_db = db

if 'final_result_text' not in st.session_state:
    st.session_state.final_result_text = ""

# --- 4. 사이드바: 설정 및 인원 체크 ---
with st.sidebar:
    st.header("⚙️ 실시간 현장 설정")
    
    # [교대수 및 모드 설정]
    n_shift = st.selectbox("교대수(N) 선택", [2, 3, 4, 5, 6], index=2) # 4교대 기본
    all_in_mode = st.toggle("전부 투입 모드", value=False)
    
    # 규칙: N교대 시 부스 그룹은 N-1개, 인원은 N명
    group_size = n_shift if all_in_mode else (n_shift - 1)
    ppl_per_group = n_shift
    
    st.divider()

    # [인원 선택] - A~J, 지원1~10 순서 고정
    selected_staff = []
    st.subheader("👥 인원 선택")
    for name in REG_NAMES:
        if st.checkbox(name, value=True, key=f"r_{name}"): selected_staff.append(name)
    for name in SUP_NAMES:
        if st.checkbox(name, value=False, key=f"s_{name}"): selected_staff.append(name)

    st.divider()

    # [부스 선택] - 번호 순서 고정
    selected_booths = []
    st.subheader("📍 부스 선택")
    for b_name in BOOTHS_MASTER:
        if st.checkbox(b_name, value=(b_name in BOOTHS_MASTER[:9]), key=f"b_{b_name}"):
            selected_booths.append(b_name)

# --- 5. 현황 진단 및 미리보기 가이드 ---
st.subheader("📊 근무 투입 현황 진단")
num_staff = len(selected_staff)
if num_staff > 0:
    # 현재 인원으로 만들 수 있는 최대 그룹 수와 필요한 부스 계산
    possible_groups = num_staff // n_shift
    extra_people = num_staff % n_shift
    required_booths = possible_groups * (n_shift - 1)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("투입 가능 인원", f"{num_staff}명")
        st.write(f"✅ **{n_shift}교대** 기준: **{possible_groups}개 조** 편성 가능")
    with col2:
        st.metric("적정 부스 개수", f"{required_booths}개")
        st.write(f"현재 선택된 부스: **{len(selected_booths)}개**")

    # 안내 문구 로직
    if extra_people > 0:
        st.warning(f"⚠️ **인원 남음:** 현재 {extra_people}명이 어느 조에도 속하지 못합니다. 인원을 추가하거나 '전부 투입'을 고려하세요.")
    if len(selected_booths) > required_booths:
        st.error(f"🚨 **부스 과다:** 인원 대비 부스가 {len(selected_booths) - required_booths}개 많습니다. 일부 부스는 'X'로 표시됩니다.")
    elif len(selected_booths) < required_booths:
        st.info(f"ℹ️ **부스 부족:** 인원 대비 부스가 {required_booths - len(selected_booths)}개 부족합니다. 인원을 줄이거나 부스를 더 선택하세요.")
    else:
        st.success("✨ 인원과 부스 비율이 완벽하게 일치합니다!")
else:
    st.info("사이드바에서 근무자를 선택하면 배정 분석이 시작됩니다.")

# --- 6. 배정 로직 ---
def run_assignment():
    if not selected_staff or not selected_booths: return [], []
    
    # 1. 휴식 순번 결정 (포인트 높은 순)
    sorted_for_rest = sorted(selected_staff, key=lambda x: st.session_state.staff_db[x]['work_units'], reverse=True)
    num_rest = 0 if all_in_mode else (len(selected_staff) // n_shift)
    resters = sorted_for_rest[:num_rest]
    working_pool = [p for p in selected_staff if p not in resters]
    
    # 2. 배치 우선순위 (고정 A-J -> 지원 1-10)
    def priority(name):
        if name in REG_NAMES: return (0, name)
        return (1, int(name.replace("지원", "")))
    
    sorted_workers = sorted(working_pool, key=priority)
    sorted_active_booths = [b for b in BOOTHS_MASTER if b in selected_booths]
    
    num_groups = math.ceil(len(sorted_workers) / n_shift)
    res_lines = []
    
    for i in range(num_groups):
        # 부스 그룹화 및 유령 부스(X)
        g_booths = sorted_active_booths[i * (n_shift-1) : (i+1) * (n_shift-1)]
        while len(g_booths) < (n_shift - 1): g_booths.append("X")
        
        # 인원 배정 (N명)
        g_workers = sorted_workers[i * n_shift : (i+1) * n_shift]
        
        line = f"{'/'.join(g_booths)} {' '.join(sorted(g_workers, key=priority))}"
        res_lines.append(line)
        
    return res_lines, resters

# --- 7. 메인 실행 및 수동 조작 ---
st.divider()
if st.button("🔄 근무 스케줄 자동 생성", use_container_width=True):
    lines, rests = run_assignment()
    if lines:
        st.session_state.final_result_text = "\n".join(lines)
        # 휴식 데이터 업데이트 (쉰 사람은 0으로 초기화하여 다음 순번 마지막으로 이동)
        for p in selected_staff:
            if p in rests: st.session_state.staff_db[p]['work_units'] = 0
            else: st.session_state.staff_db[p]['work_units'] += 1

# [수동 조작 및 결과 확인]
if st.session_state.final_result_text:
    st.subheader("📍 근무 배치 결과 (수정 가능)")
    # 수동 편집이 가능하도록 text_area 사용
    edited_result = st.text_area("결과가 마음에 들지 않으면 여기서 직접 수정하세요:", 
                                 value=st.session_state.final_result_text, 
                                 height=250)
    st.session_state.final_result_text = edited_result
    
    st.success("위 텍스트 박스에서 수동으로 이름을 바꾸거나 부스를 조정할 수 있습니다.")
