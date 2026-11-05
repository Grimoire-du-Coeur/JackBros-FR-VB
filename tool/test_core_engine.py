# -*- coding: utf-8 -*-
"""
Tests du moteur d'encodage, sans dépendance externe et sans ROM.

    python tool/test_core_engine.py

Une ROM synthétique remplie de zéros suffit : ce qu'on vérifie, c'est que
réinjecter puis relire redonne bien le texte de départ, et que le moteur
refuse franchement ce qui ne rentre pas.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# La console Windows n'est pas en UTF-8 par défaut.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

from core_engine import (  # noqa: E402
    ErreurEncodage, TABLE_F1, TABLE_F2, decoder_slot, encode_and_insert_text,
    encoder_texte, extract_all_text, table_pour,
)

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADUCTION = os.path.join(RACINE, 'traduction', 'JackBros_FR.json')
TAILLE_ROM = 1024 * 1024

echecs = []


def verifie(condition, message):
    if condition:
        print('  ok   %s' % message)
    else:
        print('  ECHEC %s' % message)
        echecs.append(message)


def attendu_apres_aller_retour(texte, font):
    """Le texte tel qu'on peut espérer le relire. L'encodage est volontairement
    destructeur sur deux points : en police 1 le tiret devient une espace,
    faute de glyphe dans la cartouche ; et sans balise de fin, le remplissage
    final ne se distingue plus d'espaces réels."""
    if font == 1:
        texte = texte.replace('-', ' ')
    texte = texte.replace('\\n', '\n')
    if '<END>' not in texte:
        texte = texte.rstrip(' ')
    return texte


def sans_chevauchement(entrees):
    """Les répliques dont l'emplacement n'est partagé avec aucune autre.

    Plusieurs répliques se chevauchent volontairement : le jeu possède un
    pointeur vers un dialogue complet et un second vers l'une de ses pages,
    au milieu du même texte. Un aller-retour n'a donc de sens que sur les
    emplacements exclusifs. La cohérence des zones partagées est vérifiée
    par tool/verifier_traduction.py.
    """
    seules = []
    for e in entrees:
        fin = e['offset'] + e['slot_size']
        partage = any(v is not e
                      and v['offset'] < fin
                      and e['offset'] < v['offset'] + v['slot_size']
                      for v in entrees)
        if not partage:
            seules.append(e)
    return seules


def charge_entrees():
    with open(TRADUCTION, 'r', encoding='utf-8') as f:
        return json.load(f)


# --------------------------------------------------------------------------
print('\n[1] Les tables de caractères sont sans collision')
for nom, table in (('police 1', TABLE_F1), ('police 2', TABLE_F2)):
    octets = {}
    collisions = []
    for caractere, octet in table.items():
        if octet in octets and {caractere, octets[octet]} != {' ', '-'}:
            collisions.append((octet, octets[octet], caractere))
        octets.setdefault(octet, caractere)
    verifie(not collisions,
            '%s : aucun octet partagé par deux caractères distincts (%r)'
            % (nom, collisions))

# --------------------------------------------------------------------------
print("\n[2] Aller-retour sur les 142 répliques du jeu")
entrees = charge_entrees()
rom = bytearray(TAILLE_ROM)
patchee = encode_and_insert_text(bytes(rom), TRADUCTION)
verifie(len(patchee) == TAILLE_ROM,
        'la ROM garde sa taille : %d octets' % len(patchee))

exclusives = sans_chevauchement(entrees)
divergences = []
for e in exclusives:
    relu = decoder_slot(patchee, e['offset'], e['slot_size'], e['font'])
    attendu = attendu_apres_aller_retour(e['texte_fr'], e['font'])
    if relu != attendu:
        divergences.append((e['id'], attendu, relu))
verifie(not divergences,
        'les %d répliques à emplacement exclusif se relisent à l\'identique'
        % len(exclusives))
for id_, attendu, relu in divergences[:5]:
    print('       id=%s\n         attendu %r\n         relu    %r'
          % (id_, attendu, relu))
partagees = [e for e in entrees if e not in exclusives]
verifie(len(exclusives) + len(partagees) == len(entrees),
        'aucune réplique n\'échappe aux contrôles : %d exclusives + %d en '
        'zone partagée = %d' % (len(exclusives), len(partagees), len(entrees)))

