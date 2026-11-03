# Tifin · apprendre le kabyle

Application Next.js + FastAPI + PostgreSQL pour des débutants francophones.

## Voir la mise à jour sur ton ordinateur

Arrêter le serveur avec Ctrl+C, puis :

```bash
cd ~/Documents/projet_kabyle/Kabyle
git pull --ff-only
npm --prefix frontend run build
bash scripts/start.sh
```

Ouvrir **http://localhost:3000**. Le démarrage applique la migration 004 et importe les nouveaux contenus sans écraser les corrections ni les validations de l’administrateur. Le `.env`, le port PostgreSQL local et les dépendances verrouillées restent ceux de ton installation. Si `scripts/db.sh` a été adapté au port 5433, conserver cette adaptation et la même valeur dans `DATABASE_URL`.

Première installation : `bash scripts/install.sh`, puis `bash scripts/start.sh`. Il faut Node.js 22+, Python avec `uv`, Docker actif et accessible. Le cloud utilise Python 3.12 ; pour Python 3.10, conserver le verrou de dépendances compatible déjà généré sur ton PC. Les journaux sont dans `artifacts/`. Ctrl+C arrête les serveurs ; PostgreSQL conserve ses données dans le volume Docker.

## Bibliothèque publique et catégories

**Ma bibliothèque** affiche les lettres, mots et phrases sans jeu obligatoire ni connexion. Elle propose une recherche en kabyle/français/tifinagh, des catégories et une pagination.

Le catalogue livré contient **8 lettres, 442 entrées lexicales, 133 paires de phrases et 30 photos**. Les entrées lexicales incluent les mots des leçons et les formes des mini-dictionnaires : ce ne sont pas toutes des noms isolés. Les 15 fichiers de compétences LibreLingo sont traités, y compris `juniors/skills/nombres_jr.yaml`, `test_jr.yaml` et `verb_plurals.yaml`. Ce dernier comportait une tabulation YAML : seule sa mise en forme a été réparée. Aucun fichier de compétences n’est exclu. Les 21 fichiers de cours/configuration/documentation sont référencés dans l’inventaire.

**La visibilité ne dépend plus de la validation humaine.** Les fiches `draft` sont publiques avec le badge **À vérifier** ; les fiches `validated` portent **Validé**. Les fiches retirées (`rejected`) restent masquées au public. Les catégories proposées peuvent être corrigées. Les catégories et chapitres d’origine sont également conservés dans les métadonnées.

## Administration

Dans **Gestion des contenus**, saisir `ADMIN_TOKEN` depuis ton `.env`, puis **Ouvrir la bibliothèque**. Le jeton reste en mémoire dans l’onglet.

- Consulter toutes les lettres, tous les mots et toutes les phrases par pages ; rechercher et filtrer par catégorie et validation.
- Cliquer sur **Valider** à côté d’une fiche après relecture. Le serveur mémorise la validation et sa date ; aucune transcription tifinagh ni photo n’est exigée pour valider une paire kabyle/français.
- Ouvrir une fiche pour modifier le texte, la traduction, la catégorie ou ajouter une photo. Enregistrer une modification remet la fiche **À vérifier**, en la gardant publique.
- **Enregistrer uniquement la catégorie** conserve le texte et son état de validation.

Une incohérence de la source est signalée sur `ṭam` : dans le chapitre Nombres, les images indiquent 8 mais la traduction est « un ours ». Le texte d’origine est conservé pour correction humaine. Le bouton de validation ne corrige aucune traduction automatiquement.

## Importer le TSV Sifal

