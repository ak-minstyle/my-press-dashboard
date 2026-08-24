import streamlit as st
import pandas as pd
import os

# 페이지 기본 설정
st.set_page_config(page_title="국회 법안·입법예고 / 보도자료 통합 대시보드", page_icon="📰", layout="wide")

# CSS 스타일링 (기존과 동일)
st.markdown("""
    <style>
        [data-testid="stStatusWidget"] { visibility: hidden !important; display: none !important; }
        html, body, [data-testid="stAppViewContainer"], .stApp, .main, .block-container { background-color: #ffffff !important; color: #0f172a !important; }
        h1, h2, h3, h4, h5, h6, p, span, label, div { color: #0f172a !important; }
        div[data-baseweb="tab-list"] { background-color: #ffffff !important; border-bottom: 2px solid #cbd5e1 !important; flex-wrap: nowrap; overflow-x: auto; }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] { background-color: #f1f5f9 !important; border: 1px solid #cbd5e1 !important; border-bottom: none !important; border-radius: 6px 6px 0 0 !important; padding: 10px 20px !important; margin-right: 4px !important; white-space: nowrap; }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] * { color: #0f172a !important; font-weight: bold !important; font-size: 15px !important; }
        div[data-baseweb="tab-list"] button[aria-selected="true"] { background-color: #2563eb !important; border-color: #2563eb !important; }
        div[data-baseweb="tab-list"] button[aria-selected="true"] * { color: #ffffff !important; font-weight: bold !important; }
        div[data-baseweb="input"] { background-color: #f8fafc !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; }
        div[data-baseweb="input"] input { color: #0f172a !important; background-color: #f8fafc !important; }
        .stButton > button { background-color: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; font-weight: bold !important; }
        .stButton > button:hover { background-color: #2563eb !important; color: #ffffff !important; }
        .table-responsive { width: 100%; margin-bottom: 1rem; }
        .custom-table { width: 100%; border-collapse: collapse; background-color: #ffffff !important; }
        .custom-table th { background-color: #f1f5f9 !important; color: #0f172a !important; font-weight: bold; padding: 12px; border-bottom: 2px solid #cbd5e1; text-align: left; white-space: nowrap !important; }
        .custom-table td { padding: 12px; border-bottom: 1px solid #e2e8f0; color: #334155 !important; text-align: left; }
        .nowrap-col { white-space: nowrap !important; }
        .custom-table tr:hover { background-color: #f8fafc !important; }
        .dash-link { color: #1d4ed8 !important; font-weight: bold !important; text-decoration: none !important; word-break: keep-all; }
        .dash-link:hover { text-decoration: underline !important; color: #1e40af !important; }
        @media screen and (max-width: 768px) {
            h1 { font-size: 1.4rem !important; line-height: 1.4 !important; }
            p { font-size: 0.85rem !important; }
            .custom-table, .custom-table tbody { display: block; width: 100%; }
            .custom-table thead { display: none; }
            .custom-table tr { display: block; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            .custom-table td { display: flex; flex-direction: column; border: none !important; padding: 6px 0; font-size: 14px; }
            .custom-table td::before { content: attr(data-label); font-size: 11px; color: #64748b; font-weight: bold; margin-bottom: 4px; }
            .nowrap-col { white-space: normal !important; }
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #0f172a; font-weight: 700; margin-bottom: 0.5rem;'>📜국회 발의 법안 · ⚖️정부 입법 행정예고<br>📰 정부·지자체 보도자료 통합 대시보드</h1>", unsafe_allow_html=True)

# 데이터 로딩 (ttl=60으로 설정해두면 백그라운드 파일 갱신 시 자동 반영됨)
@st.cache_data(ttl=60)
def load_data():
    if not os.path.exists("data.csv"):
        return pd.DataFrame()
    df = pd.read_csv("data.csv")
    df.fillna("", inplace=True)
    return df

df_total = load_data()

col_title, col_btn = st.columns([8, 2])
with col_btn:
    if st.button("🔄 화면 새로고침 (즉시로딩)"):
        st.cache_data.clear()
        st.rerun()

if df_total.empty:
    st.info("데이터를 수집 중이거나 data.csv 파일이 없습니다. (수집 봇 작동 대기 중)")
else:
    search_kw = st.text_input("🔍 실시간 통합 검색 (제목, 담당부서, 대표발의자)", "")
    if search_kw:
        df_total = df_total[df_total['제목'].str.contains(search_kw, case=False, na=False) | df_total['담당부서'].str.contains(search_kw, case=False, na=False)]

    tabs = st.tabs([
        "전체 보기", "📜 국토교통위원회", "📜 기후에너지환경노동위원회", "📜 정무위원회", 
        "⚖️ 입법예고", "⚖️ 행정예고", "국토교통부", "기후에너지환경부", "행정안전부", "국방부", "공정거래위원회", "산림청", "서울특별시"
    ])

    def render_custom_table(filtered_df, tab_name="전체 보기"):
        if filtered_df.empty:
            st.info("해당 조건의 데이터가 없습니다.")
            return
        
        st.write(f"총 **{len(filtered_df)}**건 표시 중")
        
        if "📜" in tab_name: col1, col2, col3, col4 = "상임위 구분", "대표발의자", "날짜", "법안명"
        elif "⚖️" in tab_name: col1, col2, col3, col4 = "구분", "소관부처", "접수기간", "예고명"
        elif tab_name == "전체 보기": col1, col2, col3, col4 = "기관 / 구분", "담당부서 / 발의자", "날짜(접수기간)", "보도자료 제목 / 법안·입법예고명"
        else: col1, col2, col3, col4 = "기관명", "담당부서", "날짜", "보도자료 제목"
        
        html = f"<div class='table-responsive'><table class='custom-table'><thead><tr><th style='width: 150px;'>{col1}</th><th style='width: 160px;'>{col2}</th><th style='width: 130px;'>{col3}</th><th>{col4}</th></tr></thead><tbody>"
        for _, r in filtered_df.iterrows():
            html += f"<tr><td class='nowrap-col' data-label='{col1}'><b>{r['기관']}</b></td><td class='nowrap-col' data-label='{col2}'>{r['담당부서']}</td><td class='nowrap-col' data-label='{col3}'>{r['날짜']}</td><td data-label='{col4}'><a href='{r['링크']}' target='_blank' rel='noreferrer noopener' class='dash-link'>{r['제목']}</a></td></tr>"
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)

    with tabs[0]: render_custom_table(df_total, "전체 보기")
    with tabs[1]: render_custom_table(df_total[df_total['기관'] == '📜 국토교통위원회'], "📜 국토교통위원회")
    with tabs[2]: render_custom_table(df_total[df_total['기관'] == '📜 기후에너지환경노동위원회'], "📜 기후에너지환경노동위원회")
    with tabs[3]: render_custom_table(df_total[df_total['기관'] == '📜 정무위원회'], "📜 정무위원회")
    with tabs[4]: render_custom_table(df_total[df_total['기관'] == '⚖️ 입법예고'], "⚖️ 입법예고")
    with tabs[5]: render_custom_table(df_total[df_total['기관'] == '⚖️ 행정예고'], "⚖️ 행정예고")
    with tabs[6]: render_custom_table(df_total[df_total['기관'] == '국토교통부'], "국토교통부")
    with tabs[7]: render_custom_table(df_total[df_total['기관'] == '기후에너지환경부'], "기후에너지환경부")
    with tabs[8]: render_custom_table(df_total[df_total['기관'] == '행정안전부'], "행정안전부")
    with tabs[9]: render_custom_table(df_total[df_total['기관'] == '국방부'], "국방부")
    with tabs[10]: render_custom_table(df_total[df_total['기관'] == '공정거래위원회'], "공정거래위원회")
    with tabs[11]: render_custom_table(df_total[df_total['기관'] == '산림청'], "산림청")
    with tabs[12]: render_custom_table(df_total[df_total['기관'] == '서울특별시'], "서울특별시")
