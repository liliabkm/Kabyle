"use client";
import { useState } from "react";
import {
  ArrowRight,
  BookOpen,
  ChevronLeft,
  Check,
  LockKeyhole,
  RotateCcw,
  Star,
  X,
} from "lucide-react";
import { request } from "../lib/api";
import WordVisual, { type WordMedia } from "./WordVisual";
type Citation = { url: string; author: string; license: string };
type Word = {
  id: string;
  latin: string;
  french: string;
  media: WordMedia;
  sources: Citation[];
};
type Phrase = {
  id: string;
  latin: string;
  french: string;
  target_word_id: string;
  sources: Citation[];
};
type Exercise = {
  id: string;
  type: "recognize" | "order" | "cloze" | "recall";
  french: string;
  word_id?: string;
  option_ids?: string[];
  tokens?: string[];
  before?: string;
  after?: string;
  keyboard?: string[];
};
type Bundle = {
  id: string;
  title: string;
  preview: boolean;
  notice: string;
  words: Word[];
  phrases: Phrase[];
  exercises: Exercise[];
};
export default function VocabularyPreview() {
  const [token, setToken] = useState(""),
    [bundle, setBundle] = useState<Bundle | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function open(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      setBundle(
        await request("admin/learning-lessons/premiers-mots", {
          headers: { Authorization: "Bearer " + token },
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (bundle)
    return (
      <WordLesson
        bundle={bundle}
        token={token}
        onExit={() => setBundle(null)}
      />
    );
  return (
    <section className="vocabulary-entry">
      <div className="vocabulary-entry-icon">
        <BookOpen size={32} />
      </div>
      <h2>Des mots, puis des phrases.</h2>
      <p>
        Découvrir avec une image, reconstruire une phrase, puis retrouver le mot
        sans aide.
      </p>
      <div className="vocabulary-roadmap">
        <span>1 · Je découvre</span>
        <span>2 · Je comprends</span>
        <span>3 · Je retrouve</span>
      </div>
      <details className="teacher-preview-gate">
        <summary>
          <LockKeyhole size={17} /> Essayer la leçon privée (enseignant)
        </summary>
        <p>
          Un aperçu pédagogique utilise des mots déjà récupérés. Ils restent en
          relecture : cet essai n’est pas un cours publié, ni une validation
          linguistique. Usage privé et non commercial ; aucun audio généré.
        </p>
        <form onSubmit={open}>
          <label htmlFor="word-preview-token">
            Jeton enseignant (ADMIN_TOKEN du fichier .env)
          </label>
          <input
            id="word-preview-token"
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
          />
          <button className="primary" disabled={busy || !token}>
            {busy ? "Chargement…" : "Lancer l’aperçu privé"}{" "}
            <ArrowRight size={18} />
          </button>
        </form>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
      </details>
    </section>
  );
}
function WordLesson({
  bundle,
  token,
  onExit,
}: {
  bundle: Bundle;
  token: string;
  onExit: () => void;
}) {
  const [phase, setPhase] = useState<
      "words" | "phrases" | "practice" | "result"
    >("words"),
    [index, setIndex] = useState(0),
    [answer, setAnswer] = useState(""),
    [chips, setChips] = useState<number[]>([]),
    [feedback, setFeedback] = useState<{
      correct: boolean;
      expected: string;
      french: string;
    } | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [errors, setErrors] = useState(0),
    [successes, setSuccesses] = useState(0),
    [revealed, setRevealed] = useState(true);
  const exercise = bundle.exercises[index],
    word = bundle.words[index],
    phrase = bundle.phrases[index];
  const clear = () => {
    setAnswer("");
    setChips([]);
    setFeedback(null);
    setError("");
  };
  async function check(value: string) {
    if (busy || feedback) return;
    setBusy(true);
    setError("");
    try {
      const result = await request(
        `admin/learning-lessons/${bundle.id}/answers`,
        {
          method: "POST",
          headers: { Authorization: "Bearer " + token },
          body: JSON.stringify({ exercise_id: exercise.id, answer: value }),
        },
      );
      setFeedback(result);
      if (result.correct) setSuccesses((n) => n + 1);
      else setErrors((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function advance() {
    clear();
    window.scrollTo(0, 0);
    if (index + 1 === bundle.exercises.length) {
      setPhase("result");
      setIndex(0);
    } else setIndex(index + 1);
  }
  function highlight(p: Phrase) {
    const w = bundle.words.find((w) => w.id === p.target_word_id);
    const start = w
      ? p.latin.toLocaleLowerCase().indexOf(w.latin.toLocaleLowerCase())
      : -1;
    return start < 0 ? (
      p.latin
    ) : (
      <>
        {p.latin.slice(0, start)}
        <mark>{p.latin.slice(start, start + w!.latin.length)}</mark>
        {p.latin.slice(start + w!.latin.length)}
      </>
    );
  }
  return (
    <section className="word-lesson">
      <button className="back" disabled={busy} onClick={onExit}>
        <ChevronLeft size={18} /> Quitter l’aperçu
      </button>
      <p className="word-preview-notice">
        <LockKeyhole size={16} />
        <span>Aperçu privé · contenus en relecture · sans audio</span>
      </p>
      <div className="lesson-topline">
        <span>{bundle.title}</span>
        <span>
          {bundle.words.length} mots · {bundle.phrases.length} phrases
        </span>
      </div>
      <ol className="lesson-steps" aria-label="Étapes de la leçon de mots">
        {[
          { id: "words", label: "Je découvre" },
          { id: "phrases", label: "Je comprends" },
          { id: "practice", label: "Je retrouve" },
        ].map((s) => (
          <li key={s.id} aria-current={phase === s.id ? "step" : undefined}>
            {s.label}
          </li>
        ))}
      </ol>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {phase === "words" ? (
        <>
          <div className="eyebrow">
            MOT {index + 1} SUR {bundle.words.length}
          </div>
          <h1>Regarde et retiens le mot.</h1>
          <div className="word-discovery-card">
            <WordVisual media={word.media} label={word.french} />
            <h2 lang="kab-Latn">{revealed ? word.latin : "?"}</h2>
            <p>{word.french}</p>
            <button
              className="text-button"
              onClick={() => setRevealed(!revealed)}
            >
              {revealed ? "Je cache le mot" : "Je regarde le mot"}
            </button>
          </div>
          <button
            className="primary"
            onClick={() => {
              setRevealed(true);
              window.scrollTo(0, 0);
              if (index + 1 === bundle.words.length) {
                setPhase("phrases");
                setIndex(0);
              } else setIndex(index + 1);
            }}
          >
            {index + 1 === bundle.words.length
              ? "Je découvre les phrases"
              : "Mot suivant"}{" "}
            <ArrowRight size={18} />
          </button>
        </>
      ) : phase === "phrases" ? (
        <>
          <div className="eyebrow">
            PHRASE {index + 1} SUR {bundle.phrases.length}
          </div>
          <h1>Le mot dans une phrase.</h1>
          <div className="phrase-discovery-card">
            <WordVisual
              media={
                bundle.words.find((w) => w.id === phrase.target_word_id)!.media
              }
              label={phrase.french}
            />
            <h2 lang="kab-Latn">{highlight(phrase)}</h2>
            <p>{phrase.french}</p>
          </div>
          <button
            className="primary"
            onClick={() => {
              window.scrollTo(0, 0);
              if (index + 1 === bundle.phrases.length) {
                setPhase("practice");
                setIndex(0);
                clear();
              } else setIndex(index + 1);
            }}
          >
            {index + 1 === bundle.phrases.length
              ? "À moi de jouer !"
              : "Phrase suivante"}{" "}
            <ArrowRight size={18} />
          </button>
        </>
      ) : phase === "practice" ? (
        <>
          <div className="eyebrow">
            DÉFI {index + 1} SUR {bundle.exercises.length}
          </div>
          <div
            className="discovery-track"
            role="progressbar"
            aria-label="Défis de la séance"
            aria-valuemin={0}
            aria-valuemax={bundle.exercises.length}
            aria-valuenow={successes}
          >
            <span
              style={{
                width: (successes / bundle.exercises.length) * 100 + "%",
              }}
            />
          </div>
          <h1>
            {exercise.type === "recognize"
              ? "Retrouve le mot."
              : exercise.type === "order"
                ? "Remets les mots dans l’ordre."
                : exercise.type === "cloze"
                  ? "Complète la phrase."
                  : "Retrouve le mot sans image."}
          </h1>
          <p className="exercise-french">{exercise.french}</p>
          {exercise.type === "recognize" ? (
            <>
              <WordVisual
                media={
                  bundle.words.find((w) => w.id === exercise.word_id)!.media
                }
                label={exercise.french}
              />
              <div className="word-choices">
                {[...(exercise.option_ids || [])].reverse().map((id) => (
                  <button
                    key={id}
                    disabled={busy || feedback !== null}
                    onClick={() =>
                      check(bundle.words.find((w) => w.id === id)!.latin)
                    }
                  >
                    {bundle.words.find((w) => w.id === id)!.latin}
                  </button>
                ))}
              </div>
            </>
          ) : exercise.type === "order" ? (
            <>
              <p className="muted">Touche les mots, un après l’autre.</p>
              <div className="assembled-phrase" aria-label="Ta phrase">
                {chips.length ? (
                  chips.map((n, i) => (
                    <button
                      key={n}
                      disabled={busy || feedback !== null}
                      onClick={() => setChips(chips.filter((_, j) => j !== i))}
                    >
                      {exercise.tokens![n]} <X size={13} />
                    </button>
                  ))
                ) : (
                  <span>Ta phrase apparaîtra ici.</span>
                )}
              </div>
              <div className="word-chips">
                {exercise.tokens!.map((t, i) => (
                  <button
                    key={i}
                    disabled={chips.includes(i) || busy || feedback !== null}
                    onClick={() => setChips([...chips, i])}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <button
                className="primary"
                disabled={
                  chips.length !== exercise.tokens!.length ||
                  busy ||
                  feedback !== null
                }
                onClick={() =>
                  check(chips.map((n) => exercise.tokens![n]).join(" "))
                }
              >
                Vérifier
              </button>
            </>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                check(answer);
              }}
            >
              <div className="cloze-line">
                {exercise.type === "cloze" && <span>{exercise.before}</span>}
                <input
                  aria-label="Ta réponse en kabyle"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  autoComplete="off"
                  autoCapitalize="none"
                  spellCheck={false}
                  required
                  disabled={busy || feedback !== null}
                />
                {exercise.type === "cloze" && <span>{exercise.after}</span>}
              </div>
              <div className="character-keys">
                {exercise.keyboard?.map((c) => (
                  <button
                    key={c}
                    type="button"
                    disabled={busy || feedback !== null}
                    onClick={() => setAnswer(answer + c)}
                    aria-label={"Ajouter " + c}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <button
                className="primary"
                disabled={!answer.trim() || busy || feedback !== null}
              >
                Vérifier
              </button>
            </form>
          )}
          {feedback && (
            <div
              className={feedback.correct ? "feedback good" : "feedback"}
              role="status"
            >
              <b>
                {feedback.correct
                  ? "Bien joué !"
                  : "Regarde la correction, puis réessaie."}
              </b>
              <p lang="kab-Latn">{feedback.expected}</p>
              <p className="feedback-translation">{feedback.french}</p>
              <button
                className="primary"
                disabled={busy}
                onClick={() => {
                  if (feedback.correct) advance();
                  else clear();
                }}
              >
                {feedback.correct
                  ? index + 1 === bundle.exercises.length
                    ? "Voir mon bilan"
                    : "Défi suivant"
                  : "Je réessaie"}{" "}
                <ArrowRight size={18} />
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="lesson-finished">
          <div className="lesson-award">
            <Star size={45} fill="currentColor" />
          </div>
          <h1>Tu as retrouvé les mots !</h1>
          <p>
            {successes} défis réussis.{" "}
            {errors ? "Tu as appris avec les corrections." : "Bien joué !"}
          </p>
          <div className="vocab-summary">
            {bundle.words.map((w) => (
              <div key={w.id}>
                <b lang="kab-Latn">{w.latin}</b>
                <span>{w.french}</span>
                <Check size={18} />
              </div>
            ))}
          </div>
          <p className="tiny">
            Bilan de cet essai privé : il n’est pas ajouté aux progrès des
            leçons publiées. Les textes restent à relire.
          </p>
          <button
            className="primary"
            onClick={() => {
              setPhase("words");
              setIndex(0);
              setSuccesses(0);
              setErrors(0);
              setRevealed(true);
              clear();
            }}
          >
            <RotateCcw size={18} /> Revoir les cartes
          </button>
        </div>
      )}
      <details className="parent-note word-source-note">
        <summary>Textes, illustrations et droits</summary>
        <p>
          {bundle.notice} Textes du cours LibreLingo-KAB-from-FR, dont la
          licence racine est BY-NC-SA 4.0 et la licence de cours annoncée BY-SA
          4.0 : cette divergence reste à clarifier. Aucun texte n’a été traduit
          par une IA pour cet aperçu.
        </p>
        {bundle.words.map((w) => (
          <div key={w.id}>
            <b>{w.latin}</b>
            {w.sources.map((s, i) => (
              <a
                className="source"
                key={i}
                href={s.url}
                target="_blank"
                rel="noreferrer"
              >
                {s.author} · {s.license} ↗
              </a>
            ))}
            {w.media.url ? (
              <p className="tiny">
                Photo : {w.media.author} ·{" "}
                <a href={w.media.license_url} target="_blank" rel="noreferrer">
                  {w.media.license}
                </a>
                . {w.media.presentation}
              </p>
            ) : (
              <p className="tiny">
                Illustration originale du projet, pas une photo du corpus.
              </p>
            )}
          </div>
        ))}
        {bundle.phrases.map((p) => (
          <a
            className="source"
            key={p.id}
            href={p.sources[0].url}
            target="_blank"
            rel="noreferrer"
          >
            Phrase : {p.latin} ↗
          </a>
        ))}
      </details>
    </section>
  );
}
