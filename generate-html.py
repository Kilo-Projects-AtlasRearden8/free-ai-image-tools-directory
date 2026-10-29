#!/usr/bin/env python3
"""Build a printable HTML directory from README.md.

Pure standard library. Converts the subset of Markdown used by README.md
(headings, bold, links, inline code, code fences, ordered/unordered lists,
tables, horizontal rules) into a self-contained HTML document with A4 print
styles.
"""
import html
import re
import sys


def escape(text):
    return html.escape(text, quote=False)


_SEP_RE = re.compile(r"^:?-{3,}:?$")


def inline(md):
    """Convert inline Markdown to HTML."""
    # Code spans first
    md = re.sub(r"`([^`]+)`", lambda m: "<code>" + escape(m.group(1)) + "</code>", md)
    # Bold **text**
    md = re.sub(r"\*\*(.+?)\*\*", lambda m: "<strong>" + escape(m.group(1)) + "</strong>", md)
    # Links [text](url)
    md = re.sub(
        r"\[([^\]]*)\]\(([^)]*)\)",
        lambda m: '<a href="' + escape(m.group(2), quote=True) + '">' + escape(m.group(1)) + "</a>",
        md,
    )
    return md


def is_separator_row(cells):
    """True if every cell is a Markdown table separator (e.g. |---|)."""
    return cells and all(_SEP_RE.match(c) for c in cells if c)


def convert_blocks(markdown):
    lines = markdown.split("\n")
    out = []
    i = 0
    n = len(lines)
    in_code = False
    code_lines = []
    code_lang = ""

    def flush_paragraph(par):
        if not par:
            return
        text = "\n".join(par).strip()
        if not text:
            return
        out.append("<p>" + inline(text) + "</p>")

    def close_code():
        nonlocal in_code, code_lines, code_lang
        if in_code:
            out.append(
                '<pre><code class="lang-' + escape(code_lang) + '">'
                + escape("\n".join(code_lines)) + "</code></pre>"
            )
            in_code = False
            code_lines = []
            code_lang = ""

    while i < n:
        line = lines[i]

        # Blank lines separate blocks; also close an open code block.
        if line.strip() == "":
            close_code()
            i += 1
            continue

        # Code fences (allow leading indentation).
        mf = re.match(r"^(\s*)```", line)
        if mf:
            if in_code:
                close_code()
            else:
                code_lang = line[mf.end():].strip()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            close_code()
            level = len(m.group(1))
            text = m.group(2).strip()
            out.append("<h%d>%s</h%d>" % (level, inline(text), level))
            i += 1
            continue

        # Tables
        if re.match(r"^\s*\|", line):
            close_code()
            raw_rows = []
            while i < n and re.match(r"^\s*\|", lines[i]):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not is_separator_row(cells):
                    html_cells = []
                    for c in cells:
                        if _SEP_RE.match(c):
                            html_cells.append("")
                        else:
                            html_cells.append(inline(c))
                    raw_rows.append(html_cells)
                i += 1
            out.append("<table>")
            if raw_rows:
                out.append("<thead><tr>")
                for c in raw_rows[0]:
                    out.append("<th>%s</th>" % c)
                out.append("</tr></thead>")
                out.append("<tbody>")
                for cells in raw_rows[1:]:
                    out.append("<tr>")
                    for c in cells:
                        out.append("<td>%s</td>" % c)
                    out.append("</tr>")
                out.append("</tbody>")
            out.append("</table>")
            continue

        # Ordered lists (1., 2., ...)
        mo = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if mo:
            close_code()
            items = []
            while i < n and re.match(r"^(\s*)\d+\.\s+(.+)$", lines[i]):
                mm = re.match(r"^(\s*)\d+\.\s+(.+)$", lines[i])
                items.append(mm.group(2))
                i += 1
            out.append("<ol>")
            for it in items:
                out.append("<li>" + inline(it) + "</li>")
            out.append("</ol>")
            continue

        # Unordered lists (- * +)
        mu = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if mu:
            close_code()
            items = []
            while i < n and re.match(r"^(\s*)[-*+]\s+(.+)$", lines[i]):
                mm = re.match(r"^(\s*)[-*+]\s+(.+)$", lines[i])
                items.append(mm.group(2))
                i += 1
            out.append("<ul>")
            for it in items:
                out.append("<li>" + inline(it) + "</li>")
            out.append("</ul>")
            continue

        # Paragraph lines
        par = []
        while i < n and lines[i].strip() != "" \
                and not re.match(r"^\s*```", lines[i]) \
                and not re.match(r"^(#{1,6})\s+", lines[i]) \
                and not re.match(r"^\s*\|", lines[i]) \
                and not re.match(r"^(\s*)\d+\.\s+", lines[i]) \
                and not re.match(r"^(\s*)[-*+]\s+", lines[i]) \
                and not re.match(r"^[-*_]{3,}\s*$", lines[i]):
            par.append(lines[i])
            i += 1
        flush_paragraph(par)

    close_code()
    return "\n".join(out)


