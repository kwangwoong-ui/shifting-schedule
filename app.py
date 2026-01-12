import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 지능형 부스 순환 및 조별 관리 시스템")

# 2. 데이터 초기화 (세션 상태)
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0
if 'staff_data' not in st.session_state:
    # A~L까지 기본 12명 설정
    st.session_state.staff_data = {
        chr(i): {"name": chr(i), "group": "A" if i < 71 else ("B" if i < 75 else "C")} 
        for i in range(ord('A'), ord('M'))
    }

# --- 3. 사이드바: 정갈한 인터페이스 (이름 + 조 선택) ---
with st.sidebar:
    st.header("👤 근무자 및 조 설정")
    with st.expander("✅ 명단 및 조 수정 (펼치기/접기)", expanded=False):
        for uid in st.session_state.staff_data.keys():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.staff_data[uid]["name"] = st.text_input(f"슬롯 {uid}", value=st.session_state.staff_data[uid]["name"], key=f"nm_{uid}")
            with col2:
                st.session_state.staff_data[uid]["group"] = st.selectbox(f"조", ["A", "B", "C", "D"], 
                                                                       index=["A", "B", "C", "D"].index(st.session_state.staff_data[uid]["group"]), 
                                                                       key=f"gr_{uid}")

    st.divider()
    st.header("⚙️ 운영 설정")
    mode = st.radio("🔄 운영 모드 선택", ["정규 4교대 (조별 운영)", "밀어내기 (전체 순환)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)
    
    st.divider()
    # 투입 인원 선택
    selected_uids = []
    st.subheader("👥 투입 인원 선택")
    # 조별로 정렬해서 보여줌
    sorted_uids = sorted(st.session_state.staff_data.keys(), key=lambda x: st.session_state.staff_data[x]["group"])
    for uid in sorted_uids:
        info = st.session_state.staff_data[uid]
        if st.checkbox(f"[{info['group']}조] {info['name']}", value=True, key=f"chk_{uid}"):
            selected_uids.append(uid)

    st.divider()
    st.subheader("📍 운영 부스 선택")
    selected_booths = []
    BOOTHS_MASTER = ["감독", "자동", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    for b in BOOTHS_MASTER:
        if st.checkbox(b, value=True, key=f"bth_{b}"):
            selected_booths.append(b)

# --- 4. [요청사항] 실시간 부스 개수 및 잔여 인원 안내 ---
num_p = len(selected_uids)
if num_p > 0:
    st.subheader("📊 부스 운영 가이드")
    
    # 4교대 계산: 4명당 3부스 + 나머지 전원 투입
    groups_4 = num_p // 4
    rem_4 = num_p % 4
    req_4 = (groups_4 * 3) + rem_4
    
    # 밀어내기: 1명 휴식
    req_push = max(0, num_p - 1)
    # 전부 투입
    req_allin = num_p
    
    c1, c2, c3 = st.columns(3)
    c1.metric("4교대 부스", f"{req_4}개", f"({groups_4}개조 + 잔여 {rem_4}명)" if rem_4 > 0 else "완전 배분")
    c2.metric("밀어내기 부스", f"{req_push}개")
    c3.metric("전부 투입 부스", f"{req_allin}개")
    
    current_req = req_allin if all_in_mode else (req_4 if "4교대" in mode else req_push)
    if len(selected_booths) < current_req:
        st.error(f"🚨 부스 부족: 현재 {len(selected_booths)}개 선택됨. (X 유령부스 {current_req - len(selected_booths)}개 발생)")
    else:
        st.success(f"✅ 부스 충분: 현재 {len(selected_booths)}개 선택됨.")

# --- 5. 배정 로직: 조별 우선순위 및 부스 이름표 롤링 ---
def get_final_lines(current_mode, count, uids, booths, is_all_in):
    # 부스 풀 (감독/자동/1 우선순위)
    important = [b for b in ["감독", "자동", "1"] if b in booths]
    others = [b for b in booths if b not in important]
    booth_pool = important + others
    
    # 투입 인원을 조별(A->D)로 정렬 [핵심: 밀어내기 시 조별 위치 유지]
    sorted_staff = sorted(uids, key=lambda x: (st.session_state.staff_data[x]["group"], st.session_state.staff_data[x]["name"]))
    
    lines = []
    
    if "4교대" in current_mode:
        # 조별로 나누어 처리
        groups = {"A": [], "B": [], "C": [], "D": []}
        for u in sorted_staff:
            groups[st.session_state.staff_data[u]["group"]].append(u)
            
        for g_label, g_uids in groups.items():
            if not g_uids: continue
            
            actual_n = len(g_uids)
            # 4명 미만인 경우 전원 투입, 4명 이상인 경우 첫 번째 인덱스부터 순환 휴식
            rest_idx = -1 if (is_all_in or actual_n < 4) else (count % actual_n)
            
            b_count = actual_n if rest_idx == -1 else (actual_n - 1)
            g_booths = booth_pool[:b_count]
            booth_pool = booth_pool[b_count:]
            while len(g_booths) < b_count: g_booths.append("X")
            
            # 부스 이름표 롤링 (감독/자동/1 순환)
            offset = count % max(1, len(g_booths))
            rolled_booths = g_booths[offset:] + g_booths[:offset]
            
            mapping = []
            b_ptr = 0
            for j in range(len(g_uids)):
                name = st.session_state.staff_data[g_uids[j]]["name"]
                if j == rest_idx: mapping.append(f"--- {name}")
                else:
                    b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                    mapping.append(f"{b_name} {name}")
                    b_ptr += 1
            lines.append(f"[{g_label}조] " + " | ".join(mapping))
            
    else: # 밀어내기 모드
        # 전체 인원을 A조~D조 순서대로 정렬하여 배치 (A조가 가장 왼쪽)
        actual_n = len(sorted_staff)
        rest_idx = -1 if is_all_in else (count % actual_n)
        
        b_count = actual_n if rest_idx == -1 else (actual_n - 1)
        rolled_booths = booth_pool[:b_count]
        # 전체 부스 롤링
        offset = count % max(1, len(rolled_booths))
        rolled_booths = rolled_booths[offset:] + rolled_booths[:offset]
        
        mapping = []
        b_ptr = 0
        for i in range(actual_n):
            name = st.session_state.staff_data[sorted_staff[i]]["name"]
            if i == rest_idx: mapping.append(f"--- {name}")
            else:
                b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                mapping.append(f"{b_name} {name}")
                b_ptr += 1
        lines.append("🔸 " + " | ".join(mapping))
        
    return lines

# --- 6. 실행 및 출력 ---
if st.button("🔄 다음 교대 갱신 (부스 롤링)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader("📍 현재 근무 배치 (조별 위치 고정)")
if num_p > 0:
    results = get_final_lines(mode, st.session_state.shift_count, selected_uids, selected_booths, all_in_mode)
    for res in results:
        st.markdown(f"#### `{res}`")

    st.divider()
    st.subheader("📱 카카오톡 보고용")
    kakao_text = f"📢 [{mode} 현황]\n" + "\n".join(results)
    st.text_area("텍스트 복사:", value=kakao_text, height=150)
