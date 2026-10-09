"""抓國家影視聽中心的全國票房開放資料，存快照，算出每週票房。

官方這支 API 只給「2016 年至今每部片的累計」，沒有每週明細。
所以每週存一份快照，跟上一份相減，就是那一週每部片賣了多少。

用法：python3 scripts/fetch_official.py
輸出：
  data/snapshots/YYYY-MM-DD.json   原始快照（檔名是資料截止的週日）
  data/national_cumulative.csv     最新一份快照的全部影片累計
  data/weekly_national.csv         相鄰快照相減得到的每週票房
"""
import csv, json, pathlib, ssl, urllib.request

try:  # 本機 python.org 版沒帶系統憑證，有 certifi 就用它；GitHub Actions 上不需要
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAP = ROOT / 'data' / 'snapshots'
URL = 'https://boxofficetw.tfai.org.tw/OpenData/statistic/since2016'


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (boxoffice-tw portfolio)'})
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r:
        return json.load(r)


def key(x):
    return (x['Name'].strip(), x['ReleaseDate'][:10])


def main():
    SNAP.mkdir(parents=True, exist_ok=True)
    d = fetch()
    end = d['End'][:10]
    path = SNAP / f'{end}.json'
    if path.exists():
        print(f'{end} 的快照已經有了，不重存')
    else:
        path.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        print(f'存了新快照 {end}，{len(d["List"])} 部片')

    snaps = sorted(SNAP.glob('*.json'))
    latest = json.loads(snaps[-1].read_text(encoding='utf-8'))['List']
    cols = ['Name', 'ReleaseDate', 'Country', 'Issue', 'Produce', 'TheaterCount', 'TotalTickets', 'TotalAmounts']
    with open(ROOT / 'data' / 'national_cumulative.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['片名', '上映日', '國別', '發行商', '製作', '院數', '累計票數', '累計金額'])
        for x in sorted(latest, key=lambda x: x['ReleaseDate'], reverse=True):
            w.writerow([x[c] if c != 'ReleaseDate' else x[c][:10] for c in cols])

    rows = []
    for a, b in zip(snaps, snaps[1:]):
        prev = {key(x): x for x in json.loads(a.read_text(encoding='utf-8'))['List']}
        for x in json.loads(b.read_text(encoding='utf-8'))['List']:
            p = prev.get(key(x))
            t = x['TotalTickets'] - (p['TotalTickets'] if p else 0)
            m = (x['TotalAmounts'] or 0) - ((p['TotalAmounts'] or 0) if p else 0)
            if t or m:
                rows.append([b.stem, x['Name'].strip(), x['ReleaseDate'][:10], x['Issue'], x['TheaterCount'], t, round(m)])
    with open(ROOT / 'data' / 'weekly_national.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['週截止日', '片名', '上映日', '發行商', '院數', '當週票數', '當週金額'])
        w.writerows(rows)
    print(f'快照 {len(snaps)} 份，算出 {len(rows)} 筆每週資料')


if __name__ == '__main__':
    main()
