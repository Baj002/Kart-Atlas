"""Regression cases found while auditing additional organizer calendars."""
import datetime as dt
import json
import unittest
from scripts.discovery_engine import extract_page, identity, reconcile, feed_url
from scripts.check_sources import normalized_ics
from scripts.pdf_schedules import lines_to_events
from scripts.text_schedules import extract_text_schedule
from tests.test_engine import SOURCE, TODAY


class SeriesIdentityTests(unittest.TestCase):
    def series(self, dates=('2026-11-01','2026-11-08'), names=('Race Round 1','Race Round 2')):
        return '<script type="application/ld+json">'+json.dumps([
            {'@type':'SportsEvent','name':name,'startDate':date,'url':SOURCE['url']}
            for name,date in zip(names,dates)])+'</script>'
    def test_shared_series_url_does_not_collapse_rounds(self):
        events=extract_page(self.series(),SOURCE,TODAY)['events']
        records,_=reconcile([],events,'2026-10-19')
        self.assertEqual(len(records),2)
        moved=extract_page(self.series(dates=('2026-11-02','2026-11-08')),SOURCE,TODAY)['events']
        self.assertEqual(identity(events[0]),identity(moved[0]))
        records,_=reconcile(records,moved,'2026-10-20')
        self.assertEqual(len(records),2);self.assertEqual(records[0]['start'],'2026-11-02')
    def test_repeated_generic_title_gets_distinct_dates(self):
        events=extract_page(self.series(names=('Club Race','Club Race')),SOURCE,TODAY)['events']
        self.assertEqual(len({identity(e) for e in events}),2)
    def test_unique_explicit_ids_survive_shared_event_detail_url(self):
        raw='<script type="application/ld+json">'+json.dumps([
            {'@type':'SportsEvent','@id':uid,'name':'Club Race','startDate':'2026-11-01','url':'https://club.example/events/championship'}
            for uid in ('morning','afternoon')])+'</script>'
        events=extract_page(raw,SOURCE,TODAY)['events']
        self.assertEqual(len({identity(e) for e in events}),2)
    def test_annual_rounds_do_not_retarget_previous_season(self):
        events=extract_page(self.series(dates=('2026-11-01','2027-03-01'),names=('Race Round 1','Race Round 1')),SOURCE,TODAY)['events']
        self.assertEqual(len({identity(e) for e in events}),2)


class ReviewedTextTests(unittest.TestCase):
    def source(self):
        return dict(SOURCE,text_profile={'paths':['/calendar'],'sections':[{
            'start':r'^(?P<year>20\d{2}) Kart Championship$', 'end':r'^Car Championship$',
            'row':r'^(?P<event>Round \d+) (?P<date>[^\n@]+) @ (?P<venue>[^\n]+)$',
            'name':'Kart Championship {event}','auto_import':True,
            'venues':{'Home':{'name':'Home Kart Track','address':{'addressCountry':'USA','addressRegion':'OR','addressLocality':'Canby'}}}}]})
    def html(self,year='2027',venue='Home'):
        return f'<h2>{year} Kart Championship</h2><p>Round 1 July 31 - August 1 @ {venue}</p><h2>Car Championship</h2><p>Round 2 November 20 @ Home</p>'
    def test_sections_keep_car_dates_out_and_preserve_multimonth_range(self):
        source=self.source();source['url']='https://club.example/calendar'
        events=extract_page(self.html(),source,TODAY)['events']
        self.assertEqual(len(events),1);self.assertEqual((events[0]['start'],events[0]['end']),('2027-07-31','2027-08-01'))
        self.assertEqual(events[0]['city'],'Canby');self.assertFalse(events[0]['location_needs_review'])
    def test_missing_year_or_section_boundary_fails_closed(self):
        source=self.source();source['url']='https://club.example/calendar'
        self.assertEqual(extract_text_schedule(self.html(year='Next Season'),source),[])
        self.assertEqual(extract_text_schedule(self.html().replace('Car Championship','Updated News'),source),[])
    def test_profile_only_applies_to_reviewed_path(self):
        self.assertEqual(extract_text_schedule(self.html(),dict(self.source(),url='https://club.example/archive')),[])
    def test_unknown_venue_and_unapproved_profile_stay_in_review(self):
        source=self.source();source['url']='https://club.example/calendar'
        event=extract_page(self.html(venue='Away'),source,TODAY)['events'][0]
        self.assertTrue(event['location_needs_review'])
        source['text_profile']['sections'][0]['auto_import']=False
        event=extract_page(self.html(),source,TODAY)['events'][0]
        self.assertTrue(event['publication_needs_review'])
    def test_hidden_script_dates_are_not_schedule_text(self):
        source=self.source();source['url']='https://club.example/calendar'
        self.assertEqual(extract_text_schedule('<script>'+self.html()+'</script>',source),[])
    def test_explicit_winter_season_and_accessible_track_labels(self):
        source=dict(SOURCE,url='https://club.example/calendar',text_profile={'paths':['/calendar'],'image_labels':{'Home Track Logo':'Home'},'sections':[{
            'start':r'^(?P<year>20\d{2})-(?P<end_year>\d{2})$', 'end':r'^Next Championship$',
            'row':r'^(?P<event>Race \d+) (?P<date>[^\n@]+) @\n(?P<venue>Home)$',
            'name':'Winter {event}','rollover_month':7,'auto_import':True,
            'venues':{'Home':{'name':'Home Track'}}}]})
        raw='<h3>2026-27</h3><p>Race 1 November 21 @</p><img alt="Home Track Logo"><p>Race 2 January 23 @</p><div title="Home Track Logo"><img></div><h3>Next Championship</h3>'
        found=extract_text_schedule(raw,source)
        self.assertEqual([e['startDate'] for e in found],['2026-11-21','2027-01-23'])
        self.assertEqual(extract_text_schedule(raw.replace('2026-27','2026-29'),source),[])
        self.assertEqual(extract_text_schedule(raw.replace('Home Track Logo','Unknown Logo'),source),[])


