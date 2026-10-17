# -*- coding: utf-8 -*-
"""Fetch authoritative metadata for specific DOIs + targeted follow-up searches."""
import urllib.request, urllib.parse, json, io, sys, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}


def http(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode('utf-8', 'replace')


def doi_meta(doi):
    print('=' * 100)
    print('DOI:', doi)
    # CrossRef
    try:
        d = json.loads(http('https://api.crossref.org/works/' + urllib.parse.quote(doi)))['message']
        au = '; '.join('%s %s' % (a.get('given', ''), a.get('family', '')) for a in (d.get('author') or []))
        print('  [CR] title :', (d.get('title') or [''])[0])
        print('  [CR] journal:', (d.get('container-title') or [''])[0])
        print('  [CR] year  :', d.get('issued', {}).get('date-parts', [['?']])[0])
        print('  [CR] volume/issue/page:', d.get('volume'), '/', d.get('issue'), '/', d.get('page'), '| article:', d.get('article-number'))
        print('  [CR] type  :', d.get('type'))
        print('  [CR] authors:', au[:400])
        print('  [CR] publisher:', d.get('publisher'))
        ab = (d.get('abstract') or '')
        if ab:
            print('  [CR] abstract:', ab[:700].replace('\n', ' '))
    except Exception as e:
        print('  [CR] FAIL', type(e).__name__, e)
    time.sleep(0.5)
    # OpenAlex
    try:
        d = json.loads(http('https://api.openalex.org/works/doi:' + urllib.parse.quote(doi))) 
        print('  [OA] title  :', d.get('title'))
        print('  [OA] year   :', d.get('publication_year'), '| date:', d.get('publication_date'), '| type:', d.get('type'))
        src = (d.get('primary_location') or {}).get('source') or {}
        print('  [OA] source :', src.get('display_name'), '| ISSN-L', src.get('issn_l'), '| host', src.get('host_organization_name'))
        print('  [OA] authors:', '; '.join((a.get('author') or {}).get('display_name', '') for a in (d.get('authorships') or [])[:12]))
        print('  [OA] cited_by:', d.get('cited_by_count'), '| is_oa:', d.get('open_access', {}).get('is_oa'))
        insts = []
        for a in (d.get('authorships') or []):
            for i in (a.get('institutions') or []):
                if i.get('display_name') not in insts:
                    insts.append(i.get('display_name'))
        print('  [OA] institutions:', '; '.join(insts[:10]))
    except Exception as e:
        print('  [OA] FAIL', type(e).__name__, e)
    time.sleep(0.5)


DOIS = [
    '10.1038/s44221-026-00727-5',        # C1 Shen Nature Water
    '10.1016/j.ese.2026.100702',         # C2 competitor
    '10.1038/s44221-023-00087-4',        # C5 300 cities
    '10.1016/j.resconrec.2025.108310',   # C8 determinants review
    '10.1038/s41893-025-01681-y',        # Xiao AI servers Nature Sust
    '10.1038/s44221-024-00303-9',        # decentralization Nature Water
    '10.1016/j.enbuild.2023.113006',     # C4 LCA cooling device
    '10.1038/s41586-025-08832-3',        # LCA cool clouds Nature
    '10.1016/j.jclepro.2025.146528',     # C3 scenario water footprint
]
for d in DOIS:
    doi_meta(d)
