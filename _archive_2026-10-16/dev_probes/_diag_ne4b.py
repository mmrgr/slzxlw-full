import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path('..')/'A10_敏感性与边界'))
src = Path('ne4_sobol_bootstrap.py').read_text(encoding='utf-8').replace(
    '\nif __name__ == "__main__":\n    main()', '')
ns = {'__file__': str(Path('ne4_sobol_bootstrap.py').resolve()), '__name__': '_n'}
exec(compile(src, 'ne4', 'exec'), ns)
chem = ns['load_chem'](); base = list(chem.values())[0]
BOUNDS, PARAMS, evaluate, saltelli_design = ns['BOUNDS'], ns['PARAMS'], ns['evaluate'], ns['saltelli_design']
rng = np.random.default_rng(ns['SEED'])
A, B = saltelli_design(128, 7, rng)
def phys(row):
    return {k: BOUNDS[k][0] + row[j]*(BOUNDS[k][1]-BOUNDS[k][0]) for j, k in enumerate(PARAMS)}

yA = np.array([evaluate('ha', base, phys(A[i])) if evaluate('ha', base, phys(A[i])) is not None else np.nan for i in range(128)])
yB = np.array([evaluate('ha', base, phys(B[i])) if evaluate('ha', base, phys(B[i])) is not None else np.nan for i in range(128)])
print(f"yA finite={np.isfinite(yA).sum()}/128   yB finite={np.isfinite(yB).sum()}/128")
# yAB
fin = 0
for j in range(7):
    AB = A.copy(); AB[:, j] = B[:, j]
    col = [evaluate('ha', base, phys(AB[i])) for i in range(128)]
    f = sum(1 for x in col if x is not None and np.isfinite(x))
    print(f"  yAB[{PARAMS[j]:<14}] finite={f}/128")
    if j == 0: fin = f
