import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TIMEOUT = 10 

def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try: requests.post(url, data=payload, timeout=5)
    except: pass

def fetch_molit_detail(item):
    try:
        resp = requests.get(item['링크'], headers=HEADERS, timeout=TIMEOUT, verify=False)
        soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
        for f in soup.find_all('a'):
            m = re.search(r'\(([가-힣]+(과|팀|단|실))\)', f.text)
            if m:
                item['담당부서'] = m.group(1)
                break
    except: pass
    return item

def fetch_molit():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp?cate=1&search_page={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 4:
                    items.append({"기관": "국토교통부", "담당부서": "국토교통부", "날짜": tds[3].text.strip(), "제목": a_tag.text.strip(), "링크": "https://www.molit.go.kr/USR/NEWS/m_71/" + a_tag['href']})
        with ThreadPoolExecutor(max_workers=10) as executor:
            items = list(executor.map(fetch_molit_detail, items))
    except: pass
    return items

def fetch_mcee():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mcee.go.kr/home/web/index.do?menuId=10598&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 5:
                    items.append({"기관": "기후에너지환경부", "담당부서": tds[-4].get_text(separator=' ', strip=True), "날짜": tds[-2].text.strip(), "제목": a_tag.text.strip(), "링크": urljoin("https://www.mcee.go.kr/home/web/", a_tag.get('href', ''))})
    except: pass
    return items

def fetch_forest():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.forest.go.kr/kfsweb/cop/bbs/selectBoardList.do?mn=NKFS_04_02_01&bbsId=BBSMSTR_1036&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            posts = {}
            for a in soup.find_all('a', href=re.compile(r'nttId=')):
                raw_href = a.get('href', '')
                ntt_m = re.search(r'nttId=(\d+)', raw_href)
                if not ntt_m: continue
                parent_box = a.find_parent(['li', 'tr', 'td', 'div'])
                box_text = parent_box.get_text(separator=' ', strip=True) if parent_box else a.get_text()
                dm = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', box_text)
                date = dm.group(1).replace('.', '-').replace('/', '-') if dm else "날짜 미표기"
                clean_title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a.get_text()).strip()
                clean_title = re.sub(r'20\d{2}[-.\/]\d{2}[-.\/]\d{2}', '', clean_title).strip()
                posts[ntt_m.group(1)] = {"기관": "산림청", "담당부서": "산림청", "날짜": date, "제목": clean_title, "링크": urljoin("https://www.forest.go.kr", raw_href)}
            items.extend(posts.values())
    except: pass
    return items

