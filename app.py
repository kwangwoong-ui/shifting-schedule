import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="근무 규모 계산기", layout="centered")
st.title("🧮 운영 모드별 부스 계산기")
st.caption("인원수만 입력하면 각 교대별 적정 부스 숫자를 즉시 계산합니다.")

# 2. 인원수 입력 (가장 크게 배치)
num_p = st.number_input("🔢 현재 전체 투입 인원수를 입력하세요", min_value=1, max_value=100, value=12)

st.divider()

# 3. 계산 로직 함수
def calculate_booths(n_total):
    results = []
    
    # 교대 모드 정의 (N교대: N명당 1명 휴식)
    modes = {
        "2교대": 2,
        "3교대": 3,
        "4교대": 4,
        "5교대": 5
    }
    
    for label, n_shift in modes.items():
        resters = n_total // n_shift  # 휴식 인원
        booths = n_total - resters    # 근무 부스
        rem = n_total % n_shift       # 나누어 떨어지지 않는 잔여 인원
        
        results.append({
            "운영 모드": label,
            "휴식 인원": f"{resters}명",
            "오픈 부스": f"✨ {booths}개",
            "비고": f"{resters}개조 운영" + (f" (잔여 {rem}명 포함)" if rem > 0 else "")
        })
    
    # 밀어내기 (전체에서 1명만 휴식)
    results.append({
        "운영 모드": "밀어내기",
        "휴식 인원": "1명",
        "오픈 부스": f"✨ {max(0, n_total - 1)}개",
        "비고": "전체 인원 순환 휴식"
    })
    
    # 전부 투입 (휴식 없음)
    results.append({
        "운영 모드": "전부 투입",
        "휴식 인원": "0명",
        "오픈 부스": f"✨ {n_total}개",
        "비고": "전원 근무 투입"
    })
    
    return results

# 4. 결과 출력
if num_p > 0:
    res_list = calculate_booths(num_p)
    
    # 주요 지표 (Metric) 시각화
    st.subheader(f"📊 {num_p}명 투입 시 모드별 부스 현황")
    
    # 상단 3개 모드 강조
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("4교대 시 부스", res_list[2]["오픈 부스"])
    with c2:
        st.metric("밀어내기 시 부스", res_list[4]["오픈 부스"])
    with c3:
        st.metric("전부 투입 시 부스", res_list[5]["오픈 부스"])
    
    st.divider()
    
    # 전체 비교표
    df = pd.DataFrame(res_list)
    st.table(df)

    st.info(f"💡 **관리자님 필독:**\n4교대 기준, {num_p}명 중 {num_p // 4}명이 쉬고 나머지 인원이 근무에 투입되어 총 {num_p - (num_p // 4)}개의 부스를 운영하게 됩니다.")
