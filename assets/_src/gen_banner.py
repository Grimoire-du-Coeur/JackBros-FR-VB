# -*- coding: utf-8 -*-
"""Generateur du bandeau anime 'CRT Virtual Boy' pour le README de JackBros-FR-VB.

Tout est auto-contenu : police en tuiles 5x7 dessinee en rects, labyrinthe genere
par DFS (graine fixe = rendu reproductible), aucune ressource externe (GitHub
bloque polices/images externes dans un SVG servi en <img>).
"""
import random
import sys
import io

OUT = sys.argv[1]

# ---------------------------------------------------------------- police 5x7
F = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    '.': [".....", ".....", ".....", ".....", ".....", "..##.", "..##."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}
TITLE = "JACK BROS."
ADV = {'.': 4, ' ': 4}
PX = 16
GAP = 1

W, H = 1200, 470

# palette Virtual Boy : 4 rouges sur noir absolu
RED_DIM, RED_MID, RED, RED_HOT = "#5E0000", "#9E0000", "#D40000", "#FF3B2F"
BLACK = "#000000"


# ---------------------------------------------------------------- labyrinthe
def maze_path(cols, rows, cell, seed=1995):
    rnd = random.Random(seed)
    vert = [[True] * (cols + 1) for _ in range(rows)]
    horz = [[True] * cols for _ in range(rows + 1)]
    seen = [[False] * cols for _ in range(rows)]
    stack = [(0, 0)]
    seen[0][0] = True
    while stack:
        x, y = stack[-1]
        nb = []
        if x > 0 and not seen[y][x - 1]:
            nb.append((x - 1, y, 'W'))
        if x < cols - 1 and not seen[y][x + 1]:
            nb.append((x + 1, y, 'E'))
        if y > 0 and not seen[y - 1][x]:
            nb.append((x, y - 1, 'N'))
        if y < rows - 1 and not seen[y + 1][x]:
            nb.append((x, y + 1, 'S'))
        if not nb:
            stack.pop()
            continue
        nx, ny, d = rnd.choice(nb)
        if d == 'W':
            vert[y][x] = False
        if d == 'E':
            vert[y][x + 1] = False
        if d == 'N':
            horz[y][x] = False
        if d == 'S':
            horz[y + 1][x] = False
        seen[ny][nx] = True
        stack.append((nx, ny))
    seg = []
    for y in range(rows):
        for x in range(cols + 1):
            if vert[y][x]:
                seg.append("M%d %dv%d" % (x * cell, y * cell, cell))
    for y in range(rows + 1):
        for x in range(cols):
            if horz[y][x]:
                seg.append("M%d %dh%d" % (x * cell, y * cell, cell))
    return "".join(seg)


