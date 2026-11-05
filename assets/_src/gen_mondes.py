# -*- coding: utf-8 -*-
"""Les 6 mondes de Jack Bros., noms tires de traduction/JackBros_FR.json
(entrees 14 a 20), plus l'echeance de minuit. Animations 100 % CSS."""
import sys
import io

OUT = sys.argv[1]
W, H = 1060, 150
RED_DIM, RED_MID, RED, RED_HOT = "#5E0000", "#9E0000", "#D40000", "#FF3B2F"

MONDES = [
    ("01", u"Forêt des Fées"),
    ("02", u"Caverne du Faucheur"),
    ("03", u"Temple du Cauchemar"),
    ("04", u"Ventre Dragon"),
    ("05", u"Fort Mecha"),
    ("06", u"Palais Cristal"),
]

X0, STEP = 90, 156
END_X = X0 + 6 * STEP          # 1026 -> marqueur minuit
RAIL_Y = 62
CYCLE = 10.0                   # duree de la boucle

nodes, labels, nums = [], [], []
for i, (num, nom) in enumerate(MONDES):
    cx = X0 + i * STEP
    delay = (i / 7.0) * CYCLE
    nodes.append(
        '<g class="nd" style="animation-delay:%.2fs">'
        '<rect x="%d" y="%d" width="26" height="26" rx="3"/></g>'
        % (delay, cx - 13, RAIL_Y - 13)
    )
    nums.append('<text class="num" x="%d" y="%d" text-anchor="middle">%s</text>'
                % (cx, RAIL_Y - 26, num))
    labels.append('<text class="nom" x="%d" y="%d" text-anchor="middle" '
                  'style="animation-delay:%.2fs">%s</text>'
                  % (cx, RAIL_Y + 44, delay, nom))

NODES = "\n  ".join(nodes)
NUMS = "\n  ".join(nums)
LABELS = "\n  ".join(labels)
MIDNIGHT_DELAY = (6 / 7.0) * CYCLE

SVG = u'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Les six mondes de Jack Bros. et l'échéance de minuit">
  <title>Les six mondes, traduits</title>
  <defs>
    <filter id="g3" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="railclip"><rect id="rc" x="{X0}" y="{RY}" width="0" height="4"/></clipPath>
    <pattern id="scan3" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#000" opacity="0.28"/>
    </pattern>
  </defs>

  <style>
    text {{ font-family: ui-monospace, "SFMono-Regular", "Consolas", "Liberation Mono", monospace; }}
    .num {{ fill: #8A0000; font-size: 12px; letter-spacing: 2px; }}
    .nom {{ fill: {RED_MID}; font-size: 11.5px; letter-spacing: .5px;
            animation: light {CYCLE}s linear infinite; }}
    .nd rect {{ fill: #140000; stroke: {RED_DIM}; stroke-width: 1.5; }}
    .nd {{ animation: nodeon {CYCLE}s linear infinite; }}
    @keyframes nodeon {{
      0%   {{ opacity: .45 }}
      2%   {{ opacity: 1 }}
      60%  {{ opacity: 1 }}
      100% {{ opacity: .45 }}
    }}
    @keyframes light {{
      0%   {{ fill: {RED_DIM} }}
      3%   {{ fill: {RED_HOT} }}
      60%  {{ fill: {RED_MID} }}
      100% {{ fill: {RED_DIM} }}
    }}
    #rc {{ animation: fill {CYCLE}s linear infinite; }}
    @keyframes fill {{ 0% {{ width: 0 }} 90% {{ width: {RAILW}px }} 100% {{ width: {RAILW}px }} }}
    .mid {{ animation: midon {CYCLE}s linear infinite; }}
    @keyframes midon {{ 0%,80% {{ opacity: .3 }} 88%,100% {{ opacity: 1 }} }}
    @media (prefers-reduced-motion: reduce) {{
      .nd,.nom,#rc,.mid {{ animation: none !important; }}
      .nom {{ fill: {RED_MID} }} #rc {{ width: {RAILW}px }} .mid {{ opacity: 1 }}
    }}
  </style>

  <rect width="{W}" height="{H}" fill="#000"/>

  <!-- rail : trace eteint, puis la portion parcourue -->
  <rect x="{X0}" y="{RY}" width="{RAILW}" height="4" rx="2" fill="#1A0000"/>
  <g clip-path="url(#railclip)">
    <rect x="{X0}" y="{RY}" width="{RAILW}" height="4" rx="2" fill="{RED}"/>
  </g>

  {NUMS}
  <g filter="url(#g3)">
    {NODES}
  </g>
  {LABELS}

  <!-- l'echeance : minuit -->
  <g class="mid" filter="url(#g3)">
    <rect x="{MX}" y="{MY}" width="26" height="26" rx="3" fill="#2A0000"
          stroke="{RED_HOT}" stroke-width="1.5"/>
    <circle cx="{MCX}" cy="{RAIL_Y}" r="3" fill="{RED_HOT}"/>
  </g>
  <text class="num" x="{MCX}" y="{NUMY}" text-anchor="middle" fill="{RED_HOT}">00:00</text>
  <text class="nom" x="{MCX}" y="{LABY}" text-anchor="middle" fill="{RED_HOT}"
        style="animation:none">MINUIT</text>

  <rect width="{W}" height="{H}" fill="url(#scan3)"/>
</svg>
'''.format(W=W, H=H, X0=X0, RY=RAIL_Y - 2, RAILW=END_X - X0, RAIL_Y=RAIL_Y,
           RED=RED, RED_DIM=RED_DIM, RED_MID=RED_MID, RED_HOT=RED_HOT,
           CYCLE=CYCLE, NODES=NODES, NUMS=NUMS, LABELS=LABELS,
           MX=END_X - 13, MY=RAIL_Y - 13, MCX=END_X,
           NUMY=RAIL_Y - 26, LABY=RAIL_Y + 44)

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(SVG)
print("ecrit: %s | %d octets | %d mondes" % (OUT, len(SVG), len(MONDES)))
