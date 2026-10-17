"""Offline regression checks. No web request or paid service needed."""
import copy,datetime as dt,json,tempfile,unittest
from pathlib import Path
from scripts.build_site import build
from scripts.check_sources import normalized_ics,parse_ics,run,visible_text

FEED='''BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:race-23@example.test
DTSTART;VALUE=DATE:20270301
DTEND;VALUE=DATE:20270303
SUMMARY:TRAK Race 23
URL:https://goodwoodkartways.com/trak/
END:VEVENT
BEGIN:VEVENT
UID:practice-1@example.test
DTSTART;VALUE=DATE:20270305
DTEND;VALUE=DATE:20270306
SUMMARY:Kart Owner Lapping / Practice
END:VEVENT
BEGIN:VEVENT
UID:rental@example.test
DTSTART;VALUE=DATE:20270305
DTEND;VALUE=DATE:20270306
SUMMARY:Mini Indy Championship Race
END:VEVENT
BEGIN:VEVENT
UID:cancelled@example.test
DTSTART;VALUE=DATE:20270306
SUMMARY:TRAK Race 24
STATUS:CANCELLED
END:VEVENT
END:VCALENDAR
'''
SOURCE={'id':'test-ics','club':'Goodwood Kartways','city':'Uxbridge','region':'ON','country':'Canada','venue':'Goodwood Kartways','url':'https://example.test/calendar.ics','mode':'ics','auto_import':True,'level':'Club'}

class TestIngest(unittest.TestCase):
    def test_ics_safe_dates_and_filters(self):
        events=normalized_ics(FEED,SOURCE,dt.date(2026,10,16))
        self.assertEqual(len(events),1)
        self.assertEqual((events[0]['start'],events[0]['end']),('2027-03-01','2027-03-02'))
        self.assertEqual(events[0]['verification'],'Automated')
    def test_ics_recurring_skipped(self):
        feed=FEED.replace('UID:race-23@example.test','UID:race-23@example.test\nRRULE:FREQ=DAILY')
        self.assertEqual(normalized_ics(feed,SOURCE,dt.date(2026,10,16)),[])
    def test_html_watch_normalization(self):
        self.assertEqual(visible_text('<html><script>fake race</script><p>Race 1</p>\n <p>June 1</p></html>'),'Race 1 June 1')
    def test_baseline_then_changed_then_fetch_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)
            for sub in ('data','site','reports'): (r/sub).mkdir()
            (r/'data/monitor_sources.json').write_text(json.dumps({'sources':[SOURCE]}))
            (r/'data/source_state.json').write_text('{"sources":{}}')
            (r/'data/automated_events.json').write_text('{"events":[]}')
            now=dt.datetime(2026,10,17,tzinfo=dt.timezone.utc)
            first=run(r,lambda _:FEED,lambda _:True,now)
            self.assertEqual(len(first['new_races']),1)
            self.assertEqual(first['baseline_sources'],['test-ics'])
            self.assertEqual(first['watch_changes'],[])
            second=run(r,lambda _:FEED,lambda _:True,now)
            self.assertEqual(second['new_races'],[])
            self.assertEqual(second['watch_changes'],[])
            changed=run(r,lambda _:FEED.replace('20270301','20270304'),lambda _:True,now)
            self.assertEqual(len(changed['watch_changes']),1)
            self.assertEqual(len(changed['possible_date_changes']),1)
            existing=json.loads((r/'data/automated_events.json').read_text())['events']
            self.assertEqual(len(existing),1)
            self.assertEqual(existing[0]['start'],'2027-03-01')  # review changes; no silent overwrite
            failure=run(r,lambda _: (_ for _ in ()).throw(ValueError('mock failure')),lambda _:True,now)
            self.assertEqual(len(failure['errors']),1)
            self.assertEqual(len(json.loads((r/'data/automated_events.json').read_text())['events']),1)
    def test_robots_refusal_prevents_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp)
            for sub in ('data','site','reports'):(r/sub).mkdir()
            (r/'data/monitor_sources.json').write_text(json.dumps({'sources':[SOURCE]}))
            (r/'data/source_state.json').write_text('{"sources":{}}')
            (r/'data/automated_events.json').write_text('{"events":[]}')
            def fetch(url):raise RuntimeError('Should not fetch')
            result=run(r,fetch,lambda _:False,dt.datetime(2026,10,17,tzinfo=dt.timezone.utc))
            self.assertEqual(result['successful'],0)
            self.assertEqual(len(result['errors']),1)

class TestBuild(unittest.TestCase):
    def test_real_dataset(self):
        root=Path(__file__).resolve().parents[1]
        db=build(root)
        self.assertGreaterEqual(len(db['events']),97)
        self.assertEqual(len({e['id'] for e in db['events']}),len(db['events']))
        self.assertTrue(all(e['start']<=e['end'] for e in db['events']))
        clubs=json.loads((root/'site/clubs.json').read_text())['clubs']
        self.assertEqual(len(clubs),132)
        self.assertTrue(any(c['monitor_id'] for c in clubs))

if __name__=='__main__':unittest.main()
