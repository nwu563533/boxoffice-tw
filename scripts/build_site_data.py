"""把 data/ 底下的檔案整理成網站讀的一份 site/data.json。

每次資料有更新（官方快照、台北每日、行銷事件、單片明細）都跑一次。
用法：python3 scripts/build_site_data.py
"""
import csv, collections, datetime, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / 'data'


def rows(name):
    p = D / name
    if not p.exists():
        return []
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def norm(name):
    """比對片名用：拿掉空格與常見標點，官方資料跟粉專的寫法才對得上"""
    return re.sub(r'[\s：:・·\-－—()（）《》〈〉]', '', name or '')


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0


def main():
    cum = rows('national_cumulative.csv')
    films = rows('films.csv')
    by_name = {}
    for r in cum:
        by_name.setdefault(r['片名'], r)

    weekly = collections.defaultdict(list)
    for r in rows('weekly_national.csv'):
        weekly[r['片名']].append({'week': r['週截止日'], 'theaters': num(r['院數']),
                                 'tickets': num(r['當週票數']), 'amount': num(r['當週金額'])})
    for p in sorted((D / 'film_weekly').glob('*.csv')):
        with open(p, encoding='utf-8') as f:
            manual = [{'week': r['週截止日'], 'theaters': num(r['院數']), 'tickets': num(r['當週票數']),
                       'amount': num(r['當週金額'])} for r in csv.DictReader(f)]
        have = {w['week'] for w in weekly[p.stem]}
        weekly[p.stem] += [w for w in manual if w['week'] not in have]

    weekend = collections.defaultdict(list)
    for p in sorted((D / 'film_weekend').glob('*.csv')):
        with open(p, encoding='utf-8') as f:
            weekend[p.stem] = [{'start': r['週末起日'], 'week': r['週末迄日'], 'theaters': num(r['院數']),
                                'tickets': num(r['週末票數']), 'amount': num(r['週末金額'])} for r in csv.DictReader(f)]

    events = collections.defaultdict(list)
    for r in rows('events.csv'):
        events[r['片名']].append({'date': r['日期'], 'type': r['類型'], 'text': r['事件'], 'link': r['來源連結']})
    taipei = collections.defaultdict(list)
    for r in rows('taipei_daily.csv'):
        taipei[r['片名']].append({'date': r['日期'], 'amount': num(r['台北票房'])})

    wiki = {}
    for p in sorted((D / 'wiki_views').glob('*.csv')):
        wk = collections.OrderedDict()
        with open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                d = datetime.date.fromisoformat(r['日期'])
                end = (d + datetime.timedelta(days=6 - d.weekday())).isoformat()  # 歸到週日結束的那一週
                wk[end] = wk.get(end, 0) + int(r['瀏覽量'])
        wiki[p.stem] = [{'week': k, 'views': v} for k, v in wk.items()]

    # 案例用的多條時間線（片方／媒體／明星宣傳／網路聲量）、新聞報導的累計里程碑、PTT 每週發文數
    timeline, milestones, ptt = {}, {}, {}
    for p in sorted((D / 'timeline').glob('*.csv')):
        with open(p, encoding='utf-8') as f:
            timeline[p.stem] = [{'date': r['日期'], 'lane': r['線'], 'type': r['類型'], 'text': r['事件'],
                                 'link': r['來源連結'], 'seen': r['可信度']} for r in csv.DictReader(f)]
    for p in sorted((D / 'milestones').glob('*.csv')):
        with open(p, encoding='utf-8') as f:
            milestones[p.stem] = [{'date': r['日期'], 'amount': num(r['累計票房']), 'text': r['說明'], 'link': r['來源連結']}
                                  for r in csv.DictReader(f)]
    for p in sorted((D / 'ptt').glob('*.csv')):
        wk = collections.Counter()
        with open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                d = datetime.date.fromisoformat(r['發文時間'][:10])
                wk[(d + datetime.timedelta(days=6 - d.weekday())).isoformat()] += 1
        ptt[p.stem] = [{'week': k, 'posts': v} for k, v in sorted(wk.items())]

    out_films = []
    for f in films:
        c = by_name.get(f['片名'], {})
        out_films.append({
            'name': f['片名'], 'release': f['上映日'], 'group': f['分組'], 'why': f['為什麼選'],
            'distributor': c.get('發行商', ''), 'producer': c.get('製作', ''), 'theaters': num(c.get('院數')),
            'tickets': num(c.get('累計票數')), 'amount': num(c.get('累計金額')),
            'weekly': sorted(weekly.get(f['片名'], []), key=lambda w: w['week']),
            'weekend': weekend.get(f['片名'], []),
            'events': sorted(events.get(f['片名'], []), key=lambda e: e['date']),
            'taipei': sorted(taipei.get(f['片名'], []), key=lambda t: t['date']),
            'wiki': wiki.get(f['片名'], []),
            'timeline': sorted(timeline.get(f['片名'], []), key=lambda e: e['date']),
            'milestones': milestones.get(f['片名'], []),
            'ptt': ptt.get(f['片名'], []),
        })

    tw = [r for r in cum if r['國別'] in ('中華民國', '台灣', '臺灣') and r['上映日'][:4] in ('2025', '2026')]
    dist = collections.defaultdict(lambda: {'films': 0, 'amount': 0, 'titles': []})
    for r in tw:
        k = r['發行商'] or '（未登記）'
        dist[k]['films'] += 1
        dist[k]['amount'] += num(r['累計金額'])
        dist[k]['titles'].append(r['片名'])
    dist_list = sorted(({'name': k, **v} for k, v in dist.items()), key=lambda x: -x['amount'])

    nat = rows('weekly_national.csv')
    last = max((r['週截止日'] for r in nat), default='')
    tw_names = {norm(r['片名']) for r in cum if r['國別'] in ('中華民國', '台灣', '臺灣')}
    this_week = sorted(({'name': r['片名'], 'distributor': r['發行商'], 'theaters': num(r['院數']),
                         'amount': num(r['當週金額']), 'tw': norm(r['片名']) in tw_names}
                        for r in nat if r['週截止日'] == last), key=lambda x: -x['amount'])[:10]
    daily = rows('daily_boxoffice.csv')
    taipei_daily = [{'date': r['日期'], 'film': r['片名'], 'amount': num(r['票房']), 'rank': int(r['排名'] or 99),
                     'derived': r['來源'].startswith('推算')}
                    for r in daily if r['地區'] == '台北' and r['類型'] == '單日']
    latest_tp = max((r['date'] for r in taipei_daily), default='')
    latest_all = max((r['日期'] for r in daily if r['地區'] == '全台' and r['類型'] == '單日'), default='')
    def day_table(region, date):
        return [{'rank': int(r['排名'] or 99), 'film': r['片名'], 'amount': num(r['票房']), 'cum': num(r['累計']),
                 'people': r['人次'], 'change': r['變動率'], 'tw': norm(r['片名']) in tw_names}
                for r in daily if r['地區'] == region and r['類型'] == '單日' and r['日期'] == date]

    # 最新週末：粉專週一公布的完整版（有人次），日期鍵是「起~迄」字串，取最新的一個
    def weekend(region):
        keys = sorted({r['日期'] for r in daily if r['地區'] == region and r['類型'] == '週末'})
        if not keys:
            return {'date': '', 'rows': [], 'total': None}
        k = keys[-1]
        tot = next((t for t in (rows('weekend_totals.csv') if (D / 'weekend_totals.csv').exists() else [])
                    if t['日期'] == k and t['地區'] == region), None)
        return {'date': k, 'total': {'amount': num(tot['總票房']), 'people': tot['總人次'], 'change': tot['較上週']} if tot else None,
                'rows': [{'rank': int(r['排名'] or 99), 'film': r['片名'], 'amount': num(r['票房']), 'cum': num(r['累計']),
                          'people': r['人次'], 'change': r['變動率'], 'tw': norm(r['片名']) in tw_names}
                         for r in daily if r['地區'] == region and r['類型'] == '週末' and r['日期'] == k]}

    snaps = sorted((D / 'snapshots').glob('*.json'))
    out = {
        'updated': snaps[-1].stem if snaps else '',
        'snapshots': len(snaps),
        'films': out_films,
        'top_tw': sorted(({'name': r['片名'], 'release': r['上映日'], 'distributor': r['發行商'],
                           'amount': num(r['累計金額']), 'tickets': num(r['累計票數'])} for r in tw),
                         key=lambda x: -x['amount'])[:15],
        'distributors': dist_list[:15],
        'this_week': this_week,
        'this_week_label': f'{last} 那一週' if last else '',
        'taipei_daily': taipei_daily,
        'taipei_latest': {'date': latest_tp, 'rows': day_table('台北', latest_tp)},
        'national_latest': {'date': latest_all, 'rows': day_table('全台', latest_all)},
        'weekend_taipei': weekend('台北'),
        'weekend_national': weekend('全台'),
    }
    (ROOT / 'site' / 'data.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
    print(f"site/data.json：{len(out_films)} 部追蹤片、{len(tw)} 部 2025–26 國片、{len(dist_list)} 家發行商，資料截至 {out['updated']}")


if __name__ == '__main__':
    main()
