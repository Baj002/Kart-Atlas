"""Read public RaceSelect list cards; never request private APIs or sign in."""
import datetime as dt
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
from zoneinfo import ZoneInfo

class RaceSelectParser(HTMLParser):
    def __init__(self):
        super().__init__();self.events=[];self.current=None;self.span_depth=0;self.title_depth=None;self.status_depth=None;self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):
            url=a['href'];self.links.append(url)
            if urlsplit(url).path.lower().endswith('/eventdetails'):
                self.current={'@type':'Event','name':'','url':url,'_parser':'raceselect','_texts':[]};self.span_depth=0
        if self.current is None:return
        if tag=='span':
            self.span_depth+=1
            classes=a.get('class','').split()
            if not self.current['name'] and 'font-semibold' in classes and 'break-words' in classes:self.title_depth=self.span_depth
            if 'data-race-countdown-label' in a:self.status_depth=self.span_depth;self.current['_registration_status']=''
        if tag=='time' and a.get('data-browser-date')=='weekday-range':
            self.current['startDate']=a.get('data-browser-date-from') or a.get('datetime','')
            self.current['endDate']=a.get('data-browser-date-to') or self.current['startDate']
    def handle_data(self,data):
        if self.current is None:return
        if self.title_depth is not None:self.current['name']+=data
        if self.status_depth is not None:self.current['_registration_status']+=data
    def handle_endtag(self,tag):
        if self.current is None:return
        if tag=='span':
            if self.span_depth==self.title_depth:self.title_depth=None
            if self.span_depth==self.status_depth:self.status_depth=None
            self.span_depth-=1
        if tag=='a':
            if self.current.get('startDate') and self.current['name']:self.events.append(self.current)
            self.current=None;self.title_depth=None;self.status_depth=None

def extract_raceselect(raw,source):
    if (urlsplit(source['url']).hostname or '').removeprefix('www.')!='raceselect.com':return []
    parser=RaceSelectParser();parser.feed(raw);output=[]
    for event in parser.events:
        event['url']=urljoin(source['url'],event['url']);event['@id']=event['url']
        event['_publication_needs_review']=not bool(source.get('platform_venue_verified'))
        try:
            for field in ('startDate','endDate'):
                value=dt.datetime.fromisoformat(event[field].replace('Z','+00:00'))
                if source.get('timezone'):value=value.astimezone(ZoneInfo(source['timezone']))
                else:event['_publication_needs_review']=True
                event[field]=value.date().isoformat()
        except (ValueError,TypeError):continue
        status=event.get('_registration_status','').strip().casefold()
        event['_registration_status']=('open' if status=='registration open' else 'closed' if status=='registration closed' else 'disabled' if status=='registration disabled' else 'unknown')
        details=urlsplit(event['url']).path
        registration=details.rsplit('/',1)[0]+'/registration'
        if registration in parser.links:event['_registration_url']=urljoin(source['url'],registration)
        output.append(event)
    return output
