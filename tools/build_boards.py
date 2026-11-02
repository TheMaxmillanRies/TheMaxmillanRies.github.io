"""Build index.html, the site itself: one fixed landscape board per project (big image, text block, small images),
with the full write-up from content.html folded under each board.
usage: python tools/build_boards.py   (after tools/diagrams.py)
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
src = (root / "content.html").read_text(encoding="utf8")
IMG = "assets/img/"
sections = {m.group(1): m.group(2) for m in re.finditer(r'<section class="project" id="([^"]+)">(.*?)</section>', src, re.S)}


def alt(path):
    m = re.search(rf'<img src="assets/img/{re.escape(path)}" alt="([^"]*)"', src)
    return m.group(1) if m else ""


def fig(path, area, cap, cls="", text=None):
    c = f' class="{cls}"' if cls else ""
    return (f'<figure{c} style="grid-area:{area}"><img src="{IMG}{path}" alt="{text or alt(path)}" loading="lazy">'
            f'<figcaption>{cap}</figcaption></figure>')


def diagram(name, area, cap):
    m = re.search(rf"<!--dg:{name}-->.*?(<svg.*?</svg>)", src, re.S)
    body = m.group(1).replace(f"ah-{name}", f"ah-{name}-b")  # the write-up below holds the same svg
    return f'<figure class="dgm" style="grid-area:{area}">{body}<figcaption>{cap}</figcaption></figure>'


def facts(sid):
    m = re.search(r'<dl class="facts">(.*?)</dl>', sections[sid], re.S)
    rows = re.findall(r"<dt>(Stack|Data|Code)</dt><dd>(.*?)</dd>", m.group(1))
    return "<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


def nums(pairs):
    return '<div class="nums">' + "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in pairs) + "</div>"


def text(n, sid, title, meta, summary, area, extra="", cls="text", dl=None):
    rows = "<dl>" + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in dl) + "</dl>" if dl else facts(sid)
    return (f'<div class="{cls}" style="grid-area:{area}"><p class="no">{n}</p><h2>{title}</h2><p class="meta">{meta}</p>'
            f'<p class="sum">{summary}</p>{extra}{rows}</div>')


def notes(sid, name="", keep=None):
    """the full write-up in two columns: each text block sits beside the pictures that follow it in content.html,
    text with no pictures runs in two columns, and wide figures and diagrams span the sheet.
    keep: only the blocks containing one of these strings (one section split over several boards)"""
    s = sections[sid]
    parts = re.findall(r'(<!--dg:(?!marks)([\w-]+)-->.*?<!--/dg:\2-->|<div class="(body|results|gallery[^"]*)">.*?\n    </div>)', s, re.S)
    if keep:
        parts = [p for p in parts if any(k in p[0] for k in keep)]
    out, i = [], 0
    while i < len(parts):
        block, dg, kind = parts[i]
        if kind == "body":
            gal = parts[i + 1] if i + 1 < len(parts) and parts[i + 1][2].startswith("gallery") else None
            figs = re.findall(r'(<figure(?: class="([^"]*)")?>.*?</figure>)', gal[0], re.S) if gal else []
            side = [f for f, c in figs if "wide" not in c]
            wide = [f for f, c in figs if "wide" in c]
            if len(side) > 3:  # too many to sit beside the text: lay them out in a row instead
                side, wide = [], side + wide
            if side:
                out.append(f'<div class="wu-row"><div class="wu-text">{block}</div><div class="wu-figs">{"".join(side)}</div></div>')
            else:
                out.append(f'<div class="wu-cols">{block}</div>')
            if wide:
                out.append(f'<div class="wu-wide">{"".join(wide)}</div>')
            i += 2 if gal else 1
            continue
        if kind.startswith("gallery"):
            out.append(f'<div class="wu-strip">{block}</div>')
        else:
            out.append(block)
        i += 1
    return (f'<details class="notes"><summary>Full write-up{" · " + name if name else ""}</summary><div class="notes-body">\n'
            + "\n".join(out) + "\n</div></details>")


def board(page, title, inner, sid=None, cls=""):
    c = f"board {cls}".strip()
    i = f' id="{sid}"' if sid else ""
    foot = f'<footer class="foot"><span>Maxmillan Ries · Portfolio</span><span>{title}</span><span>{page}</span></footer>'
    return f'<section class="{c}"{i}>\n{inner}\n{foot}\n</section>'


# the chess photo keeps its numbered markers: image and markers share one viewBox, so cropping moves them together
marks = re.search(r'<svg class="marks" viewBox="0 0 1200 1600" aria-hidden="true">(.*?)</svg>', src, re.S).group(1)
chess_hero = (f'<figure class="marked" style="grid-area:1 / 1 / 9 / 7"><svg class="marks" viewBox="0 0 1200 1600" preserveAspectRatio="xMidYMid slice" '
              f'role="img" aria-label="{alt("chess-arm/arm-photo.webp")}"><image href="{IMG}chess-arm/arm-photo.webp" width="1200" height="1600"/>'
              f'{marks}</svg><figcaption>1 Gripper · 2 Aluminium truss · 3 Dynamixel servo · 4 MX-106 servo · 5 Rotating base</figcaption></figure>')

def pv(path=None, cap="", dg=None):
    """Data attributes for a cover contents link: hovering it shows this picture or diagram on the cover."""
    if dg:
        return f' data-pv="{dg}" data-cap="{cap}"'
    return f' data-pic="{IMG}{path}" data-alt="{alt(path)}" data-cap="{cap}"'


def pv_svg(name):
    # a separate copy of the diagram (own marker ids) for the cover preview; templates are not rendered until used
    m = re.search(rf"<!--dg:{name}-->.*?(<svg.*?</svg>)", src, re.S)
    return f'<template id="pv-{name}">{m.group(1).replace(f"ah-{name}", f"ah-{name}-c")}</template>'


# the PhD papers, used by the PhD overview sheet and by the cover preview
PAPERS = [("tracer", "TraCeR", "Competing risks: which outcome happens first, and when", "Under review"),
          ("nmsm", "nMSM · ML4H", "States and measurements forecast together", "Accepted"),
          ("apc", "APC", "Calendar drift: age, period and cohort in neural models", "Under review")]


def paper_rows(tag):
    rows = []
    for i, (k, t, d, st) in enumerate(PAPERS, 1):
        attr = f' href="#{k}"' if tag == "a" else ""
        rows.append(f"  <{tag}{attr}><span>{i:02d}</span><div>{t}<small>{d}</small></div><em>{st}</em></{tag}>\n")
    return "".join(rows)


def pv_phd():
    return f'<template id="pv-phd"><div class="pv-list"><p class="meta">PhD research · Papers</p><ul>{paper_rows("li")}</ul></div></template>'


def pv_list():
    # smaller work has no pictures, so its preview is the list itself: year and title
    rows = re.findall(r'<span class="y">(.*?)</span><span><strong>(.*?)</strong>', sections["other"])
    li = "".join(f"<li><span>{y}</span>{t}</li>" for y, t in rows)
    return f'<template id="pv-other"><div class="pv-list"><p class="meta">Smaller work</p><ul>{li}</ul></div></template>'


B = []

B.append(board("00", "Contents", f'''
<div class="cover-name" style="grid-area:1 / 1 / 4 / 8">
  <p class="meta">Portfolio · Selected work 2020 – 2026</p>
  <h1>Maxmillan Ries</h1>
  <p class="sum">PhD researcher at the University of Edinburgh working on generative sequence modelling, survival analysis and temporal distribution shift. At UReason, I develop predictive-maintenance models for industrial equipment and local LLM systems combining agent orchestration, computer vision and structured retrieval.</p>
  <p class="meta">PhD University of Edinburgh · MSc TU Delft · BSc University of Groningen<br><a href="https://github.com/TheMaxmillanRies">GitHub</a> · <a href="https://www.linkedin.com/in/maxmillanries">LinkedIn</a></p>
</div>
{fig("chess-arm/arm-photo.webp", "4 / 1 / 9 / 8", "Robot Chess Arm: the arm over the board, with the depth camera above.", "cover-pic")}
<nav class="contents" style="grid-area:1 / 8 / 9 / 13">
  <p class="meta">Contents</p>
  <a href="#chess-arm"{pv("chess-arm/arm-photo.webp", "Robot Chess Arm: the arm over the board, with the depth camera above.")}><span>01</span>Robot Chess Arm<em>2020 – 21</em></a>
  <a href="#procedural-world"{pv("procedural-world/cobble.webp", "Procedural World: cobble walls and a round tower, every stone laid along a drawn curve.")}><span>02</span>Procedural World<em>2026</em></a>
  <a href="#dnd-vtt"{pv("dnd-app/workspace.webp", "D&amp;D VTT: the workspace during a game. Every panel is a window you can move, pin or pop out.")}><span>03</span>D&amp;D VTT<em>2023 – now</em></a>
  <a href="#mathisfactory"{pv("mathisfactory/lava.webp", "Mathisfactory: level curves on the real volcano model, and the simulated lava flow.")}><span>04</span>Mathisfactory<em>2023</em></a>
  <a href="#kidney-stones"{pv(dg="kidney-model", cap="Kidney Stone Classification: transfer learning from ImageNet, with extra task heads sharing the same features.")}><span>05</span>Kidney Stone Classification<em>2021</em></a>
  <a href="#kidney-stones"{pv(dg="indoor-bayes", cap="Indoor Localization: Bayesian localization, illustrated (schematic bar heights).")}><span>06</span>Indoor Localization<em>2022</em></a>
  <a href="#style-transfer"{pv("style-transfer/result-stvae.webp", "Neural Style Transfer: the room in stained glass (ST-VAE).")}><span>07</span>Neural Style Transfer<em>2022</em></a>
  <a href="#other"{pv(dg="other", cap="Smaller work: course projects, a reproduction study, a data tool and teaching.")}><span>+</span>Smaller work<em>2020 – 22</em></a>
  <a href="#phd"{pv(dg="phd", cap="PhD research: forecasting patient trajectories from large databases of health records.")}><span>→</span>PhD research<em>2023 – now</em></a>
</nav>
{pv_svg("kidney-model")}{pv_svg("indoor-bayes")}{pv_phd()}{pv_list()}''', cls="cover"))

B.append(board("01", "Robot Chess Arm", f'''
{chess_hero}
{text("01", "chess-arm", "Robot Chess Arm", "2020 – 2021 · Personal project",
      "A six-axis arm that plays chess on a real board. I extended a PhantomX Reactor kit with an aluminium truss and an extra elbow rotation, driven by Dynamixel servos from a MATLAB app. A RealSense depth camera looks down on the board. Instead of recognising pieces, it works out which squares are occupied and compares that with the last position to infer your move. Stockfish picks the reply.",
      "1 / 7 / 5 / 13", nums([("72/96", "boards read perfectly"), ("99.1%", "per-square accuracy"), ("0.76 s", "per detection")]))}
{fig("chess-arm/rgb-start.webp", "5 / 7 / 7 / 10", "Colour frame from the depth camera")}
{fig("chess-arm/ir-speckle.webp", "5 / 10 / 7 / 13", "Projected infrared speckle")}
{fig("chess-arm/clusters.webp", "7 / 7 / 9 / 10", "Point cloud clusters, board removed")}
{fig("chess-arm/cad.webp", "7 / 10 / 9 / 13", "CAD of the extended arm")}''', "chess-arm") + "\n" + notes("chess-arm"))

B.append(board("02", "Procedural World", f'''
{fig("procedural-world/trees.webp", "1 / 1 / 6 / 10", "Trees grown by species, each with its own root flare, branching and crown.", "hero")}
{text("02", "procedural-world", "Procedural World", "2026 · Personal project",
      "A tool for building 3D game worlds from rules instead of hand-placed models. The world is a graph of pure nodes, and each node’s fingerprint hashes its type, parameters, seed and inputs, so an edit re-cooks only what it touches. Eight packs add ground, cliffs, walls, trees, caves, water, sea life and props, and the renderer is written straight on wgpu. Cliffs are drawn as Bezier curves, caves are dug as distance fields, and walls interlock course by course.",
      "1 / 10 / 9 / 13", nums([("8", "packs"), ("18", "crates")]))}
{fig("procedural-world/cave-hall.webp", "6 / 1 / 9 / 5", "Underground: a hall of stalactites in a generated cave")}
{fig("procedural-world/cliff.webp", "6 / 5 / 9 / 10", "A cliff in the world: layered rock grown from its drawn edge", text="A grey layered rock mesa with a grassy top rising from green ground, generated from a drawn outline")}''', "procedural-world") + "\n" + notes("procedural-world"))

B.append(board("03", "D&amp;D VTT", f'''
{text("03", "dnd-vtt", "D&amp;D VTT", "2023 – present · Personal project",
      "A desktop virtual tabletop for playing D&amp;D online: maps, character sheets, dice, chat, music and combat in one window. It is built from 92 plugins, each its own webpack build loaded at runtime with Module Federation, which will each get their own repository and CI/CD pipeline. Plugins never share state; they send each other intents, such as “roll these dice”. The rules engine knows no particular game, and D&amp;D 5e is one plugin, with more than 20 sourcebooks. The desktop app keeps campaigns in SQLite; only the small Node and mediasoup server, which handles rooms, voice and video, runs in Docker.",
      "1 / 1 / 9 / 4", nums([("92", "plugins"), ("1", "container: the server")]))}
{fig("dnd-app/workspace.webp", "1 / 4 / 6 / 13", "The workspace during a game. Every panel is a window you can move, pin or pop out.", "hero")}
{fig("dnd-app/map-3d.webp", "6 / 4 / 9 / 7", "A battle map tilted into 3D")}
{fig("dnd-app/dice-tray.webp", "6 / 7 / 9 / 10", "Dice rolled in the 3D tray")}
{fig("dnd-app/ship-combat.webp", "6 / 10 / 9 / 13", "Ship combat")}''', "dnd-vtt") + "\n" + notes("dnd-vtt"))

B.append(board("04", "Mathisfactory", f'''
{fig("mathisfactory/lava.webp", "1 / 1 / 6 / 9", "Through the headset: level curves on the real volcano model, and the simulated lava flow.", "hero")}
<div class="stack" style="grid-area:1 / 9 / 6 / 13">
  {fig("mathisfactory/arrows.webp", "auto", "Steepest-descent arrows")}
  {fig("mathisfactory/level-curves.webp", "auto", "Level curves and the in-game menu")}
</div>
{text("04", "mathisfactory", "Mathisfactory", "2023 · TU Delft · Group project",
      "An augmented reality game for HoloLens 2 that teaches first-year Earth Sciences students to read level curves and gradients, projected onto a physical volcano model. You explore the mountain, build research stations where they look safe, then run the eruption: the lava follows the gradient. We tested it with 12 students.",
      "6 / 1 / 9 / 13", nums([("75%", "said it helped them understand level curves"), ("75%", "found the build–simulate loop useful"), ("66%", "said AR improved their learning")]), "text wide")}''', "mathisfactory") + "\n" + notes("mathisfactory"))

B.append(board("05 – 06", "Kidney Stones · Indoor Localization", f'''
{text("05", "kidney-stones", "Kidney Stone Classification", "2021 · BSc thesis, University of Groningen",
      "Identifying the type of a kidney stone from endoscope images, so a urologist can tell during the procedure instead of waiting for a lab. I fine-tuned ImageNet-pretrained networks and explored multi-task learning. The clinical images are private, so the page shows the set-up instead.",
      "1 / 1 / 5 / 5")}
{diagram("kidney-model", "1 / 5 / 5 / 13", "Transfer learning from ImageNet, with extra task heads sharing the same features")}
{text("06", "indoor-localization", "Indoor Localization", "2022 · TU Delft · Group project",
      "Two Android apps that locate a phone indoors using WiFi signal strengths and the phone’s motion sensors. The second splits the floor into 13 cells and updates its belief with Bayes’ rule, one access point at a time, until one cell reaches 90%.",
      "5 / 1 / 9 / 5")}
{diagram("indoor-bayes", "5 / 5 / 9 / 13", "Bayesian localization, illustrated (schematic bar heights)")}''', "kidney-stones", "pair") + "\n" + notes("kidney-stones", "Kidney stones") + "\n" + notes("indoor-localization", "Indoor localization"))

B.append(board("07", "Neural Style Transfer", f'''
<div class="trio" style="grid-area:1 / 1 / 5 / 13">
  {fig("style-transfer/content.webp", "auto", "Content")}
  <span class="op">+</span>
  {fig("style-transfer/style.webp", "auto", "Style")}
  <span class="op">=</span>
  {fig("style-transfer/result-stvae.webp", "auto", "Result: the room in stained glass (ST-VAE)")}
</div>
{text("07", "style-transfer", "Neural Style Transfer", "2022 · TU Delft · With Nafie El Coudi El Amrani",
      "Repainting a photo in the style of another image. We reproduced ST-VAE, a variational method built on a VGG-19 autoencoder, then swapped its backbone for ResNet-50. Without retraining on a large dataset, the ResNet version kept only a faint trace of the content, which showed how much the method relies on VGG’s features.",
      "5 / 1 / 9 / 5")}
{fig("style-transfer/result-resnet.webp", "5 / 5 / 9 / 9", "Same inputs, ResNet-50 backbone")}
{fig("style-transfer/archer.webp", "5 / 9 / 9 / 13", "ST-VAE on a fantasy illustration")}''', "style-transfer") + "\n" + notes("style-transfer"))

other = re.search(r'<ul class="minor">.*?</ul>', sections["other"], re.S).group(0)
B.append(f'<section class="appendix" id="other"><p class="meta">Appendix · Smaller work</p>\n{other}\n</section>')

# ---------- the PhD tab: an overview sheet, then one sheet per paper ----------
P = []
PT = "patient-trajectories"


def paper(n, sid, title, meta, summary, num, dl, dg, cap, qmr, keep):
    cols = "".join(f'<div><p class="meta">{h}</p><p>{p}</p></div>' for h, p in zip(("Question", "Method", "Result"), qmr))
    return board(f"PhD · {n}", title, f'''
{text(n, PT, title, meta, summary, "1 / 1 / 9 / 5", nums(num), dl=dl)}
{diagram(dg, "1 / 5 / 5 / 13", cap)}
<div class="papers" style="grid-area:5 / 5 / 9 / 13">{cols}</div>''', sid) + "\n" + notes(PT, title, keep)


P.append(board("PhD · 00", "Forecasting Patient Trajectories", f'''
{text("PhD", PT, "Forecasting Patient Trajectories", "2023 – present · PhD, University of Edinburgh",
      "My PhD is on forecasting how patients move between clinical states, such as levels of breathing support in intensive care, from large databases of health records. The three papers share the same groundwork: building cohorts and states from raw records, treating missing values as information, and testing on later patients or later years. The SAIL data stays in its secure environment, so these pages show the models, not patients.",
      "1 / 1 / 9 / 5", nums([("≈13M", "people in SAIL, Wales"), ("50,873", "ICU stays, MIMIC-IV")]))}
{diagram("health-data", "1 / 5 / 4 / 13", "How the SAIL work runs: the records never leave the secure environment, and only checked aggregates do")}
<nav class="contents flat" style="grid-area:4 / 5 / 9 / 13">
  <p class="meta">Papers</p>
{paper_rows("a")}</nav>''', PT) + "\n" + notes(PT, "Working with patient databases", ["Working with large patient databases", "<!--dg:health-data-->"]))

STACK = ("Stack", "Python, PyTorch")
P.append(paper("01", "tracer", "TraCeR", "Competing risks · Under review",
               "A Transformer for competing risks. When several outcomes can end a patient’s follow-up, it forecasts the probability of each one over time, from an irregular history full of gaps.",
               [("0.840", "time-dependent AUC, MIMIC-IV"), ("0.808", "Dynamic-DeepHit")],
               [STACK, ("Data", "MIMIC-IV, MIMIC-III, eICU, PBC2, synthetic")],
               "tracer", "Attention along each measurement’s timeline, then across measurements; a softmax with a fixed no-event score",
               ("In intensive care, sepsis, death and discharge race to happen first, and each one stops the others from being observed. Treating them as separate survival problems gives probabilities that can add up to more than one.",
                "Each value becomes a token with a learned “missing” token and a decay for its age. Attention is factorised over time, then over measurements. Each future hour gets a score per cause, against a fixed no-event score.",
                "On MIMIC-IV, from 24 hours of history: time-dependent AUC 0.840 against 0.808 for Dynamic-DeepHit, and a lower Brier score (0.059 against 0.066). The gains on MIMIC-III were smaller, and every method struggled on eICU."),
               ["<h3>TraCeR", "<!--dg:tracer-->"]))

P.append(paper("02", "nmsm", "nMSM", "ML4H · Accepted",
               "A neural multi-state model that forecasts a patient’s states and measurements together, so simulated values steer later transitions, as they would in reality.",
               [("0.061", "integrated Brier score, nMSM-GRU"), ("0.064", "next best, Direct MLP")],
               [STACK, ("Data", "MIMIC-IV, SAIL Databank, synthetic")],
               "nmsm", "One step of nMSM, and the MIMIC-IV state graph (self-loops omitted)",
               ("A falling oxygen level is what moves a patient onto a ventilator, so forecasting the course means forecasting the measurements too. Most multi-state models predict the states alone.",
                "The model samples the next state from the transitions the graph allows, then generates the next measurements given that state, including whether each is measured at all. 500 rollouts per patient give state probabilities and full paths.",
                "On 50,873 MIMIC-IV stays, forecasting 48 hours ahead, both nMSM variants had the best integrated Brier score and AUROC of seven methods, ahead of multi-state Cox and SurvNODE. Removing the missingness masks hurt the most."),
               ["<h3>nMSM", "<!--dg:nmsm-->"]))

P.append(paper("03", "apc", "APC", "Calendar drift · Under review",
               "Where should calendar time go inside a neural multi-state model? Records spanning ten years also span changes in practice, coding and the patients themselves, and a model trained on the past is used on the future.",
               [("3", "places calendar time can enter"), ("4", "test sets: simulated, SAIL, ELSA, MIMIC-IV")],
               [STACK, ("Data", "SAIL Databank, ELSA, MIMIC-IV, simulations")],
               "apc", "Three places to add calendar context, and the constraint that makes age, period and cohort identifiable",
               ("Age, period and cohort are tied together (cohort = period − age), so they cannot be told apart from the data alone. Which form of calendar context actually helps a neural model forecast after a cutoff year?",
                "A continuous-time Transformer multi-state model, with context added on each event, as biases in attention, or as age, period and cohort curves on each transition’s risk, plus all three together.",
                "Trained before a cutoff year and tested after it. Output curves did best when outcome rates drifted; the representation and attention routes did best when measurements changed meaning. On SAIL no variant won on every measure."),
               ["<h3>APC", "<!--dg:apc-->"]))

FONTS = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Jost:wght@200;300;400;500&display=swap"
html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Maxmillan Ries · Portfolio</title>
  <meta name="description" content="Projects by Maxmillan Ries: robotics, computer vision, machine learning for health, procedural generation, AR and tools.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS}">
  <link rel="stylesheet" href="boards.css">
  <link rel="stylesheet" href="diagrams.css">
</head>
<body>

<header class="tabs"><div class="tabs-in">
  <span class="tabs-name">Maxmillan Ries</span>
  <nav role="tablist" aria-label="Sections">
    <a href="#projects" role="tab" aria-controls="projects">Projects</a>
    <a href="#phd" role="tab" aria-controls="phd">PhD research</a>
  </nav>
</div></header>

<main class="panel" id="projects" role="tabpanel">
{chr(10).join(B)}
</main>

<main class="panel" id="phd" role="tabpanel">
{chr(10).join(P)}
</main>

<div class="lightbox" id="lightbox"><img alt=""></div>
<script>
  // two tabs; without scripts both panels simply show one after the other
  const panels = [...document.querySelectorAll('.panel')];
  const tabs = [...document.querySelectorAll('.tabs [role=tab]')];
  function show(scroll) {{
    const target = location.hash && document.getElementById(location.hash.slice(1));
    const on = (target && target.closest('.panel')) || panels[0];
    panels.forEach(p => p.hidden = p !== on);
    tabs.forEach(t => t.setAttribute('aria-selected', t.getAttribute('aria-controls') === on.id));
    if (!scroll) return;
    const behavior = scroll === 'instant' ? 'instant' : 'smooth';
    if (target && target !== on) target.scrollIntoView({{ behavior }});
    else window.scrollTo({{ top: 0, behavior }});
  }}
  tabs.forEach(t => t.addEventListener('click', e => {{
    e.preventDefault();
    history.pushState(null, '', t.getAttribute('href'));
    show(true);
  }}));
  window.addEventListener('hashchange', () => show(true));
  window.addEventListener('popstate', () => show(true));
  show('instant');
</script>
<script>
  const box = document.getElementById('lightbox');
  const big = box.querySelector('img');
  document.querySelectorAll('.board figure img, .notes figure img').forEach(img => {{
    img.addEventListener('click', () => {{ big.src = img.src; big.alt = img.alt; box.classList.add('open'); }});
  }});
  const close = () => box.classList.remove('open');
  box.addEventListener('click', close);
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') close(); }});
</script>
<script>
  // cover: hovering a contents entry shows that project's picture, which stays until another entry is hovered
  const pic = document.querySelector('.cover-pic');
  if (pic && matchMedia('(hover: hover)').matches) {{
    const img = pic.querySelector('img'), cap = pic.querySelector('figcaption');
    const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let extra = null, shown = null;
    function set(d) {{
      if (d === shown) return;
      shown = d;
      if (extra) {{ extra.remove(); extra = null; }}
      if (d.pv) {{
        extra = document.getElementById('pv-' + d.pv).content.firstElementChild.cloneNode(true);
        pic.insertBefore(extra, cap);
      }} else {{
        img.src = d.pic; img.alt = d.alt;
      }}
      img.hidden = !!d.pv;
      cap.textContent = d.cap;
      if (!still) (extra || img).animate([{{ opacity: 0 }}, {{ opacity: 1 }}], 180);
    }}
    document.querySelectorAll('.cover .contents a').forEach(a => {{
      const d = a.dataset;
      if (!d.pic && !d.pv) return;
      if (d.pic) new Image().src = d.pic;
      a.addEventListener('mouseenter', () => set(d));
      a.addEventListener('focus', () => set(d));
    }});
  }}
</script>

</body>
</html>
'''
(root / "index.html").write_text(html, encoding="utf8", newline="\n")
print("wrote index.html")
