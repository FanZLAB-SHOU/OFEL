"""Record today's Busuanzi site totals for the More page's daily visit chart.

Busuanzi only reports running totals, so a daily chart needs one reading per day. Run at 00:00
Beijing time (the workflow does this); the reading is stored under that Beijing date in
assets/stats/busuanzi-daily.json.

Each reading is itself counted by Busuanzi as one visit and one visitor. Every entry therefore keeps
`reads`, the cumulative number of snapshot readings, so the page can subtract them.
Usage: python3 scripts/snapshot-busuanzi.py [--date YYYY-MM-DD]
"""

import argparse
import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / 'assets' / 'stats' / 'busuanzi-daily.json'
API = 'https://busuanzi.ibruce.info/busuanzi?jsonpCallback=BusuanziCallback_snapshot'
# A path that is not a real page, so the reading never inflates a page's own count.
REFERER = 'https://fanzhang-lab-shou.github.io/OFEL/__visit-snapshot__/'
BEIJING = timezone(timedelta(hours=8))


def read_totals():
    request = urllib.request.Request(API, headers={'Referer': REFERER, 'User-Agent': 'Mozilla/5.0 (OFEL visit snapshot)'})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode('utf-8')
    match = re.search(r'\((\{.*\})\)', body)
    if not match:
        raise SystemExit(f'Unexpected Busuanzi response: {body[:200]}')
    data = json.loads(match.group(1))
    pv, uv = data.get('site_pv'), data.get('site_uv')
    if not (isinstance(pv, int) and isinstance(uv, int) and pv >= 0 and uv >= 0):
        raise SystemExit(f'Invalid Busuanzi totals: {data}')
    return pv, uv


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--date', help='Beijing date to record (default: today in Beijing)')
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    date = args.date or now.astimezone(BEIJING).date().isoformat()
    store = json.loads(STORE.read_text()) if STORE.exists() else {'source': 'busuanzi', 'timezone': 'Asia/Shanghai', 'snapshots': []}
    snapshots = store['snapshots']
    if any(entry['date'] == date for entry in snapshots):
        print(f'Snapshot for {date} already recorded; nothing to do.')
        return
    pv, uv = read_totals()
    reads = (snapshots[-1]['reads'] if snapshots else 0) + 1
    snapshots.append({'date': date, 'site_pv': pv, 'site_uv': uv, 'reads': reads, 'at': now.isoformat(timespec='seconds').replace('+00:00', 'Z')})
    snapshots.sort(key=lambda entry: entry['date'])
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(store, indent=1) + '\n')
    print(f'Recorded {date}: site_pv={pv}, site_uv={uv}, reads={reads}.')


if __name__ == '__main__':
    main()
