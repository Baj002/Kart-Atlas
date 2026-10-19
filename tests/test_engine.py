"""Behavioral regressions for discovery, event lifecycle, coverage and publication."""
import datetime as dt
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.discovery_engine import clean_url, extract_page, scan_source, reconcile, identity, run, PublicClient
from scripts.build_site import build, is_dup
from scripts.coverage_report import build as coverage
from scripts.validate_data import validate
from scripts.check_sources import normalized_ics

TODAY=dt.date(2026,10,19)
SOURCE={'id':'club','url':'https://club.example/events','club':'Example Kart Club','venue':'Club Raceway',
    'city':'Town','region':'BC','country':'Canada','trusted':True}
EVENT={'@type':'SportsEvent','@id':'https://club.example/events/final','name':'Fall Endurance Race',
    'startDate':'2026-10-24T09:00:00-07:00','endDate':'2026-10-24T17:00:00-07:00'}

def page(event=EVENT):return '<script type="application/ld+json">'+json.dumps(event)+'</script>'
def normalized(**changes):return extract_page(page(dict(EVENT,**changes)),SOURCE,TODAY)['events'][0]

class ExtractionTests(unittest.TestCase):
    def test_nested_jsonld_and_location(self):
        e=dict(EVENT,location={'name':'Actual Track','address':{'addressCountry':{'name':'US'},'addressRegion':'WA','addressLocality':'Seattle'}})
        found=extract_page(page({'@type':'ItemList','itemListElement':[{'item':e}]}),SOURCE,TODAY)['events']
        self.assertEqual(len(found),1);self.assertEqual(found[0]['country'],'USA');self.assertEqual(found[0]['venue'],'Actual Track')
        self.assertEqual(found[0]['format'],'Endurance')
    def test_end_date_validation(self):
        for end in ('2026-10-23','2027-01-01','unknown'):
            self.assertEqual(extract_page(page(dict(EVENT,endDate=end)),SOURCE,TODAY)['events'],[])
    def test_date_window_and_practice(self):
        for changes in ({'startDate':'TBA'},{'startDate':'2025-01-01','endDate':'2025-01-02'},
                        {'name':'Race Practice'},{'name':'Annual Members Meeting'}):
            self.assertEqual(extract_page(page(dict(EVENT,**changes)),SOURCE,TODAY)['events'],[])
    def test_spanish_french_competitions(self):
        for name in ('Campeonato de Karting','Coupe de Montréal','Carrera Final'):
            self.assertEqual(len(extract_page(page(dict(EVENT,name=name)),SOURCE,TODAY)['events']),1)
    def test_cancellation_and_postponement(self):
        self.assertEqual(normalized(eventStatus='https://schema.org/EventCancelled')['status'],'cancelled')
        self.assertEqual(normalized(eventStatus='https://schema.org/EventPostponed')['status'],'postponed')
    def test_squarespace_card_with_registration(self):
        html='''<article class="eventlist-event"><h1><a class="eventlist-title-link" href="/events/final">Fall Endurance Race</a></h1>
          <time datetime="2026-10-24">Saturday</time><time class="event-time-localized-end" datetime="2026-10-25">Sunday</time>
          <a href="https://register.example/race">Registration</a></article>
          <article class="eventlist-event"><a class="eventlist-title-link" href="/events/meeting">Members Meeting</a><time datetime="2026-10-22"></time></article>'''
        found=extract_page(html,SOURCE,TODAY)['events'];self.assertEqual(len(found),1)
        self.assertEqual(found[0]['end'],'2026-10-25');self.assertEqual(found[0]['registration_url'],'https://register.example/race')
    def test_schedule_table_requires_explicit_year_and_defers_offsite(self):
        html='<h2>2027 Race Schedule</h2><table><tr><td>May 1st</td><td>Club Race 1</td></tr><tr><td>June 4–5</td><td>Race 2 hosted at Other Track</td></tr></table>'
        found=extract_page(html,SOURCE,TODAY)['events']
        self.assertEqual(len(found),2);self.assertEqual(found[0]['start'],'2027-05-01')
        self.assertTrue(found[1]['location_needs_review'])
        self.assertEqual(extract_page(html.replace('2027 ',''),SOURCE,TODAY)['events'],[])
    def test_calendar_formats_and_cross_domain(self):
        found=extract_page('''<a href="/events/final?format=ical">ICS</a><link type="text/calendar" href="/export"/>
          <a href="https://untrusted.example/feed.ics">Feed</a>''',SOURCE,TODAY)
        self.assertEqual(found['feeds'],['https://club.example/events/final?format=ical','https://club.example/export'])
    def test_invalid_event_types_and_names_are_skipped(self):
        self.assertEqual(extract_page(page(dict(EVENT,**{'@type':42})),SOURCE,TODAY)['events'],[])
        self.assertEqual(extract_page(page(dict(EVENT,name={'value':'Kart Race'})),SOURCE,TODAY)['events'],[])
    def test_malformed_jsonld_does_not_lose_other_events(self):
        self.assertEqual(len(extract_page('<script type="application/ld+json">broken</script>'+page(),SOURCE,TODAY)['events']),1)
    def test_relative_event_url(self):self.assertEqual(normalized(url='/events/final')['source'],'https://club.example/events/final')
    def test_private_and_unsafe_urls(self):
        for url in ('file:///etc/passwd','http://127.0.0.1/x','http://169.254.169.254/','https://localhost/','https://a.internal/','https://u:p@club.example/','https://club.example:22/'):
            self.assertEqual(clean_url(url),'',url)
    def test_discovery_leads_do_not_inherit_trust(self):
        source=dict(SOURCE,directory=True)
        found=extract_page('<a href="https://newclub.example/">New Kart Club</a><a href="https://facebook.com/kart">Kart</a>',source,TODAY)
        self.assertEqual(len(found['leads']),1);self.assertEqual(found['leads'][0]['status'],'unverified_organizer_source')

