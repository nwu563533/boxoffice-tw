"""把 data/raw_daily/ 底下的截圖轉錄稿，整理成 data/daily_boxoffice.csv。

轉錄稿格式（一張截圖一段）：
  @日期|地區|類型         例：@2026-10-07|台北|單日、@2026-10-02~2026-10-04|全台|週末
  片名|票房(萬)|累計(萬)|人次|變動率
排名照出現順序。金額存成「元」。同一天同地區同類型如果重複出現，以後讀到的為準。

用法：python3 scripts/import_daily.py
"""
import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    rows = {}
    for p in sorted((ROOT / 'data' / 'raw_daily').glob('*.txt')):
        head, rank = None, 0
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('@'):
                head, rank = line[1:].split('|'), 0
                continue
            rank += 1
            name, amt, cum, people, change = line.split('|')
            key = (head[0], head[1], head[2], name)
            rows[key] = [head[0], head[1], head[2], rank, name, round(float(amt) * 1e4),
                         round(float(cum) * 1e4), people, change, '台北票房觀測站']
    # 缺單日貼文的那天（例如 10/4）用累計推回來：缺的那天 = 隔天累計 − 前一天累計 − 隔天票房。
    # 只補「前一天、隔天都有出現」的片；人次推不出來，留空；來源標「推算」。
    import datetime
    D = datetime.date.fromisoformat
    singles = {(r[0], r[1], r[4]): r for r in rows.values() if r[2] == '單日'}
    for region in {r[1] for r in rows.values()}:
        dates = sorted({r[0] for r in rows.values() if r[1] == region and r[2] == '單日'})
        for a, b in zip(dates, dates[1:]):
            if (D(b) - D(a)).days != 2:
                continue
            gap = (D(a) + datetime.timedelta(days=1)).isoformat()
            for (d, reg, name), r in list(singles.items()):
                if d != a or reg != region or (b, region, name) not in singles:
                    continue
                nxt = singles[(b, region, name)]
                amt = nxt[6] - r[6] - nxt[5]
                if amt >= 0:
                    rows[(gap, region, '單日', name)] = [gap, region, '單日', '', name, amt, nxt[6] - nxt[5], '', '', '推算（累計相減）']

    out = ROOT / 'data' / 'daily_boxoffice.csv'
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['日期', '地區', '類型', '排名', '片名', '票房', '累計', '人次', '變動率', '來源'])
        w.writerows(sorted(rows.values(), key=lambda r: (r[0], r[1], r[2], r[3] if r[3] != '' else 99, -r[5])))
    days = sorted({(r[0], r[1]) for r in rows.values()})
    print(f'{len(rows)} 筆，{len(days)} 個（日期×地區）→ {out.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
