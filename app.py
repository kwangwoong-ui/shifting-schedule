import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="wide")
st.title("📋 조별 위치 고정 및 부스 순환 시스템")

# 2. 데이터 초기화
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0
if 'staff_count' not in st.session_state:
    st.session_state.staff_count = 12
if 'staff_registry' not in st.session_state:
    st.session_state.staff_registry = {
        chr(i): {"name": chr(i), "group": ["a", "b", "c", "d"][(i-65)%4]} 
        for i in range(65, 65 + 40) # 넉넉히 슬롯 생성
    }

# --- 3. 사이드바: 설정창 (UI 간소화) ---
with st.sidebar:
    st.header("⚙️ 기본 설정")
    new_count = st.number_input("투입 인원수", min_value=1, max_value=40, value=st.session_state.staff_count)
    st.session_state.staff_count = new_count
    
    st.divider()
    mode = st.radio("🔄 운영 모드", ["정규 4교대", "밀어내기 (1명 휴식)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)

    st.divider()
    st.subheader("👤 근무자 정보 (성함 / 조)")
    with st.expander("명단 및 조 수정", expanded=True):
        for i in range(65, 65 + st.session_state.staff_count):
            uid = chr(i) if i < 91 else f"Z{i-90}"
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.staff_registry[uid]["name"] = st.text_input(f"슬롯 {uid}", value=st.session_state.staff_registry[uid]["name"], key=f"nm_{uid}")
            with col2:
                st.session_state.staff_registry[uid]["group"] = st.selectbox(f"조", ["a", "b", "c", "d"], 
                                                                           index=["a", "b", "c", "d"].index(st.session_state.staff_registry[uid]["group"]), 
                                                                           key=f"gr_{uid}")

    st.divider()
    st.subheader("📍 부스 선택")
    BOOTHS_MASTER = ["자동", "감독", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    selected_booths = [b for b in BOOTHS_MASTER if st.checkbox(b, value=True, key=f"bth_{b}")]

# --- 4. 상단 안내: 부스 개수 및 잔여 인원 가이드 ---
num_p = st.session_state.staff_count
st.subheader(f"📊 실시간 운영 진단 (현재 {num_p}명)")

req_4 = (num_p // 4 * 3) + (num_p % 4)
req_push = max(0, num_p - 1)
req_allin = num_p

c1, c2, c3 = st.columns(3)
c1.metric("4교대 부스", f"{req_4}개", f"잔여 {num_p % 4}명" if num_p % 4 > 0 else "완전 배분")
c2.metric("밀어내기 부스", f"{req_push}개")
c3.metric("전부 투입 부스", f"{req_allin}개")

# --- 5. 배정 로직: ABCD 위치 고정 및 이름표 롤링 ---
def generate_schedule():
    count = st.session_state.shift_count
    # 현재 설정된 인원 리스트 (A, B, C... 순서 고정)
    active_staff = [st.session_state.staff_registry[chr(65+i)] for i in range(num_p)]
    booth_pool = selected_booths.copy()
    lines = []

    if "4교대" in mode:
        # 조별(a, b, c, d)로 인원 분류
        groups = {"a": [], "b": [], "c": [], "d": []}
        for s in active_staff:
            groups[s["group"]].append(s["name"])
        
        max_rows = max(len(groups[k]) for k in groups)
        for r in range(max_rows):
            # 한 줄(Row) 구성: [a조원, b조원, c조원, d조원] - 순서 절대 고정
            row_members = [groups[k][r] if r < len(groups[k]) else None for k in ["a", "b", "c", "d"]]
            row_valid = [m for m in row_members if m is not None]
            
            n = len(row_valid)
            # 휴식 인덱스 결정 (count에 따라 a->b->c->d 순서로 휴식)
            rest_idx = -1 if (all_in_mode or n < 4) else (count % n)
            
            # 부스 레이블 준비 및 롤링
            b_needed = n if rest_idx == -1 else (n - 1)
            g_booths = booth_pool[:b_needed]
            booth_pool = booth_pool[b_needed:]
            while len(g_booths) < b_needed: g_booths.append("X")
            
            offset = count % max(1, len(g_booths))
            rolled_booths = g_booths[offset:] + g_booths[:offset]
            
            # 출력 조립 (ABCD 이름을 그대로 두되, 부스 라벨만 매칭)
            display_parts = []
            b_ptr = 0
            for j in range(len(row_valid)):
                if j == rest_idx:
                    display_parts.append(f"--- {row_valid[j]}")
                else:
                    b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                    display_parts.append(f"{b_name} {row_valid[j]}")
                    b_ptr += 1
            lines.append(" | ".join(display_parts))

    else: # 밀어내기 모드
        # a->b->c->d 조별 순서대로 정렬하여 일렬 배치
        sorted_staff = sorted(active_staff, key=lambda x: x["group"])
        names = [s["name"] for s in sorted_staff]
        n = len(names)
        
        rest_idx = -1 if all_in_mode else (count % n)
        
        b_needed = n if all_in_mode else (n - 1)
        g_booths = booth_pool[:b_needed]
        while len(g_booths) < b_needed: g_booths.append("X")
        
        offset = count % max(1, len(g_booths))
        rolled_booths = g_booths[offset:] + g_booths[:offset]
        
        display_parts = []
        b_ptr = 0
        for i in range(n):
            if i == rest_idx:
                display_parts.append(f"--- {names[i]}")
            else:
                b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                display_parts.append(f"{b_name} {names[i]}")
                b_ptr += 1
        lines.append(" | ".join(display_parts))

    return lines

# --- 6. 실행 및 출력 ---
if st.button("🔄 다음 교대 진행 (부스 라벨 순환)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader(f"📍 현재 근무 배치 현황 ({mode})")
results = generate_schedule()
for res in results:
    st.markdown(f"#### `🔸 {res}`")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 현황]\n" + "\n".join([f"🔸 {r}" for r in results])
st.text_area("텍스트 복사:", value=kakao_text, height=150)
