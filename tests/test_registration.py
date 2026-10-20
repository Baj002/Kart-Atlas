import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.registration import extract_registration_rows,refresh,instant

URL='https://raceselect.com/example/2026'
def row(name='Example Race 1',slug='race-1',status='Registration open',deadline='2026-11-01T07:00:00Z'):
    return f'''<div class="rs-row"><h3><a href="/example/{slug}/EventDetails">{name}</a></h3>
    <time datetime="2026-11-05T07:00:00Z">Event starts</time><span>{status}</span>
    <span>Closes <time datetime="{deadline}">Closing time</time></span>
    <a href="/example/{slug}/registration">Register now</a></div>'''

class RegistrationTests(unittest.TestCase):
    def test_featured_and_membership_deadlines_are_isolated(self):
        records=extract_registration_rows(row()+row('Membership','membership',deadline='2026-12-31T08:00:00Z'),URL)
        event=records['https://raceselect.com/example/race-1/eventdetails']
        self.assertEqual(event['registration_status'],'open')
        self.assertEqual(event['registration_deadline'],'2026-11-01T07:00:00+00:00')
        self.assertEqual(event['registration_url'],'https://raceselect.com/example/race-1/registration')
        self.assertNotIn('registration_opens_at',event)
    def test_no_timezone_or_link_guesses(self):
        records=extract_registration_rows(row(deadline='2026-11-01').replace('<a href="/example/race-1/registration">Register now</a>',''),URL)
        record=next(iter(records.values()))
        self.assertNotIn('registration_deadline',record);self.assertNotIn('registration_url',record)
        self.assertIsNone(instant('2026-11-01T12:00:00'))
    def test_opens_and_closes_are_distinct(self):
        records=extract_registration_rows(row().replace('Closes','Opens'),URL)
        record=next(iter(records.values()));self.assertIn('registration_opens_at',record);self.assertNotIn('registration_deadline',record)
    def test_refresh_fails_without_renewing_cached_open_status(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir()
            (root/'data/registration_sources.json').write_text(json.dumps({'sources':[{'event_id':'race','url':URL,'event_url':'https://raceselect.com/example/race-1/EventDetails'}]}))
            refresh(root,lambda u:row(),now='2026-10-20T00:00:00+00:00')
            first=json.loads((root/'data/event_registration.json').read_text())['records']['race']
            refresh(root,lambda u:row(slug='different-race'),now='2026-10-23T00:00:00+00:00')
            saved=json.loads((root/'data/event_registration.json').read_text())
            self.assertEqual(saved['records']['race'],first)
            self.assertEqual(saved['checks'][0]['status'],'retained_unverified')
    def test_other_platform_is_not_interpreted_as_raceselect(self):
        self.assertEqual(extract_registration_rows(row(),'https://other.example/events'),{})

class RegistrationValidation(unittest.TestCase):
    def test_published_claims_require_timezone_and_dated_evidence(self):
        from scripts.validate_data import validate
        from tests.test_engine import normalized
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'site').mkdir()
            event=dict(normalized(),id='entry',registration_status='open',registration_evidence=URL,registration_checked_at='2026-10-20T00:00:00+00:00',registration_deadline='2026-11-01T07:00:00Z')
            def write(): (root/'site/events.json').write_text(json.dumps({'events':[event]}))
            write();self.assertTrue(validate(root))
            event['registration_deadline']='2026-11-01';write()
            with self.assertRaisesRegex(AssertionError,'timezone-aware'):validate(root)
            event['registration_deadline']='2026-11-01T07:00:00Z';event.pop('registration_evidence');write()
            with self.assertRaisesRegex(AssertionError,'dated source evidence'):validate(root)


if __name__=='__main__':unittest.main()
