# -*- coding: utf-8 -*-
"""把 md 中的 LaTeX 公式转换成 Word 原生公式对象（OMML），并采用线性排版。

【为什么需要这个脚本】
md 是论文的单一源码（LaTeX 是学术写作的通用存储格式，投稿系统也认它），
但 `$r^{*}=(L/\\mathrm{CoC}_d-C_p)/(C_r-C_p)$` 这种源码直接进 Word 是不可读的。
上一版 `_build_docx.py` 把 LaTeX 原样印成浅黄底文本，作者反馈"要线性格式"。

线性格式（linear format）指数学式排成一行：用 `a/b` 而不是上下堆叠的分式，
用真正的上下标而不是 `^{}`、`_{}` 字面符号。因此本模块：

  * 分式 `\\frac{a}{b}` → `a/b`（分子分母为复合式时自动加括号）
  * 上下标 `^{...}`、`_{...}` → OMML 的 m:sSup / m:sSub / m:sSubSup
    （视觉上是一行，上标是真上标）
  * `\\mathrm{CoC}` → 正体 CoC；希腊字母、≤、≥、×、≡、∈、± 等 → 对应 Unicode 字符
  * 输出 OMML 对象，Word/WPS 里双击即可编辑，而不是死文本

【覆盖范围】
本项目实际用到的 LaTeX 命令只有 27 种（见 `_tmp_probe_latex.py` 统计），
没有 \\sqrt、\\sum、\\int、\\begin 环境。本模块按这个真实子集实现，
遇到未知命令时降级为原样文本并在报告里记一笔，不抛异常。

用法：
    from _latex_omml import latex_to_omath
    xml = latex_to_omath(r"r^{*}=(L/\\mathrm{CoC}_d-C_p)/(C_r-C_p)")
    p._p.append(parse_xml(xml))
"""
from __future__ import annotations

import re

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSDECL = 'xmlns:m="%s" xmlns:w="%s"' % (M_NS, W_NS)

# ---------------------------------------------------------------------------
# 符号表
# ---------------------------------------------------------------------------
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "varrho": "ϱ", "sigma": "σ", "varsigma": "ς",
    "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}

SYMBOLS = {
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "neq": "≠",
    "approx": "≈", "equiv": "≡", "sim": "∼", "simeq": "≃", "propto": "∝",
    "in": "∈", "notin": "∉", "subset": "⊂", "supset": "⊃",
    "to": "→", "rightarrow": "→", "leftarrow": "←", "Rightarrow": "⇒",
    "leftrightarrow": "↔", "mapsto": "↦",
    "times": "×", "cdot": "·", "div": "÷", "pm": "±", "mp": "∓",
    "ast": "∗", "star": "⋆", "circ": "∘", "bullet": "∙",
    "infty": "∞", "partial": "∂", "nabla": "∇",
    "sum": "∑", "prod": "∏", "int": "∫",
    "ldots": "…", "dots": "…", "cdots": "⋯", "vdots": "⋮", "ddots": "⋱",
    "prime": "′", "degree": "°", "deg": "°",
    "langle": "⟨", "rangle": "⟩", "lvert": "|", "rvert": "|",
    "lVert": "‖", "rVert": "‖",
    "forall": "∀", "exists": "∃", "emptyset": "∅", "neg": "¬",
    "land": "∧", "lor": "∨", "oplus": "⊕", "otimes": "⊗",
    "perp": "⊥", "parallel": "∥", "angle": "∠", "triangle": "△",
    "checkmark": "✓", "dagger": "†", "S": "§", "P": "¶",
    "copyright": "©", "pounds": "£", "euro": "€",
}

# 间距命令 → 空白字符
SPACES = {
    ",": "\u2009",    # thin space
    ":": "\u2005",    # medium space
    ";": "\u2004",    # thick space
    "!": "",          # negative thin space
    " ": "\u00a0",    # control space
    "quad": "\u2003",
    "qquad": "\u2003\u2003",
    "enspace": "\u2002",
    "thinspace": "\u2009",
}

