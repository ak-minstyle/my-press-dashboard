import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
url = "https://www.mnd.go.kr/mnd/167/subview.do?pageIndex=1"

resp = requests.get(url, headers=headers, verify=False)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'html.parser')

print("=== 국방부 보도자료 파싱 테스트 ===\n")
for i, row in enumerate(soup.find_all('tr')):
    a_tag = row.find('a')
    if not a_tag: continue
    
    title = a_tag.get_text(strip=True)
    if "자세히보기" in title or len(title) < 2: continue
    
    # 💡 [핵심] td-etc 클래스들 중에서 담당부서만 정확히 골라내기
    dept = "국방부"
    etc_tds = row.find_all('td', class_=re.compile(r'td-etc'))
    
    for td in etc_tds:
        text = td.get_text(strip=True)
        # 텍스트가 비어있지 않고, 숫자(조회수)가 아니며, 202X(날짜)가 아닌 것을 부서명으로 확정
        if text and not re.match(r'^\d+$', text) and not re.search(r'20\d{2}', text):
            dept = text
            break
            
    print(f"부서: {dept} | 제목: {title}")
