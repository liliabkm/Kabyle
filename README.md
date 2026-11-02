# Tifin · apprendre le kabyle

Une première application fonctionnelle Next.js + FastAPI + PostgreSQL, destinée aux débutants francophones. Le dépôt a été initialisé à partir du cahier des charges.

## Démarrer

Prérequis : Node.js 22+ (testé 24), Python 3.12, `uv`, Docker local actif et accessible. Dans le cloud géré, conserver le proxy et les certificats injectés ; ne pas désactiver TLS.

```bash
cd /workspace/Kabyle
bash scripts/install.sh
bash scripts/start.sh
```

Le setup crée un environnement Python, installe les versions verrouillées, démarre PostgreSQL 17 sur la boucle locale, génère `.env` avec un jeton admin aléatoire, applique les migrations, importe les lettres et compile Next.js. Réexécutable ; ne remplace pas un `.env` existant. Les mots de passe de développement dans `.env.example` ne sont pas destinés à la production.

Web : port 3000 ; API : port 8000 ; documentation OpenAPI : chemin `/docs` de l’API. Les appels frontend `/api/*` sont réécrits vers FastAPI. `scripts/start.sh` garde les processus au premier plan, les arrête avec Ctrl+C et écrit les journaux dans `artifacts/`. PostgreSQL utilise le volume Docker `kabyle-postgres-data`. Les processus ne survivent pas à une nouvelle machine : relancer le script.

Pour développer avec rechargement, dans deux terminaux après installation :

```bash
cd /workspace/Kabyle
set -a; source .env; set +a
cd backend
../.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Autre terminal : cd /workspace/Kabyle/frontend && npm run dev
```

Chaque tâche cloud est déjà isolée : utiliser le checkout existant, ne pas créer de worktree sauf demande explicite.

## Interface ludique

Accueil simplifié avec une mascotte originale, accès direct au jeu, grandes cartes colorées, consignes courtes et navigation « Les lettres », « Les mots », « Dessiner », « Ma voix ». Les précisions sur l’alphabet restent accessibles dans un volet pour les parents. Les boutons de réponse sont disposés sur deux colonnes sur téléphone ; les mouvements non nécessaires sont désactivés quand le navigateur demande une réduction des animations. Cette refonte a été vérifiée dans Chromium ordinateur/mobile, sans étude utilisateur auprès d’enfants.

Pour récupérer une mise à jour de l’interface sur une installation existante : arrêter le site avec Ctrl+C, exécuter `git pull --ff-only`, puis `npm --prefix frontend run build` et `bash scripts/start.sh`. Cela conserve le `.env` local et ne réinstalle pas les dépendances Python.

## Ce qui fonctionne

- Parcours de 8 lettres Unicode, fiches avec équivalent latin et indications de base.
- Exercices choix multiple, association de cartes ou saisie, vérification serveur, erreurs, progression anonyme et révisions espacées en PostgreSQL.
- Atelier de tracé à la souris/au doigt et export PNG.
- Enregistrement et écoute dans le navigateur, suppression ; pas de téléversement ni conservation serveur.
- Administration par jeton : import JSON, correction et passage brouillon/validé avec garde-fous d’attribution ; import batch atomique.
- Fiches lexicales alimentées par l’API, disponibles après import et validation ; aucun mot non validé publié.

## Ce qui reste à livrer

Les 30 mots illustrés, les exemples kabyles validés, les exercices photo avec vocabulaire réel, les paires audio–texte, le modèle visuel et la transcription vocale ne sont pas livrés. Les écrans les présentent honnêtement en attente ou indisponibles. L’audit a identifié des licences/mappings manquants et des destinations réseau bloquées ; voir [les sources](docs/SOURCES.md) et [l’état IA](ml/EVALUATION.md). Le stockage S3 est prévu par séparation de service mais pas implémenté. Ne pas présenter cette tranche comme la totalité du cahier des charges.

## Administration et import

Saisir le jeton de votre `.env` dans « Gestion des contenus ». Ne pas le partager ni le versionner. Charger les entrées, modifier le JSON ou ouvrir un fichier, puis enregistrer. Un import en `draft` doit précéder la relecture humaine ; les contrôles techniques ne remplacent pas cette relecture.

```bash
set -a; source .env; set +a
.venv/bin/python scripts/import_content.py chemin/lot-valide.json
```

Exemple d’une entrée (schéma indicatif, non une traduction à importer) :

```json
[{"id":"identifiant-stable","kind":"word","variety":"kab","script":"Tfng","theme":"animaux","status":"draft","data":{"latin":"À vérifier","tifinagh":"","french":"","sources":[],"images":[],"audios":[],"examples":[]}}]
```

Pour publier : remplir sources (url/author/license), reviewed_by, reviewed_at ; pour les mots, traduction, tifinagh et au moins une image attribuée. Les photos sont des URL HTTPS sourcées, aucun scraping automatique ni transfert S3 dans cette version.

## Validation

```bash
cd /workspace/Kabyle/backend
../.venv/bin/python -m pytest -q
cd ../frontend
npm run typecheck
npm run build
cd ..
.venv/bin/python scripts/browser_smoke.py
```

Le test navigateur nécessite `uv pip install --python .venv/bin/python playwright==1.56.0` et Chromium (`/usr/bin/chromium` dans ce cloud), ainsi que l’application démarrée. Les tests API utilisent la base locale initialisée ; ils nettoient uniquement leurs entrées `test-*` et identités anonymes de test. Ne pas utiliser ces tests sur une base de production.

Voir [architecture et convention d’écriture](docs/ARCHITECTURE.md), [inventaire des sources](docs/SOURCES.md) et [résultats de validation](docs/VALIDATION.md).
