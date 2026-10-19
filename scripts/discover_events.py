#!/usr/bin/env python3
"""Compatibility entry point for public race discovery."""
import datetime as dt
from scripts.discovery_engine import Parser as DiscoverParser, extract_page, run

def extract(raw, source, today=None):
    source=dict(source)
    source.setdefault('id','discovery')
    found=extract_page(raw,source,today or dt.date.today())
    return {'feeds':found['feeds'],'events':[dict(e,status='needs_review') for e in found['events']]}

if __name__=='__main__':run()
