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
