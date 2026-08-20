import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor
import urllib3

# SSL 경고 메시지 숨김
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 웹 페이지 기본 설정
st.set_page_config(page_title="통합 보도자료 대시보드", page_icon="📰", layout="wide")

# 다크모드 방어 및 표 스타일링
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp, .main, .block-container {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, label, div {
            color: #0f172a !important;
        }
        div[data-baseweb="tab-list"] {
            background-color: #ffffff !important;
            border-bottom: 2px solid #cbd5e1 !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
            background-color: #f1f5f9 !important;
            border: 1px solid #cbd5e1 !important;
            border-bottom: none !important;
            border-radius: 6px 6px 0 0 !important;
            padding: 10px 20px !important;
            margin-right: 4px !important;
        }
        div[data-baseweb="tab-list"] button[data-baseweb="tab"] * {
            color: #0f172a !important;
            font-weight: bold !important;
            font-size: 15px !important;
        }
        div[data-baseweb="tab-list"] button[aria-selected="true"] {
            background-color: #2563eb !important;
            border-color: #2563eb !important;
        }
        div[data-baseweb="tab-list"] button[aria-selected="true"] * {
            color: #ffffff !important;
            font-weight: bold !important;
        }
        div[data-baseweb="input"] {
            background-color: #f8fafc !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        div[data-baseweb="input"] input {
            color: #0f172a !important;
            background-color: #f8fafc !important;
        }
        .stButton > button {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: bold !important;
        }
        .stButton > button:hover {
            background-color: #2563eb !important;
            color: #ffffff !important;
        }
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            background-color: #ffffff !important;
        }
        .custom-table th {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            font-weight: bold;
            padding: 12px;
            border-bottom: 2px solid #cbd5e1;
            text-align: left;
            white-space: nowrap !important;
        }
        .custom-table td {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            color: #334155 !important;
            text-align: left;
        }
        .nowrap-col {
            white-space: nowrap !important;
        }
        .custom-table tr:hover {
            background-color: #f8fafc !important;
        }
        .dash-link {
            color: #1d4ed8 !important;
            font-weight: bold !important;
            text-decoration: none !important;
            word-break: keep-all;
        }
        .dash-link:hover {
            text-decoration: underline !important;
            color: #1e40af !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📰 정부·지자체 통합 보도자료 대시보드")
st.caption("국토교통부, 기후에너지환경부, 산림청, 서울특별시 보도자료 모니터링")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def fetch_molit_dept(item):
    try:
        # 국토부 전용 방화벽 우회 헤더 설정 (Referer 필수)
        molit_headers = HEADERS.copy()
        molit_headers["Referer"] = "https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp"
        
        resp = requests.get(item['link'], headers=molit_headers, timeout=5, verify=False)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'
            html = resp.text
            
            # 1. 첨부파일명 속 (OO과/팀/단/실) 패턴 파싱
            m_file = re.search(r'[\(\[]([가-힣]{2,10}(?:과|팀|단|실|센터|부|관))[\)\]]', html)
            if m_file:
                item['담당부서'] = m_file.group(1)
                return item

            # 2. '담당부서 : OO과' 텍스트 패턴 파싱
            m_text = re.search(r'담당부서\s*[:]?\s*([가-힣]{2,10}(?:과|팀|단|실|센터|부|관))', html)
            if m_text:
                item['담당부서'] = m_text.group(1)
                return item
    except: pass
    return item

@st.cache_data(ttl=1800)
def fetch_data():
    all_data = []

    # 1. 국토교통부
    molit_items = []
    try:
        for page in range(1, 3):
            url = f"https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp?cate=1&search_page={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 4:
                    title = a_tag.text.strip()
                    raw_href = a_tag.get('href', '')
                    m_id = re.search(r'id=([^&]+)', raw_href)
                    link = f"https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id={m_id.group(1)}" if m_id else urljoin("https://www.molit.go.kr/USR/NEWS/m_71/", raw_href)
                    date = tds[3].text.strip()
                    molit_items.append({"기관": "국토교통부", "담당부서": "국토교통부", "날짜": date, "제목": title, "링크": link})
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            molit_items = list(executor.map(fetch_molit_dept, molit_items))
        all_data.extend(molit_items)
    except: pass

    # 2. 기후에너지환경부
    try:
        for page in range(1, 3):
            url = f"https://www.mcee.go.kr/home/web/index.do?menuId=10598&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 5:
                    title = a_tag.text.strip()
                    link = urljoin("https://www.mcee.go.kr/home/web/", a_tag.get('href', ''))
                    date = tds[-2].text.strip()
                    dept = tds[-4].get_text(separator=' ', strip=True)
                    all_data.append({"기관": "기후에너지환경부", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass

    # 3. 산림청
    try:
        for page in range(1, 3):
            url = f"https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_02_01&bbsId=BBSMSTR_1036&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            posts = {}
            for a in soup.find_all('a', href=re.compile(r'nttId=')):
                raw_href = a.get('href', '')
                ntt_m = re.search(r'nttId=(\d+)', raw_href)
                if not ntt_m: continue
                
                ntt_id = ntt_m.group(1)
                link = urljoin("https://www.forest.go.kr", raw_href)
                
                parent_box = a.find_parent(['li', 'tr', 'td', 'div'])
                box_text = parent_box.get_text(separator=' ', strip=True) if parent_box else a.get_text()
                
                dm = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', box_text)
                date = dm.group(1).replace('.', '-').replace('/', '-') if dm else "날짜 미표기"
                
                clean_title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a.get_text()).strip()
                clean_title = re.sub(r'20\d{2}[-.\/]\d{2}[-.\/]\d{2}', '', clean_title).strip()
                
                if ntt_id not in posts or len(clean_title) > len(posts[ntt_id]['제목']):
                    posts[ntt_id] = {
                        "기관": "산림청",
                        "담당부서": "산림청",
                        "날짜": date,
                        "제목": clean_title,
                        "링크": link
                    }
            all_data.extend(posts.values())
    except: pass

    # 4. 서울특별시
    try:
        for page in range(1, 3):
            url = f"https://www.seoul.go.kr/news/news_report.do?pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    raw_href = a_tag.get('href', '')
                    ntt_m = re.search(r'nttNo=(\d+)|(\d{5,})', raw_href)
                    link = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&nttNo={ntt_m.group(1) or ntt_m.group(2)}" if ntt_m else urljoin("https://www.seoul.go.kr/news/", raw_href)
                    date = tds[-1].text.strip()
                    dept = tds[-2].get_text(separator=' ', strip=True)
                    all_data.append({"기관": "서울특별시", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass

    return pd.DataFrame(all_data)

col_title, col_btn = st.columns([8, 2])
with col_btn:
    if st.button("🔄 최신 데이터 강제 갱신"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("실시간으로 각 부처 데이터를 가져오는 중입니다..."):
    df = fetch_data()

if not df.empty:
    search_kw = st.text_input("🔍 실시간 키워드 검색 (제목 또는 담당부서)", "")
    if search_kw:
        df = df[df['제목'].str.contains(search_kw, case=False, na=False) | df['담당부서'].str.contains(search_kw, case=False, na=False)]

    tabs = st.tabs(["전체 보기", "국토교통부", "기후에너지환경부", "산림청", "서울특별시"])

    def render_custom_table(filtered_df):
        if filtered_df.empty:
            st.info("검색 조건에 해당되는 보도자료가 없습니다.")
            return
        
        st.write(f"총 **{len(filtered_df)}**건 표시 중")
        
        table_html = "<table class='custom-table'><thead><tr>"
        table_html += "<th style='width: 120px;'>기관</th>"
        table_html += "<th style='width: 160px;'>담당부서</th>"
        table_html += "<th style='width: 110px;'>날짜</th>"
        table_html += "<th>보도자료 제목</th>"
        table_html += "</tr></thead><tbody>"
        
        for _, r in filtered_df.iterrows():
            table_html += f"<tr>"
            table_html += f"<td class='nowrap-col'><b>{r['기관']}</b></td>"
            table_html += f"<td class='nowrap-col'>{r['담당부서']}</td>"
            table_html += f"<td class='nowrap-col'>{r['날짜']}</td>"
            table_html += f"<td><a href='{r['링크']}' target='_blank' class='dash-link'>{r['제목']}</a></td>"
            table_html += f"</tr>"
            
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

    with tabs[0]: render_custom_table(df)
    with tabs[1]: render_custom_table(df[df['기관'] == '국토교통부'])
    with tabs[2]: render_custom_table(df[df['기관'] == '기후에너지환경부'])
    with tabs[3]: render_custom_table(df[df['기관'] == '산림청'])
    with tabs[4]: render_custom_table(df[df['기관'] == '서울특별시'])
else:
    st.error("데이터 수집 중 오류가 발생했습니다.")
