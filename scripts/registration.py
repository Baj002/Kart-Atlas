"""Evidence-backed registration data; links alone never imply availability."""
import datetime as dt
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

FIELDS=('registration_url','registration_status','registration_deadline','registration_opens_at','registration_checked_at','registration_evidence')

def instant(value):
    try:
        parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        return parsed if parsed.tzinfo else None
    except (ValueError,TypeError,AttributeError):return None

class RegistrationRows(HTMLParser):
    """Keep featured and compact RaceSelect rows isolated, including memberships."""
    def __init__(self,url):
        super().__init__();self.url=url;self.depth=0;self.row=None;self.rows=[];self.anchor=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='div':
            self.depth+=1
            if 'rs-row' in a.get('class','').split() and self.row is None:
                self.row={'depth':self.depth,'texts':[],'links':[],'times':{}}
        if self.row is None:return
        if tag=='a':self.anchor={'url':urljoin(self.url,a.get('href','')),'text':''}
        if tag=='time' and instant(a.get('datetime')):
            context=' '.join(self.row['texts'][-2:]).strip()
            field='registration_deadline' if re.search(r'Closes\s*$',context,re.I) else 'registration_opens_at' if re.search(r'Opens\s*$',context,re.I) else None
            if field:self.row['times'][field]=instant(a['datetime']).isoformat()
    def handle_data(self,text):
        if self.row is None:return
        if text.strip():self.row['texts'].append(text.strip())
        if self.anchor is not None:self.anchor['text']+=text
    def handle_endtag(self,tag):
        if tag=='a' and self.row is not None and self.anchor is not None:
            self.row['links'].append(self.anchor);self.anchor=None
        if tag=='div':
            if self.row is not None and self.row['depth']==self.depth:
                self.rows.append(self.row);self.row=None;self.anchor=None
            self.depth-=1

def extract_registration_rows(raw,url):
    if (urlsplit(url).hostname or '').removeprefix('www.')!='raceselect.com':return {}
    parser=RegistrationRows(url);parser.feed(raw);records={}
    for row in parser.rows:
        detail=next((a['url'] for a in row['links'] if urlsplit(a['url']).path.lower().endswith('/eventdetails')),None)
        if not detail:continue
        text=' '.join(row['texts'])
        status='open' if re.search(r'\bRegistration open\b',text,re.I) else 'closed' if any(t.casefold() in ('closed','registration closed') for t in row['texts']) else 'sold_out' if re.search(r'\bsold out\b',text,re.I) else 'not_announced'
        registration=next((a['url'] for a in row['links'] if urlsplit(a['url']).path.lower().endswith('/registration') and urlsplit(a['url']).path.rsplit('/',1)[0]==urlsplit(detail).path.rsplit('/',1)[0]),None)
        record=dict(row['times'],registration_status=status,registration_evidence=url)
        if registration:record['registration_url']=registration
        records[detail.rstrip('/').casefold()]=record
    return records

def refresh(root=None,fetcher=None,now=None):
    from scripts.discovery_engine import PublicClient
    root=root or Path(__file__).resolve().parents[1];fetcher=fetcher or PublicClient()
    now=now or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    config=json.loads((root/'data/registration_sources.json').read_text())
    path=root/'data/event_registration.json'
    prior=json.loads(path.read_text()) if path.exists() else {'records':{}}
    records=prior.get('records',{});checks=[];cache={}
    for source in config['sources']:
        try:
            if source['url'] not in cache:cache[source['url']]=extract_registration_rows(fetcher(source['url']),source['url'])
            observation=cache[source['url']].get(source['event_url'].rstrip('/').casefold())
            if observation is None:raise ValueError('Specific event registration row not found')
            records[source['event_id']]=dict(observation,registration_checked_at=now)
            checks.append({'event_id':source['event_id'],'url':source['url'],'status':'verified'})
        except Exception as error:
            checks.append({'event_id':source['event_id'],'url':source['url'],'status':'retained_unverified','error':str(error)[:180]})
    path.write_text(json.dumps({'updated':now,'records':records,'checks':checks},indent=2)+'\n')
    print('Registration:',sum(c['status']=='verified' for c in checks),'verified;',len(checks),'checked')
    return checks

if __name__=='__main__':refresh()
