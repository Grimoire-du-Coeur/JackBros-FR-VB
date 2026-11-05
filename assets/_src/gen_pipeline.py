# -*- coding: utf-8 -*-
"""Schema anime du patch : ROM d'origine + .xdelta -> ROM francaise.

Animations 100 % CSS (offset-path pour les paquets, width pour la barre) :
verifiable au rendu, et c'est ce qui passe le mieux quand GitHub sert le SVG
via <img>.
"""
import sys
import io

OUT = sys.argv[1]
W, H = 1000, 268
RED_DIM, RED_MID, RED, RED_HOT = "#5E0000", "#9E0000", "#D40000", "#FF3B2F"

PATH_A = "M320 70 C 404 70, 420 130, 464 130"
PATH_B = "M320 190 C 404 190, 420 130, 464 130"
PATH_C = "M536 130 L 666 130"


def packets(path_d, count, dur, base_delay):
    """Petits paquets qui glissent le long d'un cable, via offset-path."""
    out = []
    for i in range(count):
        delay = base_delay + i * (dur / count)
        out.append(
            '<rect class="pk" x="-3.5" y="-3.5" width="7" height="7" rx="1" '
            'style="offset-path:path(\'%s\');animation-duration:%.2fs;'
            'animation-delay:%.2fs"/>' % (path_d, dur, delay)
        )
    return "\n  ".join(out)


def box(x, y, w, h, cls=""):
    return ('<rect class="box %s" x="%d" y="%d" width="%d" height="%d" rx="6"/>'
            % (cls, x, y, w, h))


SVG = u'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Schéma : votre ROM américaine plus le patch xdelta donnent la ROM française">
  <title>Comment le patch est appliqué</title>
  <defs>
    <marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
            orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" fill="{RED_MID}"/>
    </marker>
    <filter id="g2" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <pattern id="scan2" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#000" opacity="0.30"/>
    </pattern>
  </defs>

  <style>
    text {{ font-family: ui-monospace, "SFMono-Regular", "Consolas", "Liberation Mono", monospace; }}
    .box {{ fill: #0B0000; stroke: {RED_DIM}; stroke-width: 1.5; }}
    .box.out {{ stroke: {RED}; }}
    .t1 {{ fill: {RED}; font-size: 17px; }}
    .t2 {{ fill: {RED_MID}; font-size: 12.5px; }}
    .tag {{ fill: #8A0000; font-size: 11px; letter-spacing: 2.5px; }}
    .wire {{ fill: none; stroke: {RED_DIM}; stroke-width: 1.5; }}
    .node {{ fill: #140000; stroke: {RED}; stroke-width: 1.5; }}

    .pk {{ fill: {RED_HOT}; transform-box: fill-box; transform-origin: center;
           offset-rotate: 0deg;
           animation-name: flow; animation-timing-function: linear;
           animation-iteration-count: infinite; }}
    @keyframes flow {{
      0%   {{ offset-distance: 0%;   opacity: 0 }}
      12%  {{ opacity: 1 }}
      85%  {{ opacity: 1 }}
      100% {{ offset-distance: 100%; opacity: 0 }}
    }}
    .ring {{ transform-origin: 500px 130px; animation: spin 9s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg) }} }}
    .core {{ animation: corepulse 2.6s ease-in-out infinite; }}
    @keyframes corepulse {{ 0%,100% {{ opacity: .35 }} 50% {{ opacity: 1 }} }}
    .fill {{ animation: load 6s linear infinite; }}
    @keyframes load {{
      0% {{ width: 0 }} 45% {{ width: 258px }} 92% {{ width: 258px }} 100% {{ width: 0 }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .pk {{ animation: none !important; opacity: 0 }}
      .ring,.core {{ animation: none !important; }}
      .fill {{ animation: none !important; width: 258px }}
    }}
  </style>

  <rect width="{W}" height="{H}" fill="#000"/>

  <!-- entrée 1 : la ROM de l'utilisateur -->
  {BOX_A}
  <text class="tag" x="46" y="22">ENTRÉE 1 &#183; À VOUS</text>
  <text class="t1"  x="46" y="62">Jack Bros. (USA).vb</text>
  <text class="t2"  x="46" y="86">1 048 576 o &#183; CRC32 A44DE03C</text>

  <!-- entrée 2 : le patch -->
  {BOX_B}
  <text class="tag" x="46" y="142">ENTRÉE 2 &#183; RELEASES</text>
  <text class="t1"  x="46" y="182">[T-Fr v1.0].xdelta</text>
  <text class="t2"  x="46" y="206">que les différences, zéro code du jeu</text>

  <!-- câblage + paquets -->
  <path class="wire" d="{PATH_A}"/>
  <path class="wire" d="{PATH_B}"/>
  <path class="wire" d="{PATH_C}" marker-end="url(#head)"/>
  {PK_A}
  {PK_B}
  {PK_C}

  <!-- nœud xdelta3 -->
  <g filter="url(#g2)">
    <circle class="node" cx="500" cy="130" r="36"/>
    <g class="ring">
      <circle cx="500" cy="130" r="27" fill="none" stroke="{RED}" stroke-width="1.5"
              stroke-dasharray="7 11" opacity="0.85"/>
    </g>
    <circle class="core" cx="500" cy="130" r="6" fill="{RED_HOT}"/>
  </g>
  <text class="tag" x="500" y="78" text-anchor="middle">XDELTA3 &#183; WASM</text>
  <text class="t2"  x="500" y="200" text-anchor="middle">dans votre navigateur</text>
  <text class="t2"  x="500" y="218" text-anchor="middle">hors ligne, rien n'est envoyé</text>

  <!-- sortie -->
  {BOX_C}
  <text class="tag" x="696" y="76">SORTIE</text>
  <text class="t1"  x="696" y="116">Jack Bros (Fr).vb</text>
  <text class="t2"  x="696" y="140">prêt pour émulateur ou flashcart</text>
  <rect x="696" y="156" width="258" height="5" rx="2.5" fill="#1A0000"/>
  <rect class="fill" x="696" y="156" width="0" height="5" rx="2.5" fill="{RED}"/>

  <rect width="{W}" height="{H}" fill="url(#scan2)"/>
</svg>
'''.format(W=W, H=H, RED=RED, RED_DIM=RED_DIM, RED_MID=RED_MID, RED_HOT=RED_HOT,
           PATH_A=PATH_A, PATH_B=PATH_B, PATH_C=PATH_C,
           BOX_A=box(30, 32, 290, 72), BOX_B=box(30, 152, 290, 72),
           BOX_C=box(680, 86, 290, 88, "out"),
           PK_A=packets(PATH_A, 3, 2.6, 0.0),
           PK_B=packets(PATH_B, 3, 2.6, 0.45),
           PK_C=packets(PATH_C, 2, 1.9, 1.1))

with io.open(OUT, 'w', encoding='utf-8') as f:
    f.write(SVG)
print("ecrit: %s | %d octets" % (OUT, len(SVG)))
