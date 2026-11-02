"""Build versions/*.html from the site's content.html (old design drafts, not published), so every design variant shows the same content.
usage: python build_versions.py "E:/Github Website"
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
src = (root / "content.html").read_text(encoding="utf8")

FONTS = "https://fonts.googleapis.com/css2?{}&display=swap"
VERSIONS = [
    ("a-drawing-set", "A · Drawing set", "family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600"),
    ("b-monograph", "B · Monograph", "family=Inter+Tight:wght@300;400;500;600"),
    ("c-plates", "C · Plates", "family=DM+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600&family=Instrument+Serif"),
    ("d-book", "D · Book", "family=Inter:wght@400;500&family=Jost:wght@200;300;400;500"),
]


def switcher(current):
    links = ['<a href="../content.html">Plain</a>'] + [
        f'<a href="{slug}.html"{" aria-current=page" if slug == current else ""}>{label.split(" · ")[0]}</a>' for slug, label, _ in VERSIONS
    ] + ['<a href="e-boards.html">E</a>']  # E is built by build_boards.py
    return (
        '<nav style="position:fixed;right:12px;bottom:12px;z-index:20;display:flex;gap:2px;'
        'font:12px/1 ui-monospace,Menlo,Consolas,monospace;background:#111;padding:3px;border-radius:3px">'
        + "".join(links).replace("<a ", '<a style="color:#eee;text-decoration:none;padding:6px 9px" ')
        .replace("aria-current=page", 'aria-current="page" data-on')
        + "</nav><style>nav [data-on]{background:#eee;color:#111!important}</style>"
    )


def plates(html):
    """the index as a grid of plates, each with the first picture of its project"""
    sections = {m.group(1): m.group(2) for m in re.finditer(r'<section class="project" id="([^"]+)">(.*?)</section>', html, re.S)}
    out = ['  <nav class="plates">']
    for n, li in enumerate(re.finditer(r'<a href="#([^"]+)"><span class="y">([^<]+)</span><span class="t">([^<]+)</span>', html), 1):
        pid, year, title = li.groups()
        img = re.search(r'<img src="([^"]+)"', sections[pid])
        pic = f'<span class="img"><img src="{img.group(1)}" alt="" loading="lazy"></span>' if img else '<span class="img empty"></span>'
        out.append(f'    <a class="plate" href="#{pid}">{pic}<span class="cap"><span class="n">{n:02d}</span><span class="t">{title}</span><span class="y">{year}</span></span></a>')
    out.append("  </nav>")
    return "\n".join(out)


(root / "versions").mkdir(exist_ok=True)
for slug, label, fam in VERSIONS:
    t = src.replace('src="assets/', 'src="../assets/').replace('href="diagrams.css"', 'href="../diagrams.css"')
    t = t.replace(
        '<link rel="stylesheet" href="style.css">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'  <link rel="stylesheet" href="{FONTS.format(fam)}">\n'
        f'  <link rel="stylesheet" href="{slug}.css">',
    )
    t = t.replace("<title>Maxmillan Ries</title>", f"<title>Maxmillan Ries · {label}</title>")
    if slug == "c-plates":
        t = t.replace("  </ul>\n", "  </ul>\n" + plates(t) + "\n", 1)
    t = t.replace("</body>", switcher(slug) + "\n</body>")
    (root / "versions" / f"{slug}.html").write_text(t, encoding="utf8", newline="\n")
    print("wrote", slug)
