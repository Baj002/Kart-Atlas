import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from scripts.reminder_calendars import build,calendar

NOW=dt.datetime(2026,10,20,tzinfo=dt.timezone.utc)
EVENT={'id':'race','name':'Example 🏁 '+('é'*80),'source':'https://example.com/race','registration_evidence':'https://example.com/race','registration_url':'https://register.example/race','registration_deadline':'2026-11-01T19:00:00-06:00'}
class ReminderCalendars(unittest.TestCase):
    def test_utc_alarm_feed_and_utf8_folding(self):
        text=calendar(EVENT,dt.datetime.fromisoformat(EVENT['registration_deadline']),NOW)
        self.assertIn('DTSTART:20261102T010000Z',text)
        self.assertIn('TRIGGER:-P1D',text);self.assertIn('TRIGGER:-PT1H',text)
        self.assertTrue(all(len(line.encode())<=75 for line in text.split('\r\n')))
        self.assertEqual(text.count('BEGIN:VEVENT'),1)
    def test_revision_cancel_and_missing_deadline_keep_stable_subscription(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir();events=[dict(EVENT)]
            build(root,events,NOW);path=root/'site/reminders/race.ics'
            self.assertEqual(events[0]['registration_reminder_url'],'/reminders/race.ics')
            first=path.read_text();self.assertIn('STATUS:CONFIRMED',first)
            events[0]['registration_deadline']='2026-11-03T01:00:00Z';build(root,events,NOW)
            revised=path.read_text();self.assertIn('DTSTART:20261103T010000Z',revised)
            self.assertIn('UID:registration-race@kartatlas.local',revised);self.assertIn('SEQUENCE:2',revised)
            events[0].pop('registration_deadline');build(root,events,NOW)
            self.assertIn('STATUS:CANCELLED',path.read_text());self.assertIn('DTSTART:20261103T010000Z',path.read_text())
            events[0]['registration_deadline']='2026-11-03T01:00:00Z'
            events[0]['status']='cancelled';build(root,events,NOW)
            self.assertIn('STATUS:CANCELLED',path.read_text());self.assertNotIn('VALARM',path.read_text())
            build(root,[],NOW);self.assertIn('STATUS:CANCELLED',path.read_text())
    def test_empty_feed_for_unknown_deadline_and_old_alias_subscription_updates(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data').mkdir()
            unknown=dict(EVENT,end='2026-11-05');unknown.pop('registration_deadline')
            build(root,[unknown],NOW);self.assertTrue((root/'site/reminders/race.ics').exists());self.assertNotIn('BEGIN:VEVENT',(root/'site/reminders/race.ics').read_text())
            build(root,[dict(EVENT)],NOW)
            self.assertIn('BEGIN:VEVENT',(root/'site/reminders/race.ics').read_text())
            replacement=dict(EVENT,id='canonical',alias_ids=['race'],registration_deadline='2026-11-04T01:00:00Z')
            build(root,[replacement],NOW)
            self.assertIn('DTSTART:20261104T010000Z',(root/'site/reminders/race.ics').read_text())
            self.assertIn('UID:registration-race@kartatlas.local',(root/'site/reminders/race.ics').read_text())
            self.assertEqual(replacement['registration_reminder_url'],'/reminders/canonical.ics')
if __name__=='__main__':unittest.main()
