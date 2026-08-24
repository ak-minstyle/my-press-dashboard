import streamlit as st
import pandas as pd
import requests
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="국회 법안·입법예고 / 보도자료 통합 대시보드", page_icon="📰", layout="wide")

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
        .stButton > button { background-color: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #cbd5e1 !important; font-weight: bold !important; }
        .stButton > button:hover { background-color: #2563eb !important; color: #ffffff !important; }
        
        /* 상단 타이틀 정렬 및 반응형 CSS */
        .header-box {
            text-align: center;
            padding: 10px 0 20px 0;
            word-break: keep-all;
            line-height: 1.4;
        }
        .header-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #0f172a !important;
            margin-bottom: 6px;
        }
        .header-subtitle {
            font-size: 1.3rem;
            font-weight: 700;
            color: #2563eb !important;
        }

        /* 데스크톱 기본 테이블 스타일 */
        .table-responsive { width: 100%; margin-bottom: 1rem; }
        .custom-table { width: 100%; border-collapse: collapse; background-color: #ffffff !important; }
        .custom-table th { background-color: #f1f5f9 !important; color: #0f172a !important; font-weight: bold; padding: 12px; border-bottom: 2px solid #cbd5e1; text-align: left; white-space: nowrap !important; }
        .custom-table td { padding: 12px; border-bottom: 1px solid #e2e8f0; color: #334155 !important; }
        .nowrap-col { white-space: nowrap !important; }
        .custom-table tr:hover { background-color: #f8fafc !important; }
        .dash-link { color: #1d4ed8 !important; font-weight: bold !important; text-decoration: none !important; word-break: keep-all; }
        .dash-link:hover { text-decoration: underline !important; color: #1e40af !important; }

        /* 📱 스마트폰 모바일 카드 UI */
        @media screen and (max-width: 768px) {
            .header-title { font-size: 1.3rem; }
            .header-subtitle { font-size: 1.1rem; }
            .custom-table, .custom-table thead, .custom-table tbody, .custom-table th, .custom-table td, .custom-table tr {
                display: block !important;
            }
            .custom-table thead {
                display: none !important;
            }
            .custom-table tr {
                margin-bottom: 14px !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 10px !important;
                padding: 12px 14px !important;
                background-color: #ffffff !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04) !important;
            }
            .custom-table td {
                border: none !important;
                border-bottom: 1px solid #f1f5f9 !important;
                position: static !important;
                padding: 6px 0 !important;
                text-align: left !important;
                white-space: normal !important;
                word-break: break-word !important;
                font-size: 14px !important;
            }
            .custom-table td:last-child {
                border-bottom: none !important;
                padding-bottom: 0 !important;
            }
            .custom-table td::before {
                content: attr(data-label) !important;
                display: block !important;
                font-weight: bold !important;
                color: #64748b !important;
                font-size: 12px !important;
                margin-bottom: 2px !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="header-box">
        <div class="header-title">📜 국회 발의 법안 · ⚖️ 정부 입법·행정예고</div>
        <div class="header-subtitle">📰 정부·지자체 보도자료 통합 대시보드</div>
    </div>
""", unsafe_allow_html=True)

ASSEMBLY_API_KEY = "4771fb319fc6421c96f412002daa0e91"

@st.cache_data(ttl=60)
def load_csv_data():
    if not os.path.exists("data.csv"):
        return pd.DataFrame()
    df = pd.read_csv("data.csv")
    df.fillna("", inplace=True)
    return df

@st.cache_data(ttl=600)
def fetch_live_assembly_bills():
    bills = []
    try:
        url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
        params = {"KEY": ASSEMBLY_API_KEY, "Type": "json", "pIndex": 1, "pSize": 500, "AGE": "22"}
        resp = requests.get(url, params=params, timeout=10, verify=False)
        data = resp.json()
        if "nzmimeepazxkubdpn" in data:
            for r in data["nzmimeepazxkubdpn"][1]["row"]:
                bill_id, comm, title = r.get("BILL_ID", ""), r.get("COMMITTEE", "") or "", r.get("BILL_NAME", "")
                if not bill_id: continue
                link = f"https://likms.assembly.go.kr/bill/bi/billDetailPage.do?billId={bill_id}"
                
                is_kokto = "국토" in comm or (not comm and any(kw in title for kw in ["국토", "건축", "주택", "도로", "철도", "토지", "부동산", "교통", "물류"]))
                is_hwan = any(kw in comm for kw in ["환경", "노동", "기후"]) or (not comm and any(kw in title for kw in ["기후", "환경", "폐기물", "대기", "노동", "고용", "근로", "에너지", "전력", "신재생", "탄소", "생태", "수질"]))
                is_jungmu = "정무" in comm or (not comm and any(kw in title for kw in ["금융", "공정거래", "보훈", "자본시장", "가상자산", "가맹", "하도급"]))
                
                base = {"담당부서": f"발의: {r.get('PROPOSER', '국회의원')}", "날짜": r.get("PROPOSE_DT", ""), "제목": title, "링크": link}
                if is_kokto: bills.append({"기관": "📜 국토교통위원회", **base})
                elif is_hwan: bills.append({"기관": "📜 기후에너지환경노동위원회", **base})
                elif is_jungmu: bills.append({"기관": "📜 정무위원회", **base})
    except Exception:
        pass
    return pd.DataFrame(bills)

col_title, col_btn = st.columns([8, 2])
with col_btn:
    if st.button("🔄 화면 새로고침 (즉시로딩)"):
        st.cache_data.clear()
        st.rerun()

df_csv = load_csv_data()
df_bills = fetch_live_assembly_bills()
df_total = pd.concat([df_csv, df_bills], ignore_index=True)

if df_total.empty:
    st.info("데이터 수집 로봇이 작동 중입니다. 잠시 후 새로고침 해주세요.")
else:
    df_total = df_total.drop_duplicates(subset=['기관', '제목', '날짜'], keep='first')
    df_total['sort_date'] = pd.to_datetime(df_total['날짜'].str.extract(r'(\d{4}[-.\/]\d{2}[-.\/]\d{2})')[0], errors='coerce')
    df_total = df_total.sort_values(by='sort_date', ascending=False, na_position='last').drop(columns=['sort_date'])
    df_total.fillna("", inplace=True)

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
