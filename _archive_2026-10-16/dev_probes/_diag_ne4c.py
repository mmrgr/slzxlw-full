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

yA = np.array([evaluate('ha', base, phys(A[i])) for i in range(128)], dtype=float)
yB = np.array([evaluate('ha', base, phys(B[i])) for i in range(128)], dtype=float)
yAB = np.full((7,128), np.nan)
for j in range(7):
    AB = A.copy(); AB[:, j] = B[:, j]
    yAB[j] = [evaluate('ha', base, phys(AB[i])) for i in range(128)]

valid = np.isfinite(yA) & np.isfinite(yB) & np.all(np.isfinite(yAB), axis=0)
print("initial valid:", valid.sum())
DEGEN=1e6
degen = np.zeros(128, dtype=bool)
degen[valid] = ((np.abs(yA[valid])>DEGEN) | (np.abs(yB[valid])>DEGEN) | (np.abs(yAB[:,valid])>DEGEN).any(axis=0))
print("degen:", degen.sum())
print("valid & ~degen:", (valid & ~degen).sum())
print()
allv = np.concatenate([yA, yB, yAB.ravel()])
print(f"全体值范围 [{np.nanmin(allv):.4g}, {np.nanmax(allv):.4g}]")
print(f"|y|>1e6 的点数 = {(np.abs(allv)>1e6).sum()} / {allv.size}")
print()
print("大值样本 (前10):", np.sort(np.abs(allv))[-10:])
