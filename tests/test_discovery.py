"""Offline checks for public structured event discovery."""
import datetime as dt
import unittest
from scripts.discover_events import extract

SOURCE={'url':'https://kartclub.example/events','club':'Example Kart Club',
        'venue':'Kart Track','city':'Town','region':'BC','country':'Canada'}

class DiscoveryTests(unittest.TestCase):
    def test_structured_race_and_calendar_link(self):
        raw='''<a href="/calendar/?ical=1">Subscribe</a>
        <script type="application/ld+json">{"@graph":[
        {"@type":"SportsEvent","name":"Fall Endurance Race","startDate":"2026-10-24T09:00:00-07:00","url":"https://kartclub.example/enduro"},
        {"@type":"Event","name":"Practice Session","startDate":"2026-10-25"}]}</script>'''
        found=extract(raw,SOURCE,dt.date(2026,10,18))
        self.assertEqual(len(found['events']),1)
        self.assertEqual(found['events'][0]['start'],'2026-10-24')
        self.assertEqual(found['feeds'],['https://kartclub.example/calendar/?ical=1'])
    def test_no_unverified_dates_or_cross_domain_feed(self):
        raw='''<a href="https://other.example/calendar.ics">External</a>
        <script type="application/ld+json">{"@type":"Event","name":"Championship Race","startDate":"TBA"}</script>'''
        found=extract(raw,SOURCE,dt.date(2026,10,18))
        self.assertEqual(found['events'],[])
        self.assertEqual(found['feeds'],[])

if __name__=='__main__':unittest.main()
