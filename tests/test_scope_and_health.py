"""Competition-kart scope, retained races, source health and explicit season evidence."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.racing_scope import event_scope_reason,source_scope_reason,apply_reviewed_override
from scripts.discovery_engine import extract_page,scan_source
from scripts.check_sources import normalized_ics
from scripts.source_health import update_health
from scripts.organizer_coverage import audit
from scripts.validate_data import validate
from tests.test_engine import SOURCE,EVENT,TODAY,page

NOW='2026-10-19T18:00:00+00:00'


class CircuitScopeTests(unittest.TestCase):
    def test_unknown_engine_details_are_not_a_filter(self):
        for name in ('Club Race 1','Rotax Championship','Briggs LO206 Enduro','ROK Cup','Shifter Grand Prix','KA100 Sprint Race'):
            self.assertIsNone(event_scope_reason({'name':name,'format':'Sprint','classes':''}))
    def test_explicit_excluded_disciplines_do_not_pass_even_with_lo206(self):
        for name in ('LO206 Dirt Oval Race','Vintage Kart Grand Prix','Rental Kart Race','Mini Moto Championship','Stock Car Race','AKRA Road Racing Round 1','Canadian Mini Indy Championship'):
            self.assertIsNotNone(event_scope_reason({'name':name,'classes':'LO206'}),name)
    def test_speedway_venue_road_america_and_pkra_vintage_layout_are_not_disciplines(self):
        for event in ({'name':'Club Race','venue':'Langley Speedway'}, {'name':'Road America Kart Club Race'}, {'name':'Championship Race Round 1 — Vintage CW'}):
            self.assertIsNone(event_scope_reason(event))
    def test_concession_event_but_not_rental_transponder_or_mixed_owner_class(self):
        self.assertEqual(event_scope_reason({'name':'Halloween Enduro','description':'Teams use our concession karts.'}),'rental')
        self.assertIsNone(event_scope_reason({'name':'Club Championship','description':'Rental transponders are available.'}))
        self.assertIsNone(event_scope_reason({'name':'Club Championship','description':'Rotax and LO206 classes, plus rental karts.'}))
    def test_scope_applies_to_both_html_and_ics(self):
        for name in ('Vintage Kart Race','Dirt Oval Race','Rental Kart Championship'):
            self.assertEqual(extract_page(page(dict(EVENT,name=name)),SOURCE,TODAY)['events'],[])
            feed='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:one\nDTSTART:20261101\nSUMMARY:'+name+'\nEND:VEVENT\nEND:VCALENDAR'
            self.assertEqual(normalized_ics(feed,SOURCE,TODAY),[])
    def test_mixed_venue_source_requires_kart_event_name(self):
        source=dict(SOURCE,event_name_pattern=r'QCKS|Kart Race')
        self.assertEqual(extract_page(page(dict(EVENT,name='Super Pro Championship Race')),source,TODAY)['events'],[])
        self.assertEqual(len(extract_page(page(dict(EVENT,name='QCKS Championship Race')),source,TODAY)['events']),1)
    def test_source_path_rules_do_not_exclude_sprint_or_generic_road_america(self):
        self.assertTrue(source_scope_reason({'url':'https://club.example/daytona-kartweek-road/'}))
        self.assertFalse(source_scope_reason({'url':'https://club.example/daytona-kartweek-sprint/'}))
        self.assertFalse(source_scope_reason({'name':'Road America Karting Club','url':'https://club.example/calendar/'}))
    def test_reviewed_circuit_correction_retains_saved_id(self):
        original={'id':'saved','name':'KartWeek','format':'Sprint / Road / Dirt'}
        policy={'event_overrides':{'saved':{'fields':{'format':'Sprint','name':'KartWeek Circuit Karting'}}}}
        result=apply_reviewed_override(original,policy)
        self.assertEqual(result['id'],'saved');self.assertIsNone(event_scope_reason(result))
        self.assertEqual(original['format'],'Sprint / Road / Dirt')
    def test_validator_blocks_scope_leakage(self):
        event={'id':'dirt','name':'LO206 Dirt Oval Race','start':'2026-11-01','end':'2026-11-01','organizer':'Club','country':'USA','source':'https://club.example/'}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'site').mkdir();(root/'site/events.json').write_text(json.dumps({'events':[event]}))
            with self.assertRaisesRegex(AssertionError,'Out-of-scope'):validate(root)


def result(events=None,reached=True,errors=None):
    return {'source_id':'club','club':'Club','url':'https://club.example/','pages':[{'events':len(events or [])}] if reached else [],'events':events or [],'errors':errors or []}


class SourceHealthTests(unittest.TestCase):
    def event(self,id='race',end='2026-11-01',**changes):return dict({'id':id,'uid':id,'feed_id':'club','end':end,'status':'scheduled'},**changes)
    def test_reachable_empty_schedule_is_not_healthy_when_future_races_were_known(self):
        states,alerts=update_health([result()],{},[self.event()],TODAY,NOW)
        self.assertEqual(states['club']['status'],'unexpected_empty');self.assertEqual(alerts[0]['kind'],'unexpected_empty')
    def test_failed_fetch_streak_and_recovery_preserve_expectations(self):
        states,_=update_health([result([self.event()])],{},[],TODAY,NOW)
        for count in (1,2):
            states,alerts=update_health([result(reached=False)],states,[],TODAY,NOW)
            self.assertEqual(states['club']['consecutive_failures'],count)
            self.assertEqual(states['club']['last_success'],NOW)
        states,_=update_health([result([self.event()])],states,[],TODAY,NOW)
        self.assertEqual(states['club']['consecutive_failures'],0);self.assertEqual(states['club']['status'],'healthy')
    def test_disappeared_event_stays_flagged_across_partial_scans(self):
        a,b=self.event('a'),self.event('b')
        states,_=update_health([result([a,b])],{},[],TODAY,NOW)
        for i in range(2):
            states,alerts=update_health([result([a])],states,[],TODAY,NOW)
            self.assertEqual(states['club']['status'],'observation_drop');self.assertEqual(states['club']['missing_event_keys'],['b'])
    def test_explicit_cancellation_is_not_a_disappeared_event(self):
        states,_=update_health([result([self.event()])],{},[],TODAY,NOW)
        states,alerts=update_health([result([self.event(status='cancelled')])],states,[],TODAY,NOW)
        self.assertEqual(alerts,[])
        states,alerts=update_health([result()],states,[],TODAY,NOW)
        self.assertNotEqual(states['club']['status'],'unexpected_empty')
    def test_finished_dates_do_not_trigger_empty_schedule_alarm(self):
        states,_=update_health([result([self.event(end='2026-11-01')])],{},[],TODAY,NOW)
        states,alerts=update_health([result()],states,[],dt.date(2026,11,2),NOW)
        self.assertEqual(alerts,[])
    def test_parser_notices_and_partial_failures_are_visible(self):
        r=result(errors=[{'error':'timeout'}]);r['pages'][0]['notice']='Image-only schedule'
        _,alerts=update_health([r],{},[],TODAY,NOW)
        self.assertEqual({a['kind'] for a in alerts},{'partial_fetch_failure','parser_review_required'})
    def test_numbered_round_detail_page_can_represent_its_series_page_copy(self):
        a=self.event('series',name='Championship Round 10',start='2026-11-01',venue='Kart Track')
        b=dict(a,id='detail',uid='detail')
        states,_=update_health([result([a,b])],{},[],TODAY,NOW)
        states,alerts=update_health([result([b])],states,[a,b],TODAY,NOW)
        self.assertEqual(states['club']['missing_event_keys'],[]);self.assertEqual(alerts,[])
    def test_histories_are_bounded(self):
        states={}
        for i in range(25):states,_=update_health([result()],states,[],TODAY,NOW)
        self.assertEqual(len(states['club']['history']),20)


class OrganizerSeasonTests(unittest.TestCase):
    def organizer(self,**changes):return dict({'id':'club','name':'Club','aliases':['Club Alias'],'country':'Canada','scope_status':'eligible','source_ids':['club'],'season_declarations':[]},**changes)
    def audit(self,organizers,**changes):
        args={'organizers':organizers,'monitors':[dict(SOURCE)],'results':[result()],'health':{},'races':[],'candidates':[],'today':TODAY,'now':NOW}
        args.update(changes);return audit(**args)
    def test_empty_reachable_page_never_means_season_complete_or_next_year_not_announced(self):
        row=self.audit([self.organizer()])['organizers'][0]
        self.assertEqual([s['status'] for s in row['seasons']],['no_dates_verified','no_dates_verified'])
    def test_explicit_season_evidence_and_declaration_expiry(self):
        declaration={'year':2027,'status':'not_announced','reviewed_on':'2026-10-19','evidence':'https://club.example/calendar'}
        organizer=self.organizer(season_declarations=[declaration])
        self.assertEqual(self.audit([organizer])['organizers'][0]['seasons'][1]['status'],'not_announced')
        self.assertEqual(self.audit([organizer],today=dt.date(2026,11,1))['organizers'][0]['seasons'][1]['status'],'declaration_stale')
    def test_aliases_match_and_new_dates_override_old_not_announced_statement(self):
        organizer=self.organizer(season_declarations=[{'year':2027,'status':'not_announced','reviewed_on':'2026-10-19'}])
        race={'id':'race','organizer':'Club Alias','start':'2027-05-01','end':'2027-05-01','source':'https://club.example/'}
        data=self.audit([organizer],races=[race]);self.assertEqual(data['summary']['unmatched_races'],0)
        self.assertEqual(data['organizers'][0]['seasons'][1]['status'],'indexed_future_events')
    def test_unknown_directory_entry_is_a_research_target_not_a_verified_club(self):
        organizer=self.organizer(scope_status='needs_review',source_ids=[])
        report=self.audit([organizer]);self.assertEqual(report['summary']['by_scope'],{'needs_review':1})
        self.assertEqual(report['organizers'][0]['seasons'][0]['status'],'no_source_configured')
    def test_cached_future_listing_is_not_automatically_recently_verified(self):
        race={'id':'race','organizer':'Club','start':'2026-11-01','end':'2026-11-01','source':'https://club.example/'}
        report=self.audit([self.organizer()],races=[race])
        season=report['organizers'][0]['seasons'][0]
        self.assertEqual(season['recently_verified_upcoming'],0);self.assertEqual(season['unconfirmed_future_event_ids'],['race'])
        self.assertEqual(report['priorities'][0]['reason'],'published_dates_need_reverification')
        report=self.audit([self.organizer()],races=[dict(race,last_verified=NOW)])
        self.assertEqual(report['organizers'][0]['seasons'][0]['recently_verified_upcoming'],1)


if __name__=='__main__':unittest.main()
