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

Ouvrir **http://localhost:3000**. Le démarrage applique les migrations jusqu’à 005 et importe les nouveaux contenus sans écraser les corrections ni les validations de l’administrateur. Le `.env`, le port PostgreSQL local et les dépendances verrouillées restent ceux de ton installation. Si `scripts/db.sh` a été adapté au port 5433, conserver cette adaptation et la même valeur dans `DATABASE_URL`.

Première installation : `bash scripts/install.sh`, puis `bash scripts/start.sh`. Il faut Node.js 22+, Python avec `uv`, Docker actif et accessible. Le cloud utilise Python 3.12 ; pour Python 3.10, conserver le verrou de dépendances compatible déjà généré sur ton PC. Les journaux sont dans `artifacts/`. Ctrl+C arrête les serveurs ; PostgreSQL conserve ses données dans le volume Docker.

## Tatoeba : importer et apprendre avec des enregistrements

Après la mise à jour et le démarrage du site, ouvrir un deuxième terminal :

```bash
cd ~/Documents/projet_kabyle/Kabyle
bash scripts/import_tatoeba.sh --download
```

Cette commande télécharge les quatre exports hebdomadaires utiles depuis `downloads.tatoeba.org` : phrases kabyles détaillées, phrases françaises détaillées, liens kabyle–français et métadonnées audio kabyles. Elle applique les migrations, aligne les identifiants, garde uniquement les traductions directement reliées et importe les paires en PostgreSQL. Aucun texte kabyle ou français n’est généré. La collecte peut prendre quelques minutes selon la connexion. Le rapport annonce les quantités réellement importées.

**Dans ce cloud, le site Tatoeba et son serveur de téléchargement sont refusés par le proxy (403). Aucun millier de phrases Tatoeba ni enregistrement réel n’est donc annoncé comme déjà chargé.** Le pipeline et les exercices sont disponibles ; le téléchargement doit être exécuté sur une machine ayant accès à Tatoeba, ou remplacé par un téléversement des exports officiels.

Dans **Gestion des contenus → Importer Tatoeba : phrases et enregistrements**, on peut choisir un export de paires `kab → fra` et le fichier de métadonnées `sentences_with_audio`. Un aperçu affiche les textes, identifiants et nombres d’enregistrements avant **Importer Tatoeba et rendre public**. Les formats sont vérifiés contre le code officiel [Tatoeba/tatoeba2 à la révision f2c80b8](https://github.com/Tatoeba/tatoeba2/tree/f2c80b81032630648f7896182174a9f5784ccde2).

Formats pris en charge :

- Paires TSV à quatre colonnes : `id_kab`, `texte_kab`, `id_fra`, `texte_fra`. Les exports à six colonnes avec codes langue sont aussi reconnus.
- Ou, via le script, fichiers de phrases `id / langue / texte` (détaillés à six colonnes également acceptés) et fichier de liens `id / id`.
- Audio : **cinq colonnes**, `sentence_id / audio_id / auteur / licence / attribution_url`. Plusieurs voix peuvent correspondre à une phrase. L’URL est construite avec l’**identifiant audio**, selon le format officiel ; elle n’est jamais déduite du seul identifiant de phrase.
- TSV/CSV séparés par tabulations, `.bz2`, `.gz` et archives `.tar.bz2`/`.tar.gz`. Les archives sont lues sans extraire leurs chemins sur le disque. L’interface accepte 128 Mo au total ; le script convient aux exports plus grands.

Import de fichiers déjà téléchargés :

```bash
bash scripts/import_tatoeba.sh --pairs "/chemin/paires-kab-fra.tsv" --audio "/chemin/sentences_with_audio.tar.bz2"
# Ou les fichiers bruts, alignés sur leurs identifiants :
bash scripts/import_tatoeba.sh --sentences "/chemin/kab_sentences_detailed.tsv.bz2" "/chemin/fra_sentences_detailed.tsv.bz2" --links "/chemin/kab-fra_links.tsv.bz2" --audio "/chemin/kab_sentences_with_audio.tsv.bz2"
```

Ajouter `--preview` prépare le rapport sans écrire dans PostgreSQL. Les empreintes des fichiers et les identifiants des phrases/enregistrements sont conservés. Une réimportation dédoublonne les paires et enrichit leurs sources/voix en conservant textes édités, catégories et validations. Les fichiers de travail et rapports sont dans `artifacts/tatoeba-imports/`, exclus de Git et non servis publiquement.

### Les quatre activités

Dans **Mots et phrases → Je choisis mon thème**, filtrer par catégorie, difficulté, présence d’audio ou source Tatoeba. Une séance propose jusqu’à cinq phrases ; on peut aussi choisir une phrase seule. Dans **Ma bibliothèque → Phrases**, **M’entraîner avec cette phrase** ouvre directement ses activités. Les phrases déjà présentes sont utilisables sans attendre Tatoeba.

1. **Je découvre** : carte à retourner, traduction, mots cliquables, note grammaticale si renseignée et voix disponibles.
2. **Je construis** : étiquettes mélangées, reconstruction, correction serveur et nouvelle tentative. Les mots répétés conservent chacun leur position.
3. **Je fais la dictée** : écouter un enregistrement puis saisir la phrase kabyle, avec clavier des caractères particuliers.
4. **J’écoute et je choisis** : trois traductions provenant de vraies fiches de la bibliothèque ; le serveur vérifie la réponse. Les autres traductions d’une même phrase kabyle ne servent pas de mauvaises réponses.

La dictée et le QCM audio sont désactivés sans métadonnées d’enregistrement attribué. Un échec de lecture est affiché ; aucun son synthétique ni texte parlé artificiellement n’est substitué. Les MP3 sont lus à la demande depuis Tatoeba, sans être copiés dans Git. Les crédits de chaque voix sont conservés. Le fait qu’un enregistrement soit dans Tatoeba n’est pas présenté comme une preuve indépendante que son auteur est natif. Les réponses, erreurs et révisions sont enregistrées dans la progression anonyme ; retourner une carte ne crée pas une réussite.

### Lexique, niveaux et grammaire

Le découpage lexical conserve les formes telles que `Axxam-a` ; il ne prétend pas analyser automatiquement l’annexion. Les mots cliquables cherchent une forme ou un synonyme attesté dans le lexique existant. Si une traduction individuelle manque, le site le dit : l’alignement de deux phrases ne suffit pas à inventer l’alignement de leurs mots.

La difficulté proposée est **une estimation par longueur** : jusqu’à quatre mots, cinq à huit mots, neuf mots ou plus. Ce classement ne constitue pas une évaluation CECR. Dans l’éditeur d’une phrase, l’administrateur peut attribuer **A1 à C2** et ajouter une **note grammaticale**. Ces champs apparaissent sur la carte ; les niveaux attribués A1/A2 sont filtrables. Les fiches restent publiques et le bouton **Valider** garde son rôle de relecture humaine.

La migration 005 ajoute les index de difficulté, présence d’audio et recherche exacte du lexique. Les imports Sifal remplissent également ces champs, afin que leurs phrases puissent utiliser les mêmes activités.


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

Les autres phrases disposent également de cartes et d’exercices de construction dans les séances par thème. Les activités audio dépendent des enregistrements importés ; ces exercices ne constituent pas une validation linguistique automatique. Le dessin et l’enregistrement/écoute locale sont disponibles ; aucun audio kabyle ni score de prononciation n’est simulé.

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