CELL = 30
MAZE = maze_path(W // CELL, H // CELL + 1, CELL)

TITLE_Y = 112


# ---------------------------------------------------------------- titre
def title_pixels():
    total = sum(ADV.get(c, 5) + GAP for c in TITLE) - GAP
    x0 = (W - total * PX) / 2.0
    out, col = [], 0
    for ch in TITLE:
        glyph = F[ch]
        adv = ADV.get(ch, 5)
        for ry, row in enumerate(glyph):
            for rx in range(adv):
                if rx < len(row) and row[rx] == '#':
                    out.append((x0 + (col + rx) * PX, TITLE_Y + ry * PX, col + rx))
        col += adv + GAP
    return out


PIX = title_pixels()

rnd = random.Random(7)
rects = []
for (x, y, c) in PIX:
    delay = 0.45 + c * 0.018 + rnd.random() * 0.06
    size = PX * 0.84
    rects.append('<rect class="p" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="1.5" '
                 'style="animation-delay:%.2fs"/>' % (x, y, size, size, delay))
RECTS = "\n      ".join(rects)

# ------------------------------------------- sous-titre frappe a la machine
SUB = "&gt; TRADUCTION FRANCAISE INTEGRALE"
NSUB = 32                       # nombre de caracteres reels (&gt; compte pour 1)
FS = 23
ADVM = FS * 0.62                # avance imposee via textLength -> exacte
SUBW = NSUB * ADVM
SUBX = (W - SUBW) / 2.0
SUBY = 272
TYPED = 2.4
START = 1.35

# Frappe en CSS pur : animation de la geometrie SVG (width du masque, x du
# curseur) en steps(). Pas de SMIL, pas de transform : c'est ce qui se rend le
# plus fidelement quand GitHub sert le SVG via <img>.
CARET_END = SUBX + 3 + SUBW

# --------------------------------------------- HUD : compte a rebours minuit
HUD_R = "TIME 23:59:5"
HUD_FS = 19
HUD_ADV = HUD_FS * 0.72
HUD_RW = len(HUD_R) * HUD_ADV
HUD_RX = W - 42 - HUD_RW - HUD_ADV      # on reserve la place du dernier chiffre
DIGIT_X = HUD_RX + HUD_RW + 5          # petit jour avant le dernier chiffre

digits = "\n      ".join(
    '<text class="tick" x="%.1f" y="52" style="animation-delay:%.1fs">%d</text>'
    % (DIGIT_X, i, 9 - i) for i in range(10)
)

# ------------------------------------------------- Frost / Lantern / Skelton
G = {
    'frost':   ["..#..", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "..#.."],
    'lantern': [".#.#.", ".###.", "#####", "#.#.#", "#####", ".###.", "....."],
    'skull':   [".###.", "#####", "#.#.#", "#####", ".###.", ".#.#.", "....."],
}
GPX = 10
GW = 5 * GPX
GGAP = 104
GY = 338
LABEL_Y = GY + 7 * GPX + 26
BASE = (W - (3 * GW + 2 * GGAP)) / 2.0

trio, labels = [], []
for i, (name, label) in enumerate([('frost', 'FROST'), ('lantern', 'LANTERN'),
                                   ('skull', 'SKELTON')]):
    ox = BASE + i * (GW + GGAP)
    cells = "".join(
        '<rect x="%.0f" y="%.0f" width="%d" height="%d"/>'
        % (ox + rx * GPX, GY + ry * GPX, GPX - 2, GPX - 2)
        for ry, row in enumerate(G[name]) for rx, ch in enumerate(row) if ch == '#')
    trio.append('<g class="jg" style="animation-delay:%.2fs">%s</g>'
                % (3.1 + i * 0.3, cells))
    labels.append('<text class="jl" x="%.1f" y="%d" text-anchor="middle" '
                  'style="animation-delay:%.2fs">%s</text>'
                  % (ox + GW / 2.0, LABEL_Y, 3.5 + i * 0.3, label))
TRIO = "\n      ".join(trio)
LABELS = "\n      ".join(labels)

SVG = u'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Jack Bros. (Virtual Boy) - Traduction francaise integrale, version 1.0">
  <title>Jack Bros. (Virtual Boy) - Traduction francaise integrale</title>
  <defs>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="softglow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#000" opacity="0.42"/>
    </pattern>
    <radialGradient id="vig" cx="50%" cy="44%" r="74%">
      <stop offset="0%" stop-color="#000" stop-opacity="0"/>
      <stop offset="58%" stop-color="#000" stop-opacity="0.40"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.96"/>
    </radialGradient>
    <linearGradient id="roll" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{RED}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{RED}" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="{RED}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="typeclip">
      <rect id="tc" x="{SUBX:.1f}" y="{TCY}" width="0" height="34"/>
    </clipPath>
  </defs>

  <style>
    .mono {{ font-family: ui-monospace, "SFMono-Regular", "Consolas", "Liberation Mono", monospace; }}
    .p {{ fill: {RED}; opacity: 0; transform-box: fill-box; transform-origin: center;
          animation: pop .42s cubic-bezier(.2,.9,.3,1.4) both; }}
    @keyframes pop {{
      0%   {{ opacity: 0; transform: scale(.2); fill: {RED_HOT}; }}
      55%  {{ opacity: 1; transform: scale(1.35); fill: {RED_HOT}; }}
      100% {{ opacity: 1; transform: scale(1); fill: {RED}; }}
    }}
    #tc {{ animation: type {TYPED}s steps({NSUB}) {START}s both; }}
    @keyframes type {{ from {{ width: 0 }} to {{ width: {SUBW:.1f}px }} }}
    .caret {{ fill: {RED_HOT};
              animation: caretmove {TYPED}s steps({NSUB}) {START}s both,
                         blink 1s steps(1) infinite; }}
    @keyframes caretmove {{ from {{ x: {CARET_START:.1f}px }} to {{ x: {CARET_END:.1f}px }} }}
    @keyframes blink {{ 0%,49% {{ opacity: 1 }} 50%,100% {{ opacity: 0 }} }}
    .maze {{ animation: drift 72s linear infinite; }}
    @keyframes drift {{ from {{ transform: translateX(0) }} to {{ transform: translateX(-{W}px) }} }}
    .band {{ animation: rolldown 7s linear infinite; }}
    @keyframes rolldown {{ from {{ transform: translateY(-160px) }} to {{ transform: translateY({BANDEND}px) }} }}
    .crt {{ animation: flick 5.5s steps(1) infinite; }}
    @keyframes flick {{
      0%,96% {{ opacity: 1 }} 96.5% {{ opacity: .82 }} 97% {{ opacity: 1 }}
      98% {{ opacity: .9 }} 98.5% {{ opacity: 1 }}
    }}
    .hud {{ fill: {RED_MID}; font-size: {HUD_FS}px; opacity: 0; animation: fade .8s .15s both; }}
    @keyframes fade {{ from {{ opacity: 0 }} to {{ opacity: .92 }} }}
    .tick {{ fill: {RED}; font-size: {HUD_FS}px; opacity: 0; animation: show 10s steps(1) infinite; }}
    @keyframes show {{ 0%,9.99% {{ opacity: .92 }} 10%,100% {{ opacity: 0 }} }}
    .sub {{ fill: {RED}; font-size: {FS}px; }}
    .meta {{ fill: #C01818; font-size: 15px; letter-spacing: 5.5px; opacity: 0;
             animation: fade 1s 4.1s both; }}
    .jg {{ fill: {RED_MID}; opacity: 0; transform-box: fill-box; transform-origin: center;
           animation: jin .6s both, bob 3.6s ease-in-out infinite 3.9s; }}
    @keyframes jin {{ from {{ opacity: 0; transform: translateY(10px) }}
                      to {{ opacity: .9; transform: translateY(0) }} }}
    @keyframes bob {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-5px) }} }}
    .jl {{ fill: #A81414; font-size: 12px; letter-spacing: 3px; opacity: 0;
           animation: fadedim .7s both; }}
    @keyframes fadedim {{ from {{ opacity: 0 }} to {{ opacity: 1 }} }}
    .rule {{ stroke: {RED_DIM}; stroke-width: 1; opacity: 0; animation: fade 1s .3s both; }}
    @media (prefers-reduced-motion: reduce) {{
      .p,.maze,.band,.crt,.caret,#tc,.jg,.tick,.hud,.meta,.jl,.rule {{ animation: none !important; }}
      .p,.jg,.hud,.meta,.jl,.rule {{ opacity: 1 }}
      #tc {{ width: {SUBW:.1f}px }}
      .tick,.caret {{ opacity: 0 }}
    }}
  </style>

  <rect width="{W}" height="{H}" fill="{BLACK}"/>

  <g class="crt">
    <!-- labyrinthe defilant : DFS graine 1995, deux copies pour une boucle propre -->
    <g class="maze" opacity="0.26">
      <path d="{MAZE}" fill="none" stroke="{RED_DIM}" stroke-width="2"/>
      <g transform="translate({W},0)">
        <path d="{MAZE}" fill="none" stroke="{RED_DIM}" stroke-width="2"/>
      </g>
    </g>

    <rect width="{W}" height="{H}" fill="url(#vig)"/>

    <!-- HUD du jeu : etage + compte a rebours jusqu'a minuit -->
    <g class="mono">
      <text class="hud" x="42" y="52" textLength="{HUD_LW:.1f}" lengthAdjust="spacing">FLOOR 06</text>
      <text class="hud" x="{HUD_RX:.1f}" y="52" textLength="{HUD_RW:.1f}" lengthAdjust="spacing">{HUD_R}</text>
      {DIGITS}
    </g>
    <line class="rule" x1="42" y1="68" x2="{RULE_X2}" y2="68"/>

    <!-- titre : police en tuiles 5x7, comme celle de la cartouche -->
    <g filter="url(#glow)">
      {RECTS}
    </g>

    <!-- sous-titre frappe caractere par caractere -->
    <g class="mono" filter="url(#softglow)">
      <g clip-path="url(#typeclip)">
        <text class="sub" x="{SUBX:.1f}" y="{SUBY}" textLength="{SUBW:.1f}"
              lengthAdjust="spacing" xml:space="preserve">{SUB}</text>
      </g>
      <rect class="caret" x="{CARET_START:.1f}" y="{CARETY}" width="{CARETW:.1f}" height="24"/>
      <text class="meta mono" x="{CX}" y="{METAY}" text-anchor="middle">ATLUS 1995 &#183; NINTENDO VIRTUAL BOY &#183; v1.0</text>
    </g>

    <!-- les trois freres -->
    <g filter="url(#softglow)">
      {TRIO}
    </g>
    <g class="mono">
      {LABELS}
    </g>
  </g>

  <!-- balayage CRT + scanlines, par dessus tout -->
  <rect class="band" width="{W}" height="150" fill="url(#roll)"/>
  <rect width="{W}" height="{H}" fill="url(#scan)"/>
</svg>
'''.format(W=W, H=H, RED=RED, RED_DIM=RED_DIM, RED_MID=RED_MID, RED_HOT=RED_HOT,
           BLACK=BLACK, MAZE=MAZE, RECTS=RECTS, DIGITS=digits, TRIO=TRIO, LABELS=LABELS,
           SUB=SUB, SUBX=SUBX, SUBY=SUBY, SUBW=SUBW, FS=FS, TYPED=TYPED, START=START,
           NSUB=NSUB, CARET_START=SUBX + 3, CARET_END=CARET_END,
           TCY=SUBY - 24, CARETY=SUBY - 19, CARETW=ADVM * 0.8,
           METAY=SUBY + 38, CX=W / 2.0, BANDEND=H + 60,
           HUD_FS=HUD_FS, HUD_R=HUD_R, HUD_RX=HUD_RX, HUD_RW=HUD_RW,
           HUD_LW=len("FLOOR 06") * HUD_ADV, RULE_X2=W - 42)

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(SVG)
print("ecrit: %s | %d octets | %d pixels de titre | %d segments de labyrinthe"
      % (OUT, len(SVG), len(PIX), MAZE.count('M')))
