# Documentation Technique - Jack Bros. (Virtual Boy)

Notes de romhacking et détails techniques sur la ROM américaine de **Jack Bros.** (Virtual Boy, 1995, Atlus).

<br/>

---

## 1. Informations sur la ROM

- **Plateforme** : Nintendo Virtual Boy
- **Processeur** : NEC V810 (32 bits RISC)
- **Taille de la ROM** : 1 048 576 octets (1 Mo)
- **Format interne** : Données en Little-Endian

<br/>

---

## 2. Le système de texte

Le jeu utilise deux polices distinctes avec leurs propres règles d'affichage.

<br/>

### Police 1 (Dialogues en jeu et astuces)

- Utilisée pour les boîtes de dialogue des fées et les conseils dans les labyrinthes.
- Largeur maximale conseillée : **14 caractères par ligne**.
- Particularité : la cartouche d'origine **ne possède pas de tiret `-`** dans cette police.  
  Le code hexadécimal `0x3E` correspond au caractère `#` et `0x3F` correspond à `&`. Utiliser un tiret dans un mot (comme `Bats-le`) affichait donc un dièse à l'écran (`Bats#le`). Dans la traduction, les tirets sont remplacés par un espace propre.

<br/>

### Police 2 (Cinématiques et menus)

- Utilisée pour l'écran-titre, l'introduction d'Halloween et les fins de mondes.
- Largeur maximale : **26 à 28 caractères par ligne**, 4 lignes maximum par page.
- Le tiret est disponible ici à l'octet `0x3F`.

<br/>

### Balises de contrôle

- `\n` (`0x05`) : retour à la ligne.
- `<PAGE>` (`0x06`) : saut de page (attend l'appui sur une touche du joueur pour continuer).
- `<END>` (`0x02`) : fin de la réplique (indique au jeu d'arrêter la lecture).
- `0x00` : espace et octet de remplissage (padding).

<br/>

### Taille des répliques (slots)

Il y a 142 entrées textuelles identifiées dans le fichier `traduction/JackBros_FR.json`.  
Chaque texte est stocké à un emplacement mémoire précis avec une taille maximale allouée (`slot_size`). La traduction ne doit jamais dépasser cette taille pour éviter d'écraser les données voisines dans la cartouche.

<br/>

### Emplacements partagés : le piège des pages

**48 des 142 répliques se chevauchent volontairement.** Le jeu possède deux pointeurs vers la même zone : un vers le dialogue complet, un second vers l'une de ses pages, au beau milieu du même texte.

Prenons l'astuce de la Zone Sombre :

| Entrée | Offset | Taille | Contenu |
|---|---|---|---|
| 55 | 525900 | 121 | `Vois tu le sol cache...<PAGE>C'est la Zone Sombre...<PAGE>Des ennemis...` |
| 56 | 525944 | 77 | `C'est la Zone Sombre...<PAGE>Des ennemis...` |

L'entrée 56 n'est pas un doublon : c'est le pointeur du jeu vers la **deuxième page** de l'entrée 55, à 44 octets de son début. Les deux se terminent au même endroit.

La conséquence est piégeuse. Si la page 1 française n'occupe pas exactement le même nombre d'octets que l'anglaise, la frontière de page se décale, le second pointeur tombe au milieu d'un mot, et le joueur voit un fragment en double à l'écran — alors que chaque réplique, prise isolément, tient parfaitement dans son emplacement.

Une page traduite doit donc respecter **deux** contraintes : ne pas dépasser `slot_size`, et conserver la longueur exacte de la page d'origine quand une autre entrée pointe au milieu.

`python tool/verifier_traduction.py` contrôle les deux et indique, le cas échéant, de combien d'octets rallonger la page fautive.

<br/>

### Outils de contrôle

| Commande | Rôle |
|---|---|
| `python tool/verifier_traduction.py` | Valide la traduction : encodage, tailles, zones partagées |
| `python tool/test_core_engine.py` | Teste le moteur : tables, aller-retour, refus des cas invalides |

Aucune ROM ni dépendance externe n'est nécessaire pour les exécuter.

<br/>

---

## 3. Remarque sur les graphismes du HUD

Les éléments du HUD en jeu (`FLOOR`, `AUTOSHOT`, jauges et chronomètre) sont stockés sous forme de tuiles 2bpp (format Virtual Boy, 16 octets par tuile 8x8). 

Ces tuiles sont réutilisées et combinées dynamiquement par le moteur graphique en cours de partie. Modifier directement les octets de ces tuiles dans la ROM sans réadapter l'ensemble de la table d'assemblage provoquait du bruit visuel en jeu. Nous avons donc fait le choix de préserver les graphismes d'origine intacts pour assurer une stabilité parfaite à 100%.

<br/>

---

## 4. Fonctionnement du Tool

Le dossier `tool/` contient un petit serveur local en Python :

1. Il lit la ROM américaine d'origine `Jack Bros. (USA).vb`.
2. Il charge les textes traduits depuis `traduction/JackBros_FR.json`.
3. Il convertit les caractères selon la table appropriée (Police 1 ou Police 2).
4. Il vérifie que chaque phrase rentre bien dans son slot mémoire.
5. Il écrit la ROM traduite finale `Jack Bros (Fr).vb`.
