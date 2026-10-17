import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path('..')/'A10_敏感性与边界'))
import city_model as cm
src = Path('ne4_sobol_bootstrap.py').read_text(encoding='utf-8').replace(
    '\nif __name__ == "__main__":\n    main()', '')
ns = {'__file__': str(Path('ne4_sobol_bootstrap.py').resolve()), '__name__': '_ne4'}
exec(compile(src, 'ne4', 'exec'), ns)
chem = ns['load_chem'](); base = list(chem.values())[0]
BOUNDS, PARAMS, evaluate, saltelli_design = ns['BOUNDS'], ns['PARAMS'], ns['evaluate'], ns['saltelli_design']

rng = np.random.default_rng(ns['SEED'])
A, B = saltelli_design(128, 7, rng)
def phys(row):
    return {k: BOUNDS[k][0] + row[j]*(BOUNDS[k][1]-BOUNDS[k][0]) for j, k in enumerate(PARAMS)}
yA = [evaluate('ha', base, phys(A[i])) for i in range(128)]
ok = [y for y in yA if y is not None]
print(f"yA: OK={len(ok)}/128  None={128-len(ok)}")
if ok:
    a = np.array(ok)
    print(f"  范围 [{a.min():.4g}, {a.max():.4g}]  中位 {np.median(a):.4g}")
    print(f"  零值数 = {int((a==0).sum())}  方差 = {np.var(a):.4g}")
# 看 None 对应的参数
idx_none = [i for i in range(128) if yA[i] is None]
print(f"\nNone 点的参数样本 (前5):")
for i in idx_none[:5]:
    p = phys(A[i])
    print("  " + ", ".join(f"{k}={v:.3g}" for k, v in p.items()))
