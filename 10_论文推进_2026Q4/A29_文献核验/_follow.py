# -*- coding: utf-8 -*-
"""Targeted follow-ups: Shen abstract, C6/C9/C10 candidates, AI-DC water quality papers."""
import urllib.request, urllib.parse, json, io, sys, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}


def http(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode('utf-8', 'replace')


def oa_search(q, per=6, extra=''):
    u = 'https://api.openalex.org/works?per-page=%d&search=%s&mailto=research@example.org%s' % (per, urllib.parse.quote(q), extra)
    print('### ' + q)
    try:
        d = json.loads(http(u))
    except Exception as e:
        print('   FAIL', type(e).__name__, e); return
    for it in d.get('results', []):
        src = (it.get('primary_location') or {}).get('source') or {}
        print('  %-34s | %-95s | %-45s | %s | %s' % (
            (it.get('doi') or '').replace('https://doi.org/', ''),
            (it.get('title') or '')[:95], (src.get('display_name') or '')[:45],
            it.get('publication_year'), it.get('type')))
    print()
    time.sleep(0.4)


# Shen Nature Water full abstract via OpenAlex abstract_inverted_index
print('=========== C1 Shen et al. Nature Water 2026 — full record ===========')
try:
    d = json.loads(http('https://api.openalex.org/works/doi:10.1038/s44221-026-00727-5'))
    inv = d.get('abstract_inverted_index')
    if inv:
        pos = {}
        for w, ps in inv.items():
            for p in ps:
                pos[p] = w
        print('ABSTRACT:', ' '.join(pos[k] for k in sorted(pos)))
    else:
        print('no abstract_inverted_index')
    print('concepts:', [c['display_name'] for c in (d.get('concepts') or [])][:10])
    print('biblio:', d.get('biblio'))
    print('topic:', (d.get('primary_topic') or {}).get('display_name'))
except Exception as e:
    print('FAIL', e)
print()

print('=========== C1 cross-check: 10826 plants / China WWTP count ===========')
oa_search('China wastewater treatment plants 10826 reclaimed water potential water scarcity national')
oa_search('reclaimed water utilization potential China wastewater treatment plants spatial economics')

print('=========== C6 urban unit process model candidates ===========')
oa_search('unit process model urban water system cost resilience decentralized resource recovery city scale')
oa_search('WaterMet2 urban water metabolism unit process model')

print('=========== C9 data center cooling + urban sustainability review ===========')
oa_search('data center cooling technology review urban sustainability water energy')
oa_search('review data centre cooling sustainability cities water energy nexus')

print('=========== C10 daily urban water metabolism ===========')
oa_search('urban water metabolism model daily time step supply wastewater recycling')
oa_search('city scale water metabolism model daily resolution water supply demand reuse')

print('=========== C7 AI data center water quality compatibility ===========')
oa_search('AI data center water assessment beyond water quantity quality compatibility recycled water')
oa_search('recycled water quality cooling tower data center fit for purpose assessment')
