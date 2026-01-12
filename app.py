import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="공항 근무 관리 시스템", layout="wide")
st.title("📋 조별 위치 고정 부스 순환 시스템")

# 2. 데이터 초기화
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0
if 'staff_count' not in st.session_state:
    st.session_state.staff_count = 12

if 'staff_registry' not in st.session_state:
    # A~Z 슬롯 40명 생성
    st.session_state.staff_registry = {
        chr(65+i) if i < 26 else f"Z{i-25}": {"name": chr(65+i), "group": ["a", "b", "c", "d"][i % 4]} 
        for i in range(40)
    }

# --- 3. 사이드바: 인원수 설정 및 알파벳 슬롯별 이름/조 설정 ---
with st.sidebar:
    st.header("⚙️ 인원 및 부스 설정")
    # 1. 인원수 설정 (알파벳 슬롯 자동 생성)
    st.session_state.staff_count = st.number_input("투입 인원수 입력", min_value=1, max_value=40, value=st.session_state.staff_count)
    
    st.divider()
    # 2. 알파벳 슬롯별 상세 설정 (이름 / 조)
    st.subheader("👤 근무자 설정 (성함 / 조)")
    with st.container():
        for i in range(st.session_state.staff_count):
            uid = chr(65+i) if i < 26 else f"Z{i-25}"
            with st.expander(f"슬롯 {uid}", expanded=False):
                st.session_state.staff_registry[uid]["name"] = st.text_input(f"성함 ({uid})", value=st.session_state.staff_registry[uid]["name"], key=f"nm_{uid}")
                st.session_state.staff_registry[uid]["group"] = st.selectbox(f"소속 조", ["a", "b", "c", "d"], 
                                                                           index=["a", "b", "c", "d"].index(st.session_state.staff_registry[uid]["group"]), 
                                                                           key=f"gr_{uid}")

    st.divider()
    # 3. 운영 모드 및 부스 선택
    mode = st.radio("🔄 운영 모드 선택", ["정규 4교대 (조별 운영)", "밀어내기 (전체 순환)"])
    
    st.subheader("📍 운영 부스 체크")
    BOOTHS_MASTER = ["감독", "자동", "1", "19", "20", "25", "26", "2", "3", "4", "5", "6"]
    selected_booths = [b for b in BOOTHS_MASTER if st.checkbox(f"부스 {b}", value=True, key=f"bth_{b}")]

# --- 4. 상단 안내: 모드별 부스 가이드 ---
num_p = st.session_state.staff_count
st.subheader(f"📊 실시간 부스 가이드 (투입: {num_p}명)")

b_4shift = (num_p // 4 * 3) + (num_p % 4)
b_push = max(0, num_p - 1)
b_allin = num_p

c1, c2, c3 = st.columns(3)
c1.metric("4교대 운영 시", f"{b_4shift}개", f"잔여 {num_p % 4}명 포함" if num_p % 4 > 0 else "정배열")
c2.metric("밀어내기 운영 시", f"{b_push}개")
c3.metric("전부 투입 시", f"{b_allin}개")

# --- 5. 배정 로직: 조별 위치 고정 및 부스 이름표 슬라이딩 ---
def generate_schedule():
    count = st.session_state.shift_count
    # 현재 설정된 인원 명단 호출
    active_staff = [st.session_state.staff_registry[chr(65+i) if i < 26 else f"Z{i-25}"] for i in range(num_p)]
    booth_pool = selected_booths.copy()
    lines = []

    if "4교대" in mode:
        # 조별(a, b, c, d)로 인원 분류
        groups = {"a": [], "b": [], "c": [], "d": []}
        for s in active_staff:
            groups[s["group"]].append(s["name"])
        
        # 최대 행 수만큼 반복
        max_rows = max(len(groups[k]) for k in groups)
        for r in range(max_rows):
            # 한 행 구성 (a-b-c-d 순서 절대 고정)
            row_names = [groups[k][r] if r < len(groups[k]) else None for k in ["a", "b", "c", "d"]]
            row_valid = [n for n in row_names if n is not None]
            n = len(row_valid)
            
            # 부스 레이블 준비 (4명당 1명 휴식 기준)
            b_count = n if n < 4 else (n - 1)
            g_booths = booth_pool[:b_count]
            booth_pool = booth_pool[b_count:]
            while len(g_booths) < b_count: g_booths.append("X")
            
            # [핵심] 부스 레이블 슬라이딩: 맨 앞은 휴식(/)으로 시작
            # count에 따라 / 위치가 이동하며 인원들과 매칭됨
            labels = ([None] if n >= 4 else []) + g_booths
            offset = count % len(labels)
            rolled_labels = labels[offset:] + labels[:offset]
            
            label_parts = [f"{b}" if b is not None else "" for b in rolled_labels]
            lines.append(f"` / {' / '.join(label_parts)}` &nbsp;&nbsp;&nbsp; **{' '.join(row_valid)}**")

    else: # 밀어내기
        # 전체 인원을 a->b->c->d 순서대로 일렬 정렬 (a가 가장 왼쪽)
        sorted_staff = sorted(active_staff, key=lambda x: (x["group"], x["name"]))
        names = [s["name"] for s in sorted_staff]
        n = len(names)
        
        # 부스 레이블 준비 (1명 휴식)
        g_booths = booth_pool[:n-1]
        while len(g_booths) < (n-1): g_booths.append("X")
        
        # 휴식(/) 포함 레이블 슬라이딩
        labels = [None] + g_booths
        offset = count % len(labels)
        rolled_labels = labels[offset:] + labels[:offset]
        
        label_parts = [f"{b}" if b is not None else "" for b in rolled_labels]
        lines.append(f"` / {' / '.join(label_parts)}` &nbsp;&nbsp;&nbsp; **{' '.join(names)}**")

    return lines

# --- 6. 실행 및 출력 ---


if st.button("🔄 다음 교대 진행 (부스 번호 슬라이딩)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader("📍 현재 근무 배치 현황 (이름 고정)")
results = generate_schedule()
for res in results:
    st.markdown(f"#### {res}")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = "📢 [공항 근무 배치 현황]\n" + "\n".join([r.replace("&nbsp;", "").replace("**", "").replace("`", "") for r in results])
st.text_area("텍스트 복사:", value=kakao_text, height=150)
