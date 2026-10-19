"""Produce a review issue for changed schedules and newly discovered event/feed candidates."""
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'reports/latest.json').read_text())
changes=r.get('watch_changes',[])+r.get('possible_date_changes',[])
discovery_path=root/'reports/discovery.json'
discovery=json.loads(discovery_path.read_text()) if discovery_path.exists() else {}
new_events=discovery.get('event_candidates',[])
new_feeds=discovery.get('calendar_feed_candidates',[])
if not changes and not new_events and not new_feeds:sys.exit(2)
lines=['## Kart Atlas schedule-review queue','Organizer-source content changed or new event candidates were found. Verify before publishing.','']
for c in changes[:20]:
    if 'club' in c:lines.append(f"- **{c['club']}** — {c['url']} — review organizer schedule")
    else:lines.append(f"- **{c['name']}** — previously {c['original_start']}; feed now {c['new_start']} — {c['source']}")
if new_events:
    lines.append('')
    lines.append('## Structured event candidates')
    for e in new_events[:30]:
        lines.append(f"- **{e['name']}** — {e['start']} — {e['organizer']} — {e['source']}")
if new_feeds:
    lines.append('')
    lines.append('## Newly discovered calendar feeds')
    for f in new_feeds[:30]:
        lines.append(f"- **{f['club']}** — {f['url']}")
lines.append('')
lines.append('Review sources and update curated races or allowlisted feeds after verification.')
(root/'reports/issue.md').write_text('\\n'.join(lines)+'\\n')
