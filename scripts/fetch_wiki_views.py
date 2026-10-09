"""抓中文維基百科條目的每日瀏覽量，當作「大眾關注度」的替代指標。

Threads、臉書要登入才能搜，不爬。維基百科有公開 API（Wikimedia Pageviews），
可以看大家什麼時候開始查一部片，跟票房曲線對照。

用法：python3 scripts/fetch_wiki_views.py 條目名稱 起日 迄日
例：  python3 scripts/fetch_wiki_views.py 大濛 2025-10-01 2026-06-01
輸出：data/wiki_views/條目名稱.csv（日期,瀏覽量）
"""
import csv, json, pathlib, ssl, sys, urllib.parse, urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/zh.wikipedia/all-access/user/{}/daily/{}/{}'


def main():
    title, start, end = sys.argv[1], sys.argv[2].replace('-', ''), sys.argv[3].replace('-', '')
    url = API.format(urllib.parse.quote(title, safe=''), start, end)
    req = urllib.request.Request(url, headers={'User-Agent': 'boxoffice-tw portfolio'})
    items = json.load(urllib.request.urlopen(req, timeout=60, context=CTX))['items']
    out = ROOT / 'data' / 'wiki_views' / f'{title}.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['日期', '瀏覽量'])
        for x in items:
            t = x['timestamp']
            w.writerow([f'{t[:4]}-{t[4:6]}-{t[6:8]}', x['views']])
    print(f'{title}：{len(items)} 天，合計 {sum(x["views"] for x in items):,} 次 → {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
