# -*- coding: utf-8 -*-
"""
Jack Bros (Virtual Boy) - Moteur de romhacking et d'encodage texte
Dédié à la ROM américaine officielle (1995, Atlus)

La cartouche utilise deux polices en tuiles, chacune avec sa propre table de
caractères. Elles sont définies une seule fois ci-dessous et servent aussi bien
à l'encodage (texte -> ROM) qu'à l'extraction (ROM -> texte), ce qui évite que
les deux sens divergent.

Voir DOCUMENTATION.md pour le détail des polices et des balises de contrôle.
"""

import json
import os

# --------------------------------------------------------------------------
# Balises de contrôle, communes aux deux polices
# --------------------------------------------------------------------------
CTRL_END = 0x02       # fin de réplique
CTRL_NEWLINE = 0x05   # retour à la ligne
CTRL_PAGE = 0x06      # saut de page (attend une touche)
PADDING = 0x00        # espace, et octet de remplissage


def _table(ponctuation, decalage_minuscules):
    """Construit une table caractère -> octet pour une police."""
    t = dict(ponctuation)
    for c in range(ord('A'), ord('Z') + 1):
        t[chr(c)] = c - 39
    for c in range(ord('a'), ord('z') + 1):
        t[chr(c)] = c - decalage_minuscules
    for c in range(ord('0'), ord('9') + 1):
        t[chr(c)] = c - 32
    t[' '] = PADDING
    t['\n'] = CTRL_NEWLINE
    return t


# Police 1 : dialogues des fées et astuces en donjon (14 caractères par ligne).
# Attention : cette police n'a pas de tiret. L'octet 0x3E affiche un « # », ce
# qui transformait « Bats-le » en « Bats#le ». Le tiret est donc encodé comme
# une espace (voir DOCUMENTATION.md).
TABLE_F1 = _table({
    '!': 0x34, '.': 0x75, ',': 0x74, "'": 0x7A, '=': 0x4F, '?': 0x7B,
    ':': 0x37, '[': 0x78, ']': 0x79, '(': 0x39, ')': 0x3A,
    '-': PADDING,
}, decalage_minuscules=7)

# Police 2 : écran-titre, cinématiques et fins de mondes (26 à 28 caractères
# par ligne). Ici le tiret existe bien, à l'octet 0x3F.
TABLE_F2 = _table({
    '.': 0x40, ',': 0x3E, "'": 0x45, ':': 0x41, '?': 0x42, '!': 0x34,
    '-': 0x3F,
}, decalage_minuscules=1)


def table_pour(font):
    return TABLE_F2 if font == 2 else TABLE_F1


def _table_inverse(table):
    """Octet -> caractère. En cas de collision, l'espace l'emporte : en
    police 1, ' ' et '-' valent tous deux 0x00, et c'est l'espace qui est la
    lecture correcte d'un octet de remplissage."""
    inv = {}
    for caractere, octet in table.items():
        if octet in inv and caractere == '-':
            continue
        if octet == PADDING:
            inv[octet] = ' '
        else:
            inv[octet] = caractere
    return inv


INVERSE_F1 = _table_inverse(TABLE_F1)
INVERSE_F2 = _table_inverse(TABLE_F2)


class ErreurEncodage(ValueError):
    """Le texte ne peut pas être écrit dans la cartouche tel quel."""


# --------------------------------------------------------------------------
# Texte -> octets
# --------------------------------------------------------------------------
def encoder_texte(texte, font, id_entree=None):
    """Encode une réplique. Lève ErreurEncodage sur un caractère absent de la
    police, plutôt que de le remplacer silencieusement par une espace."""
    table = table_pour(font)
    out = bytearray()
    i = 0
    while i < len(texte):
        if texte[i:i + 5] == '<END>':
            out.append(CTRL_END)
            i += 5
            continue
        if texte[i:i + 6] == '<PAGE>':
            out.append(CTRL_PAGE)
            i += 6
            continue
        if texte[i:i + 2] == '\\n':          # retour à la ligne écrit « \n »
            out.append(CTRL_NEWLINE)
            i += 2
            continue

        c = texte[i]
        if c not in table:
            ou = '' if id_entree is None else ' (texte id %s)' % id_entree
            raise ErreurEncodage(
                "Caractère %r absent de la police %d%s. La cartouche n'a ni "
                "accents ni symboles hors de sa table : voir DOCUMENTATION.md."
                % (c, font, ou))
        out.append(table[c])
        i += 1
    return bytes(out)


