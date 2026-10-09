"""匯入 2018-07-30 到 2020-06-07 的每週全國票房（98 週）。

來源：github.com/Phate334/box-office-tw，把官方當年公布的週報表整理成 JSON。
只需要跑一次。

用法：python3 scripts/import_archive.py
輸出：data/weekly_archive_2018_2020.csv
"""
import csv, json, pathlib, ssl, urllib.request

try:  # 本機 python.org 版沒帶系統憑證，有 certifi 就用它；GitHub Actions 上不需要
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://phate334.github.io/box-office-tw/json/'


def get(url):
    with urllib.request.urlopen(url, timeout=60, context=CTX) as r:
        return json.load(r)


def main():
    weeks = get(BASE)
    out = ROOT / 'data' / 'weekly_archive_2018_2020.csv'
    n = 0
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['週', '片名', '上映日', '國別', '發行商', '院數', '當週票數', '當週金額', '累計票數', '累計金額'])
        for wk in weeks:
            for x in get(BASE + wk + '.json'):
                w.writerow([wk, x.get('中文片名'), x.get('上映日期'), x.get('國別地區'), x.get('申請人'), x.get('上映院數'),
                            x.get('銷售票數'), x.get('銷售金額'), x.get('累計銷售票數'), x.get('累計銷售金額')])
                n += 1
    print(f'{len(weeks)} 週，{n} 筆')


if __name__ == '__main__':
    main()
