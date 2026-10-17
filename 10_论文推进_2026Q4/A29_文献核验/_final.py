# -*- coding: utf-8 -*-
"""Final gap-closing searches for candidates 1,3,6,9,10 and novelty screening."""
import urllib.request, urllib.parse, json, io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}
def http(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=45).read().decode('utf-8', 'replace')
def oa(q, per=6, extra=''):
    print('### ' + q)
    try:
        d = json.loads(http('https://api.openalex.org/works?per-page=%d&search=%s&mailto=r@e.org%s' % (per, urllib.parse.quote(q), extra)))
    except Exception as e:
        print('   FAIL', type(e).__name__, e); return
    for it in d.get('results', []):
        src = (it.get('primary_location') or {}).get('source') or {}
        print('  %-34s | %-92s | %-40s | %s | %s' % ((it.get('doi') or '').replace('https://doi.org/', ''),
              (it.get('title') or '')[:92], (src.get('display_name') or '')[:40], it.get('publication_year'), it.get('type')))
    print(); time.sleep(0.35)

print('##### NOVELTY SCREEN: does anyone already do CoC / quality-constrained reclaimed-water DC cooling? #####')
oa('cycles of concentration water quality constraint cooling tower reclaimed water data center')
oa('water quality composition limits cooling water reuse concentration ratio economic optimum')
oa('cooling tower blowdown salinity constraint reuse benefit sign reversal')
print('##### C3 energy water carbon scenario spatial uncertainty #####')
oa('AI data center energy water carbon scenarios spatially explicit uncertainty analysis United States')
print('##### C6 unit process model city scale #####')
oa('unit process based model urban water system greenhouse gas cost decentralized city scale assessment')
print('##### C9 cooling + urban sustainability review #####')
oa('data center cooling technologies review water energy urban sustainability cities')
print('##### C10 daily urban water metabolism #####')
oa('urban water metabolism model daily time resolution water supply wastewater recycle city')
print('##### Xiao / peak-demand competitors already known #####')
oa('data centers public water systems peak demand capacity expansion')