PAGE_CSS = """
:root {
  --ink: #1a1a1a;
  --muted: #4b5563;
  --line: #e5e7eb;
  --brand: #7c3aed;
  --brand-light: #f3e8ff;
}

* { box-sizing: border-box; }
html { font-size: 11pt; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink);
  line-height: 1.5;
  margin: 0;
  padding: 0;
  background: #ffffff;
}

.titlepage {
  padding: 48px 60px;
  border-bottom: 3px solid var(--brand);
  margin-bottom: 30px;
}
.titlepage h1 {
  font-size: 30px;
  margin: 0 0 12px 0;
  color: var(--brand);
}
.titlepage .subtitle { font-size: 13px; color: var(--muted); margin: 0 0 20px 0; }
.titlepage .credit {
  font-size: 12px;
  color: var(--muted);
  border-top: 1px solid var(--line);
  padding-top: 16px;
  margin-top: 26px;
}

h1 { font-size: 22px; border-bottom: 2px solid var(--brand-light); padding-bottom: 6px; margin: 30px 0 14px 0; }
h2 { font-size: 17px; margin: 26px 0 10px 0; }
h3 { font-size: 14px; margin: 20px 0 8px 0; }
p { margin: 0 0 10px 0; }
ul, ol { margin: 4px 0 12px 0; padding-left: 22px; }
li { margin: 3px 0; }
hr { border: none; border-top: 1px solid var(--line); margin: 22px 0; }

table {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0 18px 0;
  font-size: 10.5px;
}
th, td {
  border: 1px solid var(--line);
  padding: 5px 8px;
  vertical-align: top;
  text-align: left;
}
th { background: var(--brand-light); color: var(--brand); font-size: 10px; text-transform: uppercase; letter-spacing: 0.4px; }
tbody tr:nth-child(even) td { background: #fafafa; }

pre {
  background: #f3f4f6;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 10px;
  overflow-x: auto;
  margin: 10px 0 16px 0;
}
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
pre code { font-size: inherit; padding: 0; background: transparent; }

.tip {
  background: var(--brand-light);
  border-left: 4px solid var(--brand);
  padding: 10px 14px;
  margin: 14px 0;
  font-size: 10.5px;
}
.tip b { color: var(--brand); }

.footnote {
  font-size: 9px;
  color: var(--muted);
  border-top: 1px solid var(--line);
  padding-top: 8px;
  margin-top: 30px;
}

a { color: var(--brand); text-decoration: underline; }

/* ---------- Print ---------- */
@media print {
  body { background: #fff; color: #000; }
  .no-print, .titlepage .subtitle { display: none; }
  @page { size: A4; margin: 16mm 14mm 16mm 14mm; }
  .titlepage { border-bottom: 2px solid #000; padding: 24px 0; margin-bottom: 20px; }
  .titlepage h1 { border-bottom: 1px solid #000; }
  h1, h2, h3 { page-break-after: avoid; color: #000; }
  h1 { border-bottom-color: #000; }
  table { page-break-inside: avoid; }
  tr { page-break-inside: avoid; }
  pre { page-break-inside: avoid; }
  .tip { page-break-inside: avoid; }
  a[href]::after { content: " (" attr(href) ")"; font-size: 80%; color: #555; }
  .footnote a[href]::after { content: ""; }
}
"""


def build_html(markdown):
    body = convert_blocks(markdown)
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Free AI Image Tools Directory"

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%s</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="Asdale Dynamics, LLC">
<style>
%s
</style>
</head>
<body>
%s

<p class="footnote no-print">
  Built by Asdale Dynamics, LLC &middot; Copyright (c) 2026 Asdale Dynamics, LLC &middot;
  Licensed under the MIT License &mdash; see LICENSE.<br>
  Tool names and websites belong to their respective owners. This directory is educational only.
</p>
</body>
</html>
""" % (title, PAGE_CSS, body)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    dst = sys.argv[2] if len(sys.argv) > 2 else "free-ai-image-tools.html"
    with open(src, "r", encoding="utf-8") as f:
        markdown = f.read()
    html_doc = build_html(markdown)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("Wrote %s (%d bytes)" % (dst, len(html_doc.encode("utf-8"))))


if __name__ == "__main__":
    main()
