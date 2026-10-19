"""Text-layer PDF schedule extraction with explicit, reviewed layout profiles.

No OCR guesses are published. Unprofiled named rows remain review candidates.
"""
import datetime as dt
import io
import re
from scripts.schedule_tables import MONTHS, date_range

UNCERTAIN=re.compile(r'\b(rain|weather|make[ -]?up|tbd|tba|tentative|provisional|reserve|practice|closed|clean[ -]?up|setup|banquet|swap meet)\b',re.I)
MONTH_PATTERN='|'.join(sorted((re.escape(m) for m in MONTHS),key=len,reverse=True))
DATE_PREFIX=re.compile(r'^(?:(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)[,\s]+)?'
    r'((?:'+MONTH_PATTERN+r')[\s-]+\d{1,2}(?:st|nd|rd|th)?(?:\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?)?'
    r'|\d{1,2}(?:st|nd|rd|th)?(?:\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?)?[\s-]+(?:'+MONTH_PATTERN+r'))(?:\s*,?\s*(20\d{2}))?\b',re.I)

def schedule_year(text):
    headings='\n'.join(line.strip() for line in text.splitlines() if line.strip())[:1200]
    found=re.findall(r'\b(20\d{2})[^\n]{0,80}(?:schedul[ea]|calendrier|calendario)',headings,re.I)
    return int(found[0]) if len(set(found))==1 else None

def lines_to_events(text,source,page=1):
    profile=source.get('pdf_profile') or {}
    year=schedule_year(text)
    if profile.get('year_pattern'):
        heading=re.search(profile['year_pattern'],text,re.I|re.M)
        year=int(heading['year']) if heading else None
    if year is None:return []
    if profile.get('section_start'):
        start=re.search(profile['section_start'],text,re.I|re.M)
        if not start:return []
        text=text[start.end():]
        end=re.search(profile['section_end'],text,re.I|re.M)
        if not end:return []
        text=text[:end.start()]
    layout=profile.get('layout','named_rows')
    records=[];month=None
    lines=text.splitlines()
    if layout=='named_columns':
        # Reviewed side-by-side schedules: split only before another explicit
        # month/date, not at the whitespace separating a date from its title.
        lines=[cell for line in lines for cell in re.split(r'\s{4,}(?=(?:'+MONTH_PATTERN+r')\s+\d)',line,flags=re.I)]
    for raw in lines:
        line=raw.strip()
        if not line:continue
        if line.lower() in MONTHS:month=line;continue
        if layout=='date_columns':
            for cell in re.split(r'\s{3,}',line):
                if UNCERTAIN.search(cell):continue
                match=DATE_PREFIX.fullmatch(cell)
                if not match:continue
                dates=date_range(match.group(1),year)
                if not dates:continue
                name=profile.get('race_name',source['club']+' Club Race')
                records.append(_record(name,dates,source,page,profile,True))
        else:
            # Column boundaries are kept by pypdf's layout extraction. Do not
            # combine dates and names across columns or infer merged-cell ranges.
            match=DATE_PREFIX.match(line)
            if match:
                date_text=match.group(1);tail=line[match.end():]
            else:
                day=re.match(r'^(\d{1,2}(?:st|nd|rd|th)?(?:\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?)?)\s{2,}(.+)$',line,re.I)
                if not day or not month:continue
                date_text=month+' '+day.group(1);tail=day.group(2)
            name=re.split(r'\s{3,}',tail.strip(' -–—:'))[0].strip()
            if not name or UNCERTAIN.search(name):continue
            dates=date_range(date_text,year)
            if dates:records.append(_record(name,dates,source,page,profile,False))
    return records

def _record(name,dates,source,page,profile,date_only):
    # Bare dates have no stable organizer race identifier. Use date identity and
    # retain disappearance/change signals for review instead of guessing a move.
    token=(str(dates[0]) if date_only else name.casefold())
    return {'@type':'Event','name':name,'startDate':str(dates[0]),'endDate':str(dates[1]),
        '@id':source.get('event_namespace',source['id'])+'|'+str(dates[0].year)+'|'+token,'url':source['url'],'_parser':'pdf-text',
        '_publication_needs_review':not bool(profile.get('auto_import')),
        '_pdf_page':page,'_date_only':date_only,
        '_location_ambiguous':bool(re.search(r'@|\b(?:hosted|held|away|offsite)\b',name,re.I))}

def extract_pdf(raw,source):
    if not isinstance(raw,bytes) or not raw.startswith(b'%PDF'):raise ValueError('Not a PDF document')
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError
    try:
        reader=PdfReader(io.BytesIO(raw),strict=False)
        if reader.is_encrypted:raise ValueError('Encrypted PDF requires review')
        if len(reader.pages)>8:raise ValueError('PDF exceeds eight-page schedule limit')
        all_events=[];texts=[];layout_failed=False
        for number,page in enumerate(reader.pages,1):
            try:text=page.extract_text(extraction_mode='layout') or ''
            except (ArithmeticError,ValueError,TypeError,KeyError,IndexError,NotImplementedError):
                # Some public PDFs have fonts with zero character width. A plain
                # text fallback can aid review but must never auto-publish rows.
                layout_failed=True;text=page.extract_text() or ''
            if len(text)>100000:raise ValueError('PDF text exceeds schedule extraction limit')
            texts.append(text);all_events.extend(lines_to_events(text,source,number))
        text='\n'.join(texts)
        if layout_failed:
            for event in all_events:event['_publication_needs_review']=True
        return {'events':all_events,'text':text,'pages':len(reader.pages),
            'notice':'PDF has no usable text layer; image/OCR review required' if len(text.strip())<40 and not all_events else 'PDF layout failed; plain-text candidates require review' if layout_failed else None}
    except (PyPdfError,ArithmeticError,ValueError,TypeError,KeyError,IndexError,NotImplementedError) as exc:raise ValueError('PDF extraction failed: '+str(exc)) from exc
