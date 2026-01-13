import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="공항 부스 산출기", layout="centered")
st.title("📊 부스 산출기 (잉여 합산 버전)")

# 2. 인원 입력
num_p = st.number_input("🔢 전체 투입 인원수", min_value=1, value=14)

# 3. 행 표기 로직 결정
display_modes = []
if num_p >= 2: display_modes.append(2)
if num_p >= 3: display_modes.append(3)
if num_p >= 4: display_modes.append(4)
if num_p >= 5: display_modes.append(5)
if num_p >= 6: display_modes.append(6)

# 4. 데이터 구성 (강제 줄바꿈 적용)
st.subheader(f"📋 {num_p}명 기준 운영 모드 요약")
table_data = []

# 교대제 데이터 계산
for s in display_modes:
    full_groups = num_p // s
    rem = num_p % s
    reg_booths = full_groups * (s - 1)
    # 잉여 인원 전원 투입 시 합계
    total_booths = reg_booths + rem 
    
    label = "맞교대" if s == 2 else f"{s}교대"
    
    table_data.append({
        "운영 모드": label,
        "정규 조": f"{full_groups}개",
        "오픈 부스\n(감독 자동 포함)": f"{reg_booths}개",
        "잉여 인원": f"{rem}명",
        "잉여 포함\n총 부스": f"{total_booths}개"
    })

# 7명 이상 밀어내기
if num_p >= 7:
    push_val = max(0, num_p - 1)
    table_data.append({
        "운영 모드": "밀어내기", "정규 조": "-", 
        "오픈 부스\n(감독 자동 포함)": f"{push_val}개", "잉여 인원": "-",
        "잉여 포함\n총 부스": f"{push_val}개"
    })

# 전부투입
table_data.append({
    "운영 모드": "전부투입", "정규 조": "-", 
    "오픈 부스\n(감독 자동 포함)": f"{num_p}개", "잉여 인원": "-",
    "잉여 포함\n총 부스": f"{num_p}개"
})

# 5. [중요] 연번 제거 및 표 출력
# hide_index=True를 사용하여 모바일 화면을 더 넓게 씁니다.
df = pd.DataFrame(table_data)
st.dataframe(df, hide_index=True, use_container_width=True)

# 6. X(잉여) 조 시각화 (X 표시)
st.divider()
st.subheader("👻 교대별 잉여 인원 조 편성 (X 포함)")
for s in display_modes:
    rem = num_p % s
    if rem > 0:
        ghosts = s - rem
        visual = ["X"] * ghosts + ["근무자"] * rem
        st.write(f"**{s}교대 (잉여 {rem}명):**")
        st.error(" / ".join(visual))
