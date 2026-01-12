import streamlit as st

# 1. 인원 입력
num_p = st.number_input("🔢 전체 투입 인원수", min_value=1, value=14)

# 2. 부스 산출표 (잉여 제외)
st.subheader(f"📊 정규 조 부스 산출 ({num_p}명 기준)")
modes = [2, 3, 4, 5]
table_data = []
for s in modes:
    full_groups = num_p // s
    rem = num_p % s
    booths = full_groups * (s - 1)
    table_data.append({
        "모드": f"{s}교대",
        "정규 조": f"{full_groups}개",
        "오픈 부스": f"{booths}개",
        "잉여": f"{rem}명"
    })
st.table(table_data)

# 3. X(유령) 조 시각화
st.subheader("👻 교대별 잉여 인원 조 편성 (X 포함)")
for s in modes:
    rem = num_p % s
    if rem > 0:
        ghosts = s - rem
        # 휴식 자리를 포함한 X 표기
        visual = ["X"] * ghosts + ["근무자"] * rem
        st.write(f"**{s}교대 (잉여 {rem}명):**")
        st.error(" / ".join(visual))
