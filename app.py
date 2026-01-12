import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="현장 근무 관리 마스터", layout="centered")
st.title("📋 조별 소속 관리 및 부스 진단 시스템")

# 2. 데이터 저장소
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0
if 'name_map' not in st.session_state:
    # 초기 성함 및 조 설정 (A~L)
    st.session_state.name_map = {chr(i): {"name": chr(i), "group": "A"} for i in range(ord('A'), ord('M'))}
    # 지원 부서 초기 설정
    for i in range(1, 11):
        st.session_state.name_map[f"S{i}"] = {"name": f"지원{i}", "group": "B"}

# --- 3. 사이드바: 조 설정 및 성함 수정 ---
with st.sidebar:
    st.header("👥 근무자 및 조 편성")
    with st.expander("✅ 근무자 정보 수정 (이름/조)"):
        for uid, info in st.session_state.name_map.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                new_name = st.text_input(f"슬롯 {uid}", value=info["name"], key=f"nm_{uid}")
            with col2:
                new_group = st.selectbox(f"조", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(info["group"]), key=f"gr_{uid}")
            st.session_state.name_map[uid] = {"name": new_name, "group": new_group}

    st.divider()
    st.header("⚙️ 운영 설정")
    mode = st.radio("🔄 운영 모드 선택", ["정규 4교대 (조별 순환)", "밀어내기 (전체 순환)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)
    
    st.divider()
    # 투입 인원 및 부스 선택
    selected_uids = []
    st.subheader("👥 투입 인원 선택")
    for uid, info in st.session_state.name_map.items():
        if st.checkbox(f"[{info['group']}조] {info['name']}", value=(uid in [chr(j) for j in range(ord('A'), ord('I'))]), key=f"chk_{uid}"):
            selected_uids.append(uid)

    st.divider()
    st.subheader("📍 운영 부스 선택")
    selected_booths = []
    BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 29)]
    for b in BOOTHS_MASTER:
        if st.checkbox(b, value=(b in BOOTHS_MASTER[:7]), key=f"bth_{b}"):
            selected_booths.append(b)

# --- 4. 정밀 진단: 모드별 유령부스 계산 ---
num_p = len(selected_uids)
if num_p > 0:
    st.subheader("📊 모드별 부스 운영 진단")
    
    # 각 모드별 필요 부스 계산
    req_4shift = (num_p // 4 * 3) + (num_p % 4)
    req_push = max(0, num_p - 1)
    req_allin = num_p
    
    sel_b = len(selected_booths)
    
    # 진단 데이터 구성
    diag_data = [
        {"모드": "정규 4교대", "필요": req_4shift, "현재": sel_b, "유령(X)": max(0, req_4shift - sel_b)},
        {"모드": "밀어내기", "필요": req_push, "현재": sel_b, "유령(X)": max(0, req_push - sel_b)},
        {"모드": "전부 투입", "필요": req_allin, "현재": sel_b, "유령(X)": max(0, req_allin - sel_b)}
    ]
    st.table(diag_data) #

# --- 5. 배정 로직: 조 소속 유지 및 부스 순환 ---
def get_final_lines(current_mode, count, uids, booths, is_all_in):
    # 부스 풀 준비 (감독/자동 우선)
    important = [b for b in ["감독", "자동"] if b in booths]
    others = [b for b in booths if b not in ["감독", "자동"]]
    booth_pool = important + others
    
    lines = []
    
    if "4교대" in current_mode:
        # 조별로 묶기 (A, B, C, D조 순서대로)
        groups = {"A": [], "B": [], "C": [], "D": []}
        for u in uids:
            groups[st.session_state.name_map[u]["group"]].append(u)
        
        for g_label, g_uids in groups.items():
            if not g_uids: continue
            
            actual_n = len(g_uids)
            rest_idx = -1 if is_all_in else (count % actual_n)
            
            b_count = actual_n if is_all_in else (actual_n - 1)
            g_booths = booth_pool[:b_count]
            booth_pool = booth_pool[b_count:]
            while len(g_booths) < b_count: g_booths.append("X")
            
            offset = count % max(1, len(g_booths))
            rolled_booths = g_booths[offset:] + g_booths[:offset]
            
            mapping = []
            b_ptr = 0
            for j in range(len(g_uids)):
                name = st.session_state.name_map[g_uids[j]]["name"]
                if j == rest_idx: mapping.append(f"--- {name}")
                else:
                    b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                    mapping.append(f"{b_name} {name}")
                    b_ptr += 1
            lines.append(f"[{g_label}조] | " + " | ".join(mapping))
            
    else: # 밀어내기: 전체 인원 순서 고려
        rest_idx = -1 if is_all_in else (count % len(uids))
        b_offset = count % len(booth_pool) if booth_pool else 0
        rolled_booths = booth_pool[b_offset:] + booth_pool[:b_offset]
        
        mapping = []
        b_ptr = 0
        for i in range(len(uids)):
            name = st.session_state.name_map[uids[i]]["name"]
            if i == rest_idx: mapping.append(f"--- {name}")
            else:
                b_name = rolled_booths[b_ptr] if b_ptr < len(rolled_booths) else "X"
                mapping.append(f"{b_name} {name}")
                b_ptr += 1
        lines.append("🔸 " + " | ".join(mapping))
        
    return lines

# --- 6. 실행 및 출력 ---
if st.button("🔄 근무 시간 갱신 (부스 이름표 밀어내기)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader("📍 현재 근무 배치 현황")
if num_p > 0:
    results = get_final_lines(mode, st.session_state.shift_count, selected_uids, selected_booths, all_in_mode)
    for res in results:
        st.markdown(f"#### `{res}`")

    st.divider()
    st.subheader("📱 카카오톡 보고용")
    kakao_text = f"📢 [{mode} 현황]\n" + "\n".join(results)
    st.text_area("복사하기:", value=kakao_text, height=150)
