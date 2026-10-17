"""稳健的项目根定位 (2026-10-16).

【为什么需要】
项目里 124 个脚本用 `__file__` 定位路径, 其中 11 个用 `parent.parent` 推出研究目录。
**这种"按层数推算"的写法在目录被移动/重组后必然失效** —— 2026-10-16 的
junction 重组实验正是因为这一点失败并回滚:
  `A36_终审/final_gate.py` 被移入 `04_审计/A36_终审/` 后, `parent.parent` 算出
  `04_审计/` 而不再是研究目录, 脚本内所有相对路径立即断链。

【本模块的做法: 用"标记文件"而非"层数"来定位】
  从当前文件所在目录开始**逐级向上**, 找到第一个含**哨兵文件**的目录。
  哨兵不明显依赖层数, 因此目录怎么移动都能找到根。

哨兵:
  · `10_论文推进_2026Q4` 的根  -> 含 `_PROJECT_ROOT` 标记 或 含 `_lib/` 目录
  · 算力中心 的根              -> 含 `07_代码_AI-UWM引擎` 目录

【存量脚本如何用(渐进迁移, 不必一次改完)】
  # 之前
  HERE = Path(__file__).resolve().parent
  ROOT = HERE.parent                      # 假设脚本恰好在研究目录下一层
  # 之后
  from _find_root import research_root
  ROOT = research_root()                  # 无论脚本在哪一层都对
"""
from __future__ import annotations

from pathlib import Path

# 研究目录的哨兵: 这些名字出现即认定为 10_论文推进_2026Q4 的根
RESEARCH_MARKERS = ("_PROJECT_ROOT", "_lib")
PROJECT_MARKER = "07_代码_AI-UWM引擎"


def _walk_up(start: Path, predicate) -> Path | None:
    for base in (start, *start.parents):
        try:
            if predicate(base):
                return base
        except Exception:
            continue
    return None


def research_root() -> Path:
    """找到 `10_论文推进_2026Q4` 目录 (不论调用脚本位于第几层)。"""
    here = Path(__file__).resolve().parent
    # 优先: 从调用者所在目录向上找 (兼容脚本被移动)
    import inspect
    frame = inspect.currentframe()
    try:
        caller = frame.f_back.f_back if frame and frame.f_back else None
        if caller:
            caller_dir = Path(caller.f_code.co_filename).resolve().parent
            r = _walk_up(caller_dir, lambda b: (b / "_lib").is_dir()
                         or (b / "_PROJECT_ROOT").exists())
            if r:
                return r
    finally:
        del frame
    # 回退: 从本模块位置向上
    r = _walk_up(here, lambda b: (b / "_lib").is_dir()
                 or (b / "_PROJECT_ROOT").exists())
    if r:
        return r
    raise RuntimeError("找不到研究目录(10_论文推进_2026Q4); 请确认 _lib/ 存在")


def project_root() -> Path:
    """找到 `算力中心` 目录。"""
    start = Path(__file__).resolve().parent
    r = _walk_up(start, lambda b: (b / PROJECT_MARKER).is_dir())
    if r:
        return r
    raise RuntimeError(f"找不到项目根(含 {PROJECT_MARKER} 的目录)")


def engine_repo() -> Path:
    return project_root() / PROJECT_MARKER / "aiuwm_src"


if __name__ == "__main__":
    print("research_root() =", research_root())
    print("project_root()  =", project_root())
    print("engine_repo()   =", engine_repo(), "exists=", engine_repo().is_dir())
