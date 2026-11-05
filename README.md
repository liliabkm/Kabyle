# Tifin · apprendre le kabyle

Application Next.js, FastAPI et PostgreSQL pour des débutants francophones.

## Voir la mise à jour

Arrêter le site avec Ctrl+C, puis :

```bash
cd ~/Documents/projet_kabyle/Kabyle
git pull --ff-only
npm --prefix frontend run build
bash scripts/start.sh
```

Ouvrir **http://localhost:3000 → Mots et phrases**. Le démarrage applique la migration **006** et reclasse les données existantes par sens français. Il conserve les textes, les photos ajoutées, les validations linguistiques et les catégories explicitement confirmées dans l’administration. Le `.env`, le verrou Python local et `scripts/db.sh` ne sont pas remplacés par cette mise à jour ; conserver ton adaptation au port PostgreSQL 5433 si elle est utilisée.

Première installation : `bash scripts/install.sh`, puis `bash scripts/start.sh`. Prérequis : Node.js 22+, Python avec `uv`, Docker actif et accessible. Le cloud utilise Python 3.12 ; l’installation Python 3.10 doit conserver son verrou compatible. Les serveurs restent au premier plan ; Ctrl+C les arrête. Journaux : `artifacts/`. PostgreSQL conserve ses données dans le volume Docker.

### Si le premier démarrage prend du temps

Le classement affiche sa progression : `Classement : 500/… fiches enregistrées`. Les lots de 500 sont enregistrés séparément ; après Ctrl+C, une relance reprend les fiches restantes. Une base déjà classée affiche `Classement déjà à jour.` avant le lancement du site. Le reclassement ne modifie ni les textes, ni les sources, ni les validations.

## Le parcours par images

Les utilisateurs choisissent des **cartes illustrées**, sans menus de filtres : animaux, fruits, vêtements, nature, personnes, école, métiers, nombres, couleurs, etc.

Chaque thème propose :

1. **Les mots** : illustration ou photo, mot kabyle, sens français et formes associées regroupées dans une même fiche.
2. **Les phrases** : « Utiliser ce mot » ouvre uniquement ses contextes attestés. Le français doit exprimer le même concept et une forme kabyle connue doit être présente ; elle est surlignée.
3. **À moi de jouer** : « Construire cette phrase » ouvre directement le puzzle. Le serveur corrige la réponse et enregistre la progression réelle.

Exemple : **Animaux → Cheval (`agmar`) → cinq phrases**, dont `Agmar itess aman` / « Le cheval boit de l’eau », puis construction de la phrase. **Fruits** contient trois fiches : fraises, raisin et figues. Les pluriels et formes de contexte ne sont plus présentés comme autant de nouveaux mots sans rapport.

**Ma bibliothèque** utilise les mêmes cartes et ajoute **Les lettres** : huit lettres lisibles sans jeu obligatoire. Lire une fiche ne crée aucune réussite.

Les images d’animaux sont des illustrations originales du projet. Les photos de fruits/légumes sont les fichiers Fruits-360 déjà livrés, attribués à Mihai Oltean, 100 × 100 px, pixels inchangés ; leurs crédits sont dans les sources des fiches.

## Organisation des données

Le catalogue livré comprend **442 entrées lexicales sources, 133 paires de phrases, 8 lettres et 30 photos**. Parmi les entrées lexicales, 370 viennent des mini-dictionnaires : elles comprennent des formes conjuguées, pluriels, pronoms, fragments et libellés techniques. Les compteurs des thèmes représentent les fiches regroupées, pas le nombre brut de variantes.

L’audit actuel corrige **310 classements** du catalogue livré. Exemples : souris et éléphants passent dans Animaux ; café, thé et bière dans Boissons ; pronoms dans Les petits mots ; « Merci » dans Salutations ; les phrases avec raisin ou figues quittent leur ancien chapitre Actions pour rejoindre Fruits.

