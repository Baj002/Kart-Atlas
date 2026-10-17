"""Produce GitHub issue description only when a newly changed organizer schedule needs review."""
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'reports/latest.json').read_text())
changes=r.get('watch_changes',[])+r.get('possible_date_changes',[])
if not changes:sys.exit(2)
lines=['## Kart Atlas schedule-review queue','Organizer-source content changed. Changes to general HTML pages are **not yet verified race changes**.','']
for c in changes[:20]:
    if 'club' in c:lines.append(f"- **{c['club']}** — {c['url']} — review organizer schedule")
    else:lines.append(f"- **{c['name']}** — previously {c['original_start']}; feed now {c['new_start']} — {c['source']}")
lines.append('\nUpdate `data/races.csv` after verifying any changes. The automated feed never overrides manually curated events.')
(root/'reports/issue.md').write_text('\n'.join(lines)+'\n')
