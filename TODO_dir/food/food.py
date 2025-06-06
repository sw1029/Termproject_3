'''
직원
학생
/html/body/div/form/div[3]/div[2]/table/tbody/tr[1]
/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]  조식

/html/body/div/form/div[3]/div[2]/table/tbody/tr[3]
/html/body/div/form/div[3]/div[2]/table/tbody/tr[4]  중식

/html/body/div/form/div[3]/div[2]/table/tbody/tr[5]
/html/body/div/form/div[3]/div[2]/table/tbody/tr[6]  석식

/html/body/div/form/div[3]/div[2]/table/tbody/tr[1]/td[4]  운영안함
/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]/td[2]   2학
/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]/td[3]   3학
/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]/td[4]   4학
/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]/td[5]   생과대


/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]/td[2]/ul/li/h3  ~~식(nnnn원)
/html/body/div/form/div[3]/div[2]/table/tbody/tr[2]/td[2]/ul/li/p/text()[1]  메뉴(숫자 동적임)



https://mobileadmin.cnu.ac.kr/food/index.jsp?searchYmd=2024.03.20&searchLang=OCL04.10&searchView=cafeteria&searchCafeteria=OCL03.02&Language_gb=OCL04.10#tmp


'''

import requests
from lxml import html
from datetime import datetime

from datetime import datetime
import requests
from lxml import html

def answer(inputDate: str, where: str, when: str, who: str) -> str:
    date_obj = datetime.strptime(inputDate, '%Y%m%d').date()
    if date_obj.weekday() >= 5:
        return '주말'
    time_str = date_obj.strftime('%Y.%m.%d')

    base_link = (
        f'https://mobileadmin.cnu.ac.kr/food/index.jsp'
        f'?searchYmd={time_str}'
        f'&searchLang=OCL04.10'
        f'&searchView=cafeteria'
        f'&searchCafeteria=OCL03.02'
        f'&Language_gb=OCL04.10#tmp'
    )

    if '1' in where:      caf_idx = 1
    elif '2' in where:    caf_idx = 2
    elif '3' in where:    caf_idx = 3
    elif '4' in where:    caf_idx = 4
    elif '생과대' in where or '생활' in where:
        caf_idx = 5
    else:
        return '올바르지 않은 요청'

    base_row = {'조식': 1, '중식': 3, '석식': 5}.get(when, None)
    if base_row is None:
        return '올바르지 않은 요청'

    if '직원' in who:
        row_idx = base_row
    elif '학생' in who:
        row_idx = base_row + 1
    else:
        return '올바르지 않은 요청'

    resp = requests.get(base_link)
    resp.raise_for_status()
    tree = html.fromstring(resp.content)

    table = tree.xpath("//table[contains(@class,'menu-tbl')]")
    if not table:
        return '올바르지 않은 요청'
    table = table[0]
    trs = table.xpath("./tbody/tr")
    if row_idx < 1 or row_idx > len(trs):
        return '올바르지 않은 요청'
    tr = trs[row_idx - 1]

    tds = tr.xpath("./td")
    first_cls = tds[0].get("class", "")
    offset = 2 if "building" in first_cls else 1

    target_idx = offset + (caf_idx - 2)
    if target_idx >= len(tds):
        return '운영안함'

    cell = tds[target_idx]
    text_all = cell.text_content().strip()
    if text_all == '운영안함':
        return '운영안함'

    result_lines = []
    for li in cell.xpath('.//ul/li'):
        hdr = li.xpath('./h3/text()')
        if hdr:
            result_lines.append(hdr[0].strip())
            result_lines.append('')
        for item in li.xpath('./p/text()'):
            item = item.strip()
            if item:
                result_lines.append(item)

    return "\n".join(result_lines) or '운영안함'




#print(answer('20240320','생활','중식','학생'))
