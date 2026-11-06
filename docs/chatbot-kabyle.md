# Chatbot kabyle : entraîner puis connecter le modèle

Le site possède une rubrique **Parler kabyle**, une API de conversation et un serveur de modèle local optionnel. Le candidat est Qwen2.5-0.5B-Instruct, assez compact pour essayer sur CPU. Ses capacités en kabyle ne sont pas garanties. Le modèle n’est pas fourni préentraîné sur ton corpus : le notebook doit réellement être exécuté.

Le chatbot envoie la question, les derniers échanges et jusqu’à huit exemples retrouvés dans la bibliothèque au modèle. Cette recherche lexicale complète le modèle ; elle ne remplace pas l’entraînement et peut manquer des variantes. Les références affichées sont les exemples fournis au modèle, pas des preuves de chaque affirmation générée. Aucune voix synthétique n’est ajoutée.

## 1. Exporter depuis le PC qui contient la base complète

Dans le dossier Kabyle, après avoir récupéré cette version :

```bash
git pull
npm --prefix frontend run build
bash scripts/export_chat_dataset.sh
```

Le script affiche sa progression et produit un ZIP sous `artifacts/chat-training/`. Il utilise la base configurée dans `.env`, sans exporter les comptes, jetons ni progrès personnels. Les phrases et mots kabyle/français non rejetés sont nettoyés et dédupliqués. Les contenus signalés comme fragments, noms propres ou à réexaminer sont exclus. Les contenus encore non validés restent identifiés dans la provenance : ils peuvent contenir des erreurs.

Chaque paire génère deux tâches de traduction, sans inventer de réponses conversationnelles. Les traductions partageant un texte kabyle **ou français**, y compris transitivement, restent ensemble : environ 90 % des groupes pour apprendre, 5 % pour valider, 5 % pour tester. Les proportions exactes dépendent des groupes. La provenance, les sommes SHA-256 et la révision du code sont exportées. Le même corpus ordonné et le même code donnent le même découpage et les mêmes fichiers de données ; le dossier de sortie et l’archive sont datés.

## 2. Exécuter Colab

[Ouvrir le notebook](https://colab.research.google.com/github/liliabkm/Kabyle/blob/main/notebooks/kabyle_chat_finetune.ipynb).

Active un GPU T4, importe le ZIP et exécute les cellules. Le notebook récupère le code correspondant à l’export et installe les versions indiquées. Il utilise QLoRA 4 bits, n’entraîne que les adaptateurs et masque les instructions dans la fonction de coût. Le SHA du modèle de base est enregistré. L’environnement GPU et les calculs peuvent néanmoins introduire des variations : ce n’est pas une garantie de résultats identiques bit à bit.

Commence par `MODE = 'pilot'` (200 étapes). Ce test ne parcourt pas toute la base. `MODE = 'full'` lance une époque complète, qui peut dépasser une session gratuite. Les checkpoints sont conservés dans ton Drive pour reprendre. Aucun service payant n’est lancé automatiquement. Vérifie également les conditions du modèle et les métadonnées des sources avant redistribution.

Le notebook compare les traductions de test du modèle de base et du modèle adapté et exporte `evaluation.json`. La relecture par un locuteur reste nécessaire, surtout pour une conversation libre : les données actuelles entraînent principalement la traduction. Une adaptation peut dégrader les résultats ; utilise le modèle de base si la comparaison n’est pas satisfaisante. Pour entraîner une conversation pédagogique, il faudra ensuite des dialogues et corrections relus, et un jeu de test conversationnel indépendant.

## 3. Télécharger l’adaptateur et démarrer le serveur

Télécharge le ZIP proposé en fin de notebook. Décompresse-le dans `artifacts/chat-model/`, pour obtenir `artifacts/chat-model/adapter/training_manifest.json`.

```bash
bash scripts/install_chat_model.sh
bash scripts/start_chat_model.sh
```

L’installation crée un environnement Python séparé `.venv-chat` avec PyTorch CPU. Le premier lancement télécharge le modèle de base depuis Hugging Face. Prévoir plusieurs Go de disque et de mémoire libre ; le CPU peut répondre lentement. Garde ce terminal ouvert. Dans un autre terminal, lance le site :

```bash
bash scripts/start.sh
```

Ouvre **Parler kabyle**, puis clique sur **Vérifier la connexion**. Le statut « Modèle adapté chargé » n’apparaît que lorsque le worker a chargé un adaptateur terminé. Pour comparer sans adaptation : `bash scripts/start_chat_model.sh --base-only`. Le serveur n’écoute que sur la machine locale. Le site fonctionne aussi sans ce processus ; seul le chat est indisponible.

Les paramètres optionnels `CHAT_MODEL_BASE_URL` et `CHAT_MODEL_NAME` sont documentés dans `.env.example`. La configuration par défaut utilise `http://127.0.0.1:8010/v1`. Aucun abonnement ni clé API n’est nécessaire pour ce serveur local. Un déploiement public demandera une capacité d’inférence dédiée et des limites par utilisateur ; ce worker traite une génération à la fois et refuse les requêtes simultanées.