class LifecycleTests(unittest.TestCase):
    def test_reschedule_keeps_id_and_history(self):
        first=normalized();stored,_=reconcile([], [first],'2026-10-19T00:00:00+00:00')
        next_event=normalized(startDate='2026-10-31',endDate='2026-10-31')
        updated,changes=reconcile(stored,[next_event],'2026-10-20T00:00:00+00:00')
        self.assertEqual(len(updated),1);self.assertEqual(updated[0]['id'],stored[0]['id'])
        self.assertEqual(updated[0]['start'],'2026-10-31');self.assertIn('start',changes[0]['fields'])
        again,changes=reconcile(updated,[next_event],'2026-10-21T00:00:00+00:00');self.assertEqual(changes,[])
        self.assertEqual(len(again[0]['history']),1)
    def test_missing_does_not_cancel(self):
        stored,_=reconcile([], [normalized()],'now');result,changes=reconcile(stored,[],'later')
        self.assertEqual(result,stored);self.assertEqual(changes,[])
    def test_explicit_cancellation_and_reinstatement(self):
        stored,_=reconcile([], [normalized()],'now')
        updated,_=reconcile(stored,[normalized(eventStatus='https://schema.org/EventCancelled')],'later')
        self.assertEqual(updated[0]['status'],'cancelled')
        restored,_=reconcile(updated,[normalized(eventStatus='https://schema.org/EventScheduled')],'later');self.assertEqual(restored[0]['status'],'scheduled')
    def test_cancellation_in_title_updates_known_event(self):
        stored,_=reconcile([], [normalized()],'now')
        updated,_=reconcile(stored,[normalized(name='Cancelled — Fall Endurance Race')],'later')
        self.assertEqual(updated[0]['status'],'cancelled')
    def test_cancelled_unknown_not_added(self):
        stored,_=reconcile([], [normalized(eventStatus='https://schema.org/EventCancelled')],'now');self.assertEqual(stored,[])
    def test_stale_listing_card_cannot_reinstate_cancelled_event(self):
        stored,_=reconcile([], [normalized()],'now')
        updated,_=reconcile(stored,[normalized(eventStatus='https://schema.org/EventCancelled')],'later')
        result,_=reconcile(updated,[normalized()],'next day')
        self.assertEqual(result[0]['status'],'cancelled')
    def test_known_rental_series_filtered_even_without_rental_in_title(self):
        self.assertEqual(extract_page(page(dict(EVENT,name='CRKC Attrition Fest Enduro')),dict(SOURCE,excluded_series=['CRKC']),TODAY)['events'],[])
    def test_entity_encoded_rental_excluded(self):
        self.assertEqual(extract_page(page(dict(EVENT,name='Trophy Cup (Arrive &#038; Drive)')),SOURCE,TODAY)['events'],[])
    def test_utc_feed_uses_explicit_organizer_timezone(self):
        feed='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:1\nSUMMARY:Endurance Race\nDTSTART:20261024T160000Z\nDTEND:20261025T000000Z\nEND:VEVENT\nEND:VCALENDAR'
        e=normalized_ics(feed,dict(SOURCE,timezone='America/Vancouver'),TODAY)[0]
        self.assertEqual((e['start'],e['end']),('2026-10-24','2026-10-24'))
    def test_http_and_https_event_references_share_identity(self):
        e=normalized();other=dict(e,source=e['source'].replace('https:','http:'))
        self.assertEqual(identity(e),identity(other))
    def test_duplicate_page_and_feed_share_identity(self):
        e=normalized();feed=dict(e,uid='ics-uid')
        self.assertEqual(identity(e),identity(feed))
    def test_multi_day_midnight_timed_end_not_assumed_exclusive(self):
        feed='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:1\nSUMMARY:Endurance Race\nDTSTART:20261024T090000\nDTEND:20261025T000000\nEND:VEVENT\nEND:VCALENDAR'
        e=normalized_ics(feed,SOURCE,TODAY)[0];self.assertEqual(e['end'],'2026-10-25')
        cancelled=feed.replace('UID:1','UID:1\nSTATUS:CANCELLED')
        self.assertEqual(normalized_ics(cancelled,SOURCE,TODAY),[])
        self.assertEqual(normalized_ics(cancelled,SOURCE,TODAY,include_cancelled=True)[0]['status'],'cancelled')
    def test_recurring_exception_not_misread_as_series(self):
        feed='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:1\nRECURRENCE-ID:20261024\nSUMMARY:Club Race\nDTSTART:20261024\nEND:VEVENT\nEND:VCALENDAR'
        self.assertEqual(normalized_ics(feed,SOURCE,TODAY),[])
    def test_distinct_organizers_same_day_and_generic_names(self):
        first=normalized();second=dict(first,organizer='Another Kart Club',venue='Different Raceway',source='https://another.example/events/final')
        self.assertFalse(is_dup(second,[first]))
    def test_generic_schedule_url_does_not_collapse_races(self):
        first=dict(normalized(),source=SOURCE['url']);second=dict(first,start='2026-10-25',end='2026-10-25')
        self.assertFalse(is_dup(second,[first]))

