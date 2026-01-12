import streamlit as st

# 모바일 브라우저 최적화 설정
st.set_page_config(page_title="현장 근무 관리", layout="centered")

# --- 스타일 설정 ---
st.markdown("""
    <style>
    .booth-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .booth-header {
        font-size: 16px;
        font-weight: bold;
        color: #ff4b4b;
        margin-bottom: 8px;
    }
    .staff-text {
        font-size: 18px;
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 (데이터 보존) ---
if 'master_schedule' not in st.session_state:
    st.session_state.master_schedule = {
        "08:50-10:10": "감독/자동/1: A, B, D, E\n2/19/22: C, H, G, F\n24: I(d조)",
        "10:10-11:00": "자동/감독: A, B, E\n1/2: C, D, F\n22/19: H, G, I\n3/24: 조조, 기동, 기동"
    }

st.title("📱 현장 가변 근무표")

# --- 1. [설정 메뉴] 고정 근무자 및 부스 편집 ---
with st.sidebar:
    st.header("⚙️ 근무 설정 편집")
    st.info("여기서 수정한 내용은 아래 화면에 즉시 반영됩니다.")
    
    # 시간대 추가/삭제
    new_slot = st.text_input("새 시간대 이름 (예: 13:30-16:00)")
    if st.button("시간대 추가"):
        if new_slot and new_slot not in st.session_state.master_schedule:
            st.session_state.master_schedule[new_slot] = ""
            st.rerun()

    st.divider()
    
    # 현재 선택된 시간대의 부스/인원 편집
    st.subheader("📝 현재 시간대 상세 편집")
    edit_slot = st.selectbox("편집할 시간대", list(st.session_state.master_schedule.keys()))
    
    content = st.text_area(
        "부스 및 인원 입력 (형식: 부스번호: 인원1, 인원2)",
        value=st.session_state.master_schedule[edit_slot],
        height=200,
        help="한 줄에 '부스번호: 이름, 이름' 형식으로 입력하세요."
    )
    st.session_state.master_schedule[edit_slot] = content

# --- 2. [메인 화면] 근무 현황 시각화 ---
st.subheader("⏳ 실시간 배치 현황")
display_slot = st.selectbox("보기 선택", list(st.session_state.master_schedule.keys()), key="display")

# 데이터 파싱 및 출력
raw_data = st.session_state.master_schedule[display_slot]
if raw_data:
    lines = raw_data.strip().split('\n')
    for line in lines:
        if ':' in line:
            booth, staff = line.split(':', 1)
            st.markdown(f"""
                <div class="booth-card">
                    <div class="booth-header">📍 부스 {booth.strip()}</div>
                    <div class="staff-text">👤 {staff.strip()}</div>
                </div>
            """, unsafe_allow_html=True)
else:
    st.warning("입력된 근무 데이터가 없습니다. 왼쪽 설정 메뉴에서 입력해주세요.")

st.divider()
st.caption("팁: 모바일에서는 왼쪽 상단 '>' 화살표를 눌러 설정 메뉴를 여세요.")
