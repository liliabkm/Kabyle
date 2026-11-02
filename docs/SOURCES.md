# Audit des sources — 2 novembre 2026

| Source | Vérification effectuée | Licence et compatibilité | Décision |
|---|---|---|---|
| [KabTatoebaCorpus](https://github.com/KabyleAI/KabTatoebaCorpus) | Clone Git en lecture, commit `585acbde77221211c4f4a45edebaed29adb16795`. README et fichiers examinés : export de février 2021, texte FR–kabyle et fichiers détaillés. | Pas de fichier LICENSE dans ce checkout. Les paires seules ne suffisent pas à relier une traduction à ses auteurs et droits individuels. Une licence générale de Tatoeba ne doit pas être appliquée sans vérifier provenance et conditions d’export. Pas d’audio. | Aucun texte importé ni redistribué. Obtenir un export avec identifiants et attributions pour un import reproductible. |
| [Tifinagh-MNIST](https://github.com/iseddik/Tifinagh-MNIST) | Clone Git, commit `af0085cfc0fc1b97a5e6e8a68a9675cfd4d9ce00`. README annonce 82 500 images / 33 classes. Le code référence `drive/MyDrive/DATA2/`. | Images d’entraînement absentes du dépôt, pas de LICENSE ni mapping numéro de classe → caractère. Les 33 classes ne constituent pas à elles seules un alphabet kabyle validé. | Aucune image ni code source tiers redistribué ; aucun entraînement possible sur cette seule ressource. |
| [Common Voice Kabyle](https://mozilladatacollective.com/datasets/cmu5xcvp800eao107zfex7alc) | HTTPS : proxy cloud 403. Métadonnées et conditions non accessibles. | Licence, version, consentement et paires audio–texte à vérifier sur la version exacte. | Aucun téléchargement/import ; aucun rapprochement supposé avec Tatoeba. |
| [Wikimedia Commons](https://commons.wikimedia.org) | Destination ajoutée au brouillon réseau pour le prochain audit ; pas de média récupéré. | Licence, auteur et attribution à relever pour chaque fichier, pas seulement pour le site. | Aucune photo tierce utilisée. Les décors de l’UI sont des formes CSS/SVG originales. |
| [Wiktionnaire francophone](https://fr.wiktionary.org) | HTTPS : proxy cloud 403, domaine demandé au brouillon. | Chaque entrée doit explicitement identifier le kabyle, révision et attribution/licence à conserver. | Aucun lexique importé. |
| [Unicode](https://www.unicode.org/charts/PDF/U2D30.pdf) | Les 8 caractères ont été vérifiés localement avec la base Unicode Python, noms YA/YAB/YAD/YAF/YI/YAL/YAM/YAN. Le PDF distant n’a pas été téléchargé. | Unicode License v3 pour les données de caractères. Pas une source de traductions kabyles. | Sous-ensemble graphique utilisé, périmètre documenté dans ARCHITECTURE.md. |
| [Noto Sans Tifinagh](https://github.com/google/fonts/tree/main/ofl/notosanstifinagh) | Police et OFL téléchargées depuis raw.githubusercontent.com avec TLS actif. | SIL Open Font License 1.1 ; auteurs : voir `frontend/public/FONT-LICENSE.txt`. | Police redistribuée avec sa licence, servie localement. |

Les attributions des contenus publiés sont accessibles depuis leurs fiches. Les huit lettres ne sont pas un corpus de vocabulaire validé par un locuteur. Objectif d’environ 30 mots illustrés : **non atteint**, faute de sources lexicales et médias dont la validation soit établie. Aucun contenu n’est inventé pour remplir cet objectif.

## Procédure d’ajout

1. Relever l’URL précise, l’auteur, la licence et l’attribution du texte et de chaque média ; conserver l’identifiant/version de la source.
2. Vérifier variété kabyle, latin, transcription tifinaghe suivant une convention étendue documentée, traduction, exemple et droits.
3. Importer en `draft`, effectuer une relecture humaine, renseigner `reviewed_by` et `reviewed_at`, puis publier en `validated`.
4. Les mots publiés doivent avoir au moins une illustration attribuée ; ne jamais utiliser une recherche Google comme justificatif de droits.

## Nouveau catalogue lexical et photographique

Un second audit a identifié le cours [LibreLingo-KAB-from-FR](https://github.com/LibreLingo/LibreLingo-KAB-from-FR) et les photos [Fruits-360](https://github.com/fruits-360/fruits-360-100x100). **61 entrées lexicales attestées, non relues, restent en brouillon ; 30 photos sont importées et attribuées dans une table distincte. Aucun mot supplémentaire n’est publié dans les leçons.**

La licence du texte doit être clarifiée : le LICENSE racine du cours est CC BY-NC-SA 4.0 mais `course/course.yaml` annonce CC BY-SA 4.0. L’import conserve le signalement et les blocages. Les photos ont une licence CC BY-SA 4.0 explicite, auteur Mihai Oltean ; elles sont réutilisées sans modification des pixels, avec noms locaux et empreintes vérifiables. Les justifications et attributions sont dans content/licenses et dans chaque ligne du catalogue. Voir [DATA-CATALOG.md](DATA-CATALOG.md) pour les versions, les sources écartées et les commandes de collecte.