# --------------------------------------------------------------------------
# Octets -> texte
# --------------------------------------------------------------------------
def decoder_slot(rom_bytes, offset, slot_size, font):
    """Relit une réplique dans la ROM. S'arrête à la balise de fin ; sinon,
    lit tout le slot et retire le remplissage de fin."""
    inverse = INVERSE_F2 if font == 2 else INVERSE_F1
    out = []
    fin_trouvee = False
    for octet in rom_bytes[offset:offset + slot_size]:
        if octet == CTRL_END:
            out.append('<END>')
            fin_trouvee = True
            break
        if octet == CTRL_PAGE:
            out.append('<PAGE>')
        elif octet == CTRL_NEWLINE:
            out.append('\n')
        else:
            # Un octet absent de la police est rendu tel quel plutôt que
            # deviné : « \x7F » saute aux yeux, un « ? » inventé non.
            out.append(inverse.get(octet) or '\\x%02X' % octet)
    texte = ''.join(out)
    if not fin_trouvee:
        texte = texte.rstrip(' ')
    return texte


# --------------------------------------------------------------------------
# Extraction : lit réellement la ROM
# --------------------------------------------------------------------------
def extract_all_text(rom_path, out_json_path, logger=None):
    """Relit les 142 répliques directement dans la ROM fournie et les écrit
    dans out_json_path.

    Les emplacements (offset, slot_size, font) proviennent du fichier de
    référence traduction/JackBros_FR.json : c'est la cartographie de la
    cartouche, établie par rétro-ingénierie. Le texte, lui, est bien relu
    octet par octet dans la ROM passée en argument.
    """
    with open(rom_path, 'rb') as f:
        rom = f.read()

    reference = os.path.join(os.path.dirname(__file__), '..', 'traduction',
                             'JackBros_FR.json')
    if not os.path.exists(reference):
        reference = os.path.join(os.path.dirname(__file__), 'traduction',
                                 'JackBros_FR.json')
    if not os.path.exists(reference):
        raise FileNotFoundError(
            "Cartographie introuvable : traduction/JackBros_FR.json est "
            "nécessaire pour savoir où lire dans la ROM.")

    with open(reference, 'r', encoding='utf-8') as f:
        entrees = json.load(f)

    if logger:
        logger('Lecture de %d emplacements dans %s...'
               % (len(entrees), os.path.basename(rom_path)), 'info')

    hors_limites = 0
    resultat = []
    for e in entrees:
        fin = e['offset'] + e['slot_size']
        if fin > len(rom):
            hors_limites += 1
            lu = ''
        else:
            lu = decoder_slot(rom, e['offset'], e['slot_size'], e['font'])
        resultat.append({
            'id': e['id'],
            'offset': e['offset'],
            'slot_size': e['slot_size'],
            'font': e['font'],
            'texte_orig': lu,
            'texte_fr': e.get('texte_fr') or lu,
        })

    if hors_limites and logger:
        logger('%d emplacements dépassent la taille de ce fichier : est-ce '
               'bien une ROM Virtual Boy de 1 Mio ?' % hors_limites, 'warn')

    with open(out_json_path, 'w', encoding='utf-8') as f:
        json.dump(resultat, f, indent=4, ensure_ascii=False)

    if logger:
        logger('[OK] %d répliques extraites dans %s'
               % (len(resultat), os.path.basename(out_json_path)), 'success')
    return len(resultat)


# --------------------------------------------------------------------------
# Réinjection
# --------------------------------------------------------------------------
def encode_and_insert_text(rom_bytes, json_path, logger=None):
    """Réinjecte les textes traduits dans la ROM.

    Échoue franchement si une réplique ne tient pas dans son emplacement :
    une ROM tronquée en silence produit des dialogues coupés en jeu, bien plus
    difficiles à diagnostiquer qu'une erreur ici.
    """
    rom = bytearray(rom_bytes)
    with open(json_path, 'r', encoding='utf-8') as f:
        entrees = json.load(f)

    if logger:
        logger('Encodage de %d répliques...' % len(entrees), 'info')

    for e in entrees:
        offset = e['offset']
        slot_size = e['slot_size']
        texte = e.get('texte_fr') or e.get('texte_orig') or ''

        encode = encoder_texte(texte, e['font'], e.get('id'))

        if len(encode) > slot_size:
            raise ErreurEncodage(
                "Le texte id %s ne tient pas : %d octets pour un emplacement "
                "de %d. Raccourcissez-le de %d caractère(s).\n  %r"
                % (e.get('id'), len(encode), slot_size,
                   len(encode) - slot_size, texte))

        if offset + slot_size > len(rom):
            raise ErreurEncodage(
                "Le texte id %s pointe en dehors de la ROM (offset %d, taille "
                "%d, ROM de %d octets). Vérifiez que la ROM est la bonne."
                % (e.get('id'), offset, slot_size, len(rom)))

        rom[offset:offset + len(encode)] = encode
        for j in range(len(encode), slot_size):
            rom[offset + j] = PADDING

    if logger:
        logger('[OK] Les %d répliques ont été réinjectées.' % len(entrees),
               'success')
    return bytes(rom)
