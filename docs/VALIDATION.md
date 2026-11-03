# Parcours par thèmes illustrés — 3 novembre 2026

- Audit exhaustif des 442 entrées lexicales et 133 phrases livrées : 310 reclassements, regroupements par sens, 13 éléments techniques/incohérents distingués du vocabulaire. Rapport reproductible : `content/catalog/organization-report.json`.
- **43 tests API passent** : couverture des entrées, souris/éléphants/boissons/pronoms, faux positifs français, regroupement des formes, appartenance multi-thème, correspondance bilingue entre mot et phrase, contexte kabyle réellement présent et catégories éditoriales personnalisées. Les tests API antérieurs restent inclus.
- Schéma PostgreSQL temporaire : migrations 001 à **006** et seed réussis. Vérification des classements principaux de souris, éléphant, café, nous et de la fiche source incohérente `ṭam`. Aucun texte ni validation d’une fiche existante n’est remplacé par l’organisation.
- Compilation Next.js/TypeScript réussie.
- `scripts/topic_browser_smoke.py` passe avec les vraies données livrées : cartes illustrées sans filtre apprenant, 3 fiches fruits, 12 fiches animaux, clic sur un mot, contexte attesté et surligné, cinq contextes de cheval, construction de la phrase des fraises, progrès réel et lettres consultables. Ordinateur, 390 px et 320 px, sans erreur JavaScript ou débordement.
- Captures locales ignorées par Git : `artifacts/topics-gallery.png`, `topic-animals-words.png`, `topic-horse-contexts.png`, `topics-mobile.png`.

Les sections ci-dessous sont historiques, notamment les anciens écrans utilisant des listes de filtres publiques.

---

# Tatoeba et activités de phrases — 3 novembre 2026

- **38 tests API passent** contre PostgreSQL réel : alignement direct, archives compressées, voix multiples, dédoublonnage, conservation des textes/catégories/validations, identité de source après correction des deux textes, lexique exact et variantes, exercices corrigés côté serveur et progression idempotente.
- Une base temporaire vierge a reçu les migrations **001 à 005** et le catalogue complet. Les index de difficulté/audio/lexique sont alimentés. Le schéma de vérification a été supprimé ensuite.
- Compilation Next.js/TypeScript réussie.
- `scripts/tatoeba_browser_smoke.py` passe : import avec aperçu, attribution de niveau A1 et note grammaticale dans l’éditeur, carte retournée, lexique, plusieurs métadonnées de voix, lecture HTML audio, dictée, QCM, puzzle, erreur/réessai et progression réelle. Les trois phrases sont des fixtures temporaires ; le son est un signal de test généré, pas un enregistrement Tatoeba réel. Les données de test sont nettoyées.
- `scripts/phrase_public_mobile_smoke.py` passe à 320 px : une vraie phrase LibreLingo déjà livrée s’ouvre depuis la bibliothèque publique, propose la construction, puis revient à la lecture. Aucun jeton, son inventé ou progrès de lecture n’est requis.
- Régressions navigateur : accueil/jeux/dessin, leçons de lettres, ancien parcours de mots et bibliothèque par catégories passent, sur ordinateur et téléphone.
- Les téléchargements `tatoeba.org` et `downloads.tatoeba.org` renvoient **403 depuis ce cloud**. Le nombre réel de phrases/audio Tatoeba n’a donc pas été vérifié et aucun corpus réel n’a été importé. Le script `--download` et le téléversement sont disponibles pour une machine autorisant ces destinations. La lecture des véritables MP3 doit encore être vérifiée avec ces fichiers.

Les vérifications ci-dessous concernent les versions précédentes.

---

# Validation actuelle — 3 novembre 2026

- 28 tests API passent contre PostgreSQL réel : catalogue public à vérifier, authentification des écritures, validation en un clic, catégories, variantes, pagination SQL, import TSV, dédoublonnage et conservation des corrections/validations.
- Schéma PostgreSQL temporaire vierge : migrations 001 à 004 et seed réussis, 8 lettres, 442 entrées lexicales, 133 phrases. Recherche et empreintes de paires renseignées. Schéma de vérification supprimé ensuite.
- Compilation Next.js/TypeScript réussie.
- Tests Chromium : navigation/jeux libres, parcours guidé, leçon publique de mots et phrases avec huit réussites et une erreur enregistrées, bibliothèque publique par catégories, validation et classement admin, affichage des 30 photos réelles. Affichages ordinateur, 390 et 320 px vérifiés selon les parcours.
- Test TSV navigateur : téléversement supérieur à 1 Mo, aperçu et sélection des colonnes, 25 000 lignes **synthétiques** donnant un ajout et 24 999 doublons, classement proposé et visibilité publique sans validation. Entrée de test supprimée après vérification. Ce test n’est pas un import du vrai corpus Sifal.
- L’URL du TSV Sifal demandé renvoie HTTP 403 depuis ce cloud. Le corpus réel reste à importer via le téléchargement serveur ou le téléversement local disponible dans l’administration.
- Une dépréciation Starlette/AnyIO est émise par les tests ; aucune erreur de test. Aucun benchmark linguistique ni étude auprès d’enfants n’est revendiqué.

