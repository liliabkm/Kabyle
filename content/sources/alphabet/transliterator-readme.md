# TranslitererTifinagh.jsx — tifinagh ⇄ latin dans Illustrator

**Version 1.0.0 · Adobe Illustrator CC 2018 à 2026 (ExtendScript) · Licence MIT · non testé dans Illustrator**

Script Adobe Illustrator qui convertit le **tamazight écrit en latin** (kabyle, chaoui, tamazight standard…) en **tifinagh Unicode**, directement dans les blocs de texte et **sans perdre la mise en forme** : chaque lettre garde sa police, son corps, sa couleur, son approche. Il fait aussi l'inverse (tifinagh → latin, pour relire un texte reçu en tifinagh) et peut seulement **corriger l'écriture latine berbère** (sosies grecs, signes combinants).

```
azul fell-awen        →  ⴰⵣⵓⵍ ⴼⴻⵍⵍ-ⴰⵡⴻⵏ
Tasdawit n Tizi Uzzu  →  ⵜⴰⵙⴷⴰⵡⵉⵜ ⵏ ⵜⵉⵣⵉ ⵓⵣⵣⵓ
Aγerbaz (γ grec)      →  Aɣerbaz            (mode « Corriger seulement le latin »)
```

Usage typique : panneaux et plaques trilingues arabe / tamazight / français, façades d'administrations, emballages, affiches, cartes de visite.

## Ce que fait le script

