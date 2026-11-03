> Historique : ce document décrit une étape antérieure. Depuis le 3 novembre 2026, les brouillons sont publics et le catalogue complet contient 442 entrées lexicales et 133 phrases. Voir le [README actuel](../README.md) pour la validation en un clic et l’import TSV Sifal.

# Utiliser les mots et les phrases pour apprendre

Le catalogue de 61 entrées sert de réserve éditoriale, pas de liste à mémoriser d’un seul coup. Le premier parcours d’essai sélectionne trois unités déjà attestées dans cette réserve et les rattache à des phrases sources exactes. Les mots et les phrases ne sont ni traduits ni réécrits par un modèle.

## Exemples réellement consultés

| Référence | Ce qui a été examiné | Principe retenu |
|---|---|---|
| [LibreLingo : formats de défis](https://github.com/LibreLingo/LibreLingo/blob/3c4bcfb3ef999ae48ee3d361afb0c4a5fa317dee/docs/courses/challenge.md) | Document `docs/courses/challenge.md` et captures `cards-challenge.png` / `chips-challenge.png`, dans le dépôt public ; types Cards, Short input, Options, Chips, Listening. | Partir des mots illustrés, passer aux phrases, construire la réponse avec des jetons puis retrouver sans aide. Les captures n’ont pas été copiées dans l’application. |
| [Manuel Anki : studying](https://github.com/ankitects/anki-manual/blob/91f7485236db2a89d2a8abaed618976caf971de2/src/studying.md) | Partie « Questions » : question avant réponse, rappel, correction et choix Again/Hard/Good/Easy. | Ne pas seulement relire ; cacher la réponse, la retrouver, puis utiliser la correction. Notre interface n’est pas une copie d’Anki et n’implémente pas FSRS. |
| [Duolingo : recherche Half-Life Regression](https://github.com/duolingo/halflife-regression) | README du dépôt public, révision `0041df0dcd436bf1b4aa7a17a020d9c670db70d8`, renvoyant aux travaux de Settles et Meeder (2016). | L’historique de rappel et le temps depuis la dernière rencontre sont pertinents pour organiser la révision. Le projet n’entraîne pas HLR ; la répétition espacée des lettres demeure son algorithme simple déjà documenté. |
| Sites web actuels Duolingo / Memrise | Requêtes refusées par le proxy, HTTP 403. | Aucune affirmation de consultation de leurs interfaces actuelles ni de leurs articles inaccessibles. |

Ces références justifient les types d’activités, pas une efficacité démontrée de ce prototype auprès d’enfants. Aucun code, capture ou élément de marque de ces plateformes n’a été réutilisé pour construire l’interface.

## Parcours livré

1. **Je découvre** : image ou illustration originale, mot latin kabyle et traduction française ; possibilité de cacher le mot.
2. **Je comprends** : phrase kabyle source et traduction source, mot cible surligné dans son contexte.
3. **Je retrouve** : trois reconnaissances image–mot, trois reconstructions de phrases avec des jetons, une complétion de phrase et un rappel écrit.
4. **Correction** : vérification sur le serveur, comparaison à la forme source et aux variantes explicitement attestées ; les diacritiques ne sont pas supprimés. Une erreur présente la correction et autorise un nouvel essai.
5. **Bilan d’essai** : huit réponses trouvées, possibilité de revoir les cartes. Ce bilan privé n’est pas enregistré comme progression d’une leçon publiée et ne constitue pas une note de prononciation.

Les phrases exactes retenues sont `Max d aqjun`, `D agmar` et `Tizwal uṛumi d tizeggaɣin`, avec leurs traductions telles qu’elles figurent dans les fichiers YAML de la révision LibreLingo déjà auditée. Cela ne vaut pas nouvelle validation linguistique par un locuteur. Aucun tifinagh n’est produit automatiquement et aucun audio n’est associé artificiellement à ces phrases.

Les illustrations du chien et du cheval sont des SVG originaux du projet ; ce ne sont pas des photos du corpus. Pour les fraises, la même photo Fruits-360 est affichée trois fois afin d’illustrer le pluriel. Les pixels originaux sont inchangés ; l’attribution de Mihai Oltean, la licence CC BY-SA 4.0 et la présentation répétée sont indiquées dans le volet des sources.

## Séparation entre aperçu et publication

La table PostgreSQL `lesson` (migration 003) stocke la définition. `content/catalog/vocabulary-lessons.json` référence les mots existants et `preview-phrases.json` ajoute trois phrases en `draft`. Les activités sont construites à partir des champs de la base, pas d’un vocabulaire codé dans React.

L’aperçu exige ADMIN_TOKEN sur les routes `/api/admin/learning-lessons/...`. Les routes publiques excluent la leçon tant que son statut, son périmètre et tous les contenus liés ne permettent pas une publication. Les blocages de validation et de licence de l’ancien catalogue sont conservés. Le simple fait de pouvoir faire un exercice en privé ne valide pas un texte.

La licence racine du cours source est BY-NC-SA 4.0, tandis que ses métadonnées de cours annoncent BY-SA 4.0. Cette divergence reste documentée. L’aperçu est réservé à la préparation privée non commerciale, sans autorisation commerciale présumée ni publication automatique aux apprenants. Les 61 entrées ne sont pas toutes devenues des leçons.

La collecte reproductible est optionnelle (les JSON sont livrés) :

```bash
uv pip install --python .venv/bin/python -r scripts/requirements-data.txt
.venv/bin/python scripts/collect_preview_lesson.py --source-checkout /chemin/vers/LibreLingo-KAB-from-FR
```

Le checkout source doit être exactement `e426e0fa052da1c91b6efd800d8469e6940757d5`. Le script extrait les champs sources et n’active aucune publication. Le seed ne remplace pas les corrections existantes en base.

## Dataset proposé : Sifal/Kabyle-French

Lien : <https://huggingface.co/datasets/Sifal/Kabyle-French>.

L’accès aux métadonnées et à la carte du dataset a été tenté dans le cloud, mais le tunnel proxy refuse la connexion avec HTTP 403. **Licence, nombre de lignes, schéma, provenance, qualité et éventuel alignement ne sont donc pas vérifiés. Aucune ligne n’a été importée.** Un refus réseau ne prouve ni que le dataset est privé, ni qu’une clé manque, ni qu’il ne possède pas de licence.

Un outil sans dépendance supplémentaire permet de reprendre l’audit depuis un accès autorisé, notamment le PC de développement :

```bash
python3 scripts/audit_sifal.py
```

Il lit de façon bornée l’API publique et, si possible, le README de la révision exacte. Il conserve le rapport dans `artifacts/sifal-audit/`, ignoré par Git. Il ne télécharge pas le corpus complet, ne s’authentifie pas et n’importe rien. Pour examiner un JSON public de métadonnées déjà récupéré : `python3 scripts/audit_sifal.py --metadata-file /chemin/metadata.json`.

Après accès, il faut vérifier les conditions réelles et le schéma avant de choisir des exemples courts, compréhensibles, pertinents pour les débutants et correctement alignés. Un corpus de phrases parallèles n’est pas automatiquement un dictionnaire : on ne peut pas découper une phrase kabyle et une phrase française en supposant une correspondance mot à mot. Les exemples retenus doivent être révisés avant de devenir des leçons.

Les domaines de consultation ont été ajoutés au brouillon réseau sans supprimer les précédents : `datasets-server.huggingface.co`, `blog.duolingo.com`, `www.memrise.com`, `docs.ankiweb.net`. Le domaine `huggingface.co` y figurait déjà. Sauvegarder le brouillon ne l’a pas appliqué à l’instance courante ; la révision/publication des paramètres reste distincte.