Les résultats ci-dessous sont historiques et décrivent notamment l’ancienne politique de brouillons privés, remplacée par la visibilité publique avec badge de validation.

---

# Validation — 2 novembre 2026

Vérifications réalisées dans l’instance cloud courante, contre PostgreSQL 17 réel.

| Vérification | Résultat |
|---|---|
| Installation complète `bash scripts/install.sh` | Réussie : dépendances verrouillées, base, migration, import et build |
| Migration Alembic `upgrade head` et double import | Réussis, huit lettres sans doublons |
| Tests API `python -m pytest -q` | 7 tests passés ; 1 avertissement de dépréciation Starlette/AnyIO, aucune erreur |
| TypeScript `npm run typecheck` | Réussi |
| Production `npm run build` | Réussi, dernière version modulaire avec association de cartes |
| Démarrage puis arrêt/redémarrage avec `scripts/start.sh` | Réussis, contrôle `/api/health` via Next.js et requête PostgreSQL |
| Chromium ordinateur 1440 px | Navigation, association, quiz, persistance après rechargement, canvas et export PNG, effacement du tracé, état lexical vide et admin protégée : réussis ; aucune erreur JavaScript relevée |
| Chromium mobile 390 px | Menu et huit fiches accessibles, aucune largeur débordante détectée |
| Captures | `artifacts/desktop.png`, `artifacts/mobile.png` (générées, ignorées par Git) |

Les tests API couvrent calcul serveur de réponse, erreurs et progression, répétition d’une tentative sans double comptage, isolation entre deux navigateurs anonymes, suppression, import atomique, accès admin, exclusion des brouillons, rejet des publications incomplètes et indisponibilité IA explicite.

Le lancement Next.js doit disposer des permissions réseau et de sous-processus de cet environnement cloud. Un premier build en bac à sable restreint ne pouvait pas analyser la sortie d’un sous-processus TypeScript ; le build autorisé avec les permissions nécessaires a réussi, sans désactiver les contrôles TypeScript.

## Non vérifié / absent

- Aucun entraînement ou benchmark IA ; voir `ml/EVALUATION.md`.
- Aucun test sur microphone physique ni sur gestes tactiles d’un téléphone physique. Le canvas a été exercé avec des événements pointeur Chromium.
- Aucun contenu lexical/audio exploitable publié : les objectifs de 30 mots, photo-quiz avec lexique réel et audio ne sont pas satisfaits.
- Pas de test de charge, de déploiement public ou de restauration dans une nouvelle tâche cloud.
- La publication de l’environnement cloud est distincte de l’envoi du code sur GitHub ; elle n’a pas été effectuée lors de cette validation.

La fonctionnalité d’enregistrement est implémentée mais ne reçoit pas de certificat de qualité ASR : aucune transcription automatique n’est réalisée. La comparaison de textes est testée séparément.

## Refonte ludique

Compilation TypeScript/Next.js réussie. Test Chromium réexécuté : bouton d’accueil vers le quiz, navigation simplifiée, association, réponses sauvegardées après rechargement, export/effacement du dessin, état de vocabulaire indisponible, administration protégée. Sur viewport mobile 390 px : navigation, affichage sans débordement, quatre réponses et cibles d’au moins 44 × 44 px vérifiées. Captures mises à jour dans artifacts/desktop.png, mobile.png et mobile-quiz.png. Mascotte SVG originale, sans image tierce ni nouvelle dépendance. Pas de test auprès d’enfants ni d’audit d’accessibilité exhaustif.

## Catalogue lexical et photographique