**Latin → tifinagh**
- Correspondances de l'**Unicode Technical Note #59** (jeux IRCAM et kabyle) et de l'alphabet latin berbère INALCO / HCA / IRCAM : a ⴰ, b ⴱ, c ⵛ, č ⵞ, d ⴷ, ḍ ⴹ, e ⴻ, ɛ ⵄ, f ⴼ, g ⴳ, ǧ ⴵ, ɣ ⵖ, h ⵀ ou ⵁ, ḥ ⵃ, i ⵉ, j ⵊ, k ⴽ, l ⵍ, m ⵎ, n ⵏ, q ⵇ, r ⵔ, ṛ ⵕ, s ⵙ, ṣ ⵚ, t ⵜ, ṭ ⵟ, u ⵓ, w ⵡ, x ⵅ, y ⵢ, z ⵣ, ẓ ⵥ, p ⵒ, v ⵠ, labialisation gʷ / g° → ⴳⵯ.
- Lettre **h** au choix : ⵀ U+2D40 (IRCAM, présent dans les polices courantes) ou ⵁ U+2D41 (Académie berbère, jeu kabyle de l'UTN #59).
- Affriquées kabyles : **ţ** (ou ț) → ⵜⵙ ou ⵜ ; **z̧** / ʒ → ⴷⵣ. Option **spirantes** ḇ ḏ ṯ ḵ → ⴲ ⴸ ⵝ ⴿ (sinon ⴱ ⴷ ⵜ ⴽ). **o** → ⵓ ou ⵧ.
- Accepte les lettres précomposées (ḍ), les signes **combinants** (d + ◌̣), les **capitales** (TAMAZIƔT → ⵜⴰⵎⴰⵣⵉⵖⵜ, le tifinagh n'a pas de casse), ğ pour ǧ, les **sosies grecs** ε / γ tapés à la place de ɛ / ɣ.
- Option **écriture informelle** : gh ⵖ, kh ⵅ, ch / sh ⵛ, tch ⵞ, dj ⴵ, 3 ⵄ, 7 ⵃ, 9 ⵇ (« · » pour séparer : g·h).
- **Protections** : mots avec lettres françaises (é è à ç ô œ) ou apostrophe (l'école) laissés tels quels ; paragraphes français / anglais reconnus par leurs mots courants (le, les, pour, dans, the, and…) laissés ; URL, e-mails, domaines, @comptes, #mots-dièse et codes avec chiffres (RN5, A4) protégés ; arabe, chiffres et ponctuation jamais touchés. Option « seulement les paragraphes qui ont une lettre berbère (ɛ ɣ ḍ ḥ ṛ ṣ ṭ ẓ č ǧ) ».

**Tifinagh → latin** (relecture) : casse au choix (minuscules, majuscule de phrase, Chaque Mot, CAPITALES), option ⵜⵙ → ţ / ⴷⵣ → z̧, lettres touarègues non prévues laissées et comptées.

**Corriger seulement le latin berbère** : ε → ɛ, Ε → Ɛ, γ → ɣ, Γ → Ɣ (seulement dans des mots latins ; le vrai grec reste intact), d / t / s / z / r / h + point souscrit combinant → lettre précomposée, c / g + caron → č / ǧ, t + cédille → ţ, ğ → ǧ (option), ț → ţ, g° → gʷ (pas 20°).

**Sortie**
- **Remplacer** dans le texte (lettre par lettre, chaque lettre convertie hérite des attributs de la lettre d'origine) ;
- **Copie convertie** dessous, au-dessus, à droite (écart en mm) ou à la même place sur un calque « Tifinagh » / « Latin » — pratique pour composer un panneau bilingue ;
- **Annotation de lecture** sous chaque texte, sur un calque **non imprimable** (lire un tifinagh sans le modifier).

**Police** : garder la police, ou appliquer une police aux seules lettres converties (bouton « Polices tifinagh » qui liste les polices installées connues : Noto Sans Tifinagh, Ebrima, Tifinaghe-IRCAM, Kigelia, Akatab, DejaVu… ; ou « Chercher une police »).

**Analyser** (sans rien modifier) : nombre de mots, exemples avant → après, mots laissés et pourquoi, lettres hors des 33 lettres IRCAM de base (ⴵ ⵞ ⵁ…, absentes de certaines polices), caractères inconnus, **polices qui ne sont pas dans la liste des polices tifinagh connues** (sinon : carrés vides à l'impression).

Autres points : textes dans les groupes parcourus, textes verrouillés / masqués ignorés, textes chaînés traités une fois, lettres sélectionnées à l'outil Texte (seule la sélection change), résultat recontrôlé après remplacement (textes à vérifier sélectionnés), dialogue français / anglais selon la langue d'Illustrator, message clair si aucun document n'est ouvert ou si rien n'est sélectionné.

## Pourquoi c'est nouveau (ce qui a été vérifié le 16 octobre 2026)

- **Illustrator** n'a aucune translittération : il faut taper le tifinagh au clavier tifinagh, ou passer par le panneau Glyphes lettre par lettre (aide Adobe « Character sets and alternate glyphs ») ; les questions de graphistes portent sur les carrés vides et la saisie (r/indesign 2022 « Using an obscure language supported in Unicode… » : projet français / arabe / amazigh, réponse : installer Noto Sans Tifinagh).
- **Convertisseurs existants = hors d'Illustrator, texte brut copié-collé, mise en forme perdue** : pages web amghnas.com, Sparkpond, anir-ln.github.io ; bibliothèques JavaScript / TypeScript / Python sur GitHub (Anir-Ln/Tifinagh-Latin-transliteration, hamza-bouqssim/Tifinagh-convert, mohsenuss91/tifinagh-transliterator, CollectivaT-dev/tifinagh_transliterator, adamoudad/tifinagh-tools) ; méthode de saisie wikimedia/jquery.ime ; claviers macOS / Linux. Aucun ne lit un document Illustrator, ne garde les attributs par caractère, ne protège les mots français / URL ni ne vérifie la police.
- **Rien sur GitHub** pour « tifinagh » en .jsx / ExtendScript (seule mention : une liste de plages Unicode dans un script de métriques de police de ten-A), ni chez creold, Hiroyuki Sato (shspage), Alexander Ladygin, wckdtall, sttk3, John Wundes, Kelso, ni plug-in Astute Graphics / Adobe Exchange ; rien pour « transliteration illustrator jsx ».
- Distinct des scripts déjà publiés dans ce compte : ReparerTexteArabeRTL (sens RTL, composeur), TypographieArabe (ponctuation arabe), AccentuerCapitales (accents français).

## Installation

1. Téléchargez `TranslitererTifinagh.jsx` (bouton « Raw » puis Enregistrer sous…).
2. Soit **Fichier > Scripts > Autre script…** (Ctrl+F12 sous Windows, Cmd+F12 sous macOS) et choisissez le fichier ;
   soit copiez-le dans le dossier des scripts puis redémarrez Illustrator :
   - Windows : `C:\Program Files\Adobe\Adobe Illustrator <version>\Presets\fr_FR\Scripts\`
   - macOS : `/Applications/Adobe Illustrator <version>/Presets/fr_FR/Scripts/`
   Il apparaît alors dans **Fichier > Scripts**.
3. Installez une police tifinagh si besoin : **Noto Sans Tifinagh** (Google Fonts, licence OFL) ; sous Windows, **Ebrima** contient déjà le tifinagh.

## Utilisation

1. **Travaillez sur une copie du fichier.**
2. Sélectionnez des blocs de texte (ou des lettres avec l'outil Texte).
3. Lancez le script, choisissez le sens, les options, la sortie et la police.
4. **Analyser** pour voir le résultat prévu sans rien modifier, puis **Appliquer**.
5. Annulation : Édition > Annuler (Ctrl/Cmd+Z) ; dans Illustrator un script s'annule en principe en une fois (non vérifié ici).

## Limites connues

- La liste des « polices tifinagh connues » est indicative : ExtendScript ne permet pas de lire la couverture d'une police ; vérifiez visuellement l'absence de carrés vides.
- La détection des paragraphes français / anglais repose sur des mots courants : un paragraphe d'un seul mot (Bienvenue) n'est pas reconnu — sélectionnez alors les lettres à convertir.
- ţ peut venir de tt ou de ss (INALCO) : le script écrit ⵜⵙ ou ⵜ selon l'option, sans analyse grammaticale. En tifinagh → latin, ⵜⵙ peut être t + s : l'option ţ est donc désactivée par défaut.
- Le tifinagh n'ayant pas de casse, l'aller-retour latin → tifinagh → latin perd les majuscules (choix de casse au retour).
- Les anciennes polices tifinagh « ANSI » (lettres latines dessinées en tifinagh) ne sont pas converties.

## Statut des tests

**Non testé dans Illustrator.** Tests réalisés hors Illustrator, dans Node.js (`npm install` puis `npm test`) :
- syntaxe du .jsx analysée par **acorn en ECMAScript 3 et 5** : OK ; aucun caractère non ASCII hors commentaires (chaînes en \uXXXX), aucun accès réseau, fichier ou système ;
- **94 tests du moteur** : mots de référence (ⵜⴰⵇⴱⴰⵢⵍⵉⵜ, ⵜⵉⴼⵉⵏⴰⵖ, ⴰⵣⵓⵍ de l'UTN #59), variantes, protections, écriture informelle, relecture, corrections, aller-retour sur **3 000 mots aléatoires**, invariants sur **9 000 plans** tirés de textes aléatoires mélangés (arabe, emoji, URL, signes combinants…) ;
- **45 tests sur un DOM Illustrator simulé** (mise en forme par lettre, police appliquée, longueurs qui changent, groupes, verrouillés, copies, annotation non imprimable, lettres sélectionnées, textes chaînés, emoji, messages, parcours complet) ;
- **11 tests du dialogue ScriptUI sur une simulation**.
Ces simulations ne remplacent pas un essai dans Illustrator : merci de signaler tout problème.

## English summary

Converts Tamazight written in Latin letters to Unicode Tifinagh (or back, for proofreading; or only fixes Berber Latin look-alikes such as Greek ε/γ) inside Illustrator text, letter by letter, keeping each character's formatting. Options: IRCAM or Berber Academy h, Kabyle affricates, spirants, informal spelling, protection of French words / URLs / codes, Tifinagh font for converted letters, side copy or non-printing reading note, analysis without changes, FR/EN dialog. Install via File > Scripts > Other Script… or copy into Presets/<locale>/Scripts. **Not tested in Illustrator** (syntax checked with acorn ES3/ES5, logic tested in Node on simulated objects). Work on a copy of your file. No network access, no data collection.

## Licence

MIT © 2026 Amirouche Amwanes — voir [LICENSE](LICENSE). Code 100 % original. Correspondances de lettres tirées de documents publics (Unicode Technical Note #59, tableaux de l'alphabet latin berbère).
