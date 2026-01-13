import streamlit as st

# 1. 인원 입력
num_p = st.number_input("🔢 전체 투입 인원수", min_value=1, value=14)

# 2. 부스 산출표
st.subheader(f"📊 운영 모드별 부스 산출 ({num_p}명 기준)")
modes = [2, 3, 4, 5, 6] # 6교대 추가
table_data = []

# 교대제 계산 (2, 3, 4, 5, 6교대)
for s in modes:
    full_groups = num_p // s
    rem = num_p % s
    booths = full_groups * (s - 1)
    table_data.append({
        "운영 모드": f"{s}교대",
        "정규 조": f"{full_groups}개",
        "오픈 부스 (감독 자동 포함)": f"{booths}개",
        "잉여 인원": f"{rem}명"
    })

# 밀어내기/전부투입 추가
table_data.append({
    "운영 모드": "밀어내기", "정규 조": "-", 
    "오픈 부스 (감독 자동 포함)": f"{max(0, num_p - 1)}개", "잉여 인원": "-"
})
table_data.append({
    "운영 모드": "전부투입", "정규 조": "-", 
    "오픈 부스 (감독 자동 포함)": f"{num_p}개", "잉여 인원": "-"
})

st.table(table_data)

# 3. X(유령) 조 시각화
st.subheader("👻 교대별 잉여 인원 조 편성 (X 포함)")
for s in modes:
    rem = num_p % s
    if rem > 0:
        ghosts = s - rem
        # 휴식 자리를 포함한 X 표기 로직
        visual = ["X"] * ghosts + ["근무자"] * rem
        st.write(f"**{s}교대 (잉여 {rem}명):**")
        st.error(" / ".join(visual))