# --------------------------------------------------------------------------
print('\n[3] Les zones partagées sont surveillées')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verifier_traduction import incoherences  # noqa: E402

# une réplique volontairement raccourcie doit être détectée comme décalée
sabotage = [dict(e) for e in entrees]
cible = next(e for e in sabotage if e['id'] == 56)
jumelle = next(e for e in sabotage if e['id'] == 55)
jumelle['texte_fr'] = jumelle['texte_fr'].replace(' Vois tu le', ' Vois le', 1)
detecte = incoherences(sabotage, 'texte_fr')
verifie(55 in detecte,
        'raccourcir une page décale la zone partagée, et c\'est détecté')
verifie(cible['id'] == 56, 'la réplique jumelle id 56 existe bien')

# --------------------------------------------------------------------------
print('\n[4] Un caractère hors police est refusé, pas avalé')
for font, mauvais in ((1, 'é'), (2, 'à'), (1, '#'), (2, '('), (1, '€')):
    try:
        encoder_texte('Test%s<END>' % mauvais, font)
        verifie(False, 'police %d : %r aurait dû être refusé' % (font, mauvais))
    except ErreurEncodage as exc:
        verifie(repr(mauvais) in str(exc) or mauvais in str(exc),
                'police %d : %r refusé, et l\'erreur le nomme' % (font, mauvais))

verifie('-' in table_pour(1) and table_pour(1)['-'] == 0x00,
        'police 1 : le tiret est bien encodé comme une espace (bug du dièse)')
verifie(table_pour(2)['-'] == 0x3F,
        'police 2 : le tiret existe, à l\'octet 0x3F')

# --------------------------------------------------------------------------
print("\n[5] Un texte trop long fait échouer la compilation")
trop_long = [{
    'id': 999, 'offset': 0, 'slot_size': 4, 'font': 1,
    'texte_orig': '', 'texte_fr': 'BEAUCOUP TROP LONG<END>',
}]
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False,
                                 encoding='utf-8') as f:
    json.dump(trop_long, f)
    chemin = f.name
try:
    encode_and_insert_text(bytes(TAILLE_ROM), chemin)
    verifie(False, 'un dépassement de slot aurait dû lever une erreur')
except ErreurEncodage as exc:
    verifie('999' in str(exc) and 'tient pas' in str(exc),
            'dépassement refusé, l\'erreur nomme le texte fautif')
finally:
    os.unlink(chemin)

# --------------------------------------------------------------------------
print("\n[6] L'extraction lit vraiment la ROM")
with tempfile.NamedTemporaryFile(suffix='.vb', delete=False) as f:
    f.write(patchee)
    rom_tmp = f.name
with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
    json_tmp = f.name
try:
    nb = extract_all_text(rom_tmp, json_tmp)
    with open(json_tmp, 'r', encoding='utf-8') as f:
        extrait = json.load(f)
    verifie(nb == len(entrees), '%d répliques extraites' % nb)

    attendu_14 = attendu_apres_aller_retour(
        next(e['texte_fr'] for e in entrees if e['id'] == 14), 1)
    lu_14 = next(e['texte_orig'] for e in extrait if e['id'] == 14)
    verifie(lu_14 == attendu_14,
            'le monde 1 est relu depuis la ROM : %r' % lu_14)

    # une ROM différente doit donner une extraction différente : c'est la
    # preuve que la fonction lit les octets au lieu de recopier le JSON
    autre = bytearray(patchee)
    e14 = next(e for e in entrees if e['id'] == 14)
    autre[e14['offset']:e14['offset'] + 6] = encoder_texte('ZZZZZZ', 1)
    with open(rom_tmp, 'wb') as f:
        f.write(bytes(autre))
    extract_all_text(rom_tmp, json_tmp)
    with open(json_tmp, 'r', encoding='utf-8') as f:
        extrait2 = json.load(f)
    lu2 = next(e['texte_orig'] for e in extrait2 if e['id'] == 14)
    verifie(lu2.startswith('ZZZZZZ'),
            'modifier la ROM change l\'extraction : %r' % lu2)
finally:
    os.unlink(rom_tmp)
    os.unlink(json_tmp)

# --------------------------------------------------------------------------
print('\n' + '-' * 62)
if echecs:
    print('%d test(s) en échec :' % len(echecs))
    for m in echecs:
        print('  - %s' % m)
    sys.exit(1)
print('Tous les tests passent.')
