"""Shared helpers for notebook assembly: fragment parsing, SQL splitting, HTML->Markdown."""
import html
import re


# ---------------------------------------------------------------- SQL splitting
def split_sql(sql):
    """Split a SQL script into statements, respecting strings and comments."""
    out, cur = [], []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if c == "-" and nxt == "-":
            j = sql.find("\n", i)
            j = n if j < 0 else j
            cur.append(sql[i:j])
            i = j
        elif c == "/" and nxt == "*":
            j = sql.find("*/", i + 2)
            j = n if j < 0 else j + 2
            cur.append(sql[i:j])
            i = j
        elif c in ("'", '"'):
            j = i + 1
            while j < n:
                if sql[j] == "\\":
                    j += 2
                    continue
                if sql[j] == c:
                    if sql[j + 1 : j + 2] == c:  # doubled quote escape
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            cur.append(sql[i:j])
            i = j
        elif c == ";":
            out.append("".join(cur).strip())
            cur = []
            i += 1
        else:
            cur.append(c)
            i += 1
    if "".join(cur).strip():
        out.append("".join(cur).strip())
    return [s for s in out if s]


def attach_leading_comments(stmts):
    """Re-attach a trailing comment-only chunk to the following statement."""
    out = []
    carry = ""
    for s in stmts:
        body = re.sub(r"--[^\n]*", "", s)
        body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        if not body.strip():
            carry += s + "\n"
            continue
        out.append((carry + s).strip())
        carry = ""
    if carry.strip():
        out.append(carry.strip())
    return out


# ------------------------------------------------------------ fragment parsing
CODE_RE = re.compile(
    r'<div class="code-block">.*?<span class="code-lang">(\w+)</span>'
    r".*?<pre><code>(.*?)</code></pre>\s*</div>",
    re.S,
)


def parse_fragment(text):
    """Yield ('prose', html) and ('code', (lang, source)) in document order."""
    pos = 0
    for m in CODE_RE.finditer(text):
        if m.start() > pos:
            yield "prose", text[pos : m.start()]
        yield "code", (m.group(1), html.unescape(m.group(2)).strip())
        pos = m.end()
    if pos < len(text):
        yield "prose", text[pos:]


# --------------------------------------------------------------- HTML -> Markdown
def _inline(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"<code>(.*?)</code>", lambda m: "`" + strip_tags(m.group(1)) + "`", s, flags=re.S)
    s = re.sub(r"<strong>(.*?)</strong>", r"**\1**", s, flags=re.S)
    s = re.sub(r"<b>(.*?)</b>", r"**\1**", s, flags=re.S)
    s = re.sub(r"<em>(.*?)</em>", r"*\1*", s, flags=re.S)
    s = re.sub(r"<i>(.*?)</i>", r"*\1*", s, flags=re.S)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = strip_tags(s)
    s = html.unescape(s)
    return s.strip()


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def _cells(row):
    """Cell texts for a row, expanding colspan into padding cells."""
    out = []
    for attrs, body in re.findall(r"<t[hd]([^>]*)>(.*?)</t[hd]>", row, re.S):
        span = re.search(r'colspan\s*=\s*"?(\d+)', attrs)
        out.append(_inline(body))
        out.extend([""] * (int(span.group(1)) - 1 if span else 0))
    return out


def _table(tbl):
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S)
    if not rows:
        return ""
    grid = [_cells(r) for r in rows]
    width = max(len(r) for r in grid)
    grid = [r + [""] * (width - len(r)) for r in grid]
    head, body = grid[0], grid[1:]
    md = ["| " + " | ".join(head) + " |", "|" + "---|" * width]
    md += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(md)


def _list(block, ordered):
    items = re.findall(r"<li[^>]*>(.*?)</li>", block, re.S)
    mark = (lambda i: f"{i}.") if ordered else (lambda i: "-")
    return "\n".join(f"{mark(i)} {_inline(x)}" for i, x in enumerate(items, 1))