- Le classement suit le **sens français**, pas le dossier du cours source. Les alias et frontières lexicales évitent les faux rapprochements : « achat » n’est pas « chat », « pommes de terre » ne devient pas « pommes », « un chien » n’est pas une leçon du nombre un, « Quoi de neuf ? » n’est pas le nombre neuf.
- Une phrase peut appartenir à plusieurs thèmes justifiés par son contenu : le cheval qui boit de l’eau appartient aussi aux contextes des boissons. Il reste un seul enregistrement en base.
- Les variantes d’un même sens sont regroupées ; repas, déjeuner et souper, ou assistante et infirmière, restent des sens distincts.
- **13 éléments sources à clarifier** sont séparés des fiches d’apprentissage : 12 incohérences/libellés techniques et un fragment d’expression. Ils restent publics dans **Le coin du dictionnaire**. Exemple : `ṭam` est traduit « un ours » malgré les images du nombre huit ; sa traduction n’est pas modifiée automatiquement.
- Les prénoms des personnages sont rangés dans le dictionnaire, distinctement des noms communs.
- Les phrases sans sujet suffisamment identifiable restent dans Autres situations, plutôt que d’être rattachées arbitrairement à un thème.

Fichiers de référence :

- `content/catalog/semantic-topics.json` : sens français, variantes, catégories et formes kabyles préférées lorsqu’elles existent dans le corpus.
- `content/catalog/organization-report.json` : décision pour chacune des **575 entrées** mots/phrases, anciens classements, nouveaux thèmes et éléments à clarifier.
- `content/catalog/course-words.json`, `course-phrases.json` : données sources, avec provenance et traductions conservées.
- `course-files.json`, `course-report.json` : les 15 compétences LibreLingo sont incluses, dont les juniors et les mini-dictionnaires, à la révision `e426e0fa052da1c91b6efd800d8469e6940757d5`.

Reproduire l’audit :

```bash
.venv/bin/python scripts/audit_organization.py
```

Les décisions sont conservées dans PostgreSQL : `content.theme` pour le classement principal, `topic_keys` pour les appartenances, `concept_key` pour les regroupements et `matched_concepts` pour les sens présents dans une phrase. La migration 006 ajoute des index GIN ; les mises à niveau traitent les données par lots.

## Administration et validation

Dans **Gestion des contenus**, saisir `ADMIN_TOKEN` depuis ton `.env`, puis ouvrir la bibliothèque. Le jeton reste en mémoire dans l’onglet.

- Tous les mots, phrases, lettres et photos restent consultables, avec recherche et filtres **dans l’administration**.
- **Valider** confirme la relecture d’une fiche. Le classement automatique ne transforme pas une traduction en traduction validée.
- Modifier une fiche conserve sa visibilité et la remet À vérifier. Modifier uniquement la catégorie conserve le texte et la validation. Les catégories confirmées manuellement restent utilisables dans le parcours, y compris les catégories personnalisées.
- **Classement des données et fiches à clarifier** montre les formes lexicales, petits mots, noms propres et entrées à corriger.
- Les notes grammaticales et niveaux A1–C2 peuvent être renseignés dans l’éditeur. Un niveau CECR n’est pas déduit du nombre de mots.

Les fiches `draft` sont publiques avec « À vérifier » ; `validated` indique la validation humaine. Les fiches retirées (`rejected`) restent masquées au public. Les sources, révisions, licences déclarées et empreintes des fichiers sont conservées.

## Importer Tatoeba

Dans un second terminal :

```bash
cd ~/Documents/projet_kabyle/Kabyle
bash scripts/import_tatoeba.sh --download
```

Le script télécharge les quatre exports hebdomadaires utiles depuis `downloads.tatoeba.org` : phrases kabyles détaillées, françaises détaillées, liens kabyle–français et métadonnées audio kabyles. Il aligne les identifiants, conserve les traductions directement liées et dédoublonne en préservant les corrections, même après modification des deux textes. Le rapport affiche les quantités réellement ajoutées.

