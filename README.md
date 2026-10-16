# 國片票房觀察

用全國票房開放資料，看台灣電影怎麼被賣出去：哪個行銷動作之後，票房動了。

- **案例分析**：挑幾部國片，把週末票房、行銷事件、維基百科瀏覽量疊在一起看
- **票房追蹤**：全國週票房每週三自動更新；台北每日票房手動整理

製作：Nicole Wu

## 資料來源

| 資料 | 來源 | 更新 |
|---|---|---|
| 全國累計票房 | 國家電影及視聽文化中心「全國電影票房統計」開放資料 | 每週自動（GitHub Actions） |
| 單片週末票房 | 同上，單片查詢頁手動匯出 | 手動 |
| 2018–2020 每週票房 | [Phate334/box-office-tw](https://github.com/Phate334/box-office-tw) | 一次匯入 |
| 台北／全台每日票房 | 臉書粉專「台北票房觀測站」每日貼文，人工轉錄 | 手動 |
| 行銷事件 | 新聞、戲院與官方公告，每筆附來源 | 手動 |
| 關注度 | Wikimedia Pageviews API | 手動 |
| PTT 討論量 | PTT 電影板標題搜尋（`data/ptt/`） | 手動 |
| YouTube 宣傳影片 | 影片頁的上架時間與觀看數（`data/youtube/`） | 手動 |
| 四線時間軸 | 片方／媒體／明星宣傳／網路聲量，每筆附來源與可信度（`data/timeline/`） | 手動 |
| 累計里程碑 | 沒有官方週末明細時，用新聞報導的累計數字（`data/milestones/`） | 手動 |

官方開放資料只提供累計數字，每週票房是相鄰兩週快照相減而得。

## 資料夾

```
scripts/   抓資料、轉檔、整理成網站資料的程式
data/      所有資料（CSV），每次更新都有版本紀錄
site/      網站（GitHub Pages 從這裡部署）
```

## 常用指令

```
python3 scripts/fetch_official.py                    # 抓官方資料、存快照
python3 scripts/import_weekend_export.py 檔案.csv 片名  # 轉官網單片週末票房匯出檔
python3 scripts/import_daily.py                      # 轉台北票房觀測站截圖轉錄稿
python3 scripts/fetch_wiki_views.py 條目 起日 迄日      # 抓維基瀏覽量
python3 scripts/fetch_ptt.py 片名                    # 抓 PTT 電影板標題含片名的文章
python3 scripts/build_site_data.py                   # 整理成 site/data.json
```
