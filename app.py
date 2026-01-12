import streamlit as st
import math

# 1. 초기 설정 및 페이지 구성
st.set_page_config(page_title="현장 근무 마스터", layout="centered")
st.title("📋 지능형 부스 순환 시스템")

# 2. 데이터 저장소 (세션 상태 유지)
if 'shift_count' not in st.session_state:
    st.session_state.shift_count = 0

# --- 3. 사이드바: 설정 및 최소화된 이름 입력 ---
with st.sidebar:
    st.header("⚙️ 운영 설정")
    mode = st.radio("🔄 운영 모드", ["정규 4교대", "밀어내기 (1명 휴식)"])
    all_in_mode = st.toggle("🚀 전부 투입 (휴식 없음)", value=False)
    
    st.divider()
    # [핵심] 이름 입력 칸 최소화: 텍스트 영역 하나로 관리
    st.subheader("👤 근무자 명단 편집")
    default_names = "A, B, C, D, E, F, G, H, I, J, K, L"
    raw_names = st.text_area("쉼표(,)로 구분하여 입력하세요:", value=default_names, height=100)
    current_names = [n.strip() for n in raw_names.split(",") if n.strip()]

    st.divider()
    st.subheader("📍 운영 부스 선택")
    BOOTHS_MASTER = ["감독", "자동"] + [str(i) for i in range(1, 29)]
    selected_booths = []
    for b in BOOTHS_MASTER:
        # 감독/자동은 기본 선택되도록 유도
        is_default = b in ["감독", "자동", "1", "2", "3", "4", "5", "6", "7"]
        if st.checkbox(b, value=is_default, key=f"bth_{b}"):
            selected_booths.append(b)

# --- 4. 배정 로직: 이름 고정, 부스 라벨 순환 (감독/자동 우선) ---
def get_final_schedule(current_mode, count, names, booths, is_all_in):
    # [규칙] 감독/자동이 선택되었다면 항상 부스 풀의 맨 앞으로 정렬
    important = [b for b in ["감독", "자동"] if b in booths]
    others = [b for b in booths if b not in ["감독", "자동"]]
    fixed_booth_pool = important + others
    
    lines = []
    
    if "4교대" in current_mode:
        # 4명씩 조별로 부스 레이블 회전
        for i in range(0, len(names), 4):
            group = names[i:i+4]
            # 휴식 인덱스 결정 (전부 투입 시 -1로 처리하여 휴식 없음)
            rest_idx = -1 if is_all_in else (count % 4)
            
            # 각 조에 할당될 부스 (4교대는 조당 3개, 전부 투입 시 4개)
            b_count = 4 if is_all_in else 3
            g_booths_base = fixed_booth_pool[:b_count]
            fixed_booth_pool = fixed_booth_pool[b_count:]
            while len(g_booths_base) < b_count: g_booths_base.append("X")
            
            # 부스 레이블 순환
            offset = count % len(g_booths_base)
            rolled_booths = g_booths_base[offset:] + g_booths_base[:offset]
            
            # 매핑 (이름은 고정, 부스 레이블만 덮어씌움)
            mapping = []
            b_ptr = 0
            for j in range(len(group)):
                if j == rest_idx:
                    mapping.append("---") # 휴식자는 레이블 대신 대시 표시
                else:
                    if b_ptr < len(rolled_booths):
                        mapping.append(rolled_booths[b_ptr])
                        b_ptr += 1
            
            lines.append(f"🔸 {'/'.join(mapping)} | {' '.join(group)}")
            
    else: # 밀어내기
        rest_idx = -1 if is_all_in else (count % len(names))
        
        # 전체 부스 레이블 순환
        b_offset = count % len(fixed_booth_pool) if fixed_booth_pool else 0
        rolled_booths = fixed_booth_pool[b_offset:] + fixed_booth_pool[:b_offset]
        
        mapping = []
        b_ptr = 0
        for i in range(len(names)):
            if i == rest_idx:
                mapping.append("---")
            else:
                if b_ptr < len(rolled_booths):
                    mapping.append(rolled_booths[b_ptr])
                    b_ptr += 1
        
        lines.append(f"🔸 {'/'.join(mapping)} | {' '.join(names)}")
        
    return lines

# --- 5. 화면 출력 및 카톡 보고 ---
st.subheader("📊 근무 진단 및 실행")
num_p = len(current_names)
rec_b = (num_p // 4 * 3 + (num_p % 4)) if "4교대" in mode else (num_p - 1)
if all_in_mode: rec_b = num_p

st.info(f"💡 **현재 상태:** 인원 {num_p}명 | 적정 부스 **{rec_b}개**")



if st.button("🔄 다음 교대 (부스 이름표 밀어내기)", use_container_width=True):
    st.session_state.shift_count += 1
    st.rerun()

st.divider()
st.subheader("📍 현재 근무 배치 현황")
results = get_final_schedule(mode, st.session_state.shift_count, current_names, selected_booths, all_in_mode)

for res in results:
    st.markdown(f"#### `{res}`")

st.divider()
st.subheader("📱 카카오톡 보고용")
kakao_text = f"📢 [{mode} 현황]\n" + "\n".join(results)
st.text_area("내용 복사:", value=kakao_text, height=150)