class CalendarLocationTests(unittest.TestCase):
    def test_directory_website_links_retain_club_heading_context(self):
        source=dict(SOURCE,directory=True,trusted=False)
        raw='<h2>Club de Karting de Québec</h2><a href="https://ckq.example/">Site Web</a><a href="https://facebook.com/ckq">Facebook</a>'
        leads=extract_page(raw,source,TODAY)['leads']
        self.assertEqual(len(leads),1);self.assertEqual(leads[0]['club'],'Club de Karting de Québec')
    def test_squarespace_multiday_and_reviewed_away_venue(self):
        source=dict(SOURCE,require_venue_alias=True,venue_aliases={'Pats Acres':{'name':'Pats Acres Racing Complex','address':{'addressCountry':'USA','addressRegion':'OR','addressLocality':'Canby'}}})
        raw='''<article class="eventlist-event"><a class="eventlist-title-link" href="/events/race-10">Kart Race 10</a>
        <time class="event-date" datetime="2026-10-24">Saturday</time><time class="event-time-localized" datetime="2026-10-24">8 AM</time>
        <time class="event-date" datetime="2026-10-25">Sunday</time><time class="event-time-localized" datetime="2026-10-25">5 PM</time>
        <li class="eventlist-meta-address">Pats Acres<a href="https://maps.google.com/">(map)</a></li></article>'''
        event=extract_page(raw,source,TODAY)['events'][0]
        self.assertEqual((event['start'],event['end']),('2026-10-24','2026-10-25'))
        self.assertEqual((event['venue'],event['city']),('Pats Acres Racing Complex','Canby'))
        self.assertFalse(event['location_needs_review'])
        event=extract_page(raw.replace('Pats Acres','Unknown Track'),source,TODAY)['events'][0]
        self.assertTrue(event['location_needs_review'])
    def test_dpcalendar_feed_with_verified_title_venue(self):
        url='https://club.example/index.php?option=com_dpcalendar&task=ical.download&id=39'
        self.assertTrue(feed_url(url));self.assertFalse(feed_url(url.replace('ical.download','event.edit')))
        source=dict(SOURCE,feed_race_pattern=r'GHRS Fall \d+ @ SRP',require_feed_venue_rule=True,feed_venue_rules=[{'pattern':r'GHRS Fall \d+ @ SRP','location':{'venue':'Speedsportz Racing Park','city':'New Caney','region':'TX','country':'USA'}}])
        raw='BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:fall-6\nDTSTART;VALUE=DATE:20261122\nDTEND;VALUE=DATE:20261123\nSUMMARY:GHRS Fall 6 @ SRP\nEND:VEVENT\nEND:VCALENDAR'
        event=normalized_ics(raw,source,TODAY)[0]
        self.assertEqual(event['start'],event['end']);self.assertEqual(event['city'],'New Caney');self.assertFalse(event['location_needs_review'])
        self.assertEqual(normalized_ics(raw.replace('GHRS Fall 6','GHRS Practice'),source,TODAY),[])
        event=normalized_ics(raw.replace('GHRS Fall 6 @ SRP','Club Race at Unknown Track'),source,TODAY)[0]
        self.assertTrue(event['location_needs_review'])


class AdditionalPdfTests(unittest.TestCase):
    def test_two_named_columns_never_pair_wrong_dates_and_titles(self):
        text='2026 KART SCHEDULE\nMay 31-        Club Kart Race #3                        November 1-            Club Kart Race #11\nNovember 21-   Track Clean Up\nOctober 24 & 25 (Rain Date)'
        events=lines_to_events(text,dict(SOURCE,pdf_profile={'layout':'named_columns','auto_import':True}))
        self.assertEqual([(e['startDate'],e['name']) for e in events],[('2026-05-31','Club Kart Race #3'),('2026-11-01','Club Kart Race #11')])
    def test_reviewed_pdf_section_excludes_age_cutoff_dates(self):
        profile={'layout':'date_columns','auto_import':True,'year_pattern':r'^(?P<year>20\d{2}) Karting Challenge$','section_start':r'Race Dates:','section_end':r'Competition Age:'}
        text='2026 Karting Challenge\nRace Dates:\nOctober 25       November 22       December 20\nCompetition Age:\nDecember 31'
        events=lines_to_events(text,dict(SOURCE,pdf_profile=profile))
        self.assertEqual([e['startDate'] for e in events],['2026-10-25','2026-11-22','2026-12-20'])
        self.assertEqual(lines_to_events(text.replace('Competition Age:','Class Ages:'),dict(SOURCE,pdf_profile=profile)),[])


if __name__=='__main__':unittest.main()