class PublicationTests(unittest.TestCase):
    def test_registration_reference_updates_curated_date_without_changing_saved_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for d in ('data','site'):(root/d).mkdir()
            (root/'data/clubs.json').write_text('{"clubs":[]}')
            (root/'data/monitor_sources.json').write_text('{"sources":[]}')
            (root/'data/automated_events.json').write_text('{"events":[]}')
            row={'Start Date':'2026-10-24','End Date':'2026-10-24','Race / Event':'Fall Endurance Race',
                'Club / Series':'Example Kart Club','Track / Venue':'Club Raceway','City':'Town','State / Province':'BC',
                'Country':'Canada','Source URL':'https://register.example/events/123'}
            with (root/'data/races.csv').open('w') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(row));writer.writeheader();writer.writerow(row)
            original=build(root)['events'][0]
            event=normalized(startDate='2026-10-31',endDate='2026-10-31');event.update(id=identity(event),registration_url=row['Source URL'])
            (root/'data/automated_events.json').write_text(json.dumps({'events':[event]}))
            updated=build(root)['events']
            self.assertEqual(len(updated),1);self.assertEqual(updated[0]['id'],original['id']);self.assertEqual(updated[0]['start'],'2026-10-31')

class GeographyTests(unittest.TestCase):
    def test_region_names_match_app_filter_codes(self):
        from scripts.discovery_engine import region_code
        for value,country,code in [('Mexico State','Mexico','MEX'),('Querétaro','Mexico','QUE'),('Morelos','Mexico','MOR'),('Québec','Canada','QC'),('CDMX','Mexico','CMX'),('New York','USA','NY')]:
            self.assertEqual(region_code(value,country),code)
    def test_repeated_generic_table_races_have_distinct_ids(self):
        html='<h2>2027 Race Schedule</h2><table><tr><td>May 1</td><td>Club Race</td></tr><tr><td>May 8</td><td>Club Race</td></tr></table>'
        events=extract_page(html,SOURCE,TODAY)['events']
        self.assertEqual(len(events),2);self.assertNotEqual(identity(events[0]),identity(events[1]))

