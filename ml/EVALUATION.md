# Évaluation des modèles

Aucun modèle n’a été entraîné ou évalué : il n’existe donc ni précision globale, ni score par caractère à annoncer. Aucun résultat IA n’est simulé dans l’application.

## Vision

Tifinagh-MNIST, checkout inspecté dans l’audit SOURCES.md : code public, données et labels absents, licence non établie. Bloqueurs avant entraînement : obtenir une distribution autorisée et son checksum, un mapping vers les points Unicode, vérifier l’intersection avec les 8 classes et disposer des identifiants de scripteurs. Ensuite : split par scripteur (sans fuite), baseline CNN ou classificateur simple, matrice de confusion et précision/rappel par classe, calibration et seuil d’abstention sur validation. Le test tenu à part doit inclure des PNG exportés du canvas, avec consentement et sans mélange avec l’entraînement. Les glyphes de polices ne peuvent pas remplacer cette validation manuscrite.

## Voix

Common Voice n’a pas pu être audité : proxy 403. Aucun audio ni modèle téléchargé. MMS multilingue (`facebook/mms-1b-all`) constitue une piste à vérifier pour `kab`, avec licence et dépendances exactes ; ni compatibilité réelle ni qualité ne sont établies ici. Sa page était également bloquée par le proxy. Aucun choix de fine-tuning n’a été effectué.

Prévoir un benchmark consentant avec locuteurs disjoints, normalisation documentée du kabyle, WER/CER, cas courts et bruités, audit des accents et taux d’abstention avant adaptation. Ne pas convertir un WER en note de prononciation. Les interfaces `VisionProvider` et `SpeechProvider` permettent un fournisseur évalué sans modifier les exercices.

## État livré

- Tracé tactile, export manuel et comparaison visuelle : opérationnels.
- Enregistrement local, écoute et effacement : implémentés ; accès réel au microphone dépend du navigateur et n’a pas été validé avec un appareil physique.
- Reconnaissance visuelle et transcription automatique : indisponibles explicitement.
- Comparaison de textes saisis : testée ; pas une inférence vocale.
