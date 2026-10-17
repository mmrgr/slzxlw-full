# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, json, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}
def http(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45).read().decode('utf-8', 'replace')

for doi in ['10.1021/acs.est.6c08380', '10.1016/j.wri.2022.100188', '10.1016/j.watres.2018.01.070',
            '10.1016/j.resconrec.2015.03.015', '10.3390/w16111571', '10.48550/arxiv.2606.21760',
            '10.1016/j.jclepro.2025.146528']:
    print('=' * 100); print('DOI:', doi)
    try:
        d = json.loads(http('https://api.openalex.org/works/doi:' + urllib.parse.quote(doi)))
        print(' title :', d.get('title'))
        print(' year  :', d.get('publication_year'), d.get('publication_date'), '| type:', d.get('type'))
        src = (d.get('primary_location') or {}).get('source') or {}
        print(' source:', src.get('display_name'), '| ISSN', src.get('issn_l'))
        print(' authors:', '; '.join((a.get('author') or {}).get('display_name', '') for a in (d.get('authorships') or [])[:10]))
        inv = d.get('abstract_inverted_index')
        if inv:
            pos = {}
            for w, ps in inv.items():
                for p in ps: pos[p] = w
            print(' abstract:', ' '.join(pos[k] for k in sorted(pos))[:1400])
        print(' cited_by:', d.get('cited_by_count'))
    except Exception as e:
        print(' FAIL', type(e).__name__, e)
    time.sleep(0.4)
