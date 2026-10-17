# -*- coding: utf-8 -*-
"""Resolve non-CrossRef DOIs via their correct registries: DataCite (Zenodo,
arXiv, LBNL/OSTI) and retry the two 429 rate-limited CrossRef DOIs."""
import urllib.request, urllib.parse, json, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}


def http(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45).read().decode('utf-8', 'replace')


print('===== DataCite (covers Zenodo / arXiv / OSTI-LBNL) =====')
for doi in ['10.5281/zenodo.22138940', '10.48550/arxiv.2603.02705',
            '10.48550/arxiv.2609.25437', '10.48550/arxiv.2606.21760',
            '10.71468/P1RP4F']:
    try:
        d = json.loads(http('https://api.datacite.org/dois/' + urllib.parse.quote(doi)))['data']['attributes']
        print('OK   %-28s | %-14s | %s' % (doi, d.get('publisher') or d.get('agency', ''), (d.get('titles') or [{}])[0].get('title', '')[:80]))
        print('       creators:', '; '.join(c.get('name', '') for c in (d.get('creators') or [])[:6])[:200])
        print('       year:', d.get('publicationYear'), '| type:', (d.get('types') or {}).get('resourceTypeGeneral'))
    except Exception as e:
        print('FAIL %-28s | %s %s' % (doi, type(e).__name__, e))
    time.sleep(0.5)

print('\n===== CrossRef retry (previously 429) =====')
for doi in ['10.1016/j.resconrec.2025.108310', '10.3390/w16111571']:
    for attempt in range(3):
        try:
            d = json.loads(http('https://api.crossref.org/works/' + urllib.parse.quote(doi)))['message']
            print('OK   %-32s | %-30s | %s' % (doi, (d.get('container-title') or [''])[0][:30], (d.get('title') or [''])[0][:60]))
            break
        except Exception as e:
            print('     retry %d for %s: %s' % (attempt + 1, doi, type(e).__name__))
            time.sleep(3)
    time.sleep(1)