# 函数名（正体）
FUNCS = {
    "min", "max", "sup", "inf", "lim", "log", "ln", "lg", "exp", "sin", "cos",
    "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh",
    "tanh", "det", "dim", "ker", "deg", "gcd", "Pr", "arg", "mod", "bmod",
}

# 需要整体消费一个参数并转为正体文本的命令
UPRIGHT_ARG = {"mathrm", "text", "operatorname", "mathsf", "mathtt", "textrm",
               "textit", "textup", "mbox", "hbox"}
BOLD_ARG = {"mathbf", "boldsymbol", "bm"}
ITALIC_ARG = {"mathit", "mathcal", "mathbb", "mathscr", "mathfrak"}

_CJK_RE = re.compile(r"[\u3400-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef]")


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _has_cjk(t: str) -> bool:
    return bool(_CJK_RE.search(t))


def _run(text: str, sty: str | None = None, size_pt: float | None = None) -> str:
    """生成一个公式 run。sty: None=默认(字母斜体/数字正体), 'p'=正体, 'b'=粗体。

    size_pt 用 Word 的半磅值（w:sz）写到 run 上，这样表格里的小字号公式
    与表格文字同高，不会比周围正文还大。
    """
    if not text:
        return ""
    rpr = ""
    if sty:
        rpr += '<m:rPr><m:sty m:val="%s"/></m:rPr>' % sty
    wrpr = ""
    if _has_cjk(text):
        wrpr += ('<w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"'
                 ' w:eastAsia="宋体"/>')
    if size_pt:
        half = max(2, int(round(size_pt * 2)))
        wrpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (half, half)
    if wrpr:
        rpr += "<w:rPr>%s</w:rPr>" % wrpr
    return '<m:r>%s<m:t xml:space="preserve">%s</m:t></m:r>' % (rpr, _esc(text))


