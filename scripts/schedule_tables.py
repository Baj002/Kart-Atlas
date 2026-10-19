"""Conservative HTML schedule rows: explicit dates only, no locale guessing."""
import datetime as dt
import re

MONTHS={name:i for i,name in enumerate(('january','february','march','april','may','june','july','august','september','october','november','december'),1)}
MONTHS.update({name[:3]:i for name,i in list(MONTHS.items())})
MONTHS.update({'janvier':1,'février':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'août':8,'septembre':9,'octobre':10,'novembre':11,'décembre':12,
    'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12})

def date_range(text,year=None):
    text=re.sub(r'(\d)(st|nd|rd|th)\b',r'\1',text.lower())
    explicit=re.findall(r'\b(20\d{2})\b',text)
    if explicit:
        if len(set(explicit))>1:return None
        year=int(explicit[0])
    if not year:return None
    iso=re.findall(r'\b20\d{2}-\d{2}-\d{2}\b',text)
    try:
        if iso:
            if len(iso)>2:return None
            return dt.date.fromisoformat(iso[0]),dt.date.fromisoformat(iso[-1])
        # Remove year and weekday parentheticals before examining day tokens.
        text=re.sub(r'\b20\d{2}\b|\([^)]*\)',' ',text)
        tokens=re.findall(r'[a-zéûôà]+|\d{1,2}',text)
        month_positions=[(i,MONTHS[t]) for i,t in enumerate(tokens) if t in MONTHS]
        if not month_positions:return None
        dates=[];current_month=None
        # Month-first and day-first formats, but never numeric month/day guessing.
        if tokens[0].isdigit():
            if len(month_positions)!=1:return None
            month=month_positions[0][1]
            dates=[dt.date(year,month,int(t)) for t in tokens if t.isdigit()]
        else:
            for token in tokens:
                if token in MONTHS:current_month=MONTHS[token]
                elif token.isdigit() and current_month:dates.append(dt.date(year,current_month,int(token)))
        if not dates or len(dates)>2:return None
        start,end=dates[0],dates[-1]
        if not 0<=(end-start).days<=12:return None
        return start,end
    except ValueError:return None

def row_event(cells,year):
    if len(cells)<2:return None
    dates=date_range(cells[0],year)
    if dates is None:return None
    name=' '.join(cells[1].split())
    # Offsite/combined-hosted rounds cannot inherit the home track's location.
    ambiguous=bool(re.search(r'@|\b(?:held|hosted| at |venue|location)\b',name,re.I))
    return {'@type':'Event','name':name,'startDate':str(dates[0]),'endDate':str(dates[1]),
            '_parser':'schedule-table','_location_ambiguous':ambiguous}