- Migration 002 appliquée sur PostgreSQL : table media_asset créée. Import réel : 61 brouillons, 30 photos ; second import et relance : zéro ajout, corrections conservées.
- Tests API : 12 tests passés, dont intégrité SHA-256 des 30 JPEG servis, accès admin, refus de publication malgré des champs de relecture remplis si la licence reste bloquée, chemins hors du dossier média rejetés et conservation d’une correction lors du seed.
- Test Chromium du catalogue : recherche, affichage des 30 images (dimensions naturelles 100 × 100 vérifiées), association à un brouillon avec crédits, conservation des blocages et exclusion de l’API publique. La fiche modifiée par ce test est restaurée. L’API d’administration de test utilise un jeton temporaire en mémoire, jamais celui du .env.
- Bibliothèque vérifiée à 390 px sans débordement. Capture : artifacts/photo-library.png. La vignette doit rester petite : pas de prétention à la haute définition ni de test auprès d’enfants.
- Collecte répétée avec les fichiers déjà contrôlés : aucun téléchargement nécessaire, mêmes 61/30, fichier YAML invalide toujours exclu et signalé.
- Aucun mot supplémentaire publié dans les jeux, aucune conversion tifinaghe automatique, aucune inférence de traduction ou d’audio.

## Parcours pédagogique guidé

Le test Chromium `scripts/guided_browser_smoke.py` passe : découverte avant les questions, masquage/révélation de l’équivalent latin, erreur volontaire puis nouvelle tentative, trois réponses correctes enregistrées et une erreur réelle dans PostgreSQL, bilan de réussite, atelier limité aux trois lettres vues, proposition de la leçon suivante, conservation des résultats après rechargement. Disposition vérifiée à 390 et 320 px sans débordement. Les tests des exercices libres et du dessin passent également. Compilation Next.js/TypeScript réussie. Aucune modification de schéma ni dépendance ajoutée pour ce parcours.

Captures : artifacts/learning-home.png, guided-discovery.png, guided-success.png, guided-mobile.png. Aucune étude de l’efficacité pédagogique ni validation auprès d’enfants n’a été réalisée ; il s’agit d’un parcours utilisable techniquement avec le sous-ensemble graphique déjà documenté. Le vocabulaire en brouillon reste exclu.

## Mots et phrases en aperçu privé

Migration 003 appliquée, leçon stockée en base, trois mots existants référencés et trois phrases sources ajoutées en brouillon. Suite API : **18 tests passés**, dont accès public refusé, authentification privée, phrase exacte, variante attestée, ordre incorrect, conservation des diacritiques et absence d’écriture dans la progression publique. Compilation Next.js/TypeScript réussie.

`scripts/vocabulary_browser_smoke.py` passe sur une API réelle avec un jeton temporaire : carte masquée/révélée, trois contextes, erreur volontaire et réessai, reconnaissance, trois phrases reconstruites, complétion, rappel écrit, huit réponses correctes, bilan de séance et absence de progrès public. Affichage vérifié à 390 et 320 px. Les exercices libres existants passent aussi. Captures : artifacts/vocabulary-word.png, vocabulary-context.png, vocabulary-cloze-mobile.png. Le test utilise des réponses d’exercices réels, sans simuler une prédiction IA.

Sifal/Kabyle-French : l’audit de métadonnées n’a pas pu accéder au serveur (tunnel proxy refusé HTTP 403). Aucune ligne importée, aucune licence ni qualité supposée. Rapport local ignoré par Git : artifacts/sifal-audit/report.json. Le collecteur de l’aperçu a été rejoué avec la révision source figée, sans changement des sorties.

## Bibliothèques par catégories

Import vérifié : 112 nouvelles phrases ajoutées aux 3 déjà présentes, total 115 ; 176 propositions de catégorie pour les mots/phrases sources non modifiés. Second seed : zéro ajout et zéro reclassification. Aucun brouillon publié.

**22 tests API passent** : lecture publique sans progression, recherche exacte d’une lettre et en tifinagh, pagination, filtre de catégorie, tentatives de lecture publique de brouillons refusées, accès privé aux 115 phrases, changement de catégorie conservant texte/statut et catégorie conservée après seed. Compilation TypeScript/Next.js réussie.

`scripts/library_browser_smoke.py` passe : 8 lettres lisibles sans jeu, recherche, états vides publics pour les brouillons, filtres administrateur par type/catégorie, édition de la catégorie d’une phrase sans changer son statut ni son texte, lecture privée paginée des 115 phrases et filtrage Fruits/fraises. Largeurs 390/320 px sans débordement. Le contenu de test est restauré. Les tests du dessin/exercices existants et de l’association des photos passent aussi. Captures : artifacts/reading-letters.png, reading-phrases-private.png.