class _Conv:
    """递归下降解析器：LaTeX 子集 → OMML 节点树 → XML。"""

    def __init__(self, size_pt: float | None = None) -> None:
        self.unknown: list[str] = []
        self.size_pt = size_pt

    # -- 词法 ---------------------------------------------------------------
    @staticmethod
    def tokenize(s: str) -> list[tuple]:
        toks: list[tuple] = []
        i, n = 0, len(s)
        while i < n:
            c = s[i]
            if c == "\\":
                if i + 1 < n and (s[i + 1].isalpha() or s[i + 1] == "\\"):
                    if s[i + 1] == "\\":
                        toks.append(("cmd", "\\"))
                        i += 2
                        continue
                    j = i + 1
                    while j < n and s[j].isalpha():
                        j += 1
                    toks.append(("cmd", s[i + 1:j]))
                    i = j
                elif i + 1 < n:
                    toks.append(("cmd", s[i + 1]))
                    i += 2
                else:
                    i += 1
            elif c == "{":
                toks.append(("open",))
                i += 1
            elif c == "}":
                toks.append(("close",))
                i += 1
            elif c in "^_":
                toks.append((c,))
                i += 1
            elif c in " \t\n":
                # 数学模式下空白不产生间距；但 \text{} 内部要保留，
                # 所以这里标记成 sp 而不是直接丢弃，由上层按上下文决定。
                toks.append(("sp",))
                i += 1
            else:
                toks.append(("char", c))
                i += 1
        return toks

    # -- 语法 ---------------------------------------------------------------
    def parse(self, latex: str) -> list[dict]:
        toks = self.tokenize(latex)
        nodes, _ = self.parse_seq(toks, 0, False)
        return nodes

    def parse_seq(self, toks: list, pos: int, in_group: bool):
        nodes: list[dict] = []
        while pos < len(toks):
            t = toks[pos]
            if t[0] == "sp":
                # 数学模式下的源码空白不产生间距
                pos += 1
                continue
            if t[0] == "close":
                if in_group:
                    return nodes, pos + 1
                pos += 1          # 多余右括号，跳过
                continue

            node, pos = self.parse_atom(toks, pos)

            sub = sup = None
            while pos < len(toks) and toks[pos][0] in ("^", "_"):
                which = toks[pos][0]
                operand, pos = self.read_arg(toks, pos + 1)
                if which == "^":
                    sup = operand
                else:
                    sub = operand

            if sub is not None and sup is not None:
                node = {"kind": "subsup", "base": node, "sub": sub, "sup": sup}
            elif sup is not None:
                node = {"kind": "sup", "base": node, "sup": sup}
            elif sub is not None:
                node = {"kind": "sub", "base": node, "sub": sub}
            nodes.append(node)
        return nodes, pos

    def parse_atom(self, toks: list, pos: int):
        if pos >= len(toks):
            return {"kind": "run", "text": ""}, pos
        t = toks[pos]
        kind = t[0]
        if kind == "open":
            items, pos = self.parse_seq(toks, pos + 1, True)
            return {"kind": "group", "items": items}, pos
        if kind == "close":
            return {"kind": "run", "text": ""}, pos + 1
        if kind == "char":
            return {"kind": "run", "text": t[1]}, pos + 1
        if kind == "cmd":
            return self.handle_cmd(toks, pos)
        # 悬空的 ^ 或 _
        return {"kind": "run", "text": ""}, pos + 1

    def read_arg(self, toks: list, pos: int):
        """读一个参数：{...} 或单个原子。始终返回 (nodes_list, newpos)。"""
        if pos < len(toks) and toks[pos][0] == "open":
            return self.parse_seq(toks, pos + 1, True)
        node, pos2 = self.parse_atom(toks, pos)
        return [node], pos2

    def read_raw_arg(self, toks: list, pos: int) -> tuple[str, int]:
        """读一个参数并返回**原始字面文本**（用于 \\text、\\mathrm 等）。

        这些命令的参数是文字而非数学式：`\\text{reclaimed used}` 里的空格
        必须保留，`\\mathrm{CoC}` 里的 CoC 也不能被拆成数学变量。所以这里
        不做符号解析，只按花括号配对做子串提取。
        """
        if pos >= len(toks) or toks[pos][0] != "open":
            # 单原子参数
            if pos < len(toks) and toks[pos][0] == "char":
                return toks[pos][1], pos + 1
            if pos < len(toks) and toks[pos][0] == "cmd":
                return toks[pos][1], pos + 1
            return "", pos
        depth = 1
        i = pos + 1
        parts: list[str] = []
        while i < len(toks) and depth > 0:
            t = toks[i]
            k = t[0]
            if k == "open":
                depth += 1
                parts.append("{")
            elif k == "close":
                depth -= 1
                if depth > 0:
                    parts.append("}")
            elif k == "sp":
                parts.append(" ")
            elif k == "char":
                parts.append(t[1])
            elif k == "cmd":
                # 参数内的命令保持字面，让 \text{...} 里的反斜杠不丢
                parts.append("\\" + t[1])
            elif k in ("^", "_"):
                parts.append(k)
            i += 1
        return "".join(parts), i

    # -- 命令 ---------------------------------------------------------------
    def handle_cmd(self, toks: list, pos: int):
        name = toks[pos][1]
        pos += 1

        # 转义字符
        if name in ("%", "&", "#", "_", "{", "}", "$"):
            return {"kind": "run", "text": name}, pos
        if name == "\\":
            return {"kind": "run", "text": " "}, pos   # 软换行降级为空格

        # 间距
        if name in SPACES:
            return {"kind": "run", "text": SPACES[name]}, pos

        # 希腊字母
        if name in GREEK:
            return {"kind": "run", "text": GREEK[name]}, pos

        # 关系/运算符符号
        if name in SYMBOLS:
            return {"kind": "run", "text": SYMBOLS[name], "sty": "p"}, pos

        # 正体参数命令
        if name in UPRIGHT_ARG:
            arg, pos = self.read_raw_arg(toks, pos)
            return {"kind": "group", "items": [{"kind": "run", "text": arg,
                                                "sty": "p"}]}, pos
        if name in BOLD_ARG:
            arg, pos = self.read_raw_arg(toks, pos)
            return {"kind": "group", "items": [{"kind": "run", "text": arg,
                                                "sty": "b"}]}, pos
        if name in ITALIC_ARG:
            arg, pos = self.read_raw_arg(toks, pos)
            return {"kind": "group", "items": [{"kind": "run", "text": arg}]}, pos

        # 分式 → 线性 a/b
        if name == "frac" or name == "dfrac" or name == "tfrac":
            num, pos = self.read_arg(toks, pos)
            den, pos = self.read_arg(toks, pos)
            items = (self.wrap(num) + [{"kind": "run", "text": "/", "sty": "p"}]
                     + self.wrap(den))
            return {"kind": "group", "items": items}, pos

        # 根式 → √(...)
        if name == "sqrt":
            arg, pos = self.read_arg(toks, pos)
            items = ([{"kind": "run", "text": "√"}] + self.wrap(arg))
            return {"kind": "group", "items": items}, pos

        # \left / \right 后跟定界符
        if name in ("left", "right"):
            if pos < len(toks) and toks[pos][0] == "char":
                return {"kind": "run", "text": toks[pos][1], "sty": "p"}, pos + 1
            if pos < len(toks) and toks[pos][0] == "cmd":
                return self.handle_cmd(toks, pos)
            return {"kind": "run", "text": ""}, pos

        # 函数名 → 正体
        if name in FUNCS:
            return {"kind": "run", "text": name, "sty": "p"}, pos

        # 未知命令：降级为去掉反斜杠的文本，并记录
        self.unknown.append(name)
        return {"kind": "run", "text": name, "sty": "p"}, pos

    # -- 括号包裹判定 -------------------------------------------------------
    @staticmethod
    def wrap(nodes: list[dict]) -> list[dict]:
        """为分式的分子/分母按需加括号。

        线性格式里 `a/b` 的优先级高于加减，所以只有当分子/分母含有
        "松运算符"（+ − = < > ≤ ≥ ± ≡ → ∈ 逗号等）时才必须加括号；
        `βR`、`C_mix` 这类纯并列项不加，读起来更干净。

        已经是自平衡圆括号包裹的表达式也不再加。
        """
        if not nodes:
            return nodes
        txt = nodes_text(nodes)
        if txt.startswith("(") and txt.endswith(")") and _balanced(txt):
            return nodes
        if not _has_loose_operator(nodes):
            return nodes
        return ([{"kind": "run", "text": "(", "sty": "p"}] + nodes
                + [{"kind": "run", "text": ")", "sty": "p"}])

    # -- 渲染 ---------------------------------------------------------------
    def render(self, nodes: list[dict]) -> str:
        out = []
        for n in nodes:
            k = n["kind"]
            if k == "run":
                out.append(_run(n.get("text", ""), n.get("sty"), self.size_pt))
            elif k == "group":
                out.append(self.render(n["items"]))
            elif k == "sup":
                out.append('<m:sSup><m:e>%s</m:e><m:sup>%s</m:sup></m:sSup>'
                           % (self.render([n["base"]]), self.render(n["sup"])))
            elif k == "sub":
                out.append('<m:sSub><m:e>%s</m:e><m:sub>%s</m:sub></m:sSub>'
                           % (self.render([n["base"]]), self.render(n["sub"])))
            elif k == "subsup":
                out.append('<m:sSubSup><m:e>%s</m:e><m:sub>%s</m:sub>'
                           '<m:sup>%s</m:sup></m:sSubSup>'
                           % (self.render([n["base"]]), self.render(n["sub"]),
                              self.render(n["sup"])))
        return "".join(out)

    def to_omath(self, latex: str) -> str:
        body = self.render(self.parse(latex))
        return "<m:oMath %s>%s</m:oMath>" % (NSDECL, body)


