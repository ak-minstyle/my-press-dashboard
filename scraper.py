def fetch_mnd():
    items = []
    try:
        mnd_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "text/html"}
        for page in range(1, 4):
            url = f"https://www.mnd.go.kr/mnd/167/subview.do?pageIndex={page}"
            resp = requests.get(url, headers=mnd_headers, timeout=TIMEOUT, verify=False)
            soup = BeautifulSoup(resp.content.decode('utf-8', 'ignore'), 'html.parser')
            
            # 본문 메인 콘텐츠 영역 내부 요소만 필터링
            main_area = soup.select_one('#content') or soup.select_one('#contents') or soup
            rows = main_area.find_all('tr')
            
            for row in rows:
                tds = row.find_all('td')
                if len(tds) < 3:
                    continue
                
                # 🔥 [핵심] 202X-XX-XX 형식 날짜가 없는 메뉴/헤더 행은 100% 무조건 탈락
                date_match = re.search(r'(202\d)\s*[-.\/]\s*(\d{2})\s*[-.\/]\s*(\d{2})', row.text)
                if not date_match:
                    continue
                
                a_tag = row.find('a')
                if not a_tag:
                    continue
                
                clean_title = re.sub(r'새글|첨부파일|자세히보기|\s+', ' ', a_tag.get_text(strip=True)).strip()
                if len(clean_title) < 2 or clean_title in ["제목", "자세히보기", "번호", "구분", "작성일", "부서"]:
                    continue
                
                raw_href = str(a_tag.get('href', ''))
                onclick_attr = str(a_tag.get('onclick', ''))
                combined = raw_href + onclick_attr
                
                ntt_m = re.search(r'nttId=(\d+)|fn_[a-zA-Z_]*\([\'"]?(\d+)[\'"]?\)', combined)
                if not ntt_m:
                    continue
                
                ntt_id = ntt_m.group(1) or ntt_m.group(2)
                link = f"https://www.mnd.go.kr/mnd/167/subview.do?nttId={ntt_id}"
                date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                
                dept = "국방부"
                for td in tds:
                    t_text = td.get_text(strip=True)
                    if t_text and t_text != clean_title and not re.match(r'^\d+$', t_text) and not re.search(r'202\d', t_text):
                        if any(kw in t_text for kw in ["국방", "대변인", "정책", "기획", "인사", "전력", "과", "팀", "실", "본부"]):
                            dept = t_text
                            break
                            
                items.append({"기관": "국방부", "담당부서": dept, "날짜": date, "제목": clean_title, "링크": link})
    except: pass
    return items
