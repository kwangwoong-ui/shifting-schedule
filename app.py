import streamlit as st
import math

# 1. 페이지 설정
st.set_page_config(page_title="공항 근무 비교기", layout="wide")
st.title("📊 근무 모드별 부스 개수 비교")

# 2. 인원수 입력
num_p = st.number_input("🔢 전체 투입 인원수를 입력하세요", min_value=1, max_value=100, value=14)

st.divider()

# 3. 전체 모드 한눈에 비교 (표 형태)
st.subheader(f"💡 {num_p}명 투입 시 모드별 '감독/자동 포함' 부스 개수")

def get_booth_count(n, s):
    # n: 인원수, s: 교대수 (2, 3, 4, 5)
    # 휴식 인원 = n // s
    return n - (n // s)

data = {
    "구분": ["2교대", "3교대", "4교대", "5교대", "밀어내기", "전부투입"],
    "오픈 부스 (감독/자동 포함)": [
        f"{get_booth_count(num_p, 2)}개",
        f"{get_booth_count(num_p, 3)}개",
        f"{get_booth_count(num_p, 4)}개",
        f"{get_booth_count(num_p, 5)}개",
        f"{num_p - 1}개",
        f"{num_p}개"
    ],
    "휴식 인원": [
        f"{num_p // 2}명",
        f"{num_p // 3}명",
        f"{num_p // 4}명",
        f"{num_p // 5}명",
        "1명",
        "0명"
    ],
    "잉여(유령)": [
        f"{num_p % 2}명",
        f"{num_p % 3}명",
        f"{num_p % 4}명",
        f"{num_p % 5}명",
        "-",
        "-"
    ]
}

st.table(data)

st.divider()

# 4. 선택한 교대의 '유령 조' 시각화 (예: 5교대)
st.subheader("👻 유령 인원 조 편성 (5교대 기준 예시)")

selected_shift = 5 # 관리자님 예시인 5교대 고정 혹은 선택 가능
rem = num_p % selected_shift

if rem == 0:
    st.success("✅ 모든 조가 유령 없이 꽉 찼습니다.")
else:
    num_ghosts = selected_shift - rem
    # 유령이 휴식 자리를 차지한다고 가정할 때의 구성
    # 예: 14명 5교대 -> 잉여 4명 + 유령 1명
    # 관리자님 요청 형식: 유령 근무자 근무자 근무자 근무자
    ghost_line = ["👻 유령"] + ["👤 근무자"] * rem
    
    st.info(f"마지막 조(잉여 {rem}명)는 유령이 휴식 자리를 대신하여 아래와 같이 운영됩니다.")
    
    # 시각적 표기
    st.error(" / ".join(ghost_line))
    st.caption("※ '유령' 칸이 휴식 순번일 때는 실제 근무자 4명이 모두 투입됩니다.")

st.divider()
st.subheader("📱 카톡 보고용 요약")
summary = f"""📢 [근무 운영 규모 안내]
인원: {num_p}명 기준
- 4교대: {get_booth_count(num_p, 4)}부스
- 5교대: {get_booth_count(num_p, 5)}부스
- 밀어내기: {num_p-1}부스
- 전부투입: {num_p}부스
(감독/자동 포함 숫자임)"""
st.text_area("복사해서 사용하세요", value=summary, height=150)
