import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="공항 근무 유령 인원 계산기", layout="centered")
st.title("👻 유령 인원 기반 근무 배분 시스템")
st.caption("잉여 인원에게 동일한 휴식을 보장하기 위해 '유령 슬롯'을 생성합니다.")

# 2. 입력 설정
col_in1, col_in2 = st.columns(2)
with col_in1:
    num_p = st.number_input("🔢 실 근무자 수 (명)", min_value=1, max_value=100, value=14)
with col_in2:
    shift_mode = st.selectbox("🔄 교대 방식 선택", [2, 3, 4, 5], index=3) # 기본 5교대

st.divider()

# 3. 유령 인원 및 조 편성 로직
# 조의 개수 계산 (올림 처리)
num_groups = math.ceil(num_p / shift_mode)
# 전체 슬롯 개수
total_slots = num_groups * shift_mode
# 필요한 유령 인원 수
num_ghosts = total_slots - num_p

# 4. 시각적 조 편성 및 부스 계산
st.subheader(f"📊 {shift_mode}교대 조 편성 현황 (유령 {num_ghosts}명 포함)")

booth_count = 0
for i in range(num_groups):
    with st.expander(f"📍 제 {i+1}조 배분 현황", expanded=True):
        cols = st.columns(shift_mode)
        group_start = i * shift_mode
        
        for j in range(shift_mode):
            slot_idx = group_start + j
            with cols[j]:
                if j == 0: # 첫 번째 칸은 휴식 고정 (시각적 편의)
                    st.error("휴식")
                elif slot_idx < num_p:
                    st.success(f"근무자")
                    booth_count += 1
                else:
                    st.warning("유령")
                    # 유령은 근무자가 아니므로 부스 카운트에서 제외

# 5. 최종 결과 안내
st.divider()
st.subheader("🏁 최종 운영 결과")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("실제 근무자", f"{num_p}명")
with c2:
    st.metric("생성된 유령", f"{num_ghosts}명")
with c3:
    st.metric("오픈 부스", f"{booth_count}개")

st.info(f"""
**💡 관리자 가이드 (감독/자동 부스 포함)**
* 전체 **{num_groups}개 조**가 운영되며, 각 조당 1명씩 총 **{num_groups}명**의 휴식 자리가 보장됩니다.
* 유령 인원은 실제 사람이 아니므로, 유령이 '근무' 위치에 배정된 부스는 열지 않습니다.
* 유령이 '휴식' 위치에 배정되는 교대 타임에는 해당 조의 실 근무자 4명이 모두 근무에 투입됩니다. 
* 결과적으로 **감독/자동을 포함하여 총 {booth_count}개의 부스**를 운영하시면 됩니다.
""")
