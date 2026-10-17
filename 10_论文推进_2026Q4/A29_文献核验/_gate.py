# -*- coding: utf-8 -*-
"""Final gate: re-resolve EVERY DOI in references.bib against CrossRef, fresh."""
import urllib.request, urllib.parse, json, io, sys, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
UA = {'User-Agent': 'lit-verify/1.0 (mailto:research@example.org)'}

txt = open('references.bib', encoding='utf-8').read()
body = '\n'.join(l for l in txt.split('\n') if not l.lstrip().startswith('%'))
pairs = re.findall(r'@(\w+)\{([^,]+),(.*?)\n\}', body, re.S)
print('Re-resolving %d DOIs against CrossRef...\n' % len(pairs))
bad = []
for tp, key, blk in pairs:
    m = re.search(r'doi\s*=\s*\{([^}]+)\}', blk)
    doi = m.group(1).strip()
    try:
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request('https://api.crossref.org/works/' + urllib.parse.quote(doi), headers=UA),
            timeout=45).read().decode('utf-8', 'replace'))['message']
        ti = (d.get('title') or [''])[0]
        jr = (d.get('container-title') or [''])[0]
        yr = d.get('issued', {}).get('date-parts', [['?']])[0][0]
        print('OK   %-34s %-11s | %s | %s (%s)' % (key, doi, jr[:34], ti[:62], yr))
    except Exception as e:
        print('FAIL %-34s %-11s | %s %s' % (key, doi, type(e).__name__, e))
        bad.append((key, doi, str(e)))
    time.sleep(0.45)
print('\nFAILURES:', len(bad))
for b in bad:
    print('  ', b)
