# 为何归档这两个目录

## 来源
- `07_代码_AI-UWM引擎/src/aiuwm/data_center.py`（24,064 bytes, mtime 2025-09-29）
- `07_代码_AI-UWM引擎/tests/test_data_center.py`（10,200 bytes, mtime 2025-09-29）

## 归档理由（机械核验，非猜测）
1. **无任何引用**：全项目 `.py` 中搜索 `AI-UWM引擎/src` / `AI-UWM引擎/tests`
   均为 0 命中（唯一实际使用的是 `AI-UWM引擎/aiuwm_src`）。
2. **非当前引擎**：`city_model._find_repo()` 明确解析到
   `07_代码_AI-UWM引擎/aiuwm_src`，并从中 `import aiuwm.data_center`。
3. **内容不同且更旧**：
   - `src/aiuwm/data_center.py` = 24,064 bytes
     vs 现行 `aiuwm_src/src/aiuwm/data_center.py` = 26,903 bytes
   - 两者 sha256 不同；顶层版本 mtime 更晚但体积更小，属**早期快照**。
4. **风险**：若被误 `import`，会因 `sys.path` 顺序不同而**静默使用旧版引擎**。

## 处置
**归档而非删除**（可逆）。若确认不再需要，可整体删除本目录。
