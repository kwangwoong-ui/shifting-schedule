import streamlit as st

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="공항 부스 산출기", layout="centered")
st.title("📊 모바일 최적화 부스 산출기")

# 2. 인원 입력
num_p = st.number_input("🔢 전체 투입 인원수", min_value=1, value=14)

# 3. 행 표기 로직 결정
display_modes = []
if num_p >= 2: display_modes.append(2)
if num_p >= 3: display_modes.append(3)
if num_p >= 4: display_modes.append(4)
if num_p >= 5: display_modes.append(5)
if num_p >= 6: display_modes.append(6)

st.divider()

# 4. [수정] 강제 줄바꿈 및 열 순서 조정한 HTML 표 구성
st.subheader(f"📋 {num_p}명 기준 운영 모드 요약")

# CSS: 모바일 가로폭 최적화 및 강제 글자색 지정 (다크모드 대응)
table_style = """
<style>
    .mobile-table { width: 100%; border-collapse: collapse; font-size: 11px; table-layout: fixed; background-color: white !important; }
    .mobile-table th, .mobile-table td { border: 1px solid #dddddd; padding: 10px 2px; text-align: center; color: black !important; }
    .mobile-table th { background-color: #f2f2f2; font-weight: bold; }
    .total-col { background-color: #fff0f6 !important; font-weight: bold; color: #d63384 !important; }
</style>
"""

# 표 헤더 (요청하신 순서 및 줄바꿈 적용)
html_table = f"""
{table_style}
<table class="mobile-table">
    <thead>
        <tr>
            <th>운영<br>모드</th>
            <th>정규<br>조</th>
            <th>오픈 부스<br>(감독 자동 포함)</th>
            <th>잉여<br>인원</th>
            <th class="total-col">잉여 포함<br>총 부스</th>
        </tr>
    </thead>
    <tbody>
"""

# 데이터 행 추가 로직
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

# 7명 이상 시 밀어내기
if num_p >= 7:
    push_val = max(0, num_p - 1)
    html_table += f"""
        <tr>
            <td>밀어내기</td>
            <td>-</td>
            <td>{push_val}개</td>
            <td>-</td>
            <td class="total-col">{push_val}개</td>
        </tr>
    """

# 전부투입 상시 표시
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
st.markdown(html_table, unsafe_allow_html=True)

# 5. X(유령) 조 시각화 (잉여가 있을 때만)
st.divider()
st.subheader("👻 교대별 잉여 인원 조 편성 (X 포함)")
for s in display_modes:
    rem = num_p % s
    if rem > 0:
        ghosts = s - rem
        visual = ["X"] * ghosts + ["근무자"] * rem
        st.write(f"**{s}교대 (잉여 {rem}명):**")
        st.error(" / ".join(visual))
