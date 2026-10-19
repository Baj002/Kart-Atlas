"""Schedule formats that previously produced zero races or false organizer leads."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pdf_schedules import extract_pdf, lines_to_events, schedule_year
from scripts.discovery_engine import extract_page, normalize_event, scan_source, organizer_url, identity
from scripts.check_sources import normalized_ics
from tests.test_engine import SOURCE, TODAY


def pdf_fixture(lines):
    # Synthetic text-only PDF; no third-party schedule is redistributed in tests.
    escaped=lambda s:s.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    commands=['BT /F1 12 Tf 40 750 Td']
    for i,line in enumerate(lines):
        if i:commands.append('0 -22 Td')
        commands.append('('+escaped(line)+') Tj')
    commands.append('ET');stream='\n'.join(commands).encode()
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    result=b'%PDF-1.4\n';offsets=[0]
    for number,obj in enumerate(objects,1):
        offsets.append(len(result));result+=str(number).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref=len(result);result+=b'xref\n0 6\n0000000000 65535 f \n'
    result+=b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return result+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'

class PdfScheduleTests(unittest.TestCase):
    def test_columns_keep_dates_separate_and_exclude_reserves(self):
        text='2026 RACING SCHEDULE\nSPRING                                  FALL\nAPRIL 4TH                              OCTOBER 24TH\nAPRIL 19TH (RAIN DATE)                  OCTOBER 31ST\nMAY 10TH (RAIN DATE)                    NOVEMBER 15TH (RAIN DATE)\nNOVEMBER 21ST\nOCTOBER 18TH (Sunday-TBD)'
        source=dict(SOURCE,pdf_profile={'layout':'date_columns','auto_import':True,'race_name':'Club Race'})
        found=lines_to_events(text,source)
        self.assertEqual([e['startDate'] for e in found],['2026-04-04','2026-10-24','2026-10-31','2026-11-21'])
        self.assertTrue(all(not e['_publication_needs_review'] for e in found))
    def test_explicit_year_required_and_banquet_year_does_not_override_heading(self):
        self.assertIsNone(schedule_year('Race Dates\nOctober 24'))
        self.assertEqual(schedule_year('2026 Championship Schedule\nFebruary 21: 2025 Season Banquet'),2026)
    def test_named_rows_default_to_review(self):
        text='2027 Race Schedule\nMay\n2nd     Points Race 1\n9th     Points Race 2\n16th    Rain Make-up'
        events=lines_to_events(text,SOURCE)
        self.assertEqual(len(events),2);self.assertTrue(all(e['_publication_needs_review'] for e in events))
    def test_pdf_binary_round_trip_and_scan(self):
        raw=pdf_fixture(['2026 RACING SCHEDULE','OCTOBER 24TH','OCTOBER 25TH (RAIN DATE)','NOVEMBER 7TH'])
        source=dict(SOURCE,url='https://club.example/schedule.pdf',pdf_profile={'layout':'date_columns','auto_import':True,'race_name':'Club Race'})
        result=extract_pdf(raw,source);self.assertEqual(len(result['events']),2)
        scan=scan_source(source,lambda u:raw,TODAY)
        self.assertEqual(len(scan['events']),2);self.assertEqual(scan['pages'][0]['parser'],'pdf-text')
        self.assertEqual(scan['errors'],[])
    def test_missing_text_layer_is_explicit(self):
        result=extract_pdf(pdf_fixture([]),SOURCE)
        self.assertEqual(result['events'],[]);self.assertIn('OCR review',result['notice'])
    def test_non_pdf_response_rejected(self):
        source=dict(SOURCE,url='https://club.example/schedule.pdf')
        result=scan_source(source,lambda u:'<h1>Sign In</h1>'*20,TODAY)
        self.assertEqual(result['pages'],[]);self.assertIn('non-PDF',result['errors'][0]['error'])
    def test_revised_pdf_urls_share_identity_in_verified_namespace(self):
        first=dict(SOURCE,url='https://club.example/old.pdf',event_namespace='club',pdf_profile={'layout':'date_columns','auto_import':True})
        second=dict(first,url='https://club.example/new.pdf')
        a=normalize_event(lines_to_events('2026 RACING SCHEDULE\nOCTOBER 24TH',first)[0],first,TODAY)
        b=normalize_event(lines_to_events('2026 RACING SCHEDULE\nOCTOBER 24TH',second)[0],second,TODAY)
        self.assertEqual(identity(a),identity(b))

class HtmlAndLeadTests(unittest.TestCase):
    def test_reordered_date_column_and_reviewed_curated_mapping(self):
        source=dict(SOURCE,table_events={'Round 1':{'name':'Club Winter Championship Round 1','curated_id':'saved-id'}})
        html='<table><tr><th>Round</th><th>Date</th><th>Configuration</th></tr><tr><td>Round 1</td><td>Sunday, November 1, 2026</td><td>Clockwise</td></tr><tr><td>Rain Make-Up Date</td><td>April 18, 2027</td><td>—</td></tr></table>'
        found=extract_page(html,source,TODAY)['events']
        self.assertEqual(len(found),1);self.assertEqual(found[0]['curated_id'],'saved-id')
        self.assertEqual(found[0]['name'],'Club Winter Championship Round 1')
    def test_pdf_anchor_accessible_label_is_used(self):
        html='<a href="/_files/abc123.pdf" aria-label="2027 Race Schedule.pdf"><img src="icon.png"></a>'
        found=extract_page(html,SOURCE,TODAY)
        self.assertEqual(found['schedule_documents'],['https://club.example/_files/abc123.pdf'])
    def test_media_links_are_not_organizer_sources(self):
        source=dict(SOURCE,directory=True)
        html='<a href="https://assets.kartpulse.com/image.png">Kart Club</a><a href="https://kart.smugmug.com/">Kart Gallery</a><a href="https://newkart.example/">Kart Club</a>'
        self.assertEqual(len(extract_page(html,source,TODAY)['leads']),1)
        for url in ('https://club.example/logo.png','https://club.example/schedule.pdf','https://kart.smugmug.com/'):
            self.assertFalse(organizer_url(url))
    def test_joomla_export_raw_link(self):
        found=extract_page('<a href="/calendar/event.raw">Outlook (.ics)</a>',SOURCE,TODAY)
        self.assertEqual(found['feeds'],['https://club.example/calendar/event.raw'])
    def test_race_description_opt_in_not_general_title_guessing(self):
        raw='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:one\nDTSTART:20261024T130000\nSUMMARY:Fall 5 (FWD) Halloween & Powder Puff\nDESCRIPTION:Forward race. Halloween Party\nEND:VEVENT\nEND:VCALENDAR'
        self.assertEqual(normalized_ics(raw,SOURCE,TODAY),[])
        self.assertEqual(len(normalized_ics(raw,dict(SOURCE,allow_race_description=True),TODAY)),1)


class PublicPlatformTests(unittest.TestCase):
    def test_raceselect_dates_registration_and_review_scope(self):
        source=dict(SOURCE,url='https://raceselect.com/club/2026',timezone='America/Los_Angeles')
        html='''<a href="/club/final/EventDetails"><span class="font-semibold break-words">Club Championship Race</span>
        <span data-race-countdown-label>Registration open</span><time data-browser-date="weekday-range" data-browser-date-from="2026-11-01T01:00:00Z" data-browser-date-to="2026-11-02T01:00:00Z"></time></a>
        <a href="/club/final/registration">Register now</a>'''
        found=extract_page(html,source,TODAY)['events']
        self.assertEqual(len(found),1);event=found[0]
        self.assertEqual((event['start'],event['end']),('2026-10-31','2026-11-01'))
        self.assertEqual(event['registration_status'],'open')
        self.assertEqual(event['registration_url'],'https://raceselect.com/club/final/registration')
        self.assertTrue(event['publication_needs_review'])
    def test_disabled_registration_is_not_cancellation(self):
        source=dict(SOURCE,url='https://raceselect.com/club/2026',timezone='America/New_York')
        html='<a href="/club/final/EventDetails"><span class="font-semibold break-words">Club Race</span><span data-race-countdown-label>Registration disabled</span><time data-browser-date="weekday-range" data-browser-date-from="2026-11-01T10:00:00Z" data-browser-date-to="2026-11-01T18:00:00Z"></time></a>'
        event=extract_page(html,source,TODAY)['events'][0]
        self.assertEqual(event['status'],'scheduled');self.assertEqual(event['registration_status'],'disabled')
    def test_bad_platform_card_does_not_break_other_cards(self):
        from scripts.platform_calendars import extract_raceselect
        source=dict(SOURCE,url='https://raceselect.com/club/2026',timezone='America/New_York')
        card='<a href="/club/final/EventDetails"><span class="font-semibold break-words">Club Race</span><time data-browser-date="weekday-range" data-browser-date-from="BAD" data-browser-date-to="BAD"></time></a>'
        events=extract_raceselect(card+card.replace('BAD','2026-11-01T10:00:00Z'),source)
        self.assertEqual(len(events),1)

class CrawlExportTests(unittest.TestCase):
    def test_child_export_is_processed_before_remaining_navigation(self):
        calls=[]
        feed='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:race\nDTSTART:20261101\nSUMMARY:Club Race 2\nEND:VEVENT\nEND:VCALENDAR'
        def fetch(url):
            calls.append(url)
            if url.endswith('/event.raw'):return feed
            if url.endswith('/event'):return '<h1>Public race calendar export</h1><a href="/event.raw">Outlook (.ics)</a>'*3
            return '<a href="/calendar/event">Event Calendar</a><a href="/calendar/other">Another Calendar</a>'*4
        source=dict(SOURCE,url='https://club.example/calendar')
        result=scan_source(source,fetch,TODAY,3)
        self.assertEqual(calls,['https://club.example/calendar','https://club.example/calendar/event','https://club.example/event.raw'])
        self.assertEqual(len(result['events']),1)

class CoverageAuditTests(unittest.TestCase):
    def test_region_gaps_are_measured_without_claiming_no_races_exist(self):
        from scripts.coverage_audit import regional_coverage
        clubs=[{'country':'USA','region':'CT'}]
        source={'country':'USA','region':'CT','trusted':True,'pages':[]}
        data=regional_coverage([],clubs,[source],TODAY)
        row=next(r for r in data if r['country']=='USA' and r['region']=='CT')
        self.assertEqual(row['directory_leads'],1);self.assertEqual(row['upcoming_races'],0)
        self.assertEqual(row['organizer_sources'],1);self.assertEqual(row['organizer_sources_reached'],0)
    def test_conflicting_date_windows_reported_without_mutating_published_event(self):
        from scripts.coverage_audit import date_conflicts
        original={'id':'one','name':'CCKRA Championship Race #6','organizer':'CCKRA','start':'2026-10-23','end':'2026-10-25','country':'USA','region':'CA','source':'https://club.example/'}
        candidate=dict(original,name='2026 CCKRA Championship Race #6',start='2026-10-24',source='https://raceselect.com/club/2026')
        result=date_conflicts([original],[candidate])
        self.assertEqual(len(result),1);self.assertEqual(original['start'],'2026-10-23')
        self.assertEqual(date_conflicts([original],[dict(candidate,organizer='Other Club')]),[])

class PdfFailureIsolationTests(unittest.TestCase):
    def test_zero_width_font_fallback_never_auto_publishes(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        def text(**options):
            if options.get('extraction_mode')=='layout':raise ZeroDivisionError('font width zero')
            return '2026 RACING SCHEDULE\nOCTOBER 24TH'
        reader=SimpleNamespace(is_encrypted=False,pages=[SimpleNamespace(extract_text=text)])
        source=dict(SOURCE,pdf_profile={'layout':'date_columns','auto_import':True})
        with patch('pypdf.PdfReader',return_value=reader):result=extract_pdf(b'%PDF-test',source)
        self.assertEqual(len(result['events']),1)
        self.assertTrue(result['events'][0]['_publication_needs_review']);self.assertIn('layout failed',result['notice'])
    def test_bad_pdf_becomes_source_error(self):
        source=dict(SOURCE,url='https://club.example/broken.pdf')
        result=scan_source(source,lambda u:b'%PDF-broken',TODAY)
        self.assertEqual(result['events'],[]);self.assertEqual(len(result['errors']),1)

class DataAccuracyTests(unittest.TestCase):
    def test_explicit_away_location_cannot_inherit_home_track(self):
        raw='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:away\nDTSTART:20261101\nSUMMARY:Regional Championship Race\nLOCATION:Different Raceway, Another Town\nEND:VEVENT\nEND:VCALENDAR'
        event=normalized_ics(raw,SOURCE,TODAY)[0]
        self.assertTrue(event['location_needs_review'])
    def test_explicit_dirt_oval_is_not_labelled_sprint(self):
        from tests.test_engine import page,EVENT
        event=extract_page(page(dict(EVENT,name='Dirt Karters Race 9 (dirt oval)')),SOURCE,TODAY)['events'][0]
        self.assertEqual(event['format'],'Dirt oval')
    def test_stale_curated_mapping_blocks_publication(self):
        from scripts.validate_data import validate
        from tests.test_engine import normalized
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'site').mkdir()
            event=dict(normalized(),id='auto-one',curated_id='missing-saved-id')
            (root/'site/events.json').write_text(json.dumps({'events':[event]}))
            with self.assertRaisesRegex(AssertionError,'Stale curated'):validate(root)

class SeasonIdentityTests(unittest.TestCase):
    def test_next_season_table_does_not_retarget_last_seasons_saved_race(self):
        source=dict(SOURCE,table_events={'Round 1':{'name':'Winter Championship Round 1','curated_id':'old-saved'}},table_mapping_window={'start':'2026-10-01','end':'2027-05-31'})
        def html(day):return '<table><tr><th>Round</th><th>Date</th></tr><tr><td>Round 1</td><td>'+day+'</td></tr></table>'
        old=extract_page(html('November 1, 2026'),source,TODAY)['events'][0]
        new=extract_page(html('November 7, 2027'),source,dt.date(2027,10,19))['events'][0]
        self.assertEqual(old['curated_id'],'old-saved');self.assertNotIn('curated_id',new)
        self.assertNotEqual(identity(old),identity(new))
    def test_next_season_feed_does_not_retarget_last_seasons_saved_race(self):
        source=dict(SOURCE,feed_events={'Fall 5':{'name':'NTK Fall Race 5','curated_id':'old-saved'}},feed_mapping_window={'start':'2026-08-01','end':'2026-12-31'})
        feed='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:future\nDTSTART:20271024\nSUMMARY:Fall 5 Race\nEND:VEVENT\nEND:VCALENDAR'
        event=normalized_ics(feed,source,dt.date(2027,10,19))[0]
        self.assertIsNone(event['curated_id'])


class PublicPlatformScopeTests(unittest.TestCase):
    def test_structured_platform_metadata_cannot_bypass_venue_review(self):
        from tests.test_engine import page,EVENT
        source=dict(SOURCE,url='https://raceselect.com/club/2026')
        found=extract_page(page(EVENT),source,TODAY)['events'][0]
        self.assertTrue(found['publication_needs_review'])
    def test_entry_lists_are_not_crawl_targets(self):
        source=dict(SOURCE,url='https://raceselect.com/club/2026')
        found=extract_page('<a href="/club/race/EventEntries">Event entries</a><a href="/club/race/EventDetails">Event details</a>',source,TODAY)
        self.assertEqual(found['links'],[])

if __name__=='__main__':unittest.main()
