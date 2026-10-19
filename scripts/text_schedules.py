"""Explicitly reviewed text sections; never infer a year from today's date."""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from scripts.schedule_tables import date_range


class ScheduleText(HTMLParser):
    def __init__(self,image_labels=None):
        super().__init__(); self.parts=[]; self.skip=0;self.image_labels=image_labels or {}
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript','template'):self.skip+=1
        elif not self.skip and tag in ('p','div','li','h1','h2','h3','h4','h5','h6','br','tr'):self.parts.append('\n')
        if not self.skip:
            attributes=dict(attrs)
            label=attributes.get('alt') if tag=='img' else attributes.get('title') if tag=='div' else None
            if label in self.image_labels:self.parts.extend(['\n',self.image_labels[label],'\n'])
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript','template'):self.skip=max(0,self.skip-1)
        elif not self.skip and tag in ('p','div','li','h1','h2','h3','h4','h5','h6','tr'):self.parts.append('\n')
    def handle_data(self,text):
        if not self.skip:self.parts.append(text)
    def text(self):
        return '\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())


def extract_text_schedule(raw,source):
    profile=source.get('text_profile',{})
    if urlsplit(source['url']).path not in profile.get('paths',[]):return []
    parser=ScheduleText(profile.get('image_labels'));parser.feed(raw);text=parser.text();events=[]
    for section in profile.get('sections',[]):
        for heading in re.finditer(section['start'],text,re.I|re.M):
            if not heading.groupdict().get('year'):continue
            year=int(heading['year']);end_year=heading.groupdict().get('end_year')
            if end_year:
                end_year=int(end_year) if len(end_year)==4 else (year//100)*100+int(end_year)
                if end_year!=year+1 or not 1<=section.get('rollover_month',0)<=12:continue
            body=text[heading.end():]
            end=re.search(section['end'],body,re.I|re.M)
            # A missing boundary may indicate a redesigned page. Fail closed.
            if not end:continue
            body=body[:end.start()]
            for row in re.finditer(section['row'],body,re.I|re.M):
                values=dict(heading.groupdict(),**row.groupdict());date_text=values.get('date','')
                for before,after in section.get('date_corrections',{}).items():date_text=date_text.replace(before,after)
                dates=date_range(date_text,year)
                if not dates:continue
                if end_year and dates[0].month<section['rollover_month']:
                    dates=date_range(date_text,end_year)
                    if not dates:continue
                name=section['name'].format(**values).strip()
                token=section.get('identity','{event}').format(**values) if section.get('identity') else values.get('event') or str(dates[0])
                venue_key=values.get('venue','').strip()
                location=section.get('venues',{}).get(venue_key,{})
                events.append({'_curated_id':section.get('curated_events',{}).get(str(year)+'|'+token), '@type':'Event','@id':source['id']+'|'+str(dates[0].year)+'|'+token,
                    'url':source['url'],'name':name,'startDate':str(dates[0]),'endDate':str(dates[1]),
                    'location':location,'_parser':'reviewed-text','_shared_url':True,
                    '_publication_needs_review':not section.get('auto_import',False),
                    '_location_ambiguous':bool(venue_key and not location)})
    return events


class AttributeCalendar(HTMLParser):
    """Reviewed CMS data attributes; scripts are never evaluated."""
    def __init__(self, source, profile):
        super().__init__();self.source=source;self.profile=profile;self.events=[]
    def handle_starttag(self, tag, attrs):
        attributes=dict(attrs);p=self.profile
        if p['class'] not in attributes.get('class','').split():return
        if attributes.get(p['category_attribute'],'').casefold() not in p['categories']:return
        name=attributes.get(p['name_attribute'],'').strip()
        day=attributes.get(p['date_attribute'],'').strip()
        if not name or not re.fullmatch(r'20\d{2}-\d{2}-\d{2}',day):return
        token=name.casefold() if re.fullmatch(p.get('identity_name_pattern',r'(?!)'),name,re.I) else name.casefold()+'|'+day
        self.events.append({'@type':'Event','@id':self.source['id']+'|'+day[:4]+'|'+token,
            'name':name,'startDate':day,'endDate':attributes.get(p.get('end_attribute',''),'') or day,
            'url':self.source['url'],'_shared_url':True,'_parser':'reviewed-attributes',
            '_registration_url':attributes.get(p.get('registration_attribute',''),''),
            '_publication_needs_review':not p.get('auto_import',False)})


def extract_attribute_calendar(raw, source):
    profile=source.get('attribute_calendar',{})
    if urlsplit(source['url']).path not in profile.get('paths',[]):return []
    parser=AttributeCalendar(source,profile);parser.feed(raw)
    return parser.events
