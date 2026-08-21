import requests
import datetime
import os
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import urllib3
import holidays  # 한국 공휴일 자동 감지 라이브러리

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ASSEMBLY_API_KEY = "4771fb319fc6421c96f412002daa0e91"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID_STR = os.environ.get("TELEGRAM_CHAT_ID", "")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def send_telegram_msg(text, target_chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"발송 실패 ({target_chat_id}): {e}")

def main():
    kst_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    today_str = kst_now.strftime("%Y-%m-%d")
    yesterday_str = (kst_now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 🔥 주말(토=5, 일=6) 및 한국 법정 공휴일 체크
    kr_holidays = holidays.KR()
    if kst_now.weekday() >= 5 or kst_now in kr_holidays:
        print(f"오늘은 주말 또는 공휴일({today_str})입니다. 알림 발송을 건너뜁니다.")
        return

    target_dates = [today_str, yesterday_str]
    collected_items = []

    # 1. 국회 발의 법안 수집 (국토위, 환노위, 정무위)
    try:
        url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
        params = {"KEY": ASSEMBLY_API_KEY, "Type": "json", "pIndex": 1, "pSize": 100, "AGE": "22"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "nzmimeepazxkubdpn" in data:
            for r in data["nzmimeepazxkubdpn"][1]["row"]:
                date = r.get("PROPOSE_DT", "")
                if date in target_dates:
                    comm = r.get("COMMITTEE", "") or ""
                    title = r.get("BILL_NAME", "")
                    bill_id = r.get("BILL_ID", "")
                    proposer = r.get("PROPOSER", "국회의원")
                    
                    is_kokto = "국토" in comm or any(kw in title for kw in ["국토", "건축", "주택", "도로", "철도", "부동산", "교통"])
                    is_hwan = any(kw in comm for kw in ["환경", "노동"]) or any(kw in title for kw in ["기후", "환경", "폐기물", "노동", "에너지", "탄소"])
                    is_jungmu = "정무" in comm or any(kw in title for kw in ["금융", "공정거래", "보훈", "자본시장", "가상자산", "가맹", "하도급"])
                    
                    if is_kokto or is_hwan or is_jungmu:
                        comm_label = "📜 국토위" if is_kokto else ("📜 환노위" if is_hwan else "📜 정무위")
                        link = f"https://likms.assembly.go.kr/bill/bi/billDetailPage.do?billId={bill_id}"
                        collected_items.append(f"<b>[{comm_label}]</b> {title}\n• 발의자: {proposer} | {date}\n• <a href='{link}'>상세보기</a>")
    except Exception as e:
        print(f"국회 법안 수집 에러: {e}")

    # 2. 하위법령 입법예고 수집
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
                date_raw = tds[-1].get_text(separator=' ', strip=True)
                date_match = re.search(r'(20\d{2}[-.\/]\d{2}[-.\/]\d{2})', date_raw)
                clean_date = date_match.group(1).replace('.', '-') if date_match else date_raw
                
                if clean_date in target_dates:
                    collected_items.append(f"<b>[⚖️ 입법예고]</b> {title}\n• 소관부처: {dept} | {clean_date}\n• <a href='{link}'>상세보기</a>")
    except Exception as e:
        print(f"입법예고 수집 에러: {e}")

    # 메시지 조립 및 텔레그램 전송
    if collected_items:
        msg = f"☀️ <b>[{today_str} 출근 모닝 브리핑]</b>\n새로 업데이트된 주요 안건 목록입니다. ({len(collected_items)}건)\n\n"
        msg += "\n\n".join(collected_items)
    else:
        msg = f"☀️ <b>[{today_str} 출근 모닝 브리핑]</b>\n신규 업데이트된 주요 안건이 없습니다."

    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID_STR.split(",") if cid.strip()]
    for chat_id in chat_ids:
        send_telegram_msg(msg, chat_id)

if __name__ == "__main__":
    main()
