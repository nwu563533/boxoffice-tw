"""把官網「單片查詢 → 各週週末票房資料匯出」的 CSV 轉成乾淨的檔案。

官網匯出的 CSV 數字有千分位逗號卻沒加引號，跟欄位分隔的逗號混在一起，
例如「14,430,70,14,430,70」其實是 金額 14,430／票數 70／累計金額 14,430／累計票數 70。
這支程式把逗號之間的片段重新組回四個數字，條件是：
  這週累計金額 = 上週累計金額 + 這週金額，票數同理。

用法：python3 scripts/import_weekend_export.py 匯出檔.csv 片名
輸出：data/film_weekend/片名.csv（週末起日,週末迄日,院數,週末票數,週末金額,累計票數,累計金額）
"""
import csv, itertools, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def splits(tokens, k):
    """把逗號切開的片段組成 k 個合法的千分位數字，列出所有可能。"""
    n = len(tokens)
    for cuts in itertools.combinations(range(1, n), k - 1):
        parts = [tokens[a:b] for a, b in zip((0,) + cuts, cuts + (n,))]
        if all(1 <= len(p[0]) <= 3 and all(len(g) == 3 for g in p[1:]) for p in parts):
            yield [int(''.join(p)) for p in parts]


def parse(path):
    text = pathlib.Path(path).read_text(encoding='utf-8-sig')
    out, prev_amt, prev_tix = [], 0, 0
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        date, rest = line.split(',', 1)
        start, end = date.split('~')
        head, tail = rest.rsplit('%,', 1)          # 最後一欄是院數
        theaters = int(tail)
        toks = head.split(',')
        ok = set()
        # 變動率本身也可能有千分位（3,763.46%），所以變動率從哪個片段開始要逐一試
        for i in range(1, len(toks)):
            if not re.fullmatch(r'-?\d{1,3}(,\d{3})*\.\d+', ','.join(toks[i:])):
                continue
            body = toks[:i]
            if body[:2] == ['N/A', 'N/A']:
                ok |= {(0, 0, ca, ct) for ca, ct in splits(body[2:], 2) if (ca, ct) == (prev_amt, prev_tix)}
            else:
                ok |= {tuple(c) for c in splits(body, 4) if c[2] == prev_amt + c[0] and c[3] == prev_tix + c[1]}
        if len(ok) > 1:  # 還有歧義時，用平均票價合理（100～1,000 元）再篩一次
            ok = {c for c in ok if c[1] == 0 or 100 <= c[0] / c[1] <= 1000}
        if len(ok) != 1:
            raise SystemExit(f'{date} 拆不出唯一解：{ok}（原始：{rest}）')
        amt, tix, cum_amt, cum_tix = ok.pop()
        out.append([start, end, theaters, tix, amt, cum_tix, cum_amt])
        prev_amt, prev_tix = cum_amt, cum_tix
    return out


def main():
    src, name = sys.argv[1], sys.argv[2]
    rows = parse(src)
    dst = ROOT / 'data' / 'film_weekend' / f'{name}.csv'
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['週末起日', '週末迄日', '院數', '週末票數', '週末金額', '累計票數', '累計金額'])
        w.writerows(rows)
    print(f'{name}：{len(rows)} 個週末，週末累計 {rows[-1][6]:,} 元／{rows[-1][5]:,} 張 → {dst.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
