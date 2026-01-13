import streamlit as st

# 1. 인원 입력
st.set_page_config(page_title="공항 부스 산출기", layout="centered")
st.title("📊 모바일 최적화 부스 산출기")
num_p = st.number_input("🔢 전체 투입 인원수", min_value=1, value=14)

# 2. 행 표기 로직 결정
display_modes = []
if num_p >= 2: display_modes.append(2)
if num_p >= 3: display_modes.append(3)
if num_p >= 4: display_modes.append(4)
if num_p >= 5: display_modes.append(5)
if num_p >= 6: display_modes.append(6)

# 3. HTML/CSS 기반 모바일 최적화 표 생성
st.subheader(f"📋 {num_p}명 기준 운영 모드 요약")

# CSS: 폰트 크기 조절 및 표 너비 고정
table_style = """
<style>
    .mobile-table { width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }
    .mobile-table th, .mobile-table td { border: 1px solid #ddd; padding: 6px 2px; text-align: center; word-break: keep-all; }
    .mobile-table th { background-color: #f8f9fa; font-weight: bold; }
    .total-col { background-color: #fff4f4; font-weight: bold; color: #d63384; }
</style>
"""

# 표 헤더 구성 (br 태그로 두 줄 만들기)
html_table = f"""
{table_style}
<table class="mobile-table">
    <thead>
        <tr>
            <th>운영 모드</th>
            <th>정규 조</th>
            <th>오픈 부스<br>(감독 자동 포함)</th>
            <th>잉여 인원</th>
            <th class="total-col">잉여 포함<br>총 부스</th>
        </tr>
    </thead>
    <tbody>
"""

# 데이터 행 추가
for s in display_modes:
    full_groups = num_p // s
    rem = num_p % s
    reg_booths = full_groups * (s - 1)
    total_booths = reg_booths + rem
    label = "맞교대" if s == 2 else f"{s}교대"
    
    html_table += f"""
        <tr>
            <td>{label}</td>
            <td>{full_groups}개</td>
            <td>{reg_booths}개</td>
            <td>{rem}명</td>
            <td class="total-col">{total_booths}개</td>
        </tr>
    """

# 7명 이상 밀어내기
if num_p >= 7:
    html_table += f"""
        <tr>
            <td>밀어내기</td>
            <td>-</td>
            <td>{max(0, num_p - 1)}개</td>
            <td>-</td>
            <td class="total-col">{max(0, num_p - 1)}개</td>
        </tr>
    """

# 전부투입
html_table += f"""
        <tr>
            <td>전부투입</td>
            <td>-</td>
            <td>{num_p}개</td>
            <td>-</td>
            <td class="total-col">{num_p}개</td>
        </tr>
    </tbody>
</table>
"""

# HTML 렌더링
st.write(html_table, unsafe_allow_html=True)

# 4. X(유령) 조 시각화 (잉여가 있을 때만)
st.divider()
st.subheader("👻 교대별 잉여 인원 조 편성 (X 포함)")
for s in display_modes:
    rem = num_p % s
    if rem > 0:
        ghosts = s - rem
        visual = ["X"] * ghosts + ["근무자"] * rem
        st.write(f"**{s}교대 (잉여 {rem}명):**")
        st.error(" / ".join(visual))
