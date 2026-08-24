import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import time

# 공공기관 SSL 경고 메시지 비활성화
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

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
ASSEMBLY_API_KEY = "4771fb319fc6421c96f412002daa0e91"
TIMEOUT = 6 # 각 요청당 최대 대기 시간 제한

# 🔥 국토부 개별 게시글 담당과 고속 파서
def fetch_molit_detail(item):
    try:
        resp = requests.get(item['링크'], headers=HEADERS, timeout=TIMEOUT, verify=False)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        for f in soup.find_all('a'):
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
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 4:
                    items.append({
                        "기관": "국토교통부", 
                        "담당부서": "국토교통부", 
                        "날짜": tds[3].text.strip(), 
                        "제목": a_tag.text.strip(), 
                        "링크": "https://www.molit.go.kr/USR/NEWS/m_71/" + a_tag['href']
                    })
        
        # 담당부서 파싱을 위한 20-스레드 동시 폭격
        with ThreadPoolExecutor(max_workers=20) as executor:
            items = list(executor.map(fetch_molit_detail, items))
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_mcee():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mcee.go.kr/home/web/index.do?menuId=10598&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 5:
                    items.append({
                        "기관": "기후에너지환경부", 
                        "담당부서": tds[-4].get_text(separator=' ', strip=True), 
                        "날짜": tds[-2].text.strip(), 
                        "제목": a_tag.text.strip(), 
                        "링크": urljoin("https://www.mcee.go.kr/home/web/", a_tag.get('href', ''))
                    })
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_forest():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_02_01&bbsId=BBSMSTR_1036&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            posts = {}
            for a in soup.find_all('a', href=re.compile(r'nttId=')):
                raw_href = a.get('href', '')
                ntt_m = re.search(r'nttId=(\d+)', raw_href)
                if not ntt_m: continue
                ntt_id = ntt_m.group(1)
                
                parent_box = a.find_parent(['li', 'tr', 'td', 'div'])
                box_text = parent_box.get_text(separator=' ', strip=True) if parent_box else a.get_text()
                dm = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', box_text)
                date = dm.group(1).replace('.', '-').replace('/', '-') if dm else "날짜 미표기"
                
                clean_title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a.get_text()).strip()
                clean_title = re.sub(r'20\d{2}[-.\/]\d{2}[-.\/]\d{2}', '', clean_title).strip()
                
                if ntt_id not in posts or len(clean_title) > len(posts[ntt_id]['제목']):
                    posts[ntt_id] = {
                        "기관": "산림청", "담당부서": "산림청", "날짜": date, 
                        "제목": clean_title, "링크": urljoin("https://www.forest.go.kr", raw_href)
                    }
            items.extend(posts.values())
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_seoul():
    items = []
    seen_links = set()
    try:
        for page in range(1, 6):
            url = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&curPage={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    raw_href = a_tag.get('href', '')
                    ntt_m = re.search(r'nttNo=(\d+)|(\d{5,})', raw_href)
                    link = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&nttNo={ntt_m.group(1) or ntt_m.group(2)}" if ntt_m else urljoin("https://www.seoul.go.kr/news/", raw_href)
                    
                    if link in seen_links: continue
                    seen_links.add(link)
                    
                    items.append({
                        "기관": "서울특별시", 
                        "담당부서": tds[-2].get_text(separator=' ', strip=True), 
                        "날짜": tds[-1].text.strip(), 
                        "제목": a_tag.text.strip(), 
                        "링크": link
                    })
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ftc():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.ftc.go.kr/www/selectBbsNttList.do?bordCd=3&key=12&searchCtgry=01,02&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    dept = "공정위"
                    for idx, td in enumerate(tds):
                        if td.find('a') and idx + 1 < len(tds):
                            dept_text = tds[idx + 1].get_text(separator=' ', strip=True)
                            if dept_text and not re.search(r'^\d{4}[-.\/]', dept_text): dept = dept_text
                            break
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    items.append({
                        "기관": "공정거래위원회", 
                        "담당부서": dept, 
                        "날짜": date_match.group(1).replace('.', '-') if date_match else "날짜 미표기", 
                        "제목": a_tag.text.strip(), 
                        "링크": urljoin("https://www.ftc.go.kr/www/", a_tag.get('href', ''))
                    })
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_mois():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardList.do?bbsId=BBSMSTR_000000000008&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    raw_href = a_tag.get('href', '')
                    ntt_match = re.search(r"nttId=(\d+)|'(\d{5,})'", str(row) + raw_href)
                    link = f"https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId={ntt_match.group(1) or ntt_match.group(2)}" if ntt_match else urljoin("https://www.mois.go.kr/frt/bbs/type010/", raw_href)
                    
                    dept_text = tds[-3].get_text(separator=' ', strip=True) if len(tds) >= 3 else "행정안전부"
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    
                    items.append({
                        "기관": "행정안전부", 
                        "담당부서": dept_text if dept_text and not re.search(r'^\d{4}[-.\/]', dept_text) else "행정안전부", 
                        "날짜": date_match.group(1).replace('.', '-') if date_match else "날짜 미표기", 
                        "제목": a_tag.text.strip(), 
                        "링크": link
                    })
    except: pass
    return items

# 🔥 살려둔 국방부 파서 (가장 강력한 WAF 우회 헤더 적용)
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_mnd():
    items = []
    mnd_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.mnd.go.kr/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        for page in range(1, 4):
            url = f"https://www.mnd.go.kr/mnd/167/subview.do?pageIndex={page}"
            resp = requests.get(url, headers=mnd_headers, timeout=TIMEOUT, verify=False)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for row in soup.find_all(['tr', 'li']):
                try:
                    a_tag = row.find('a')
                    if not a_tag: continue
                    
                    title = a_tag.get_text(strip=True)
                    clean_title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', title).strip()
                    if not clean_title or clean_title == "자세히보기" or len(clean_title) < 2:
                        continue
                        
                    raw_href = a_tag.get('href', '') or ''
                    onclick_attr = a_tag.get('onclick', '') or ''
                    
                    link = ""
                    ntt_m = re.search(r'nttId=(\d+)|fn_[a-zA-Z_]*\([\'"]?(\d+)[\'"]?\)', raw_href + onclick_attr)
                    
                    if ntt_m:
                        ntt_id = ntt_m.group(1) or ntt_m.group(2)
                        link = f"https://www.mnd.go.kr/mnd/167/subview.do?nttId={ntt_id}"
                    elif raw_href and not raw_href.startswith('#') and 'javascript' not in raw_href.lower():
                        link = urljoin("https://www.mnd.go.kr", raw_href)
                        
                    if not link:
                        continue 
                        
                    date_match = re.search(r'(202\d)\s*[-.\/]\s*(\d{2})\s*[-.\/]\s*(\d{2})', row.text)
                    date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else "날짜 미표기"
                    
                    dept = "국방부"
                    for td in row.find_all(['td', 'span']):
                        t_text = td.get_text(strip=True)
                        if t_text and t_text != clean_title and not re.match(r'^\d+$', t_text) and not re.search(r'202\d', t_text):
                            if any(kw in t_text for kw in ["국방", "대변인", "정책", "기획", "인사", "전력", "과", "팀", "실"]):
                                dept = t_text
                                break
                                
                    items.append({"기관": "국방부", "담당부서": dept, "날짜": date, "제목": clean_title, "링크": link})
                except Exception:
                    continue 
    except Exception:
        pass
        
    unique_items = []
    seen = set()
    for item in items:
        if item['제목'] not in seen:
            seen.add(item['제목'])
            unique_items.append(item)
            
    return unique_items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_sub_legislation():
    items = []
    try:
        for url in ["https://opinion.lawmaking.go.kr/gns/elm/stty/lst", "https://opinion.lawmaking.go.kr/gcom/ogLmPp"]:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            for row in soup.find_all('tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 6:
                    title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a_tag.get_text(strip=True)).strip()
                    if title and len(title) > 1 and "공고번호" not in title:
                        items.append({
                            "기관": "⚖️ 입법예고", 
                            "담당부서": tds[-6].get_text(separator=' ', strip=True), 
                            "날짜": tds[-4].get_text(separator=' ', strip=True), 
                            "제목": title, 
                            "링크": urljoin("https://opinion.lawmaking.go.kr", a_tag.get('href', ''))
                        })
        
        adm_url = "https://opinion.lawmaking.go.kr/gcom/admpp"
        resp = requests.get(adm_url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
        for row in soup.find_all('tr'):
            a_tag, tds = row.find('a'), row.find_all('td')
            if a_tag and len(tds) >= 3:
                title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a_tag.get_text(strip=True)).strip()
                if title and len(title) > 1 and "공고번호" not in title:
                    items.append({
                        "기관": "⚖️ 행정예고", 
                        "담당부서": tds[-3].get_text(separator=' ', strip=True), 
                        "날짜": tds[-2].get_text(separator=' ', strip=True), 
                        "제목": title, 
                        "링크": urljoin("https://opinion.lawmaking.go.kr", a_tag.get('href', ''))
                    })
    except: pass
    return items

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_assembly_bills():
    bills = []
    try:
        url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
        resp = requests.get(url, params={"KEY": ASSEMBLY_API_KEY, "Type": "json", "pIndex": 1, "pSize": 600, "AGE": "22"}, timeout=TIMEOUT, verify=False)
        data = resp.json()
        if "nzmimeepazxkubdpn" in data:
            for r in data["nzmimeepazxkubdpn"][1]["row"]:
                bill_id = r.get("BILL_ID", "")
                comm = r.get("COMMITTEE", "") or ""
                title = r.get("BILL_NAME", "")
                
                if not bill_id: continue
                link = f"https://likms.assembly.go.kr/bill/bi/billDetailPage.do?billId={bill_id}"
                
                is_kokto = "국토" in comm or (not comm and any(kw in title for kw in ["국토", "건축", "주택", "도로", "철도", "토지", "부동산", "교통", "물류"]))
                is_hwan = any(kw in comm for kw in ["환경", "노동", "기후"]) or (not comm and any(kw in title for kw in ["기후", "환경", "폐기물", "대기", "노동", "고용", "근로", "에너지", "전력", "신재생", "탄소", "생태", "수질"]))
                is_jungmu = "정무" in comm or (not comm and any(kw in title for kw in ["금융", "공정거래", "보훈", "자본시장", "가상자산", "가맹", "하도급"]))
                
                base_dict = {
                    "담당부서": f"발의: {r.get('PROPOSER', '국회의원')}", 
                    "날짜": r.get("PROPOSE_DT", ""), 
                    "제목": title, 
                    "링크": link
                }
                if is_kokto: bills.append({"기관": "📜 국토교통위원회", **base_dict})
                elif is_hwan: bills.append({"기관": "📜 기후에너지환경노동위원회", **base_dict})
                elif is_jungmu: bills.append({"기관": "📜 정무위원회", **base_dict})
    except: pass
    return bills


col_title, col_btn = st.columns([8, 2])
with col_btn:
    if st.button("🔄 최신 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

progress_bar = st.progress(0, text="초고속 병렬 데이터 수집 중...")

# 국방부 포함 9개 기관 동시 수집
fetch_functions = [
    fetch_assembly_bills, fetch_sub_legislation, fetch_molit, 
    fetch_mcee, fetch_forest, fetch_seoul, fetch_ftc, fetch_mois, fetch_mnd
]

all_data = []
with ThreadPoolExecutor(max_workers=9) as executor:
    futures = [executor.submit(func) for func in fetch_functions]
    for i, future in enumerate(as_completed(futures)):
        try:
            result = future.result()
            if result: all_data.extend(result)
        except Exception: pass
        progress_bar.progress(int((i + 1) / 9 * 100), text=f"수집 중... ({i+1}/9 완료)")

progress_bar.empty()

df_total = pd.DataFrame(all_data)

if not df_total.empty:
    df_total = df_total.drop_duplicates(subset=['기관', '제목', '날짜'], keep='first')
    df_total['sort_date'] = pd.to_datetime(df_total['날짜'].str.extract(r'(\d{4}[-.\/]\d{2}[-.\/]\d{2})')[0], errors='coerce')
    df_total = df_total.sort_values(by='sort_date', ascending=False, na_position='last').drop(columns=['sort_date'])

    search_kw = st.text_input("🔍 실시간 통합 검색 (제목, 담당부서, 대표발의자)", "")
    if search_kw:
        df_total = df_total[df_total['제목'].str.contains(search_kw, case=False, na=False) | df_total['담당부서'].str.contains(search_kw, case=False, na=False)]

    # 국방부 탭 추가 복구 (인덱스 9)
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
else:
    st.error("데이터 수집 중 오류가 발생했습니다.")
