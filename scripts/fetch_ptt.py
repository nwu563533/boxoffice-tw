"""抓 PTT 電影板（movie）標題含片名的文章，當作「網路討論聲量」的一個指標。

PTT 是公開看板、不用登入，搜尋頁一頁 20 篇。發文時間從文章代碼取（M.<unix 秒>），
不用列表上只有月日的日期。推文數是列表上顯示的數字（爆＝100 以上，X 開頭＝噓多於推）。

用法：python3 scripts/fetch_ptt.py 搜尋字 [輸出檔名]
例：  python3 scripts/fetch_ptt.py 96分鐘
輸出：data/ptt/輸出檔名.csv（發文時間,分類,標題,推文數,網址）
"""
import csv, datetime, html, pathlib, re, ssl, sys, time, urllib.error, urllib.parse, urllib.request

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://www.ptt.cc'
ROW = re.compile(r'<div class="nrec">(.*?)</div>.*?<a href="(/bbs/movie/M\.(\d+)\.A\.\w+\.html)">(.*?)</a>', re.S)
TZ = datetime.timezone(datetime.timedelta(hours=8))


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (boxoffice-tw portfolio)', 'Cookie': 'over18=1'})
    with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
        return r.read().decode('utf-8', 'replace')


def main():
    q = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else q
    out, page = [], 1
    while True:
        try:
            text = get(f'{BASE}/bbs/movie/search?page={page}&q={urllib.parse.quote(q)}')
        except urllib.error.HTTPError as e:
            if e.code == 404:  # 超過最後一頁
                break
            raise
        rows = ROW.findall(text)
        if not rows:
            break
        for nrec, href, ts, title in rows:
            title = html.unescape(title).strip()
            m = re.match(r'(Re:\s*|Fw:\s*)?\[(.+?)\]', title)
            tag = (('回文・' if m.group(1) else '') + m.group(2).replace(' ', '')) if m else ''
            push = re.sub(r'<.*?>', '', nrec).strip()
            when = datetime.datetime.fromtimestamp(int(ts), TZ).strftime('%Y-%m-%d %H:%M')
            out.append([when, tag, title, push, BASE + href])
        page += 1
        time.sleep(0.6)
    out.sort()
    p = ROOT / 'data' / 'ptt' / f'{name}.csv'
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['發文時間', '分類', '標題', '推文數', '網址'])
        w.writerows(out)
    print(f'{q}：{len(out)} 篇（{page - 1} 頁）→ {p.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
