"""Reviewed multi-season calendars must update saved races without guessing venues."""
import datetime as dt
import json
import unittest
from pathlib import Path
from scripts.discovery_engine import extract_page, identity

ROOT=Path(__file__).resolve().parents[1]

class OfficialScheduleUpdates(unittest.TestCase):
    def setUp(self):
        self.source=next(s for s in json.loads((ROOT/'data/monitor_sources.json').read_text())['sources'] if s['id']=='skusa-official-schedule')
        self.today=dt.date(2026,10,19)
        # Synthetic markup models the reviewed heading/row boundaries, including
        # navigation countdowns which must never become races.
        self.raw='''<div>2027 Winter Series</div><div>88DAYS</div>
        <h1>2026 SuperNationals 29</h1><div>November 11-15</div><div>Las Vegas Motor Speedway</div>
        <h1>2027 SKUSA EVENT SCHEDULE</h1>
        <h1>2027 SuperNationals 30</h1><div>November 10-14</div><div>Las Vegas Motor Speedway</div>
        <h1>2027 Winter Series</h1><div>Round 1/2</div><div>January 16-17</div><div>Orlando Kart Center</div>
        <div>Round 3/4</div><div>February 12-14</div><div>Orlando Kart Center</div>
        <h1>2027 Pro Tour</h1><div>Round 1/2</div><div>Apr 9-11</div><div>WinterNationals</div><div>Location TBA</div>
        <h1>2027 California ProKart Challenge</h1><div>Round 3</div><div>May 22-23</div><div>Location TBA</div>
        <footer>All content Copyright</footer>'''
    def events(self,raw=None):
        return extract_page(raw or self.raw,self.source,self.today)['events']
    def test_both_seasons_and_rounds_without_navigation_noise(self):
        found=self.events();self.assertEqual(len(found),6)
        self.assertEqual([e['start'] for e in found[:4]],['2026-11-11','2027-11-10','2027-01-16','2027-02-12'])
        self.assertEqual(len({identity(e) for e in found}),6)
    def test_explicit_unannounced_venues_stay_review_only(self):
        found=self.events();self.assertTrue(all(e['location_needs_review'] for e in found[-2:]))
        self.assertTrue(all(not e['location_needs_review'] for e in found[:4]))
    def test_rescheduled_round_preserves_identity_and_saved_mapping(self):
        a=self.events()[2];b=self.events(self.raw.replace('January 16-17','January 23-24'))[2]
        self.assertEqual(identity(a),identity(b));self.assertNotEqual(a['start'],b['start'])
        self.assertEqual(a['curated_id'],b['curated_id']);self.assertEqual(a['curated_id'],'7758fddb9bd1')
    def test_next_season_cannot_retarget_saved_mapping(self):
        raw=self.raw.replace('2027','2028')
        found=extract_page(raw,self.source,dt.date(2027,10,19))['events']
        self.assertTrue(found);self.assertTrue(all(not e.get('curated_id') for e in found))
    def test_missing_section_boundary_fails_closed(self):
        found=self.events(self.raw.replace('<h1>2027 Pro Tour</h1>',''))
        self.assertFalse(any('Winter Series' in e['name'] for e in found))
    def test_unknown_venue_never_falls_back_to_orlando(self):
        found=self.events(self.raw.replace('Orlando Kart Center','New Venue Pending'))
        winter=[e for e in found if 'Winter Series' in e['name']]
        self.assertEqual(len(winter),2);self.assertTrue(all(e['location_needs_review'] for e in winter))
    def test_nonrace_labels_are_not_enabled_by_broad_series_name(self):
        from tests.test_engine import page,EVENT
        found=extract_page(page(dict(EVENT,name='SKUSA Winter Series Banquet')),self.source,self.today)
        self.assertEqual(found['events'],[])

