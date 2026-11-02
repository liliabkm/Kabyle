# Catalogue de données : mots et photographies

Le catalogue courant contient **61 graphies lexicales kabyles distinctes**, regroupant les traductions/variantes françaises présentes dans les fichiers source, et **30 photographies** indépendantes. Il ne contient pas 61 leçons publiées, ni 30 paires mot–photo validées. Il n’inclut aucun audio. Les termes et variantes viennent de la source ; aucun mot kabyle ou tifinagh n’a été généré.

| Source | Révision auditée | Ressource retenue | Licence / décision |
|---|---|---|---|
| [LibreLingo-KAB-from-FR](https://github.com/LibreLingo/LibreLingo-KAB-from-FR) | `e426e0fa052da1c91b6efd800d8469e6940757d5` | Sections `New words` des modules hors juniors et fichier test. Regroupement par graphie latine sans réécrire les traductions ; synonymes et références conservés. | Le LICENSE racine dit **CC BY-NC-SA 4.0**, `course/course.yaml` dit **CC BY-SA 4.0**. Divergence signalée, pas d’autorisation commerciale présumée. Import en brouillon avec blocage de publication, attribution à Bouaziz Ait Driss et contributeurs. |
| [Fruits-360 100x100](https://github.com/fruits-360/fruits-360-100x100) | `bed1c24ee70de1569272de3882fbde88211c08b5` | 1 JPEG par sujet, 20 fruits + 10 légumes au sens culinaire. | **CC BY-SA 4.0**, Mihai Oltean. La section License du README autorise partage et adaptation avec attribution et partage à l’identique. Pixels inchangés ; fichiers renommés. |

## Qualité et droits

- **Mots :** `status=draft`, `script=Latn`, `validation_status=source_attested_not_reviewed`. Tifinagh, images de leçon, audios et exemples restent vides. Les identifiants d’images du cours sont conservés comme pistes mais ne sont pas transformés en URL supposée. La présence d’un mot dans ce cours ne prouve pas sa justesse pour toutes les variantes kabyles.
- Le fichier `course/basics/skills/verb_plurals.yaml` est syntaxiquement invalide dans la révision auditée : il est exclu et signalé dans le rapport. Aucun correctif linguistique ou YAML implicite n’a été appliqué au contenu tiers.
- Le droit de réutilisation du cours requiert une clarification entre ses deux déclarations. Les textes adaptés restent isolés, attribués avec la licence non commerciale de la racine signalée et la divergence explicite ; ne pas les publier dans les leçons ou les utiliser commercialement en l’état.
- **Photos :** 30 fichiers JPEG de **100 × 100 px**, conçus comme vignettes. La catégorie photographique du dataset a été traduite en français ; elle ne fournit pas de traduction kabyle. Le classement fruit/légume est pédagogique/culinaire, pas botanique.
- Le source URL, le SHA complet, la catégorie, le SHA-256, la taille, l’auteur, l’URL de licence, la preuve de licence et l’absence de modification des pixels sont conservés pour chaque photo. La notice de chaque média doit accompagner sa réutilisation. Les adaptations de ces photos doivent respecter le partage à l’identique.
- Les listes de photos et de mots sont **indépendantes**. Une association proposée dans l’administration reste à vérifier (sens exact, singulier/pluriel, variété et photo). Par exemple, une seule fraise n’illustre pas automatiquement une leçon sur le pluriel « fraises ».

## Stockage et accès

- `content/catalog/words-librelingo.json` : entrées sources et blocages.
- `content/catalog/photos-fruits360.json` : métadonnées de chaque photo.
- `content/catalog/import-report.json` : comptes, versions et fichiers exclus.
- `content/photos/fruits360/` : pixels originaux, livrés localement dans le dépôt.
- `content/licenses/` : licence du cours, métadonnées de cours contradictoires et README Fruits-360 ayant servi de preuve.
- PostgreSQL : textes dans `content`, actifs photographiques dans `media_asset` (migration 002).
- API admin : `GET /api/admin/content`, `GET /api/admin/media` et import existant. Le jeton administrateur est obligatoire. L’API publique `/api/content` continue d’exclure les brouillons.
- Les fichiers photographiques attribués sont servis par `/api/media/fruits360/<nom>.jpg`, sans service tiers. Ce dossier est une bibliothèque de fichiers distribués ; il n’est pas un point d’upload utilisateur. Ne jamais y déposer de fichiers privés.

## Import sans perdre les corrections

`bash scripts/start.sh` applique Alembic puis lance `backend/seed.py`. Le seed vérifie toutes les empreintes avant d’insérer le catalogue. Un identifiant déjà présent n’est pas remplacé : les corrections éditoriales survivent aux relances. Une photo altérée bloque l’import au lieu d’être silencieusement acceptée. Ne pas supprimer la base pour rafraîchir un catalogue.

Pour un import manuel après installation, depuis la racine du projet :

```bash
set -a
source .env
set +a
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python seed.py
```

## Refaire la collecte depuis les sources

La collecte est optionnelle : les données et les photos sont déjà incluses. Le collecteur a besoin de PyYAML, uniquement comme outil de collecte (pas comme dépendance serveur). Il ne produit jamais de mot publié. À lancer sur une copie de travail, pas sur des fichiers de catalogue modifiés manuellement.

```bash
# Depuis la racine du projet ; conserver le proxy et TLS lorsqu’ils sont configurés.
uv pip install --python .venv/bin/python -r scripts/requirements-data.txt
# Choisir un nouveau dossier extérieur au checkout pour les sources tierces.
git clone --no-checkout https://github.com/LibreLingo/LibreLingo-KAB-from-FR.git /tmp/tifin-librelingo-source
git -C /tmp/tifin-librelingo-source checkout --detach e426e0fa052da1c91b6efd800d8469e6940757d5
.venv/bin/python scripts/collect_sources.py --source-checkout /tmp/tifin-librelingo-source
```

Le script refuse une autre révision non auditée. Les noms exacts des six photographies dont le fichier n’est pas nommé `0_100.jpg` ont été relevés dans l’arbre de la révision source. Il réutilise les fichiers locaux qui correspondent déjà aux empreintes ; il ne remplace pas un fichier dont l’empreinte a changé. Les imports en base ne téléchargent rien.

## Autres pistes examinées, non importées

| Source | Constat |
|---|---|
| [sferhah/DigitizedDallet](https://github.com/sferhah/DigitizedDallet) | Révision `e0eb1290641e0f3fb762de6b0e771e651e494948`. Dictionnaire Dallet 1982 numérisé ; licence MIT de logiciel avec placeholders. Elle ne suffit pas à établir les droits sur l’ouvrage original. |
| [kabylesystem/tiwizi](https://github.com/kabylesystem/tiwizi) | Révision `345d3e276511531f9203a9aceade91337d5cdf37`. Sources mixtes, dont ouvrages et notes personnelles ; pas de licence racine trouvée. Ne pas déduire de ses propres annotations que tous les contenus sont redistribuables. |
| [tron90x/Kabyle-Language-Dictionaries-for-Large-Language-Models](https://github.com/tron90x/Kabyle-Language-Dictionaries-for-Large-Language-Models) | Révision `9940669481c10ecc0d3207e1cec14c68e2c1b59d`. README « Specify your chosen license », pas de licence effective établie. |
| [suprawall/apprendre_kabyle](https://github.com/suprawall/apprendre_kabyle) | Bases thématiques présentes, mais pas de licence trouvée ; sources externes reprises. |
| [mcteach21/Ssendu](https://github.com/mcteach21/Ssendu) | Dictionnaire applicatif, pas de licence trouvée. |
| [kzirem/-vocabulaire-kabyle](https://github.com/kzirem/-vocabulaire-kabyle) | Pages thématiques, pas de licence trouvée. |
| [assemer/kabyleWords](https://github.com/assemer/kabyleWords) | Liste de mots et base SQL, pas de licence trouvée ; ne garantit pas les paires françaises nécessaires. |
| [nabil509/kab-arrow-words](https://github.com/nabil509/kab-arrow-words) | Source de mots fléchés sous GPL-3.0, mais pas un lexique français–kabyle directement exploitable pour des fiches illustrées. Aucun fichier copié. |
| Wiktionnaire et Wikimedia Commons | Requêtes HTTPS toujours refusées par le proxy cloud (403). Les ajouts de domaines déjà enregistrés au brouillon ne prouvent pas leur application à cette instance. Aucune image Google ou donnée de ces sites n’a été importée sans accès et audit. |

L’entraînement et l’inférence IA sont sans rapport avec ce lot : aucun modèle, score de prononciation ou audio artificiel n’a été ajouté.

## Inventaire complet et catégories

Le catalogue comporte désormais 115 paires phrase kabyle–traduction française, en plus des 61 entrées lexicales. `content/catalog/phrases-librelingo.json` conserve texte, traduction, variantes, auteur, licence, fichier, révision et index source. Les phrases sont extraites telles quelles des fichiers YAML lisibles des modules actifs hors fichier test, puis dédupliquées sur la paire exacte. Les trois anciennes phrases d’aperçu réutilisent leur identifiant existant. `phrases-report.json` signale toujours le YAML invalide exclu ; aucune réparation implicite de traduction n’a été appliquée.

Le seed insère les 112 autres phrases en brouillon. Toutes restent en relecture et sous les mêmes réserves de licence : elles ne deviennent pas des fiches publiques ni des leçons validées. L’interface admin affiche les 115 phrases, les 61 mots et les 8 lettres par type, catégorie et statut, avec une vue lecture privée paginée.

Les catégories sont stockées dans le champ SQL `content.theme`. La proposition initiale, documentée par `category_status=suggested` et `category_scheme=topics-v1`, est appliquée seulement aux enregistrements sources inchangés. Les catégories déjà éditées, les contenus modifiés et les identifiants extérieurs au manifeste ne sont pas écrasés. Le changement éditorial via PATCH ajoute un marqueur temporel, conserve le statut de publication et ne modifie pas le texte. Les catégories et leurs libellés standards sont dans `backend/app/library.py` ; un identifiant supplémentaire déjà stocké est aussi reconnu.

API de lecture : `/api/library` accepte `kind`, `category`, `q`, `offset`, `limit`. Seuls les contenus publiés sans blocage sont retournés. `/api/admin/library` exige le jeton et inclut les brouillons. Recherche insensible aux accents pour la consultation, sans modifier les réponses des exercices. Les variantes attestées sont conservées et consultables. L’ordre est latin pour les lettres, français pour les autres fiches. La lecture n’écrit pas dans la progression.

Collecte optionnelle depuis le checkout source figé, après installation des outils de données :

```bash
.venv/bin/python scripts/collect_phrases.py --source-checkout /chemin/vers/LibreLingo-KAB-from-FR
```

La commande ne publie rien. Le démarrage importe les fichiers livrés sans téléchargement et sans écraser les corrections en base. Aucun nouveau service ou paquet serveur n’est requis.
