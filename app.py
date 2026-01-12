import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 시스템", layout="wide")
st.title("📋 조별 위치 고정 및 부스 순환 배정표")

# 2. 데이터 초기화
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0
if 'staff_count' not in st.session_state:
    st.session_state.staff_count = 12

if 'staff_registry' not in st.session_state:
    # 40명까지 미리 슬롯 확보
    st.session_state.staff_registry = {
        chr(65+i) if i < 26 else f"Z{i-25}": {"name": chr(65+i), "group": ["a", "b", "c", "d"][i % 4]} 
        for i in range(40)
    }

# --- 3. 사이드바: 설정 및 인원별 성함/조 설정 ---
with st.sidebar:
    st.header("⚙️ 기본 설정")
    # 인원수 설정
    st.session_state.staff_count = st.number_input("투입 인원수 설정", min_value=1, max_value=40, value=st.session_state.staff_count)
    
    st.divider()
    mode = st.radio("🔄 운영 모드 선택", ["정규 4교대", "밀어내기 (1명 휴식)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)

    st.divider()
    st.subheader("👤 인원별 상세 설정 (성함 / 조)")
    # 인원수에 맞춰 알파벳 슬롯 노출
    for i in range(st.session_state.staff_count):
        uid = chr(65+i) if i < 26 else f"Z{i-25}"
        with st.expander(f"슬롯 {uid} 설정", expanded=False):
            st.session_state.staff_registry[uid]["name"] = st.text_input(f"성함 ({uid})", value=st.session_state.staff_registry[uid]["name"], key=f"nm_{uid}")
            st.session_state.staff_registry[uid]["group"] = st.selectbox(f"소속 조", ["a", "b", "c", "d"], 
                                                                       index=["a", "b", "c", "d"].index(st.session_state.staff_registry[uid]["group"]), 
                                                                       key=f"gr_{uid}")

    st.divider()
    st.subheader("📍 운영 부스 선택")
    BOOTHS_MASTER = ["감독", "자동", "1", "2", "3", "4", "5", "6", "17", "18", "19", "20", "22", "24", "25"]
    selected_booths = [b for b in BOOTHS_MASTER if st.checkbox(f"부스 {b}", value=True, key=f"bth_{b}")]

# --- 4. 상단 안내: 진단 문구 ---
num_p = st.session_state.staff_count
st.subheader(f"📊 실시간 운영 진단 (현재 {num_p}명 투입)")

req_4 = (num_p // 4 * 3) + (num_p % 4)
req_push = max(0, num_p - 1)
req_allin = num_p

c1, c2, c3 = st.columns(3)
c1.metric("4교대 부스", f"{req_4}개", f"잔여 {num_p % 4}명" if num_p % 4 > 0 else "완전 배분")
c2.metric("밀어내기 부스", f"{req_push}개")
c3.metric("전부 투입 부스", f"{req_allin}개")

# --- 5. 배정 로직: [부스/부스/부스] 이름 이름 이름 이름 ---
def generate_schedule():
    count = st.session_state.shift_count
    # 현재 설정된 인원 명단
    active_staff = [st.session_state.staff_registry[chr(65+i) if i < 26 else f"Z{i-25}"] for i in range(num_p)]
    booth_pool = selected_booths.copy()
    lines = []

    if "4교대" in mode:
        # a, b, c, d 조별 인원 분류
        groups = {"a": [], "b": [], "c": [], "d": []}
        for s in active_staff:
            groups[s["group"]].append(s["name"])
        
        # 최대 줄 수 계산
        max_rows = max(len(groups[k]) for k in groups)
        for r in range(max_rows):
            # 조별 멤버 추출 (순서: a, b, c, d)
            row_members = [groups[k][r] if r < len(groups[k]) else None for k in ["a", "b", "c", "d"]]
            row_valid = [m for m in row_members if m is not None]
            
            n = len(row_valid)
            # 휴식 인덱스 (A->B->C->D 순서)
            rest_idx = -1 if (all_in_mode or n < 4) else (count % n)
            
            # 부스 레이블 준비
            b_needed = n if rest_idx == -1 else (n - 1)
            g_booths = booth_pool[:b_needed]
            booth_pool = booth_pool[b_needed:]
            while len(g_booths) < b_needed: g_booths.append("X")
            
            # 부스 레이블 순환
            offset = count % max(1, len(g_booths))
            rolled_booths = g_booths[offset:] + g_booths[:offset]
            
            # 최종 줄 조립: [부스/부스/부스] 이름1 이름2 이름3 이름4
            booth_labels = []
            b_ptr = 0
            for j in range(len(row_valid)):
                if j == rest_idx:
                    booth_labels.append("휴식")
                else:
                    b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                    booth_labels.append(b_name)
                    b_ptr += 1
            
            lines.append(f"`{' / '.join(booth_labels)}` &nbsp;&nbsp;&nbsp; **{' '.join(row_valid)}**")

    else: # 밀어내기 모드
        # a->b->c->d 조별 순서대로 정렬
        sorted_staff = sorted(active_staff, key=lambda x: x["group"])
        names = [s["name"] for s in sorted_staff]
        n = len(names)
        rest_idx = -1 if all_in_mode else (count % n)
        
        b_needed = n if all_in_mode else (n - 1)
        g_booths = booth_pool[:b_needed]
        while len(g_booths) < b_needed: g_booths.append("X")
        
        offset = count % max(1, len(g_booths))
        rolled_booths = g_booths[offset:] + g_booths[:offset]
        
        booth_labels = []
        b_ptr = 0
        for i in range(n):
            if i == rest_idx: booth_labels.append("휴식")
            else:
                b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                booth_labels.append(b_name)
                b_ptr += 1
        lines.append(f"`{' / '.join(booth_labels)}` &nbsp;&nbsp;&nbsp; **{' '.join(names)}**")

    return lines

# --- 6. 실행 및 출력 ---
if st.button("🔄 다음 교대 진행 (부스 라벨 롤링)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader(f"📍 현재 근무 배치 현황 ({mode})")
results = generate_schedule()
for res in results:
    st.markdown(f"#### {res}")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 현황]\n" + "\n".join([r.replace("&nbsp;", "").replace("**", "") for r in results])
st.text_area("텍스트 복사:", value=kakao_text, height=150)