class ReviewedRaceCorrections(unittest.TestCase):
    def test_rok_rounds_and_fest_are_separate_and_bound_to_saved_ids(self):
        source=next(s for s in json.loads((ROOT/'data/monitor_sources.json').read_text())['sources'] if s['id']=='rok-sonoma-2027-official')
        raw='''<p>The 2027 season marks another year.</p>
        <h2>2027 Triple Crown 1</h2><div>Round 1: April 17-18</div><div>Round 2: May 1-2</div><div>Round 3: June 5-6</div>
        <h2>2027 Triple Crown 2</h2><div>Round 4: June 26-27</div><div>Round 5: August 7-8</div><div>Round 6: September 18-19</div>
        <p>**Each Triple Crown</p><h2>ROK FEST WEST</h2>
        <p>Returning to Sonoma Raceway on July 17-18, ROK Fest West returns.</p><p>ROK Sonoma averaged</p>'''
        found=extract_page(raw,source,dt.date(2026,10,19))['events']
        self.assertEqual(len(found),7);self.assertEqual(len({e['curated_id'] for e in found}),7)
        self.assertEqual(found[-1]['start'],'2027-07-17')
        self.assertEqual(found[0]['start'],'2027-04-17')
        self.assertTrue(all(e['venue']=='Sonoma Raceway' for e in found))
    def test_reviewed_duplicates_keep_both_saved_ids(self):
        from scripts.build_site import merge_reviewed_duplicates
        a={'id':'canonical','country':'USA','organizer':'Example','name':'Winter Tour Round 2','venue':'TBA'}
        b=dict(a,id='copy',name='ROK Winter Tour Round 2',venue='Venue TBA',alias_ids=['old-copy'])
        policy={'duplicate_events':{'copy':{'canonical_id':'canonical'}}}
        found=merge_reviewed_duplicates([a,b],policy)
        self.assertEqual(len(found),1);self.assertEqual(found[0]['alias_ids'],['copy','old-copy'])
        self.assertNotIn('alias_ids',a)
        self.assertEqual(len(merge_reviewed_duplicates([a,b],{})),2)
        with self.assertRaisesRegex(AssertionError,'organizer mismatch'):
            merge_reviewed_duplicates([a,dict(b,organizer='Another')],policy)
    def test_verified_venue_announcement_updates_curated_race_without_new_id(self):
        import shutil,tempfile
        from scripts.build_site import build
        source=next(s for s in json.loads((ROOT/'data/monitor_sources.json').read_text())['sources'] if s['id']=='skusa-official-schedule')
        source=dict(source, text_profile=json.loads(json.dumps(source['text_profile'])))
        source['text_profile']['sections'][2]['venues']['Announced Circuit']={'name':'Announced Circuit','address':{'addressCountry':'USA','addressRegion':'AZ','addressLocality':'Tucson'}}
        raw='<h1>2027 Pro Tour</h1><div>Round 1/2</div><div>Apr 9-11</div><div>WinterNationals</div><div>Announced Circuit</div><h1>2027 California ProKart Challenge</h1>'
        event=extract_page(raw,source,dt.date(2026,10,19))['events'][0]
        self.assertFalse(event['location_needs_review'])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);shutil.copytree(ROOT/'data',root/'data');(root/'site').mkdir()
            event.update(id=identity(event),last_verified='2026-10-19T20:00:00+00:00')
            (root/'data/automated_events.json').write_text(json.dumps({'events':[event]}))
            snap=build(root);matches=[e for e in snap['events'] if e['id']=='750e3eda7058']
            self.assertEqual(len(matches),1);self.assertEqual(matches[0]['venue'],'Announced Circuit')
            self.assertEqual(matches[0]['region'],'AZ')

class CmsCalendarTests(unittest.TestCase):
    def setUp(self):
        self.source=next(s for s in json.loads((ROOT/'data/monitor_sources.json').read_text())['sources'] if s['id']=='mika-official')
    def card(self,name,category='MIKA',day='2027-05-02',**attrs):
        from html import escape
        values={'class':'cal-event-data','cal-event-data':name,'data-cat':category,'data-date':day,**attrs}
        return '<div '+' '.join(k+'="'+escape(v,quote=True)+'"' for k,v in values.items())+'></div>'
    def events(self,raw,source=None):
        return extract_page(raw,source or self.source,dt.date(2026,10,19))['events']
    def test_mixed_calendar_excludes_rentals_practice_and_other_motorsports(self):
        raw=''.join([self.card('MIKA Race 1'),self.card('MADRL Championship Finals','MADRL'),self.card('MIKA Open Practice'),self.card('Stock Car Championship','special'),self.card('MIKA Race 2','unknown')])
        self.assertEqual([e['name'] for e in self.events(raw)],['MIKA Race 1'])
    def test_registration_and_reschedule_survive_repeated_cards(self):
        a=self.events(self.card('MIKA Race 1',**{'data-url':'https://register.example/race-1'}))[0]
        b=self.events(self.card('MIKA Race 1',day='2027-05-09'))[0]
        self.assertEqual(identity(a),identity(b));self.assertEqual(a['registration_url'],'https://register.example/race-1')
        self.assertEqual(a['venue'],'Mosport Karting Centre')
    def test_unnumbered_races_on_different_dates_do_not_collapse(self):
        found=self.events(self.card('MIKA Club Race')+self.card('MIKA Club Race',day='2027-05-09'))
        self.assertEqual(len({identity(e) for e in found}),2)
    def test_invalid_dates_and_wrong_paths_are_not_inferred(self):
        self.assertEqual(self.events(self.card('MIKA Race 1',day='2027-02-30')),[])
        self.assertEqual(self.events(self.card('MIKA Race 1',day='May 2')),[])
        self.assertEqual(self.events(self.card('MIKA Race 1'),dict(self.source,url='https://www.mosportkartingcentre.com/arrive-drive')),[])


if __name__=='__main__':unittest.main()
