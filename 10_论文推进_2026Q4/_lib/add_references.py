"""把 5 条新文献加入 References (2026-10-17), 保持字母序与格式一致。

新增:
  1. Alissa et al. (2025) Nature 641, 331-338
  2. Behzadian & Kapelan (2015) RCR 99, 84-99
  3. Garrido-Baserba et al. (2024) Nature Water 2, 953-974
  4. Isler-Kaya & Karaosmanoglu (2023) Energy and Buildings 288, 113006
  5. Renouf et al. (2018) Water Research 137, 395-406

现有 11 条按作者姓氏字母序, 新条目按此插入并重编号。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

# 新条目正文（不含编号，稍后统一编号）
NEW = {
    "Alissa": ("Alissa, Husam, Nick, Teresa, Raniwala, Ashish, Arribas Herranz, Alberto, Frost, Kali, "
               "Manousakis, Ioannis, Lio, Kari, Warrier, Brijesh, Oruganti, Vaidehi, DiCaprio, "
               "(2025). Using life cycle assessment to drive innovation for sustainable cool clouds. "
               "*Nature* **641**, 331–338. https://doi.org/10.1038/s41586-025-08832-3"),
    "Behzadian": ("Behzadian, Kourosh, Kapelan, Zoran S. (2015). Modelling metabolism based performance "
                  "of an urban water system using WaterMet². *Resources, Conservation and Recycling* "
                  "**99**, 84–99. https://doi.org/10.1016/j.resconrec.2015.03.015"),
    "Garrido": ("Garrido-Baserba, Manel, Sedlak, David L., Molinos-Senante, Maria, Barnosell, Irene, "
                "Schraa, Oliver, Rosso, Diego, Verdaguer, Marta, Poch, Manel (2024). Using water and "
                "wastewater decentralization to enhance the resilience and sustainability of cities. "
                "*Nature Water* **2**, 953–974. https://doi.org/10.1038/s44221-024-00303-9"),
    "Isler": ("Isler-Kaya, Asli, Karaosmanoglu, Filiz (2023). Life cycle assessment of a climate-friendly "
              "data center cooling device. *Energy and Buildings* **288**, 113006. "
              "https://doi.org/10.1016/j.enbuild.2023.113006"),
    "Renouf": ("Renouf, Marguerite Anne, Kenway, Steven John, Lam, Ka Leung, Weber, Tony R., Roux, Estelle, "
               "Serrao-Neumann, Silvia, Low Choy, Darryl, Morgan, Edward A. (2018). Understanding urban "
               "water performance at the city-region scale using an urban water metabolism evaluation "
               "framework. *Water Research* **137**, 395–406. https://doi.org/10.1016/j.watres.2018.01.070"),
}

i = t.index("## References")
j = t.index("## Declarations")
refs_block = t[i:j]

# 解析现有条目
entries = re.findall(r"^(\d+)\.\s+(.+?)(?=\n\d+\.\s|\n*$)", refs_block, re.M | re.S)
print(f"  现有条目: {len(entries)}")

existing = [(int(n), txt.strip()) for n, txt in entries]

# 加入新条目并统一排序（按首字母）
allitems = [(0, v) for v in NEW.values()] + existing
def key(item):
    return item[1].split(",")[0].strip().lower()
allitems.sort(key=key)

# 重建
new_block = "## References\n\n"
for idx, (_, txt) in enumerate(allitems, 1):
    txt = " ".join(txt.split())
    new_block += f"{idx}. {txt}\n"
new_block += "\n"

t = t[:i] + new_block + t[j:]
MS.write_text(t, encoding="utf-8")
print(f"  新条目数: {len(allitems)}")
print()
for idx, (_, txt) in enumerate(allitems, 1):
    print(f"  {idx:>2}. {txt[:80]}")