Source demandée : [Kabyle-French / Sentence pairs in Kabyle-French - 2023-07-18.tsv](https://huggingface.co/datasets/Sifal/Kabyle-French/blob/main/Sentence%20pairs%20in%20Kabyle-French%20-%202023-07-18.tsv).

Dans **Gestion des contenus → Importer les phrases Kabyle–Français (Sifal)** :

1. Cliquer sur **Télécharger depuis Hugging Face**, ou télécharger le fichier sur ton ordinateur puis **Choisir le fichier TSV**.
2. Vérifier l’aperçu : choisir les colonnes kabyle/français et préciser si la première ligne est un titre.
3. Cliquer sur **Importer et rendre public**.

Les paires sont enregistrées en PostgreSQL et deviennent consultables dans **Ma bibliothèque → Phrases**. Leur catégorie est proposée à partir du français (salutations, famille, alimentation, voyages, temps, etc.), avec **Autres phrases** comme catégorie de repli. Ces propositions restent modifiables. Les nouvelles fiches sont **À vérifier**. Les traductions ne sont pas générées ou réécrites. Le rapport donne les ajouts, doublons et lignes incomplètes ; réimporter le même fichier préserve les corrections et validations existantes. L’origine et l’empreinte SHA-256 du fichier sont conservées.

**État du cloud :** le téléchargement du TSV exact renvoie HTTP 403 dans cet environnement. Il n’est donc pas inclus dans les 133 phrases livrées. Le téléversement local et l’import sont disponibles pour ce fichier ; aucune quantité issue de Sifal n’est annoncée comme déjà importée.

Alternative en terminal, après avoir téléchargé le TSV :

```bash
bash scripts/import_sifal.sh "/chemin/vers/phrases.tsv" --preview
bash scripts/import_sifal.sh "/chemin/vers/phrases.tsv"
# Si nécessaire : --kab-column 2 --fr-column 4
```

## Apprendre

Les trois petites leçons de lettres suivent découverte, rappel, jeu et bilan. Dans **Mots et phrases → Je commence !**, la leçon publique propose trois mots illustrés, trois phrases de la source et huit défis : reconnaissance, ordre des mots, phrase à compléter et rappel. Les réponses sont vérifiées par le serveur ; réussites et erreurs sont enregistrées dans la progression anonyme de l’appareil. La lecture seule ne crée aucun progrès.

Le reste du catalogue se consulte par catégories dans la bibliothèque. Il n’est pas transformé artificiellement en centaines de leçons validées. Le dessin et l’enregistrement/écoute locale sont disponibles ; aucun audio kabyle ni score de prononciation n’est simulé.

## Où sont les données ?

- **PostgreSQL**, table `content` : `kind` distingue lettre/mot/phrase ; `theme` est la catégorie ; `status` indique la validation ; `data` contient textes, variantes, sources et corrections.
- `content/catalog/course-words.json` et `course-phrases.json` : données de départ livrées avec le dépôt.
- `course-files.json` et `course-report.json` : fichiers, empreintes, quantités et anomalies de collecte.
- `content/photos/` et table `media_asset` : 30 photos Fruits-360 attribuées à Mihai Oltean, 100 × 100 px, pixels inchangés. Elles ne constituent pas 30 associations mot–photo validées.
- `artifacts/tsv-imports/` : fichiers TSV téléversés, exclus de Git et non servis publiquement.

Les sources LibreLingo, leurs révisions et les déclarations de licence sont conservées, sans en faire une condition de visibilité. Les mots sans tifinagh ou audio n’en reçoivent pas de version inventée.

Collecte reproductible avec PyYAML (`scripts/requirements-data.txt`) et les dépendances de l’application :

```bash
.venv/bin/python scripts/collect_course.py --source-checkout /chemin/LibreLingo-KAB-from-FR
```

Le checkout source doit être à la révision `e426e0fa052da1c91b6efd800d8469e6940757d5`.

## Vérifications

```bash
cd backend
../.venv/bin/python -m pytest -q
cd ../frontend
npm run typecheck
npm run build
```

Les tests utilisent la base locale initialisée, jamais une base de production. Les tests navigateur nécessitent Playwright et Chromium ainsi que l’application démarrée. Les documents d’audits plus anciens décrivent l’ancienne politique de brouillons privés ; la politique actuelle est celle décrite ici.