Alternative : **Gestion des contenus → Importer Tatoeba : phrases et enregistrements**, puis choisir l’export `kab → fra` à quatre colonnes et le fichier de métadonnées audio. L’aperçu précède l’import public. Formats vérifiés contre [le code officiel Tatoeba](https://github.com/Tatoeba/tatoeba2/tree/f2c80b81032630648f7896182174a9f5784ccde2).

```bash
bash scripts/import_tatoeba.sh --pairs "/chemin/paires.tsv" --audio "/chemin/sentences_with_audio.tar.bz2"
# Ou les exports bruts :
bash scripts/import_tatoeba.sh --sentences "/chemin/kab_sentences_detailed.tsv.bz2" "/chemin/fra_sentences_detailed.tsv.bz2" --links "/chemin/kab-fra_links.tsv.bz2" --audio "/chemin/kab_sentences_with_audio.tsv.bz2"
```

Ajouter `--preview` prépare l’alignement sans écrire dans PostgreSQL. TSV/CSV tabulés, bz2, gzip et archives tar sont acceptés sans extraction de chemins. Interface : 128 Mo au total ; utiliser le script pour les gros exports.

L’audio suit les cinq colonnes officielles `sentence_id / audio_id / auteur / licence / attribution_url`. Une phrase peut avoir plusieurs voix. L’URL utilise l’identifiant **audio**, pas le seul identifiant de phrase. Les MP3 sont lus à la demande depuis Tatoeba, pas copiés dans Git. Les crédits sont conservés ; l’application ne certifie pas indépendamment que chaque auteur est natif.

**Dans ce cloud, Tatoeba et son serveur de téléchargement sont bloqués (403). Aucun corpus Tatoeba réel n’est inclus dans les 133 phrases livrées.** Exécuter le téléchargement sur un ordinateur autorisant ces destinations, ou téléverser les exports officiels.

## Importer Sifal

Source : [le TSV Kabyle-French du 18 juillet 2023](https://huggingface.co/datasets/Sifal/Kabyle-French/blob/main/Sentence%20pairs%20in%20Kabyle-French%20-%202023-07-18.tsv).

Dans l’administration, **Importer les phrases Kabyle–Français (Sifal)** permet le téléchargement serveur ou le téléversement, l’aperçu et le choix des colonnes. Les traductions sont conservées et classées par le même moteur sémantique.

```bash
bash scripts/import_sifal.sh "/chemin/phrases.tsv" --preview
bash scripts/import_sifal.sh "/chemin/phrases.tsv"
# Si nécessaire : --kab-column 2 --fr-column 4
```

Le téléchargement Hugging Face est également bloqué dans ce cloud : le vrai corpus Sifal n’est pas inclus dans le total livré. Les fichiers téléversés et rapports sont dans `artifacts/`, exclus de Git et non servis publiquement.

## Exercices et progression

La construction de phrases fonctionne sur les paires attestées. La carte retournée, le lexique cliquable, la dictée et le QCM audio restent disponibles dans l’exercice. Les modules sonores nécessitent des métadonnées d’enregistrement ; un échec de lecture est affiché sans son artificiel de substitution. Un mot sans traduction individuelle attestée est indiqué comme absent du lexique, sans alignement inventé.

Les réussites et erreurs sont vérifiées par le serveur et enregistrées dans la progression anonyme de l’appareil. Le dessin, les trois petites leçons de lettres et l’enregistrement/écoute locale restent disponibles. Aucun modèle de prononciation ni maîtrise linguistique automatique n’est simulé.

## Vérifications

```bash
cd backend
../.venv/bin/python -m pytest -q
cd ../frontend
npm run typecheck
npm run build
cd ..
.venv/bin/python scripts/topic_browser_smoke.py
.venv/bin/python scripts/phrase_public_mobile_smoke.py
```

Playwright et Chromium sont nécessaires aux tests navigateur, ainsi que le site démarré. Les tests utilisent une base de développement, jamais une base de production, et nettoient leurs données d’essai. Les anciens points d’entrée `library_browser_smoke.py` et `vocabulary_browser_smoke.py` exécutent désormais le parcours commun par thèmes. Les anciens documents d’audit décrivent des versions historiques ; le fonctionnement actuel est celui-ci.

### Alphabet et exemples tifinagh

La bibliothèque contient 33 lettres de base et 110 exemples liés aux textes du
cours LibreLingo. Les mots sont affichés après sélection d’une lettre, en tifinagh, kabyle latin et français. Seuls les mots commençant par cette lettre sont proposés ; il n’y a aucun remplacement par un mot qui la contient seulement.
Le tifinagh est une translittération générée selon une convention documentée,
avec mention « à vérifier », et non une orthographe attestée dans le corpus.
Les sources téléchargées et leurs limites figurent dans
[content/sources/alphabet/README.md](content/sources/alphabet/README.md).

Après récupération d’une mise à jour de l’interface :

```bash
npm --prefix frontend run build
bash scripts/start.sh
```

Le démarrage ajoute les nouvelles lettres et enrichit les anciennes fiches
inchangées, en conservant leur statut éditorial. Les fiches modifiées dans
l’administration sont préservées. Le générateur reproductible est
`scripts/build_alphabet.py` ; il ne modifie pas les phrases importées.

### Écouter les phrases

Les phrases par thème et les fiches de bibliothèque affichent un lecteur quand
un enregistrement avec crédits est disponible. Le lecteur commun utilise un bouton lecture/pause et une barre de progression
personnalisés, aussi dans les exercices. Le filtre « Avec audio uniquement »
des thèmes est appliqué avant le comptage et la pagination, en conservant le mot
sélectionné. Le lecteur charge le son au clic, propose les autres voix
et interrompt le lecteur précédent. Les crédits sont accessibles sous le lecteur.
La section d’enregistrement « Ma voix » a été retirée.

Test navigateur avec WAV synthétiques (sans prétendre être du kabyle parlé) :
`KABYLE_BASE_URL=http://127.0.0.1:3000 .venv/bin/python scripts/audio_browser_smoke.py`.

### Ajouter un mot et tester automatiquement ses associations

Dans **Gestion des contenus**, saisir le jeton admin puis utiliser **Ajouter un
mot et tester ses associations** : mot kabyle, traduction française, variantes
facultatives, et jusqu’à 20 phrases bilingues facultatives.

1. **Tester sans enregistrer** affiche une catégorie proposée et les phrases
   correspondantes déjà présentes dans toute la base, sans ajouter de fiche.
2. La proposition combine le dictionnaire existant, le complément versionné
   `content/catalog/word-category-hints.json`, les mots ayant le même sens et,
   à défaut, des contextes concordants. Aucun service IA externe n’est appelé.
   Les sens ambigus restent à préciser ; une catégorie peut être choisie avant
   de relancer l’aperçu. Ce classement reste une proposition à vérifier.
3. **Enregistrer dans la base** ajoute une fiche publique à vérifier et les
   phrases renseignées, en évitant les doublons et en préservant les corrections
   des fiches existantes. Les phrases facultatives sans correspondance bilingue
   doivent être corrigées avant enregistrement.
4. Dans le parcours public, **Utiliser ce mot** cherche à chaque consultation
   dans tout le corpus, sans se limiter au thème actuel. Les phrases importées
   après la création du mot sont donc également trouvées.

L’association exige une forme kabyle entière et le sens français correspondant.
Elle accepte les variantes explicites et celles déjà connues du même concept,
conserve les distinctions kabyles (t / ṭ, etc.), les crédits et le filtre audio.
Elle ne génère ni phrase, ni traduction, ni flexion kabyle inconnue. Un même mot
français peut encore avoir plusieurs sens : les résultats restent des
associations automatiques à relire.

Les métadonnées de classement, leur version et la signature du texte sont
conservées dans le JSON de la fiche. Le recalcul des champs dérivés respecte ces
informations tant que les textes n’ont pas changé. Les associations sont
calculées en direct : aucune copie des phrases sources ni réimportation globale
n’est nécessaire. Le contenu saisi dans l’admin est une contribution manuelle,
pas une nouvelle citation de LibreLingo ou de Tatoeba.

Contrôle navigateur (données synthétiques, supprimées après essai) :
`KABYLE_BASE_URL=http://127.0.0.1:3000 .venv/bin/python scripts/word_laboratory_browser_smoke.py`.
Le serveur et le script doivent disposer du même `ADMIN_TOKEN`.

### Corpus structuré et parcours par niveaux

La migration `007` ajoute une projection relationnelle des sources, versions,
unités lexicales, formes, phrases, traductions et audios, et un modèle
**cours → niveau proposé → unité → leçon → activité**. Les activités référencent
les contenus existants ; les imports et corrections ne sont pas supprimés.

```bash
bash scripts/organize_data.sh
```

Le traitement est reprenable par lots de 500, avec progression affichée. Le
site reste utilisable sans attendre une organisation complète du gros corpus.
Les nouveaux mots admin sont projetés immédiatement ; les gros imports sont
marqués à traiter. La commande `bash scripts/start.sh` ne lance pas ce gros
traitement automatiquement à chaque ouverture.

**Mon parcours** affiche cinq leçons pilotes A1 proposées ; A2 est à composer.
**Gestion des contenus → Organiser les données et les parcours** affiche les
compteurs et permet de composer/modifier les leçons, ajouter des niveaux,
ordonner les activités et exporter le plan. Les réponses sont vérifiées côté
serveur, les révisions et essais conservés. Les prérequis restent des conseils,
et les contenus à vérifier sont publics.

[Architecture, limites, sauvegarde et reproductibilité](docs/data-architecture.md).
