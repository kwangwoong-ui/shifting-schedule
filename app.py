import streamlit as st

# 1. 인원 입력
st.title("📊 인원별 맞춤형 부스 산출기")
num_p = st.number_input("🔢 전체 투입 인원수", min_value=1, value=14)

# 2. 행 표기 로직 결정
display_modes = []

# N명 이하일 때 각 교대조 추가 로직
if num_p >= 2:
    display_modes.append(2)
if num_p >= 3:
    display_modes.append(3)
if num_p >= 4:
    display_modes.append(4)
if num_p >= 5:
    display_modes.append(5)
if num_p >= 6:
    display_modes.append(6)

# 3. 부스 산출표 데이터 구성
st.subheader(f"📋 {num_p}명 기준 운영 모드 요약")
table_data = []

# 교대제 데이터 (필터링된 결과만)
for s in display_modes:
    full_groups = num_p // s
    rem = num_p % s
    booths = full_groups * (s - 1)
    
    label = "맞교대" if s == 2 else f"{s}교대"
    
    table_data.append({
        "운영 모드": label,
        "정규 조": f"{full_groups}개",
        "오픈 부스 (감독 자동 포함)": f"{booths}개",
        "잉여 인원": f"{rem}명"
    })

# 7명 이상일 때만 밀어내기 표시
if num_p >= 7:
    table_data.append({
        "운영 모드": "밀어내기", "정규 조": "-", 
        "오픈 부스 (감독 자동 포함)": f"{max(0, num_p - 1)}개", "잉여 인원": "-"
    })

# 전부투입은 항상 표시
table_data.append({
    "운영 모드": "전부투입", "정규 조": "-", 
    "오픈 부스 (감독 자동 포함)": f"{num_p}개", "잉여 인원": "-"
})

st.table(table_data)

# 4. X(유령) 조 시각화 (잉여가 있을 때만)
st.subheader("👻 교대별 잉여 인원 조 편성 (X 포함)")
for s in display_modes:
    rem = num_p % s
    if rem > 0:
        ghosts = s - rem
        visual = ["X"] * ghosts + ["근무자"] * rem
        st.write(f"**{s}교대 (잉여 {rem}명):**")
        st.error(" / ".join(visual))
