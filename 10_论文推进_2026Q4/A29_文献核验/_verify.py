# -*- coding: utf-8 -*-
"""Read-only literature verification against CrossRef + OpenAlex + DataCite."""
import urllib.request, urllib.parse, json, io, sys, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}


def http(u):
    req = urllib.request.Request(u, headers=UA)
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')


def crossref(q, rows=5, filt=None):
    u = 'https://api.crossref.org/works?rows=%d&query.bibliographic=%s' % (rows, urllib.parse.quote(q))
    if filt:
        u += '&filter=' + filt
    try:
        d = json.loads(http(u))
    except Exception as e:
        return [('ERR', type(e).__name__ + ' ' + str(e), '', '')]
    out = []
    for it in d['message']['items']:
        out.append((
            it.get('DOI', ''),
            (it.get('title') or [''])[0][:120],
            (it.get('container-title') or [''])[0][:60],
            str(it.get('issued', {}).get('date-parts', [['']])[0][0]),
            it.get('type', ''),
            ', '.join((a.get('family', '') or '') for a in (it.get('author') or [])[:3]),
        ))
    return out


def openalex(q, per=5):
    u = 'https://api.openalex.org/works?per-page=%d&search=%s&mailto=research@example.org' % (per, urllib.parse.quote(q))
    try:
        d = json.loads(http(u))
    except Exception as e:
        return [('ERR', type(e).__name__ + ' ' + str(e), '', '', '', '')]
    out = []
    for it in d.get('results', []):
        out.append((
            (it.get('doi') or '').replace('https://doi.org/', ''),
            (it.get('title') or '')[:120],
            ((it.get('primary_location') or {}).get('source') or {}).get('display_name', '') or '',
            str(it.get('publication_year', '')),
            it.get('type', ''),
            ', '.join((a.get('author', {}) or {}).get('display_name', '') for a in (it.get('authorships') or [])[:3]),
        ))
    return out


def show(label, rows):
    print('### ' + label)
    for r in rows:
        print('   | '.join(str(x) for x in r))
    print()


QUERIES = [
    ('C1-Shen Nature Water reclaimed water China',
     'Shen reclaimed water alleviate water scarcity China wastewater treatment plants Nature Water'),
    ('C1b-OpenAlex',
     None),
    ('C2-DC WWTP symbiosis',
     'Global data-water symbiosis reduces AI infrastructure carbon and water footprint'),
    ('C3-AI server energy water carbon scenarios spatial uncertainty',
     'AI server growth energy water carbon scenarios spatially explicit uncertainty analysis data centers'),
    ('C4-DC cooling LCA',
     'life cycle assessment data center cooling technology environmental impacts'),
    ('C5-300 cities water stress wastewater GHG',
     'water stress mitigation and wastewater greenhouse gas emissions 300 cities joint analysis'),
    ('C6-urban unit process model decentralized',
     'urban scale unit process model decentralized water systems resource recovery cost resilience'),
    ('C7-AI DC water quality fit for purpose',
     'data center water use beyond water quantity quality compatibility reuse'),
    ('C8-DC workload water determinants',
     'determinants of data center water consumption variability server efficiency cooling climate grid'),
    ('C9-DC cooling urban sustainability review',
     'data center cooling technologies urban sustainability review'),
    ('C10-daily urban water metabolism',
     'daily urban water metabolism model supply demand wastewater recycling'),
]

for label, q in QUERIES:
    if q is None:
        show(label + ' [OpenAlex]', openalex('Shen Nature Water reclaimed water China wastewater treatment plants scarce'))
    else:
        show(label + ' [CrossRef]', crossref(q, rows=5))
        time.sleep(0.4)
        show(label + ' [OpenAlex]', openalex(q, per=4))
        time.sleep(0.4)
