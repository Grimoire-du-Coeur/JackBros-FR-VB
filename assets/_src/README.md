# Sources des visuels

Les SVG animés du README sont générés, pas écrits à la main : le bandeau
contient à lui seul 129 pixels de titre et 697 segments de labyrinthe.

Pour les régénérer depuis la racine du dépôt :

```sh
python assets/_src/gen_banner.py   assets/banner.svg
python assets/_src/gen_pipeline.py assets/pipeline.svg
python assets/_src/gen_mondes.py   assets/mondes.svg
```

Aucune dépendance : bibliothèque standard uniquement.

Le labyrinthe du bandeau est tiré d'un parcours en profondeur à graine fixe
(1995), donc le rendu est reproductible. Les animations sont en CSS et non en
SMIL, et les polices sont des familles génériques : GitHub sert ces fichiers
via `<img>`, ce qui bloque toute ressource externe.
