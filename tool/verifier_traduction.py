# -*- coding: utf-8 -*-
"""
Vérificateur de la traduction, sans ROM ni dépendance.

    python tool/verifier_traduction.py

Contrôle trois choses sur traduction/JackBros_FR.json :

  1. chaque réplique s'encode (aucun caractère absent de la police) ;
  2. chaque réplique tient dans son emplacement ;
  3. les emplacements qui se chevauchent restent cohérents.

Le point 3 mérite une explication. Plusieurs répliques partagent la même
zone de la cartouche : le jeu possède un pointeur vers le dialogue complet
et un second pointeur vers sa page suivante, au milieu du même texte. Tant
que la traduction garde la même longueur de page que l'anglais, les deux
écritures coïncident. Si la page française est plus courte, le second
pointeur tombe au milieu d'un mot et le joueur voit un fragment dupliqué.

Le même contrôle est passé sur les textes anglais d'origine, pour ne
signaler que ce que la traduction a réellement introduit.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# La console Windows n'est pas en UTF-8 par défaut : sans cela, les accents
# de ce rapport sortent en charabia.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

from core_engine import ErreurEncodage, encoder_texte  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADUCTION = os.path.join(RACINE, 'traduction', 'JackBros_FR.json')
TAILLE_ROM = 1024 * 1024


def construire(entrees, champ):
    """Écrit toutes les répliques dans une ROM vierge, dans l'ordre du
    fichier, et note qui a écrit chaque octet."""
    rom = bytearray(TAILLE_ROM)
    auteur = {}
    for e in entrees:
        octets = encoder_texte(e[champ], e['font'], e.get('id'))
        for j in range(e['slot_size']):
            valeur = octets[j] if j < len(octets) else 0x00
            rom[e['offset'] + j] = valeur
            auteur[e['offset'] + j] = e['id']
    return rom


def debuts_de_page(texte, font, id_entree):
    """Position, en octets, du début de chaque page d'une réplique."""
    debuts = [0]
    position = 0
    i = 0
    while i < len(texte):
        if texte[i:i + 6] == '<PAGE>':
            position += 1
            i += 6
            debuts.append(position)
            continue
        if texte[i:i + 5] == '<END>':
            position += 1
            i += 5
            continue
        if texte[i:i + 2] == '\\n':
            position += 1
            i += 2
            continue
        position += 1
        i += 1
    return debuts


def incoherences(entrees, champ):
    """Répliques dont les octets finaux en ROM ne sont plus ceux qu'elles
    demandaient, parce qu'une voisine a écrit par-dessus."""
    rom = construire(entrees, champ)
    touchees = {}
    for e in entrees:
        voulu = encoder_texte(e[champ], e['font'], e.get('id'))
        if len(voulu) > e['slot_size']:
            # texte_orig est une transcription lisible, pas une copie octet
            # pour octet : certaines répliques anglaises n'y tiennent pas.
            # Le contrôle [1] s'occupe des dépassements réels.
            continue
        # Seuls comptent les octets jusqu'à la balise de fin incluse : le jeu
        # s'arrête là. Qu'une réplique voisine occupe le remplissage qui suit
        # est normal et sans effet.
        utile = voulu.find(b'\x02') + 1 or len(voulu)
        reel = bytes(rom[e['offset']:e['offset'] + utile])
        if reel != voulu[:utile]:
            touchees[e['id']] = next(i for i in range(utile)
                                     if voulu[i] != reel[i])
    return touchees


def main():
    with open(TRADUCTION, 'r', encoding='utf-8') as f:
        entrees = json.load(f)

    problemes = 0
    print('%d répliques dans %s\n' % (len(entrees), os.path.basename(TRADUCTION)))

    # ---- 1 et 2 : encodage et taille -------------------------------------
    print('[1] Encodage et tailles')
    for e in entrees:
        try:
            octets = encoder_texte(e['texte_fr'], e['font'], e['id'])
        except ErreurEncodage as exc:
            print('  ERREUR id %-4s %s' % (e['id'], exc))
            problemes += 1
            continue
        if len(octets) > e['slot_size']:
            print('  ERREUR id %-4s dépasse de %d octet(s) (%d > %d)'
                  % (e['id'], len(octets) - e['slot_size'], len(octets),
                     e['slot_size']))
            problemes += 1
    if not problemes:
        print('  ok   les %d répliques s\'encodent et tiennent dans leur '
              'emplacement' % len(entrees))

    # ---- 3 : chevauchements ----------------------------------------------
    print('\n[2] Chevauchements d\'emplacements')
    par_id = {e['id']: e for e in entrees}
    base = incoherences(entrees, 'texte_orig')
    actuel = incoherences(entrees, 'texte_fr')
    regressions = sorted(set(actuel) - set(base))
    preexistantes = sorted(set(actuel) & set(base))

    if preexistantes:
        print('  info %d réplique(s) déjà dans ce cas en anglais, donc '
              'inhérentes à la cartouche : %s'
              % (len(preexistantes), ', '.join('id %s' % i for i in preexistantes)))

    if not regressions:
        print('  ok   la traduction n\'introduit aucun chevauchement incohérent')
    for id_ in regressions:
        e = par_id[id_]
        rupture = actuel[id_]
        # quelle réplique partage cette zone, et à partir de quel octet ?
        voisins = [v for v in entrees
                   if v['id'] != id_
                   and v['offset'] < e['offset'] + e['slot_size']
                   and e['offset'] < v['offset'] + v['slot_size']]
        print('\n  ERREUR id %s : le texte français est tronqué en ROM à '
              'partir de l\'octet %d' % (id_, rupture))
        taille = len(encoder_texte(e['texte_fr'], e['font'], id_))
        for v in voisins:
            debut = v['offset'] - e['offset']
            if not 0 <= debut < taille:
                continue
            print('        la réplique id %s est écrite à l\'octet %d de '
                  'celle-ci' % (v['id'], debut))
            frontieres = debuts_de_page(e['texte_fr'], e['font'], id_)
            proche = min(frontieres, key=lambda p: abs(p - debut))
            numero = frontieres.index(proche) + 1
            print('        or sa page %d commence à l\'octet %d'
                  % (numero, proche))
            print('        => il faut rallonger de %d octet(s) ce qui précède '
                  'la page %d' % (debut - proche, numero))
        print('        conséquence en jeu : au passage de page, un fragment '
              'du texte s\'affiche en double.')
        problemes += 1

    print('\n' + '-' * 62)
    if problemes:
        print('%d problème(s). La ROM peut être compilée, mais ces textes '
              's\'afficheront mal.' % problemes)
        return 1
    print('Traduction valide.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
