import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 조별 위치 고정 부스 순환 시스템")

# 2. 데이터 초기화
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0
if 'staff_count' not in st.session_state:
    st.session_state.staff_count = 12 # 기본 12명
if 'staff_registry' not in st.session_state:
    # 초기 데이터 생성
    st.session_state.staff_registry = {
        chr(i): {"name": chr(i), "group": ["a", "b", "c", "d"][(i-65)%4]} 
        for i in range(65, 65 + 12)
    }

# --- 3. 사이드바: 인원수 설정 및 상세 정보 입력 ---
with st.sidebar:
    st.header("⚙️ 전체 인원 설정")
    new_count = st.number_input("투입할 전체 인원수", min_value=1, max_value=40, value=st.session_state.staff_count)
    
    # 인원수 변경 시 레지스트리 갱신
    if new_count != st.session_state.staff_count:
        st.session_state.staff_count = new_count
        # 부족한 슬롯 채우기
        for i in range(65, 65 + new_count):
            uid = chr(i) if i < 91 else f"Z{i-90}"
            if uid not in st.session_state.staff_registry:
                st.session_state.staff_registry[uid] = {"name": uid, "group": "a"}
    
    st.divider()
    st.header("👤 근무자 정보 입력 (성함 / 조)")
    # 사용자가 각 알파벳별로 이름과 a-d조를 설정
    with st.expander("명단 수정하기", expanded=True):
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
    mode = st.radio("🔄 운영 모드", ["정규 4교대 (조별 위치 고정)", "밀어내기 (조별 순서 순환)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)
    
    st.divider()
    st.subheader("📍 부스 선택")
    BOOTHS_MASTER = ["자동", "감독", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    selected_booths = [b for b in BOOTHS_MASTER if st.checkbox(b, value=True, key=f"bth_{b}")]

# --- 4. 안내 문구: 모드별 부스 개수 및 잔여 인원 ---
num_p = st.session_state.staff_count
st.subheader(f"📊 실시간 운영 진단 (투입: {num_p}명)")

req_4 = (num_p // 4 * 3) + (num_p % 4)
req_push = max(0, num_p - 1)
req_allin = num_p

c1, c2, c3 = st.columns(3)
c1.metric("4교대 부스", f"{req_4}개", f"잔여 {num_p % 4}명" if num_p % 4 > 0 else None)
c2.metric("밀어내기 부스", f"{req_push}개")
c3.metric("전부 투입 부스", f"{req_allin}개")

# --- 5. 배정 로직: 조별 위치 엄수 및 부스 이름표 롤링 ---
def generate_display():
    count = st.session_state.shift_count
    # 현재 활성화된 인원 데이터
    active_staff = [st.session_state.staff_registry[chr(i)] for i in range(65, 65 + num_p)]
    booth_pool = selected_booths.copy()
    lines = []

    if "4교대" in mode:
        # [핵심] a, b, c, d 조별로 인원을 모아 격자(Grid) 생성
        groups = {"a": [], "b": [], "c": [], "d": []}
        for s in active_staff:
            groups[s["group"]].append(s["name"])
        
        # 최대 줄 수 계산
        max_rows = max(len(groups[k]) for k in groups)
        for r in range(max_rows):
            # 한 줄 구성 [a_member, b_member, c_member, d_member]
            row_names = [groups[k][r] if r < len(groups[k]) else None for k in ["a", "b", "c", "d"]]
            row_names_valid = [n for n in row_names if n is not None]
            
            actual_n = len(row_names_valid)
            rest_idx = -1 if (all_in_mode or actual_n < 4) else (count % actual_n)
            
            # 부스 레이블 준비 (3개씩)
            b_count = actual_n if rest_idx == -1 else (actual_n - 1)
            g_booths = booth_pool[:b_count]
            booth_pool = booth_pool[b_count:]
            while len(g_booths) < b_count: g_booths.append("X")
            
            # 부스 이름표 롤링 (자동/감독/1 순서 유지)
            offset = count % max(1, len(g_booths))
            rolled_booths = g_booths[offset:] + g_booths[:offset]
            
            # 최종 줄 생성: 자동/감독/1 B C D (A휴식 시)
            working_names = []
            b_ptr = 0
            for j in range(len(row_names_valid)):
                if j == rest_idx: continue
                working_names.append(row_names_valid[j])
            
            lines.append(f"🔸 {'/'.join(rolled_booths)} {' '.join(working_names)}")

    else: # 밀어내기
        # a->b->c->d 순서대로 정렬하여 일렬 배치
        sorted_staff = sorted(active_staff, key=lambda x: x["group"])
        actual_names = [s["name"] for s in sorted_staff]
        
        rest_idx = -1 if all_in_mode else (count % len(actual_names))
        
        b_count = len(actual_names) if all_in_mode else (len(actual_names) - 1)
        g_booths = booth_pool[:b_count]
        while len(g_booths) < b_count: g_booths.append("X")
        
        offset = count % max(1, len(g_booths))
        rolled_booths = g_booths[offset:] + g_booths[:offset]
        
        working_names = [actual_names[i] for i in range(len(actual_names)) if i != rest_idx]
        lines.append(f"🔸 {'/'.join(rolled_booths)} {' '.join(working_names)}")

    return lines

# --- 6. 출력 및 실행 ---
if st.button("🔄 다음 교대 진행 (부스 라벨 순환)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader(f"📍 현재 근무 배치 ({mode})")
results = generate_display()
for res in results:
    st.markdown(f"#### `{res}`")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 현황]\n" + "\n".join(results)
st.text_area("텍스트 복사:", value=kakao_text, height=150)