class TableDateTests(unittest.TestCase):
    def test_french_range_and_ambiguous_numeric_dates(self):
        from scripts.schedule_tables import date_range
        self.assertEqual(date_range('4–5 juin 2027'),(dt.date(2027,6,4),dt.date(2027,6,5)))
        self.assertIsNone(date_range('06/07/2027'))
        self.assertIsNone(date_range('30 juin – 2 juillet 2027'))

class ScanTests(unittest.TestCase):
    def test_crawl_budget_and_preserve_partial_success(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            if url==SOURCE['url']:return page()+'<a href="/calendar">Calendar</a><a href="/events/second">Next Race</a>'
            raise OSError('unavailable')
        result=scan_source(SOURCE,fetch,TODAY,max_pages=2)
        self.assertEqual(len(calls),2);self.assertEqual(len(result['events']),1)
        self.assertEqual(len(result['errors']),1);self.assertEqual(result['remaining_links'],1)
    def test_robots_refusal_never_fetches_content(self):
        from urllib.robotparser import RobotFileParser
        client=PublicClient(0);rp=RobotFileParser();rp.parse(['User-agent: *','Disallow: /'])
        client.robots['https://club.example']=rp
        with patch.object(client,'_read',side_effect=AssertionError('must not fetch')):
            with self.assertRaisesRegex(ValueError,'robots'):client(SOURCE['url'])
    def test_end_to_end_idempotence_and_failure_retention(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for d in ('data','site','reports'):(root/d).mkdir()
            (root/'data/monitor_sources.json').write_text(json.dumps({'sources':[SOURCE]}))
            (root/'data/clubs.json').write_text('{"clubs":[]}')
            (root/'data/automated_events.json').write_text('{"events":[]}')
            (root/'data/races.csv').write_text('Start Date,Race / Event\n')
            first=run(root,lambda u:page(),TODAY);self.assertEqual(len(first['changes']),1)
            build(root);self.assertTrue(validate(root));summary=coverage(root,TODAY)
            self.assertEqual(summary['trusted_sources_reached'],1);self.assertEqual(summary['future_races'],1)
            again=run(root,lambda u:page(),TODAY);self.assertEqual(again['changes'],[]);self.assertEqual(again['content_changes'],[])
            changed=run(root,lambda u:page()+'<p>New published schedule bulletin</p>',TODAY)
            self.assertEqual(len(changed['content_changes']),1)
            failed=run(root,lambda u:(_ for _ in ()).throw(OSError('offline')),TODAY)
            self.assertEqual(failed['sources_checked'],0)
            self.assertEqual(len(json.loads((root/'data/automated_events.json').read_text())['events']),1)
            build(root);coverage(root,TODAY)
            with self.assertRaisesRegex(AssertionError,'No trusted'):validate(root,live=True)

if __name__=='__main__':unittest.main()
