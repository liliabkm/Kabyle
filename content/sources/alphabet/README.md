# Sources de l’alphabet et limites

Les 33 lettres de base du parcours utilisent une convention explicitement définie
par `scripts/build_alphabet.py` (`kab-latin-tfng-v1`). Le signe de labialisation
ʷ → ⵯ est présenté séparément ; les lettres d’emprunts p/v et les notations
phonétiques de spirantisation ne font pas partie de ces 33 fiches.

- UnicodeData 16.0.0 : noms et points de code des glyphes. Extrait téléchargé,
  checksum du fichier complet dans manifest.json. Unicode ne valide pas une
  orthographe ou une traduction kabyle.
- https://github.com/Anir-Ln/Tifinagh-Latin-transliteration : tableau de
  correspondances consulté (README téléchargé ; licence non précisée).
- https://github.com/salimadour31-boop/illustrator-tifinagh-latin : seconde
  référence de correspondances, notamment ǧ → ⴵ ; licence MIT. Il s’agit d’un
  outil communautaire, pas d’une norme linguistique officielle.
- LibreLingo-KAB-from-FR, révision e426e0fa052da1c91b6efd800d8469e6940757d5 :
  les textes kabyles latins et français sont conservés, avec leurs citations
  individuelles dans chaque exemple. Ils restent à relire linguistiquement.

**Aucun corpus kabyle–tifinagh–français vérifié n’a été téléchargé.** Les exemples
tifinagh sont générés mécaniquement et portent `generated_pending_review`.
Ils n’ajoutent aucune phrase fabriquée ni traduction mot à mot déduite.
Convention e → ⴻ et h → ⵀ ; ⵁ existe dans d’autres usages du h kabyle.
Les caractères latins inconnus entraînent l’exclusion de l’exemple, sans
substitution silencieuse. Seuls les mots commençant par la lettre choisie sont proposés ; certaines
lettres n’ont pas encore de mot dans le catalogue correspondant à ce critère.

Régénération : `.venv/bin/python scripts/build_alphabet.py` depuis la racine.
Les fiches publiées peuvent être relues et modifiées dans l’espace admin ;
les nouvelles lettres sont publiques avec statut à vérifier. Au démarrage,
les lettres modifiées manuellement ne sont pas écrasées.
