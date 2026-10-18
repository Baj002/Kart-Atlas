#!/usr/bin/env python3
"""Conservative MotorsportReg public event-page enrichment; no private API or scraping bypass."""
import csv, html, json, re, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self): super().__init__();self.links=[];self.anchor=None;self.title='';self.in_title=False;self.description=''
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='title':self.in_title=True
  if tag=='meta' and a.get('name','').lower()=='description':self.description=a.get('content','')
  if tag=='a':self.anchor=[a.get('href',''),'']
 def handle_data(self,data):
  if self.in_title:self.title+=data
  if self.anchor:self.anchor[1]+=data
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='a' and self.anchor:self.links.append(self.anchor);self.anchor=None
def msr(url):
 h=urlparse(url).hostname or ''
 return h=='motorsportreg.com' or h.endswith('.motorsportreg.com')
def run():
 path=ROOT/'data/races.csv'
 with path.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
 output={}
 for row in rows:
  url=row.get('Source URL','').strip()
  if not msr(url):continue
  event_id=re.search(r'-(\\d{6})(?:[/?#]|$)',url)
  key='|'.join([row['Start Date'],row['Race / Event'].casefold().strip(),row['Track / Venue'].casefold().strip()])
  record={'source_url':url,'provider':'MotorsportReg','status':'not_verified'}
  try:
   req=Request(url,headers={'User-Agent':'KartAtlasResearch/1.0 (public event information; contact via repository)','Accept':'text/html'})
   with urlopen(req,timeout=12) as response:
    final=response.geturl()
    if not msr(final):raise ValueError('Redirect outside MotorsportReg')
    raw=response.read(450000).decode('utf-8','replace')
   page=Page();page.feed(raw)
   # Verify page corresponds to the specific race; avoid misattribution from generic club pages.
   tokens=[t for t in re.findall(r'[a-z0-9]+',row['Race / Event'].lower()) if len(t)>3 and t not in ('race','round','kart','karting','series','championship')]
   title=(page.title+' '+page.description).lower()
   matched=sum(t in title for t in tokens)
   if len(tokens)<2 or matched<2:raise ValueError('Event identity not sufficiently verified')
   record.update(status='matched',checked_at=datetime.now(timezone.utc).isoformat(),registration_url=final,description=page.description[:500])
   for href,label in page.links:
    dest=urljoin(final,href);txt=label.strip().lower()
    if not dest.startswith('https://') or len(dest)>500:continue
    if re.search(r'\\b(schedule|timetable)\\b',txt):record.setdefault('schedule_url',dest)
    if re.search(r'\\b(rulebook|regulations|supplementary rules)\\b',txt):record.setdefault('rules_url',dest)
    if re.search(r'\\b(track map|paddock map|circuit map)\\b',txt):record.setdefault('track_map_url',dest)
  except Exception as ex:record['reason']=str(ex)[:120]
  output[key]=record
  time.sleep(.8)
 dest=ROOT/'data/event_enrichment.json';dest.write_text(json.dumps({'updated':datetime.now(timezone.utc).isoformat(),'records':output},indent=2)+'\\n')
 print('Checked',len(output),'MotorsportReg source URLs;',sum(x['status']=='matched' for x in output.values()),'matched')
if __name__=='__main__':run()
