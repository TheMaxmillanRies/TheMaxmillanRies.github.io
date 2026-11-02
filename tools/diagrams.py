"""Line diagrams for the portfolio, inserted into content.html as inline SVG.
usage: python diagrams.py "E:/Github Website"   (idempotent: replaces <!--dg:NAME-->...<!--/dg:NAME--> blocks)
All strokes use currentColor; highlights use class "ac" (the page's --accent), styled in diagrams.css."""
import re
import sys
from pathlib import Path


def svg(name, w, h, label, body):
    return (f'<svg class="dg dg-{name}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">\n' + "\n".join(body) + "\n</svg>")


def t(x, y, s, cls="", anchor="start"):
    c = f' class="{cls}"' if cls else ""
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    return f'<text x="{x:g}" y="{y:g}"{c}{a}>{s}</text>'


def arrow(x1, y1, x2, y2, cls="ln"):
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" class="{cls}" marker-end="url(#ah)"/>'


DEFS = ('<defs><marker id="ah" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0.5 L7.5 4 L0 7.5" fill="none" stroke="currentColor" stroke-width="1"/></marker></defs>')


# ---------- chess: photo markers ----------
MARKS = [  # (point on the photo, marker position) in the 1200x1600 photo
    ((505, 330), (330, 430)),
    ((770, 232), (700, 470)),
    ((915, 665), (720, 650)),
    ((985, 945), (1150, 790)),
    ((1000, 1170), (1150, 1330)),
]


def marks():
    b = []
    for i, ((px, py), (mx, my)) in enumerate(MARKS, 1):
        b.append(f'<line x1="{px}" y1="{py}" x2="{mx}" y2="{my}" class="lead"/>')
        b.append(f'<circle cx="{px}" cy="{py}" r="7" class="pt"/>')
        b.append(f'<circle cx="{mx}" cy="{my}" r="26" class="mk"/>')
        b.append(t(mx, my + 10, i, "mkn", "middle"))
    return '<svg class="marks" viewBox="0 0 1200 1600" aria-hidden="true">\n' + "\n".join(b) + "\n</svg>"


# ---------- chess: occupancy diff -> move ----------
def board(ox, oy, occ, cell=22, hi=None, labels=False):
    b = []
    for r in range(8):
        for f in range(8):
            x, y = ox + f * cell, oy + r * cell
            if (r + f) % 2:
                b.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" class="sq"/>')
            sqn = f"{'abcdefgh'[f]}{8 - r}"
            if hi and sqn in hi:
                kind = hi[sqn]
                if kind == "+":
                    b.append(f'<circle cx="{x + cell / 2}" cy="{y + cell / 2}" r="7" class="ac-f"/>')
                else:
                    b.append(f'<circle cx="{x + cell / 2}" cy="{y + cell / 2}" r="6.5" class="ac-o"/>')
            elif sqn in occ:
                b.append(f'<circle cx="{x + cell / 2}" cy="{y + cell / 2}" r="6" class="dot"/>')
    b.append(f'<rect x="{ox}" y="{oy}" width="{8 * cell}" height="{8 * cell}" class="frame"/>')
    if labels:
        for f in range(8):
            b.append(t(ox + f * cell + cell / 2, oy + 8 * cell + 15, "abcdefgh"[f], "tiny", "middle"))
        for r in range(8):
            b.append(t(ox - 9, oy + r * cell + cell / 2 + 4, 8 - r, "tiny", "middle"))
    return b


def chess_move():
    start = {f"{c}{r}" for c in "abcdefgh" for r in (1, 2, 7, 8)}
    after = (start - {"e2"}) | {"e4"}
    b = [DEFS]
    b += [t(40, 22, "01  Occupied squares, before", "lb"), t(320, 22, "02  Occupied squares, after", "lb"),
          t(600, 22, "03  Difference", "lb"), t(850, 22, "04  Move", "lb")]
    b += board(40, 40, start, labels=True)
    b += board(320, 40, after)
    b += board(600, 40, set(), hi={"e2": "-", "e4": "+"})
    b += [arrow(226, 128, 308, 128), arrow(506, 128, 588, 128), arrow(786, 128, 842, 128)]
    b += [t(850, 120, "e2 → e4", "big"), t(850, 146, "sent to Stockfish", "sm"), t(850, 164, "as UCI “e2e4”", "sm")]
    b += [f'<circle cx="606" cy="236" r="5" class="ac-o"/>', t(618, 240, "vacated", "sm"),
          f'<circle cx="686" cy="236" r="5.5" class="ac-f"/>', t(698, 240, "newly occupied", "sm")]
    return svg("move", 1000, 256, "Two occupancy grids before and after a move, their difference, and the move it implies, e2 to e4", b)


# ---------- procedural: DAG with cached and re-cooked nodes ----------
def node(x, y, w, label, key, state):
    cls = "nd ac-n" if state == "cook" else "nd"
    return [f'<rect x="{x}" y="{y}" width="{w}" height="44" class="{cls}"/>', t(x + 12, y + 19, label, "nm"),
            t(x + 12, y + 35, key, "key"), t(x + w - 10, y + 35, state == "cook" and "re-cooked" or "cached",
                                              "st ac-t" if state == "cook" else "st", "end")]


def dag():
    b = [DEFS]
    b += node(30, 30, 210, "ground box 1", "#a41f…", "c")
    b += node(30, 92, 210, "ground box 2  (resized)", "#e7d0… → #5b12…", "cook")
    b += node(30, 178, 210, "cliff curve", "#71ae…", "c")
    b += node(30, 240, 210, "wall path", "#09c3…", "c")
    b += node(340, 61, 230, "terrain  (re-lays box 2 only)", "#40b9… → #f2a7…", "cook")
    b += node(700, 145, 270, "cliff  · reads tiles 3–4", "#c8e5…", "c")
    b += node(700, 230, 270, "wall  · reads tile 7", "#9d03… → #1c6e…", "cook")
    b += [arrow(240, 52, 338, 76), arrow(240, 114, 338, 92, "ln ac-l"),
          arrow(570, 90, 698, 160), arrow(570, 98, 698, 246, "ln ac-l"),
          arrow(240, 200, 698, 172), arrow(240, 262, 698, 258),
          t(600, 120, "tiles 3–4 unchanged", "sm"), t(560, 200, "tile 7 changed", "sm ac-t")]
    b += [t(30, 322, "key = hash( type, parameters, seed, keys of what the node reads )", "mono"),
          t(30, 346, "Same key: the result comes from the cache.  New key: the node cooks again.", "sm")]
    return svg("dag", 1000, 360, "A node graph: resizing ground box 2 changes its key and the terrain's; the wall reads a changed tile and re-cooks, while the cliff reads unchanged tiles and comes from the cache", b)


# ---------- procedural: one frame of the renderer ----------
def frame():
    b = [DEFS]
    steps = [("01  Prepare", ["sky, ocean, GI bake,", "only when they change"]),
             ("02  Cull", ["every instance on GPU,", "against the frustums"]),
             ("03  Shadows", ["2 cascades, held", "until the light moves"]),
             ("04  G-buffer", ["big solids first,", "multi-draw indirect"]),
             ("05  Re-cull", ["depth pyramid (HZB);", "small things tested"]),
             ("06  Light", ["GI rays, lighting,", "water, TAA upscale"])]
    w, gap, x0 = 158, 9, 2
    for i, (h, lines) in enumerate(steps):
        x = x0 + i * (w + gap)
        hi = " ac-n" if i in (1, 4) else ""
        b += [f'<rect x="{x}" y="30" width="{w}" height="92" class="nd{hi}"/>', t(x + 12, 54, h, "nm")]
        b += [t(x + 12, 80 + k * 18, ln, "sm") for k, ln in enumerate(lines)]
        if i:
            b.append(arrow(x - gap, 76, x - 2, 76))
    b += [t(10, 156, "Settled: once nothing changes, no frame is drawn at all.", "sm"),
          t(10, 176, "Wind only: the still frame is held, and only the vegetation and the water are relit and resolved.", "sm")]
    return svg("frame", 1000, 190, "One frame of the renderer in six steps: prepare, cull, shadows, G-buffer, re-cull against a new depth pyramid, and lighting with upscaling", b)


# ---------- altar: plugins, intents, stores ----------
def altar():
    b = [DEFS]
    plugins = ["Dice", "Map", "Chat", "Music", "D&amp;D 5e rules", "…"]
    x, w, gap = 130, 118, 16
    right = x + len(plugins) * (w + gap) - gap
    b += [t(30, 58, "plugins", "lb"), t(30, 146, "intents", "lb ac-t"), t(30, 228, "stores", "lb")]
    for i, p in enumerate(plugins):
        px = x + i * (w + gap)
        dashed = " dash" if p == "…" else ""
        b += [f'<rect x="{px}" y="30" width="{w}" height="46" class="nd{dashed}"/>', t(px + w / 2, 58, p, "nm", "middle")]
        b.append(arrow(px + w / 2 - 14, 78, px + w / 2 - 14, 136, "ln ac-l"))
        b.append(arrow(px + w / 2 + 14, 200, px + w / 2 + 14, 80, "ln dash"))
    b += [f'<line x1="{x}" y1="141" x2="{right}" y2="141" class="bus ac-l"/>',
          f'<rect x="{x}" y="202" width="{right - x}" height="44" class="nd fill"/>',
          t(x + 14, 229, "shared state", "sm")]
    lx = right - 236
    b += [arrow(lx, 14, lx + 26, 14, "ln ac-l"), t(lx + 34, 18, "send an intent", "sm"),
          arrow(lx + 140, 14, lx + 166, 14, "ln dash"), t(lx + 174, 18, "read state", "sm")]
    return svg("altar", 1000, 262, "Plugins send intents to a shared channel and read state from stores; they never share state directly", b)


# ---------- mathisfactory: the game loop ----------
def loop():
    b = [DEFS]
    cx, cy, r = 360, 190, 110
    steps = [("Explore", "level curves, gradient arrows,", "steepest-descent paths", 0, -1),
             ("Build", "place research stations", "where they look safe", 1, 0),
             ("Simulate", "lava follows the gradient;", "pause or rewind", 0, 1),
             ("Feedback", "stations lost and", "placement height", -1, 0)]
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" class="ln"/>')
    import math
    for k in range(4):  # arrowheads mid-arc, clockwise
        a = math.radians(-45 + 90 * k)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        dx, dy = -math.sin(a), math.cos(a)
        b.append(arrow(x - dx * 6, y - dy * 6, x + dx * 4, y + dy * 4, "ln ac-l"))
    for i, (name, l1, l2, ux, uy) in enumerate(steps):
        x, y = cx + ux * r, cy + uy * r
        b.append(f'<circle cx="{x}" cy="{y}" r="8" class="mk2"/>')
        if ux:
            tx, ty, anchor = x + 22 * ux, y - 6, "start" if ux > 0 else "end"
        else:
            tx, anchor = x, "middle"
            ty = y - 62 if uy < 0 else y + 30
        b += [t(tx, ty, f"{i + 1:02d}  {name}", "nm", anchor), t(tx, ty + 18, l1, "sm", anchor), t(tx, ty + 34, l2, "sm", anchor)]
    b.append(t(cx, cy + 5, "five levels", "lb", "middle"))
    return svg("loop", 720, 380, "The game loop: explore, build, simulate, feedback, and back to explore", b)


# ---------- kidney: transfer + multi-task ----------
def kidney():
    b = [DEFS]
    def box(x, y, w, h, l1, l2="", cls="nd"):
        r = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>', t(x + 12, y + 22, l1, "nm")]
        if l2:
            r.append(t(x + 12, y + 40, l2, "sm"))
        return r
    b += box(30, 70, 150, 56, "Endoscope image", "surface or section")
    b += box(240, 50, 250, 96, "Pretrained backbone", "ResNet152V2 or", "nd fill")
    b.append(t(252, 108, "InceptionResNetV2, ImageNet", "sm"))
    b.append(t(252, 126, "weights, fine-tuned", "sm"))
    b += box(550, 70, 140, 56, "Shared features")
    b += box(760, 20, 210, 56, "Stone type", "the main task", "nd ac-n")
    b += box(760, 120, 210, 56, "Related tasks", "multi-task heads", "nd dash")
    b += [arrow(180, 98, 238, 98), arrow(490, 98, 548, 98), arrow(690, 92, 758, 52, "ln ac-l"), arrow(690, 104, 758, 144)]
    return svg("kidney", 1000, 196, "An endoscope image passes through a pretrained backbone to shared features, which feed a stone type head and other task heads", b)


# ---------- indoor: Bayesian update over 13 cells ----------
def bayes():
    b = [DEFS]
    rows = [("Prior", [1] * 13),
            ("After AP 1", [1, 1.2, 1.6, 2.4, 1.8, 1, .7, .6, .5, .5, .4, .4, .3]),
            ("After AP 2", [.3, .6, 1.4, 4.2, 2.2, .6, .3, .2, .1, .1, .1, .1, .1]),
            ("After AP n", [0, .1, .4, 9.2, .3, 0, 0, 0, 0, 0, 0, 0, 0])]
    x0, bw, gap, rh, top = 150, 34, 8, 64, 34
    for i, (name, v) in enumerate(rows):
        s = sum(v)
        p = [q / s for q in v]
        base = top + (i + 1) * rh
        b.append(t(30, base - 6, name, "nm"))
        b.append(f'<line x1="{x0}" y1="{base}" x2="{x0 + 13 * (bw + gap) - gap}" y2="{base}" class="ln"/>')
        for c, q in enumerate(p):
            h = q * 52
            cls = "bar ac-n" if i == 3 and c == 3 else "bar"
            b.append(f'<rect x="{x0 + c * (bw + gap)}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" class="{cls}"/>')
        if i == 3:
            y90 = base - 0.9 * 52
            b += [f'<line x1="{x0}" y1="{y90:.1f}" x2="{x0 + 13 * (bw + gap) - gap}" y2="{y90:.1f}" class="ln dash"/>',
                  t(x0 + 13 * (bw + gap) + 4, y90 + 4, "90%: stop", "sm")]
    for c in range(13):
        b.append(t(x0 + c * (bw + gap) + bw / 2, top + 4 * rh + 18, c + 1, "tiny", "middle"))
    b.append(t(x0, 20, "belief over the 13 cells, updated with Bayes’ rule one access point at a time", "lb"))
    return svg("bayes", 1000, 314, "Bar charts of belief over 13 cells, sharpening with each access point until one cell passes 90 percent", b)


# ---------- research: one nMSM step, and the MIMIC-IV state graph ----------
def nmsm():
    b = [DEFS]
    def box(x, y, w, h, l1, l2="", cls="nd"):
        r = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>', t(x + 12, y + 22, l1, "nm")]
        if l2:
            r.append(t(x + 12, y + 40, l2, "sm"))
        return r
    b.append(t(20, 22, "one forecasting step", "lb"))
    b += box(20, 52, 140, 56, "History", "values, masks, gaps")
    b += box(192, 52, 150, 56, "Encoder", "GRU or Transformer", "nd fill")
    b += box(374, 52, 128, 56, "Next state", "sampled", "nd ac-n")
    b += box(374, 160, 128, 56, "Measurements", "given that state")
    b += [arrow(160, 80, 190, 80), arrow(342, 80, 372, 80, "ln ac-l"), arrow(438, 108, 438, 158),
          '<polyline points="374,188 90,188 90,110" class="ln" marker-end="url(#ah)"/>',
          t(110, 180, "the completed row is fed back", "sm")]
    b.append(t(540, 22, "MIMIC-IV respiratory support, hourly", "lb"))
    b.append('<rect x="540" y="40" width="440" height="96" class="nd dash"/>')
    for i, (l1, l2) in enumerate([("No support", "room air"), ("HFNC", "high-flow"), ("NIV", "non-invasive"), ("INV", "ventilated")]):
        b += box(552 + i * 106, 52, 98, 50, l1, l2)
    b.append(t(552, 124, "any living state can move to any other", "sm"))
    b += box(600, 176, 140, 44, "Discharge", "", "nd fill")
    b += box(800, 176, 140, 44, "Death", "", "nd fill")
    b += [arrow(670, 136, 670, 174), arrow(870, 136, 870, 174)]
    return svg("nmsm", 1000, 236, "One forecasting step: history goes through an encoder to a sampled next state, measurements are generated given that state and fed back. Beside it, four respiratory-support states that can all reach each other, with discharge and death as exits", b)


# ---------- health data: from records to a published result ----------
def health():
    b = [DEFS]
    steps = [("Records", ["linked, anonymised", "hospital, GP, deaths"]),
             ("Cohort", ["who is in, and when;", "censoring rules"]),
             ("States", ["events on a grid;", "value, mask, gap"]),
             ("Train, test", ["split by patient", "or by calendar year"]),
             ("Output check", ["aggregates only,", "small counts removed"]),
             ("Paper", ["tables and curves,", "no patient rows"])]
    w, gap, x0 = 152, 16, 2
    b.append(f'<rect x="{x0 + w + gap / 2}" y="22" width="{4 * (w + gap)}" height="122" class="nd dash"/>')
    b.append(t(x0 + w + gap / 2 + 10, 16, "inside the secure environment", "lb"))
    for i, (h, lines) in enumerate(steps):
        x = x0 + i * (w + gap)
        hi = " ac-n" if i == 4 else ""
        b += [f'<rect x="{x}" y="38" width="{w}" height="92" class="nd{hi}"/>', t(x + 12, 62, h, "nm")]
        b += [t(x + 12, 88 + k * 18, ln, "sm") for k, ln in enumerate(lines)]
        if i:
            b.append(arrow(x - gap, 84, x - 2, 84))
    return svg("health", 1000, 150, "Records go through cohort selection, state building and model training inside the secure environment; only checked aggregate results leave it for the paper", b)


# ---------- tracer: factorised attention, competing risks ----------
def tracer():
    b = [DEFS]
    rows = ["heart rate", "resp. rate", "SpO&#8322;", "lactate", "creatinine"]
    seen = ["11111111", "11011111", "10111011", "00100010", "01000100"]
    x0, y0, cw, ch = 110, 40, 34, 24
    b.append(t(20, 22, "history: measurements × hours", "lb"))
    for r, (name, row) in enumerate(zip(rows, seen)):
        b.append(t(20, y0 + r * ch + 16, name, "sm"))
        for c, v in enumerate(row):
            b.append(f'<rect x="{x0 + c * cw + 2}" y="{y0 + r * ch + 2}" width="{cw - 4}" height="{ch - 4}" class="nd{" fill" if v == "1" else " dash"}"/>')
    b.append(f'<rect x="{x0 - 2}" y="{y0 + 3 * ch - 2}" width="{8 * cw + 4}" height="{ch + 4}" class="nd ac-n"/>')
    b.append(f'<rect x="{x0 + 6 * cw - 2}" y="{y0 - 2}" width="{cw + 4}" height="{5 * ch + 4}" class="nd ac-n"/>')
    b += [t(20, 190, "1  each measurement attends along its own timeline (a row)", "sm"),
          t(20, 208, "2  each hour attends across the measurements (a column)", "sm"),
          t(20, 226, "dashed = not measured: a learned token, decayed by the time since", "sm")]
    b.append(arrow(x0 + 8 * cw + 6, 100, 440, 100))
    b += ['<rect x="442" y="70" width="170" height="60" class="nd fill"/>', t(454, 94, "Each hour ahead", "nm"),
          t(454, 114, "a score per cause", "sm")]
    b.append(arrow(612, 100, 650, 100, "ln ac-l"))
    b += ['<rect x="652" y="78" width="96" height="44" class="nd ac-n"/>', t(700, 105, "softmax", "nm", "middle")]
    b.append(arrow(748, 100, 772, 100))
    x, W = 774, 206
    for cls, f in [("nd ac-n", .12), ("nd fill", .07), ("nd", .23), ("nd dash", .58)]:
        b.append(f'<rect x="{x:g}" y="86" width="{W * f:g}" height="28" class="{cls}"/>')
        x += W * f
    b += [t(774, 140, "sepsis · death · discharge · none", "sm"), t(774, 158, "always sum to one", "sm"),
          t(454, 190, "the fixed “no event” score is the reference, so the", "sm"),
          t(454, 208, "probability of each cause by any time plus the chance", "sm"),
          t(454, 226, "of staying event-free add up to one by construction", "sm")]
    return svg("tracer", 1000, 240, "TraCeR: a grid of measurements by hours, some missing; attention runs along each row and then down each column; each future hour gets a score per cause, and a softmax with a fixed no-event score turns them into hazards that sum to one", b)


# ---------- apc: where calendar time enters ----------
def apc():
    b = [DEFS]
    boxes = [(20, 170, "Event history", "states, values, masks", "nd"),
             (240, 190, "Encoder", "causal Transformer", "nd fill"),
             (480, 210, "Transition risks", "one intensity per arrow", "nd"),
             (740, 240, "Forecast", "state probabilities over time", "nd")]
    for i, (x, w, l1, l2, cls) in enumerate(boxes):
        b += [f'<rect x="{x}" y="30" width="{w}" height="56" class="{cls}"/>', t(x + 12, 52, l1, "nm"), t(x + 12, 72, l2, "sm")]
        if i:
            px, pw = boxes[i - 1][0], boxes[i - 1][1]
            b.append(arrow(px + pw + 2, 58, x - 2, 58))
    inj = [("r · representation", "calendar time encoded", "on every event"),
           ("a · attention", "biased towards recent", "and same-era events"),
           ("h · output", "age, period and cohort", "curves on each transition")]
    for (x, w, *_), (l0, l1, l2) in zip(boxes, inj):
        cx = x + w / 2
        b += [f'<circle cx="{cx:g}" cy="128" r="6" class="mk2"/>', arrow(cx, 120, cx, 88, "ln ac-l"),
              t(x, 160, l0, "nm ac-t"), t(x, 180, l1, "sm"), t(x, 198, l2, "sm")]
    b += ['<rect x="740" y="112" width="240" height="96" class="nd dash"/>', t(752, 136, "cohort = period − age", "nm"),
          t(752, 158, "only centred age and one drift", "sm"), t(752, 176, "keep straight lines; the curves", "sm"),
          t(752, 194, "have zero mean and zero slope", "sm"),
          t(20, 232, "The combined variant uses all three. Which place works best depends on how the drift arises.", "sm")]
    return svg("apc", 1000, 244, "Event history, encoder, transition risks and forecast in a row, with three places where calendar context can be added: on each event, in the attention, or as age, period and cohort curves on each transition's risk. A note explains the cohort equals period minus age constraint", b)


BLOCKS = {
    "chess-move": (chess_move, "The move is never recognised directly. The camera only reports which squares are occupied; comparing two readings gives the move."),
    "pw-frame": (frame, "One frame, in the order the passes run. Steps 02 to 05 are occlusion culling on the GPU: the big solids are drawn first, a depth pyramid is built from them, and the small props, plants and stones are tested against it, so whatever is hidden behind a hill or a wall is never drawn."),
    "pw-dag": (dag, "Resizing one ground box. Its key changes, so the terrain cooks again, but only for the tiles under that box. The wall reads one of those tiles and cooks again; the cliff reads tiles that did not change, so its key is the same and its mesh comes from the cache."),
    "altar-arch": (altar, "Plugins never touch each other’s state. They send intents such as “roll these dice” or “apply this damage”, and read shared state from stores."),
    "math-loop": (loop, "The game loop."),
    "kidney-model": (kidney, "Set-up: transfer learning from ImageNet, with extra task heads sharing the same features."),
    "health-data": (health, "How the SAIL work runs. The records never leave the secure environment, and everything that does is checked first. MIMIC-IV is downloaded under a data use agreement instead, but the same rule holds for anything published."),
    "tracer": (tracer, "TraCeR, schematic. Attention runs along each measurement's own timeline, then across the measurements within each hour, which is far cheaper than attending over every value at once. The probabilities in the bar are illustrative, not a result."),
    "apc": (apc, "The three places calendar context can enter a neural multi-state model, and the constraint that makes the age, period and cohort curves identifiable."),
    "nmsm": (nmsm, "Left: one step of nMSM. The next state is sampled first and the measurements are generated given it, so simulated values steer later transitions. Right: the MIMIC-IV state graph (self-loops omitted)."),
    "indoor-bayes": (bayes, "Bayesian localization, illustrated. The bar heights are schematic, not measured data."),
}


def block(name):
    fn, cap = BLOCKS[name]
    # each diagram gets its own marker id; a shared one breaks when its first copy is hidden
    body = fn().replace('id="ah"', f'id="ah-{name}"').replace("url(#ah)", f"url(#ah-{name})")
    return (f'<!--dg:{name}-->\n    <figure class="diagram">\n{body}\n      <figcaption>{cap}</figcaption>\n    </figure>\n    <!--/dg:{name}-->')


if __name__ == "__main__":
    p = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent) / "content.html"
    s = p.read_text(encoding="utf8")
    for name in BLOCKS:
        s, n = re.subn(rf"<!--dg:{name}-->.*?<!--/dg:{name}-->", lambda m: block(name), s, flags=re.S)
        print(name, "replaced" if n else "NOT FOUND")
    s, n = re.subn(r"<!--dg:marks-->.*?<!--/dg:marks-->", lambda m: "<!--dg:marks-->" + marks() + "<!--/dg:marks-->", s, flags=re.S)
    print("marks", "replaced" if n else "NOT FOUND")
    p.write_text(s, encoding="utf8", newline="\n")