# ---------------------------------------------------------------------------
# 文本提取与小工具
# ---------------------------------------------------------------------------
def nodes_text(nodes: list[dict]) -> str:
    out = []
    for n in nodes:
        k = n["kind"]
        if k == "run":
            out.append(n.get("text", ""))
        elif k == "group":
            out.append(nodes_text(n["items"]))
        elif k == "sup":
            out.append(nodes_text([n["base"]]) + "^" + nodes_text(n["sup"]))
        elif k == "sub":
            out.append(nodes_text([n["base"]]) + "_" + nodes_text(n["sub"]))
        elif k == "subsup":
            out.append(nodes_text([n["base"]]) + "_" + nodes_text(n["sub"])
                       + "^" + nodes_text(n["sup"]))
    return "".join(out)


def _balanced(txt: str) -> bool:
    depth = 0
    for ch in txt:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


# 让 `a/b` 产生歧义的低优先级运算符
LOOSE_OPS = set("+-=<>,±∓≤≥≠≈≡→∈∝/…·×÷∓")


def _has_loose_operator(nodes: list[dict]) -> bool:
    """判断节点序列里是否存在优先级低于 `/` 的运算符。

    只扫描当前层级（进入 group 递归），遇到括号成对包裹的子式则跳过其内部，
    因为括号本身已经限定了作用域。
    """
    for n in nodes:
        k = n["kind"]
        if k == "run":
            if any(ch in LOOSE_OPS for ch in n.get("text", "")):
                return True
        elif k == "group":
            if _has_loose_operator(n["items"]):
                return True
        elif k == "sup":
            if _has_loose_operator([n["base"]]):
                return True
        elif k == "sub":
            if _has_loose_operator([n["base"]]):
                return True
        elif k == "subsup":
            if _has_loose_operator([n["base"]]):
                return True
    return False


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def latex_to_omath(latex: str, size_pt: float | None = None) -> str:
    """LaTeX → OMML（线性排版）。返回带命名空间声明的 m:oMath 片段。

    size_pt 传字号（磅），用于表格等小字号场景；None 表示沿用段落字号。
    """
    return _Conv(size_pt).to_omath(latex)