def first_sentences(text, n=2, max_words=60):
    """First n sentences of a paragraph, capped at max_words.

    Two sentences rather than one: in this material the headline claim and its
    payoff are almost always a pair ("TO_DATE asserts the data is clean.
    TRY_TO_DATE asserts nothing and tells you where it is not."), and cutting
    after the first drops the point.
    """
    end = 0
    for _ in range(n):
        m = re.compile(r"(?<![A-Z])[.!?](?:\s|$)").search(text, end)
        if not m:
            end = len(text)
            break
        end = m.end()
    s = text[:end].strip() or text
    words = s.split()
    if len(words) > max_words:
        s = " ".join(words[:max_words]).rstrip(",;:") + " \u2026"
    return s


def _info_box(block, tight=False):
    cls = re.search(r'class="info-box([^"]*)"', block)
    kind = (cls.group(1) or "").strip() if cls else ""
    icon = {"success": "\u2705", "warning": "\u26a0\ufe0f", "": "\U0001f4a1"}.get(kind, "\U0001f4a1")
    inner = re.sub(r'<span class="icon">.*?</span>', "", block, flags=re.S)
    inner = re.sub(r"^.*?<div>", "", inner, count=1, flags=re.S)
    title = re.search(r"<strong>(.*?)</strong>", inner, re.S)
    head = _inline(title.group(1)) if title else ""
    if title:
        inner = inner.replace(title.group(0), "", 1)
    lines = [f"> {icon} **{head}**"] if head else []
    paras = [t for t in (_inline(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", inner, re.S)) if t]
    if not paras:
        paras = [t for t in [_inline(inner)] if t]
    if tight and paras:
        paras = [first_sentences(paras[0])]
    for t in paras:
        lines.append(">")
        lines.append("> " + t)
    return "\n".join(lines)


BLOCK_RE = re.compile(
    r'(?P<infobox><div class="info-box.*?</div>\s*</div>)'
    r"|(?P<h>(<h([2-5])[^>]*>)(.*?)</h\4>)"
    r"|(?P<table><table[^>]*>.*?</table>)"
    r"|(?P<ol><ol[^>]*>.*?</ol>)"
    r"|(?P<ul><ul[^>]*>.*?</ul>)"
    r"|(?P<p><p[^>]*>.*?</p>)",
    re.S,
)


def html_to_md(fragment, mode="tight"):
    """Convert a prose HTML fragment to markdown chunks.

    mode='full'  faithful port of every element.
    mode='tight' notebook companion to the HTML guide: headings, lists, tables and
                 callout headlines are kept in full; each consecutive run of
                 paragraphs is reduced to its first and last (the payoff of the
                 previous result and the lead-in to the next cell), and callout
                 bodies to one sentence. The dropped middle is the narrative the
                 HTML guide owns.
    """
    tight = mode == "tight"
    out = []  # list of (kind, text)
    for m in BLOCK_RE.finditer(fragment):
        if m.group("infobox"):
            out.append(("infobox", _info_box(m.group("infobox"), tight=tight)))
        elif m.group("h"):
            level = int(m.group(4))
            out.append(("h", "#" * max(2, level) + " " + _inline(m.group(5))))
        elif m.group("table"):
            out.append(("table", _table(m.group("table"))))
        elif m.group("ol"):
            out.append(("list", _list(m.group("ol"), True)))
        elif m.group("ul"):
            out.append(("list", _list(m.group("ul"), False)))
        elif m.group("p"):
            t = _inline(m.group("p"))
            if t:
                out.append(("p", t))

    if tight:
        kept, run = [], []
        for kind, text in out + [("_end", "")]:
            if kind == "p":
                run.append(text)
                continue
            if run:
                kept.extend(run if len(run) <= 2 else [run[0], run[-1]])
                run = []
            if kind != "_end":
                kept.append(text)
        out = [(None, t) for t in kept]

    return [t for _, t in out if t.strip()]
