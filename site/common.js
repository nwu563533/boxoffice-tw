// 兩頁共用：數字格式、讀 CSS 變數、事件歸週
const fmt = n => n >= 1e8 ? (n/1e8).toFixed(2)+' 億' : n >= 1e4 ? Math.round(n/1e4).toLocaleString()+' 萬' : Math.round(n).toLocaleString();
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

// 事件歸到它所在的那一週（週一到週日），算進那個週日結束的週末；範圍外的事件只列在清單
function weekOf(date, weeks) {
  const d = new Date(date);
  const hit = weeks.find(w => { const end = new Date(w.week); return d <= end && (end - d) / 864e5 <= 6; });
  return hit ? hit.week : null;
}
