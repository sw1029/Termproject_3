import requests
from bs4 import BeautifulSoup


def answer(year: int, month: str = None):
    """
    Args:
        year (int): 조회할 연도 (예: 2024)
        month (str, optional): 조회할 월 (두 자리 문자열, 예: '05'). 지정하지 않으면 전체 조회.
    """
    base_url = 'https://plus.cnu.ac.kr/_prog/academic_calendar/'
    params = {
        'site_dvs_cd': 'kr',
        'menu_dvs_cd': '05020101',
        'year': str(year)
    }
    if month:
        params['month'] = month  # '01', '02', … '12'

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content.decode('utf-8'), 'lxml')

    results = []
    # 각 달 블록을 순회
    for box in soup.select('div.calen_box'):
        # 한국어 월 (예: '01월', '02월', …) :contentReference[oaicite:0]{index=0}
        month_kor = box.select_one('div.fl_month strong').get_text(strip=True)
        # 해당 달의 일정 목록
        for li in box.select('div.fr_list li'):
            date_text = li.select_one('strong').get_text(strip=True)
            desc = li.select_one('span.list').get_text(strip=True)
            results.append({
                'month': month_kor,
                'date': date_text,
                'description': desc
            })
    return results



#cal = fetch_academic_calendar(2024)
#for e in cal: print(f"{e['month']} {e['date']}: {e['description']}")
