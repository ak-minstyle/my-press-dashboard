import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor
import urllib3
import time

# 공공기관 SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 웹 페이지 기본 설정
st.set_page_config(page_title="통합 보도자료 & 국회 법안 대시보드", page_icon="📰", layout="wide")

# 다크모드 방어, 표 스타일링 및 우측 상단 'Running' 애니메이션 완전히 숨김
st.markdown("""
    <style>
        [data-testid="stStatusWidget"] {
            visibility: hidden !important;
            display: none !important;
        }
        
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

st.title("📰 정부·지자체 보도자료 & 📜 국회 법안 통합 대시보드")
st.caption("국토교통부, 기후에너지환경부, 산림청, 서울시 보도자료 및 국토위/기후에너지환경노동위 발의 법안 실시간 모니터링")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
ASSEMBLY_API_KEY = "4771fb319fc6421c96f412002daa0e91"

def fetch_molit_dept_parallel(item):
    try:
        d_resp = requests.get(item['링크'], headers=HEADERS, timeout=4, verify=False)
        d_resp.encoding = 'utf-8'
        d_soup = BeautifulSoup(d_resp.text, 'html.parser')
        for f in d_soup.find_all('a'):
            m = re.search(r'\(([가-힣]+(과|팀|단|실))\)', f.text)
            if m:
                item['담당부서'] = m.group(1)
                break
    except: pass
    return item

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_molit():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp?cate=1&search_page={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 4:
                    title = a_tag.text.strip()
                    link = "https://www.molit.go.kr/USR/NEWS/m_71/" + a_tag['href']
                    date = tds[3].text.strip()
                    items.append({"기관": "국토교통부", "담당부서": "국토교통부", "날짜": date, "제목": title, "링크": link})
        with ThreadPoolExecutor(max_workers=8) as executor:
            items = list(executor.map(fetch_molit_dept_parallel, items))
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_mcee():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mcee.go.kr/home/web/index.do?menuId=10598&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
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
                    items.append({"기관": "기후에너지환경부", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_forest():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_02_01&bbsId=BBSMSTR_1036&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
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
                    posts[ntt_id] = {"기관": "산림청", "담당부서": "산림청", "날짜": date, "제목": clean_title, "링크": link}
            items.extend(posts.values())
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_seoul():
    items = []
    seen_links = set()  # 🔥 중복 게시글 차단용 세트
    url = "https://www.seoul.go.kr/news/news_report.do"
    
    try:
        for page in range(1, 6):
            # 🔥 서울시 게시판은 POST 폼 데이터 형태로 pageIndex를 넘겨야만 실제 페이지가 이동함
            payload = {
                "bbsNo": "158",
                "pageIndex": str(page)
            }
            resp = requests.post(url, data=payload, headers=HEADERS, timeout=6, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    raw_href = a_tag.get('href', '')
                    ntt_m = re.search(r'nttNo=(\d+)|(\d{5,})', raw_href)
                    if ntt_m:
                        n_val = ntt_m.group(1) if ntt_m.group(1) else ntt_m.group(2)
                        link = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&nttNo={n_val}"
                    else:
                        link = urljoin("https://www.seoul.go.kr/news/", raw_href)
                    
                    # 🔥 중복 링크 방지
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                        
                    date = tds[-1].text.strip()
                    dept = tds[-2].get_text(separator=' ', strip=True)
                    items.append({"기관": "서울특별시", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_assembly_bills():
    bills = []
    url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
    params = {"KEY": ASSEMBLY_API_KEY, "Type": "json", "pIndex": 1, "pSize": 600, "AGE": "22"}
    try:
        resp = requests.get(url, params=params, timeout=10, verify=False)
        data = resp.json()
        if "nzmimeepazxkubdpn" in data:
            rows = data["nzmimeepazxkubdpn"][1]["row"]
            for r in rows:
                comm = r.get("COMMITTEE", "") or ""
                title = r.get("BILL_NAME", "")
                bill_id = r.get("BILL_ID", "")
                proposer = r.get("PROPOSER", "국회의원")
                date = r.get("PROPOSE_DT", "")
                
                if not bill_id: continue
                link = f"https://likms.assembly.go.kr/bill/bi/billDetailPage.do?billId={bill_id}"
                
                is_kokto, is_hwan = False, False
                if "국토" in comm: is_kokto = True
                elif any(kw in comm for kw in ["환경", "노동", "기후"]): is_hwan = True
                
                if not comm:
                    if any(kw in title for kw in ["국토", "건축", "주택", "도로", "철도", "토지", "도시", "부동산", "교통", "물류"]):
                        is_kokto = True
                    elif any(kw in title for kw in ["기후", "환경", "폐기물", "대기", "노동", "고용", "근로", "에너지", "전력", "신재생", "탄소", "생태", "수질"]):
                        is_hwan = True
                
                if is_kokto: bills.append({"기관": "📜 국토교통위원회", "담당부서": f"발의: {proposer}", "날짜": date, "제목": title, "링크": link})
                elif is_hwan: bills.append({"기관": "📜 기후에너지환경노동위원회", "담당부서": f"발의: {proposer}", "날짜": date, "제목": title, "링크": link})
    except: pass
    return bills

col_title, col_btn = st.columns([8, 2])
with col_btn:
    if st.button("🔄 최신 데이터 강제 갱신"):
        st.cache_data.clear()
        st.rerun()

progress_bar = st.progress(0, text="데이터 수집 준비 중...")

progress_bar.progress(10, text="🏢 국토교통부 보도자료 수집 중 (1/5)...")
molit_data = fetch_molit()

progress_bar.progress(30, text="🌿 기후에너지환경부 보도자료 수집 중 (2/5)...")
mcee_data = fetch_mcee()

progress_bar.progress(50, text="🌲 산림청 보도자료 수집 중 (3/5)...")
forest_data = fetch_forest()

progress_bar.progress(70, text="🏙️ 서울특별시 보도자료 집중 수집 중 (4/5)...")
seoul_data = fetch_seoul()

progress_bar.progress(90, text="📜 국회 상임위 발의법안 연동 중 (5/5)...")
bills_data = fetch_assembly_bills()

progress_bar.progress(100, text="✨ 모든 데이터 수집 및 병합 완료!")
time.sleep(0.5)
progress_bar.empty()

all_data = molit_data + mcee_data + forest_data + seoul_data + bills_data
df_total = pd.DataFrame(all_data)

if not df_total.empty:
    search_kw = st.text_input("🔍 실시간 통합 검색 (제목, 담당부서, 대표발의자)", "")
    if search_kw:
        df_total = df_total[df_total['제목'].str.contains(search_kw, case=False, na=False) | df_total['담당부서'].str.contains(search_kw, case=False, na=False)]

    tabs = st.tabs(["전체 보기", "국토교통부", "기후에너지환경부", "산림청", "서울특별시", "📜 국토교통위원회", "📜 기후에너지환경노동위원회"])

    def render_custom_table(filtered_df):
        if filtered_df.empty:
            st.info("해당 조건의 데이터가 없습니다.")
            return
        
        st.write(f"총 **{len(filtered_df)}**건 표시 중")
        
        table_html = "<table class='custom-table'><thead><tr>"
        table_html += "<th style='width: 140px;'>기관 / 구분</th>"
        table_html += "<th style='width: 160px;'>담당부서 / 발의자</th>"
        table_html += "<th style='width: 110px;'>날짜</th>"
        table_html += "<th>보도자료 제목 / 법안명</th>"
        table_html += "</tr></thead><tbody>"
        
        for _, r in filtered_df.iterrows():
            table_html += f"<tr>"
            table_html += f"<td class='nowrap-col'><b>{r['기관']}</b></td>"
            table_html += f"<td class='nowrap-col'>{r['담당부서']}</td>"
            table_html += f"<td class='nowrap-col'>{r['날짜']}</td>"
            table_html += f"<td><a href='{r['링크']}' target='_blank' rel='noreferrer noopener' class='dash-link'>{r['제목']}</a></td>"
            table_html += f"</tr>"
            
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

    with tabs[0]: render_custom_table(df_total)
    with tabs[1]: render_custom_table(df_total[df_total['기관'] == '국토교통부'])
    with tabs[2]: render_custom_table(df_total[df_total['기관'] == '기후에너지환경부'])
    with tabs[3]: render_custom_table(df_total[df_total['기관'] == '산림청'])
    with tabs[4]: render_custom_table(df_total[df_total['기관'] == '서울특별시'])
    with tabs[5]: render_custom_table(df_total[df_total['기관'] == '📜 국토교통위원회'])
    with tabs[6]: render_custom_table(df_total[df_total['기관'] == '📜 기후에너지환경노동위원회'])
else:
    st.error("데이터 수집 중 오류가 발생했습니다.")