def fetch_seoul():
    items = []
    try:
        for page in range(1, 6):
            url = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&curPage={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 3:
                    raw_href = a_tag.get('href', '')
                    ntt_m = re.search(r'nttNo=(\d+)|(\d{5,})', raw_href)
                    link = f"https://www.seoul.go.kr/news/news_report.do?bbsNo=158&nttNo={ntt_m.group(1) or ntt_m.group(2)}" if ntt_m else urljoin("https://www.seoul.go.kr/news/", raw_href)
                    items.append({"기관": "서울특별시", "담당부서": tds[-2].get_text(separator=' ', strip=True), "날짜": tds[-1].text.strip(), "제목": a_tag.text.strip(), "링크": link})
    except: pass
    return items

def fetch_ftc():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.ftc.go.kr/www/selectBbsNttList.do?bordCd=3&key=12&searchCtgry=01,02&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 3:
                    dept = "공정위"
                    for idx, td in enumerate(tds):
                        if td.find('a') and idx + 1 < len(tds):
                            dept_text = tds[idx + 1].get_text(separator=' ', strip=True)
                            if dept_text and not re.search(r'^\d{4}[-.\/]', dept_text): dept = dept_text; break
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    items.append({"기관": "공정거래위원회", "담당부서": dept, "날짜": date_match.group(1).replace('.', '-') if date_match else "날짜 미표기", "제목": a_tag.text.strip(), "링크": urljoin("https://www.ftc.go.kr/www/", a_tag.get('href', ''))})
    except: pass
    return items

def fetch_mois():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardList.do?bbsId=BBSMSTR_000000000008&pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            for row in soup.select('table tbody tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 3:
                    raw_href = a_tag.get('href', '')
                    ntt_match = re.search(r"nttId=(\d+)|'(\d{5,})'", str(row) + raw_href)
                    link = f"https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId={ntt_match.group(1) or ntt_match.group(2)}" if ntt_match else urljoin("https://www.mois.go.kr/frt/bbs/type010/", raw_href)
                    dept_text = tds[-3].get_text(separator=' ', strip=True) if len(tds) >= 3 else "행정안전부"
                    date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    items.append({"기관": "행정안전부", "담당부서": dept_text if dept_text and not re.search(r'^\d{4}[-.\/]', dept_text) else "행정안전부", "날짜": date_match.group(1).replace('.', '-') if date_match else "날짜 미표기", "제목": a_tag.text.strip(), "링크": link})
    except: pass
    return items

# 🎖️ 국방부 파서 (기본 국토부/기후부 방식으로 단일화)
def fetch_mnd():
    items = []
    try:
        for page in range(1, 4):
            url = f"https://www.mnd.go.kr/mnd/167/subview.do?pageIndex={page}"
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            
            for row in soup.select('table tbody tr'):
                a_tag, tds = row.find('a'), row.find_all('td')
                if a_tag and len(tds) >= 3:
                    title = a_tag.text.strip()
                    if not title or len(title) < 2 or title in ["제목", "번호", "작성일"]:
                        continue
                    
                    href = a_tag.get('href', '')
                    link = urljoin("https://www.mnd.go.kr/mnd/167/subview.do", href)
                    
                    date_match = re.search(r'(202\d[-.\/]\d{2}[-.\/]\d{2})', row.text)
                    date = date_match.group(1).replace('.', '-') if date_match else tds[-2].text.strip()
                    
                    dept = "국방부"
                    for td in tds:
                        t = td.get_text(strip=True)
                        if t and t != title and not re.search(r'202\d', t) and not t.isdigit():
                            if any(kw in t for kw in ["국방", "대변인", "정책", "기획", "인사", "전력", "과", "팀", "실", "본부"]):
                                dept = t
                                break
                    
                    items.append({
                        "기관": "국방부",
                        "담당부서": dept,
                        "날짜": date,
                        "제목": title,
                        "링크": link
                    })
    except: pass
    return items

def fetch_sub_legislation():
    items = []
    
    # 1. 입법예고 가져오기
    try:
        url = "https://opinion.lawmaking.go.kr/gcom/ogLmPp"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
        for row in soup.find_all('tr'):
            a_tag, tds = row.find('a'), row.find_all('td')
            if a_tag and len(tds) >= 6:
                title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a_tag.get_text(strip=True)).strip()
                if title and len(title) > 1 and "공고번호" not in title:
                    items.append({"기관": "⚖️ 입법예고", "담당부서": tds[-6].get_text(separator=' ', strip=True), "날짜": tds[-4].get_text(separator=' ', strip=True), "제목": title, "링크": urljoin("https://opinion.lawmaking.go.kr", a_tag.get('href', ''))})
    except: pass

    # 2. 행정예고 가져오기 (수정된 부분)
    try:
        url = "https://opinion.lawmaking.go.kr/gcom/admpp"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
        
        for row in soup.find_all('tr'):
            a_tag, tds = row.find('a'), row.find_all('td')
            if a_tag and len(tds) >= 3:
                
                # [추가된 핵심 코드]
                # a 태그 안에 들어있는 'ogmark' 관련 span 태그(진행 뱃지)를 찾아서 완전히 제거
                for span in a_tag.find_all('span', class_=re.compile(r'ogmark')):
                    span.decompose()

                # '진행' 태그가 잘려나간 상태에서 pure 텍스트만 가져온 뒤 불필요한 공백 정제
                title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a_tag.get_text(strip=True)).strip()
                
                if title and len(title) > 1 and "공고번호" not in title:
                    items.append({
                        "기관": "⚖️ 행정예고", 
                        "담당부서": tds[-3].get_text(separator=' ', strip=True), 
                        "날짜": tds[-2].text.strip(), 
                        "제목": title, 
                        "링크": urljoin("https://opinion.lawmaking.go.kr", a_tag.get('href', ''))
                    })
    except: pass

    return items

def main():
    fetch_functions = [
        fetch_sub_legislation, fetch_molit, fetch_mcee, fetch_forest, 
        fetch_seoul, fetch_ftc, fetch_mois, fetch_mnd
    ]
    
    all_data = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(func) for func in fetch_functions]
        for future in as_completed(futures):
            res = future.result()
            if res: all_data.extend(res)
            
    df_new = pd.DataFrame(all_data)
    DATA_FILE = "data.csv"
    
    if os.path.exists(DATA_FILE):
        df_old = pd.read_csv(DATA_FILE)
        
        # 기존 국방부 오염 데이터 제거 및 덮어쓰기
        df_old = df_old[df_old['기관'] != '국방부']
        df_old = df_old[~df_old['제목'].str.contains("🚨", na=False)]
        
        if not df_new.empty:
            fetched_orgs = df_new['기관'].unique()
            df_old_kept = df_old[~df_old['기관'].isin(fetched_orgs)]
            df_final = pd.concat([df_new, df_old_kept], ignore_index=True)
        else:
            df_final = df_old
    else:
        df_final = df_new

    if df_final.empty:
        return

    df_final = df_final.drop_duplicates(subset=['기관', '제목', '날짜'], keep='first')
    df_final['sort_date'] = pd.to_datetime(df_final['날짜'].str.extract(r'(\d{4}[-.\/]\d{2}[-.\/]\d{2})')[0], errors='coerce')
    df_final = df_final.sort_values(by='sort_date', ascending=False, na_position='last').drop(columns=['sort_date'])

    if os.path.exists(DATA_FILE) and not df_new.empty:
        existing_links = set(df_old['링크'].astype(str)) if 'df_old' in locals() else set()
        new_items = df_new[~df_new['링크'].astype(str).isin(existing_links)]
        
        if not new_items.empty:
            for _, row in new_items.head(5).iterrows():
                msg = f"🔔 <b>[새 업데이트] {row['기관']}</b>\n부서: {row['담당부서']}\n제목: <a href='{row['링크']}'>{row['제목']}</a>\n날짜: {row['날짜']}"
                send_telegram(msg)
            if len(new_items) > 5:
                send_telegram(f"<i>...외 {len(new_items) - 5}건의 새로운 업데이트가 있습니다.</i>")

    df_final.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
