import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import re

# 웹 페이지 기본 설정
st.set_page_config(page_title="통합 보도자료 대시보드", page_icon="📰", layout="wide")

# 다크모드/라이트모드 무관 강제 고대비 스타일링
st.markdown("""
    <style>
        .stApp { background-color: #ffffff !important; color: #0f172a !important; }
        div[data-baseweb="tab-list"] button { font-weight: bold !important; font-size: 15px !important; }
        a { color: #0f172a !important; font-weight: bold; text-decoration: none; }
        a:hover { color: #2563eb !important; text-decoration: underline; }
    </style>
""", unsafe_allow_html=True)

st.title("📰 정부·지자체 통합 보도자료 대시보드")
st.caption("국토교통부, 기후에너지환경부, 산림청, 서울특별시 보도자료 모니터링")

# 30분 동안 수집 결과를 저장해두어 로딩 속도 최적화
@st.cache_data(ttl=1800)
def fetch_data():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    all_data = []

    # 1. 국토교통부
    try:
        for page in range(1, 3):
            url = f"https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp?cate=1&search_page={page}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 4:
                    title = a_tag.text.strip()
                    link = "https://www.molit.go.kr/USR/NEWS/m_71/" + a_tag['href']
                    date = tds[3].text.strip()
                    dept = "국토교통부"
                    try:
                        d_resp = requests.get(link, headers=headers, timeout=5)
                        d_resp.encoding = 'utf-8'
                        d_soup = BeautifulSoup(d_resp.text, 'html.parser')
                        for f in d_soup.find_all('a'):
                            m = re.search(r'\(([가-힣]+(과|팀|단|실))\)', f.text)
                            if m:
                                dept = m.group(1)
                                break
                    except: pass
                    all_data.append({"기관": "국토교통부", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass

    # 2. 기후에너지환경부
    try:
        for page in range(1, 3):
            url = f"https://www.mcee.go.kr/home/web/index.do?menuId=10598&pageIndex={page}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 5:
                    title = a_tag.text.strip()
                    link = urljoin("https://www.mcee.go.kr", a_tag['href'])
                    date = tds[-2].text.strip()
                    dept = tds[-4].get_text(separator=' ', strip=True)
                    all_data.append({"기관": "기후에너지환경부", "담당부서": dept, "날짜": date, "제목": title, "링크": link})
    except: pass

    # 3. 산림청
    try:
        for page in range(1, 3):
            url = f"https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_02_01&bbsId=BBSMSTR_1036&pageIndex={page}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            posts = {}
            for a in soup.find_all('a', href=re.compile(r'nttId=')):
                m = re.search(r'nttId=(\d+)', a.get('href', ''))
                if m:
                    ntt_id = m.group(1)
                    link = urljoin("https://www.forest.go.kr", a['href'])
                    clean_text = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a.get_text()).strip()
                    if ntt_id not in posts or len(clean_text) > len(posts[ntt_id]['title']):
                        posts[ntt_id] = {'link': link, 'title': clean_text}
            for ntt_id, info in posts.items():
                if len(info['title']) < 5: continue
                date = "확인 불가"
                try:
                    d_resp = requests.get(info['link'], headers=headers, timeout=5)
                    d_resp.encoding = 'utf-8'
                    dm = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', BeautifulSoup(d_resp.text, 'html.parser').get_text())
                    if dm: date = dm.group(1).replace('.', '-').replace('/', '-')
                except: pass
                all_data.append({"기관": "산림청", "담당부서": "산림청", "날짜": date, "제목": info['title'], "링크": info['link']})
    except: pass

    # 4. 서울특별시
    try:
        for page in range(1, 3):
            url = f"https://www.seoul.go.kr/news/news_report.do?pageIndex={page}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag = row.find('a')
                tds = row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    link = urljoin("https://www.seoul.go.kr/news/", a_tag.get('href', ''))
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

    def render_table(filtered_df):
        if filtered_df.empty:
            st.info("검색 조건에 해당되는 보도자료가 없습니다.")
            return
        
        display_df = filtered_df.copy()
        display_df['제목'] = display_df.apply(lambda r: f"[{r['제목']}]({r['링크']})", axis=1)
        display_df = display_df[['기관', '담당부서', '날짜', '제목']]
        st.write(f"총 **{len(display_df)}**건 표시 중")
        st.markdown(display_df.to_markdown(index=False), unsafe_allow_html=True)

    with tabs[0]: render_table(df)
    with tabs[1]: render_table(df[df['기관'] == '국토교통부'])
    with tabs[2]: render_table(df[df['기관'] == '기후에너지환경부'])
    with tabs[3]: render_table(df[df['기관'] == '산림청'])
    with tabs[4]: render_table(df[df['기관'] == '서울특별시'])
else:
    st.error("데이터 수집 중 오류가 발생했습니다.")