def latex_to_omath_reported(latex: str, size_pt: float | None = None
                            ) -> tuple[str, list[str]]:
    """同 latex_to_omath，但同时返回本次遇到的未知命令列表。"""
    c = _Conv(size_pt)
    return c.to_omath(latex), c.unknown


def latex_to_plain(latex: str) -> str:
    """LaTeX → 纯文本（用于对比检查、PDF 兜底等）。"""
    return nodes_text(_Conv().parse(latex))


if __name__ == "__main__":
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    samples = [
        r"r^{*}=(L/\mathrm{CoC}_d-C_p)/(C_r-C_p)",
        r"\mathrm{CoC}(r)=\min\left(\mathrm{CoC}_d,\ \frac{L}{C_{\mathrm{mix}}(r)}\right).",
        r"r=\frac{\beta R}{\alpha P+\beta R}=\frac{1}{1+(\alpha/\beta)\,k},\qquad k\equiv\frac{P}{R}.",
        r"3.45\times10^{-13}\%",
        r"u=(\text{再生水利用量})/(\text{污水处理量})",
        r"k^{*}=(1/r^{*}-1)/\rho",
        r"0.53\le r<0.83",
        r"\pm10\%",
        r"r\in[0,1]",
        r"dS_{pot}=M_1-M_0",
        r"r^{*}_s",
        r"=|\text{inflow}-\text{outflow}|/\text{inflow}",
    ]
    for s in samples:
        x, unk = latex_to_omath_reported(s)
        print("LaTeX :", s)
        print("  线性 :", latex_to_plain(s).replace("\u2009", "~")
              .replace("\u2003", "  ").replace("\u00a0", " "))
        print("  未知 :", unk if unk else "—")
        print()
