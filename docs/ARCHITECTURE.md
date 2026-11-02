# Architecture de la première version

Monolithe modulaire : Next.js/React/TypeScript pour l’interface, FastAPI pour la logique, SQLAlchemy/PostgreSQL pour le stockage, Alembic pour les migrations.

- `frontend/app` : parcours et mise en page ; `frontend/components` : quiz d’association, canvas tactile, pratique locale et administration ; `frontend/lib` : types et accès API. Les composants lisent leurs contenus depuis l’API, jamais depuis un vocabulaire codé dans React.
- `backend/app/models.py` : contenus éditoriaux (variété ISO 639-3 `kab`, script ISO 15924 `Tfng`, traductions françaises et médias dans le document JSON), progression anonyme et tentatives idempotentes.
- `backend/app/main.py` : API OpenAPI, contrôle de publication et autorisation éditoriale. Les réponses sont vérifiées sur le serveur. Cookies anonymes HttpOnly/SameSite strict, 1 an. Le serveur garde les progrès ; effacement volontaire possible.
- `backend/app/services.py` : interfaces vision et voix et stockage local sécurisé contre les chemins sortants. Fournisseurs IA actuellement indisponibles, sans faux scores. Le futur adaptateur S3 doit implémenter un vrai stockage, non fourni ici.
- `content` : données initiales reproductibles, indépendantes de l’UI. Les mots sont extensibles avec listes `images`, `audios`, `examples`, `sources` ; chaque média a URL, auteur et licence. Une paire audio–texte doit être vérifiée, jamais assemblée implicitement entre corpus.
- `scripts/import_content.py` : import JSON via API. Toute la liste est validée avant écriture. Les brouillons ne sortent jamais dans l’API publique.

Le parcours principal comporte 8 lettres, choix multiple et saisie de transcription. Un succès planifie la révision à 1, 2, 4, 8, 16 puis 30 jours ; une erreur remet la fiche à aujourd’hui. Le résultat et l’erreur sont conservés. Il ne s’agit pas d’un algorithme SM-2.

Le tracé se fait en canvas haute résolution avec Pointer Events et export PNG manuel. L’enregistrement vocal via MediaRecorder est local en mémoire et peut être écouté puis supprimé. Le microphone nécessite HTTPS hors de localhost et une autorisation du navigateur. Aucun fichier vocal n’est téléversé. La comparaison manuelle de textes utilise un alignement de mots ; ce n’est pas une note de prononciation.

## Convention tifinaghe

Sous-ensemble d’initiation : a ⴰ, b ⴱ, d ⴷ, f ⴼ, i ⵉ, l ⵍ, m ⵎ, n ⵏ. Correspondances des noms Unicode vérifiées avec `unicodedata`, caractères U+2D30, U+2D31, U+2D37, U+2D3C, U+2D49, U+2D4D, U+2D4E, U+2D4F. Ce choix est une convention pédagogique limitée, pas une norme exhaustive d’écriture du kabyle ni une transposition automatique de l’alphabet néo-tifinagh marocain. Il n’enseigne pas encore la spirantisation, les emphatiques, la gémination ou la labialisation. Les indications phonétiques sont des valeurs de base, pas des enregistrements de locuteurs. Une relecture linguistique kabyle demeure nécessaire avant extension et publication lexicale.

## Administration et sécurité

`ADMIN_TOKEN` généré aléatoirement dans `.env` au premier setup, non versionné. Jeton Bearer saisi dans l’interface, mémoire seulement. Pour la production : HTTPS, `COOKIE_SECURE=1`, secrets et mot de passe PostgreSQL propres au déploiement, authentification nominative, droits éditoriaux, journal d’audit, quotas et limitation de débit sont à ajouter. Cette livraison est un environnement de développement, pas un déploiement public sécurisé.

Les structures JSON facilitent les ajouts sans migration, mais la validation humaine des sources n’est pas automatique. Les contrôles API imposent des métadonnées, ils ne certifient pas la justesse d’une traduction ni la licence saisie. Le stockage objet, l’import automatique Wikimedia/Common Voice ne sont pas encore implémentés. Les cartes d’association sont opérationnelles avec les lettres ; les photos de vocabulaire s’activent avec des mots validés.
