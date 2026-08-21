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

st.set_page_config(page_title="통합 보도자료·입법예고 & 국회 법안 대시보드", page_icon="📰", layout="wide")

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

st.title("📰 정부·지자체 보도자료 / ⚖️ 입법예고 & 📜 국회 법안 통합 대시보드")
st.caption("국토부, 기후부, 산림청, 서울시, 공정위, 행안부, 국방부 보도자료 / 하위법령 입법예고 / 국토위·환노위·정무위 법안 실시간 모니터링")

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
            
            for row in soup.select('table tbody tr'):
                tds = row.find_all('td')
                a_tag = row.find('a')
                if a_tag and len(tds) >= 3:
                    raw_text = a_tag.text
                    clean_title = re.sub(r'새글|첨부파일|자세히보기|\[.*?\]', '', raw_text).strip()
                    clean_title = re.sub(r'\s+', ' ', clean_title)
                    if not clean_title or len(clean_title) < 2:
                        continue
                    link = urljoin("https://www.forest.go.kr", a_tag.get('href', ''))
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    date = date_match.group(1).replace('.', '-').replace('/', '-') if date_match else "날짜 미표기"
                    items.append({"기관": "산림청", "담당부서": "산림청", "날짜": date, "제목": clean_title, "링크": link})
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_seoul():
    items = []
    seen_links = set()
    try:
        for page in range(1, 6):
            url = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&curPage={page}"
            resp = requests.get(url, headers=HEADERS, timeout=6, verify=False)
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
                    if link in seen_links: continue
                    seen_links.add(link)
                    date = tds[-1].text.strip()
                    dept = tds[-2].get_text(separator=' ', strip=True)
                    items.append({"기관": "서울특별시", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ftc():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.ftc.go.kr/www/selectBbsNttList.do?bordCd=3&key=12&searchCtgry=01,02&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    raw_href = a_tag.get('href', '')
                    link = urljoin("https://www.ftc.go.kr/www/", raw_href)
                    
                    dept = "공정위"
                    for idx, td in enumerate(tds):
                        if td.find('a'):
                            if idx + 1 < len(tds):
                                dept_text = tds[idx + 1].get_text(separator=' ', strip=True)
                                if dept_text and not re.search(r'^\d{4}[-.\/]', dept_text):
                                    dept = dept_text
                            break
                            
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    date = date_match.group(1).replace('.', '-') if date_match else "날짜 미표기"
                    items.append({"기관": "공정거래위원회", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass
    return items

# 🔥 행정안전부 맞춤 보도자료 수집기 (자바스크립트 링크 대응 파싱 포함)
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_mois():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardList.do?bbsId=BBSMSTR_000000000008&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    raw_href = a_tag.get('href', '')
                    
                    # nttId 추출 (스크립트 링크를 게시물 직접 접속 주소로 변환)
                    ntt_match = re.search(r"nttId=(\d+)|'(\d{5,})'", str(row) + raw_href)
                    if ntt_match:
                        ntt_id = ntt_match.group(1) if ntt_match.group(1) else ntt_match.group(2)
                        link = f"https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId={ntt_id}"
                    else:
                        link = urljoin("https://www.mois.go.kr/frt/bbs/type010/", raw_href)
                        
                    dept = tds[2].get_text(separator=' ', strip=True) if len(tds) >= 4 else "행정안전부"
                    if re.search(r'^\d{4}[-.\/]', dept):
                        dept = "행정안전부"
                        
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    date = date_match.group(1).replace('.', '-') if date_match else "날짜 미표기"
                    items.append({"기관": "행정안전부", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_mnd():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mnd.go.kr/mbshome/mbs/mnd/subview.jsp?id=mnd_020100000000&page={page}"
            resp = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    raw_href = a_tag.get('href', '')
                    link = urljoin("https://www.mnd.go.kr/mbshome/mbs/mnd/", raw_href)
                    dept = tds[-3].get_text(separator=' ', strip=True) if len(tds) >= 4 else "국방부"
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    date = date_match.group(1).replace('.', '-') if date_match else "날짜 미표기"
                    items.append({"기관": "국방부", "담당부서": dept if dept else "국방부", "날짜": date, "제목": title, "링크": link})
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sub_legislation():
    items = []
    try:
        url = "https://opinion.lawmaking.go.kr/gns/elm/stty/lst"
        resp = requests.get(url, headers=HEADERS, timeout=6, verify=False)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for row in soup.select('table tbody tr'):
            a_tag = row.find('a')
            tds = row.find_all('td')
            if a_tag and len(tds) >= 4:
                title = a_tag.text.strip()
                link = urljoin("https://opinion.lawmaking.go.kr", a_tag.get('href', ''))
                dept = tds[1].get_text(separator=' ', strip=True)
                date = tds[-1].get_text(separator=' ', strip=True)
                
                date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', date)
                clean_date = date_match.group(1).replace('.', '-') if date_match else date
                
                items.append({"기관": "⚖️ 하위법령 입법예고", "담당부서": dept, "날짜": clean_date, "제목": title, "링크": link})
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
                
                is_kokto, is_hwan, is_jungmu = False, False, False
                if "국토" in comm: is_kokto = True
                elif any(kw in comm for kw in ["환경", "노동", "기후"]): is_hwan = True
                elif "정무" in comm: is_jungmu = True
                
                if not comm:
                    if any(kw in title for kw in ["국토", "건축", "주택", "도로", "철도", "토지", "부동산", "교통", "물류"]):
                        is_kokto = True
                    elif any(kw in title for kw in ["기후", "환경", "폐기물", "대기", "노동", "고용", "근로", "에너지", "전력", "신재생", "탄소", "생태", "수질"]):
                        is_hwan = True
                    elif any(kw in title for kw in ["금융", "공정거래", "보훈", "자본시장", "가상자산", "가맹", "하도급"]):
                        is_jungmu = True
                
                if is_kokto: bills.append({"기관": "📜 국토교통위원회", "담당부서": f"발의: {proposer}", "날짜": date, "제목": title, "링크": link})
                elif is_hwan: bills.append({"기관": "📜 기후에너지환경노동위원회", "담당부서": f"발의: {proposer}", "날짜": date, "제목": title, "링크": link})
                elif is_jungmu: bills.append({"기관": "📜 정무위원회", "담당부서": f"발의: {proposer}", "날짜": date, "제목": title, "링크": link})
    except: pass
    return bills

col_title, col_btn = st.columns([8, 2])
with col_btn:
    if st.button("🔄 최신 데이터 강제 갱신"):
        st.cache_data.clear()
        st.rerun()

progress_bar = st.progress(0, text="데이터 수집 준비 중...")

progress_bar.progress(10, text="🏢 국토부·기후부·산림청·서울시 수집 중...")
molit_data = fetch_molit()
mcee_data = fetch_mcee()
forest_data = fetch_forest()
seoul_data = fetch_seoul()

progress_bar.progress(40, text="🏛️ 공정위·행안부·국방부 보도자료 수집 중...")
ftc_data = fetch_ftc()
mois_data = fetch_mois()
mnd_data = fetch_mnd()

progress_bar.progress(70, text="⚖️ 하위법령(시행령·시행규칙) 입법예고 수집 중...")
sub_leg_data = fetch_sub_legislation()

progress_bar.progress(90, text="📜 국회 상임위(국토·환노·정무위) 법안 연동 중...")
bills_data = fetch_assembly_bills()

progress_bar.progress(100, text="✨ 모든 데이터 수집 및 병합 완료!")
time.sleep(0.5)
progress_bar.empty()

all_data = molit_data + mcee_data + forest_data + seoul_data + ftc_data + mois_data + mnd_data + sub_leg_data + bills_data
df_total = pd.DataFrame(all_data)

if not df_total.empty:
    search_kw = st.text_input("🔍 실시간 통합 검색 (제목, 담당부서, 대표발의자)", "")
    if search_kw:
        df_total = df_total[df_total['제목'].str.contains(search_kw, case=False, na=False) | df_total['담당부서'].str.contains(search_kw, case=False, na=False)]

    tabs = st.tabs([
        "전체 보기", "국토교통부", "기후에너지환경부", "산림청", "서울특별시", 
        "공정거래위원회", "행정안전부", "국방부", "⚖️ 하위법령 입법예고", 
        "📜 국토교통위원회", "📜 기후에너지환경노동위원회", "📜 정무위원회"
    ])

    def render_custom_table(filtered_df):
        if filtered_df.empty:
            st.info("해당 조건의 데이터가 없습니다.")
            return
        
        st.write(f"총 **{len(filtered_df)}**건 표시 중")
        
        table_html = "<table class='custom-table'><thead><tr>"
        table_html += "<th style='width: 150px;'>기관 / 구분</th>"
        table_html += "<th style='width: 160px;'>담당부서 / 발의자</th>"
        table_html += "<th style='width: 110px;'>날짜</th>"
        table_html += "<th>보도자료 제목 / 법안·입법예고명</th>"
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
    with tabs[5]: render_custom_table(df_total[df_total['기관'] == '공정거래위원회'])
    with tabs[6]: render_custom_table(df_total[df_total['기관'] == '행정안전부'])
    with tabs[7]: render_custom_table(df_total[df_total['기관'] == '국방부'])
    with tabs[8]: render_custom_table(df_total[df_total['기관'] == '⚖️ 하위법령 입법예고'])
    with tabs[9]: render_custom_table(df_total[df_total['기관'] == '📜 국토교통위원회'])
    with tabs[10]: render_custom_table(df_total[df_total['기관'] == '📜 기후에너지환경노동위원회'])
    with tabs[11]: render_custom_table(df_total[df_total['기관'] == '📜 정무위원회'])
else:
    st.error("데이터 수집 중 오류가 발생했습니다.")
