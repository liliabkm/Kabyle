"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  ChevronLeft,
  Headphones,
  RotateCcw,
  Volume2,
  X,
} from "lucide-react";
import { request } from "../lib/api";
type Mode = "flashcard" | "order" | "dictation" | "audio-choice";
type Audio = {
  url: string;
  author: string;
  license: string;
  attribution_url?: string;
};
type Item = {
  id: string;
  latin: string;
  french: string;
  category: string;
  status: string;
  word_count: number;
  difficulty: string;
  has_audio: boolean;
  cefr_level?: string;
};
type Catalog = {
  items: Item[];
  total: number;
  audio_count: number;
  categories: { id: string; label: string; count: number }[];
};
type Question = Item & {
  mode: Mode;
  tokens: { id: number; text: string }[];
  words: string[];
  audios: Audio[];
  options: { id: string; text: string }[];
  question_version: string;
  grammar_note?: string;
  sources: { url: string; author: string; license: string }[];
};
type Feedback = { correct: boolean; expected: string; french: string };
type Gloss = {
  token: string;
  matches: {
    id: string;
    latin: string;
    french: string;
    french_variants: string[];
    status: string;
  }[];
  notice: string;
};
const labels: Record<Mode, string> = {
  flashcard: "Je découvre",
  order: "Je construis",
  dictation: "Je fais la dictée",
  "audio-choice": "J’écoute et je choisis",
};
export default function PhrasePractice({
  initialId,
  onExit,
  onActiveChange,
}: {
  initialId?: string;
  onExit?: () => void;
  onActiveChange?: (active: boolean) => void;
} = {}) {
  const [catalog, setCatalog] = useState<Catalog | null>(null),
    [category, setCategory] = useState(""),
    [difficulty, setDifficulty] = useState("short"),
    [audioOnly, setAudioOnly] = useState(false),
    [source, setSource] = useState(""),
    [offset, setOffset] = useState(0),
    [queue, setQueue] = useState<string[]>(initialId ? [initialId] : []),
    [position, setPosition] = useState(0),
    [mode, setMode] = useState<Mode>("flashcard"),
    [question, setQuestion] = useState<Question | null>(null),
    [flipped, setFlipped] = useState(false),
    [chips, setChips] = useState<number[]>([]),
    [answer, setAnswer] = useState(""),
    [feedback, setFeedback] = useState<Feedback | null>(null),
    [gloss, setGloss] = useState<Gloss | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false),
    [audioError, setAudioError] = useState(false),
    [finished, setFinished] = useState(false),
    [successes, setSuccesses] = useState(0);
  const attempt = useRef<string | null>(null),
    glossVersion = useRef(0);
  const id = queue[position];
  useEffect(() => {
    onActiveChange?.(!!id);
    return () => onActiveChange?.(false);
  }, [id, onActiveChange]);
  useEffect(() => {
    if (question)
      document
        .getElementById("phrase-learning-session")
        ?.scrollIntoView({ block: "start" });
  }, [question?.id, question?.mode]);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    request(
      "phrase-practice?" +
        new URLSearchParams({
          category,
          difficulty,
          audio_only: String(audioOnly),
          source,
          offset: String(offset),
        }),
      { signal: controller.signal },
    )
      .then(setCatalog)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [category, difficulty, audioOnly, source, offset]);
  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    setQuestion(null);
    setLoading(true);
    setError("");
    setFeedback(null);
    setChips([]);
    setAnswer("");
    setFlipped(false);
    setGloss(null);
    glossVersion.current++;
    setAudioError(false);
    attempt.current = null;
    request(`phrase-practice/${id}?mode=${mode}`, { signal: controller.signal })
      .then(setQuestion)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [id, mode]);
  function start(ids: string[]) {
    setQueue(ids);
    setPosition(0);
    setMode("flashcard");
    setFinished(false);
    setSuccesses(0);
  }
  async function lookup(token: string) {
    const version = ++glossVersion.current;
    setGloss(null);
    try {
      const value = await request("lexicon?" + new URLSearchParams({ token }));
      if (version === glossVersion.current) setGloss(value);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function check(value: string) {
    if (!question || busy || feedback) return;
    setBusy(true);
    setError("");
    try {
      const result = await request(`phrase-practice/${question.id}/answers`, {
        method: "POST",
        body: JSON.stringify({
          mode,
          answer: value,
          attempt_id:
            attempt.current ?? (attempt.current = crypto.randomUUID()),
          question_version: question.question_version,
        }),
      });
      setFeedback(result);
      if (result.correct) setSuccesses((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function retry() {
    attempt.current = null;
    setFeedback(null);
    setAnswer("");
    setChips([]);
  }
  function next() {
    if (position + 1 < queue.length) {
      setPosition((n) => n + 1);
      setMode("flashcard");
    } else setFinished(true);
  }
  function exit() {
    glossVersion.current++;
    setQueue([]);
    setQuestion(null);
    setFinished(false);
    setError("");
    if (onExit) onExit();
  }
  if (!id)
    return (
      <section className="phrase-catalog">
        <div className="eyebrow">DES PHRASES POUR APPRENDRE</div>
        <h2>Je choisis mon thème.</h2>
        <p>
          Des petites séances, des mots à toucher et des phrases à reconstruire.
        </p>
        <div className="practice-filters">
          <label>
            Thème des exercices
            <select
              aria-label="Thème des exercices"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">Tous les thèmes</option>
              {catalog?.categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label} ({c.count})
                </option>
              ))}
            </select>
          </label>
          <label>
            Difficulté des phrases
            <select
              aria-label="Difficulté des phrases"
              value={difficulty}
              onChange={(e) => {
                setDifficulty(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">Toutes les difficultés</option>
              <option value="short">Courtes · jusqu’à 4 mots</option>
              <option value="medium">Moyennes · 5 à 8 mots</option>
              <option value="long">Longues · 9 mots ou plus</option>
              <option value="A1">A1 · attribué par l’admin</option>
              <option value="A2">A2 · attribué par l’admin</option>
            </select>
          </label>
          <label>
            Source des phrases
            <select
              aria-label="Source des phrases"
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                setOffset(0);
              }}
            >
              <option value="">Toutes les sources</option>
              <option value="tatoeba">Tatoeba</option>
            </select>
          </label>
          <label className="practice-checkbox">
            <input
              type="checkbox"
              checked={audioOnly}
              onChange={(e) => {
                setAudioOnly(e.target.checked);
                setOffset(0);
              }}
            />{" "}
            Avec enregistrement
          </label>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {catalog && (
          <>
            <p role="status">
              {catalog.total} phrases dans cette sélection ·{" "}
              {catalog.audio_count} phrases avec audio dans la bibliothèque.
            </p>
            {!!catalog.items.length && (
              <button
                className="primary"
                onClick={() =>
                  start(catalog.items.slice(0, 5).map((c) => c.id))
                }
              >
                Ma séance · {Math.min(5, catalog.items.length)} phrases{" "}
                <ArrowRight size={18} />
              </button>
            )}
            <div className="phrase-pick-grid">
              {catalog.items.map((c) => (
                <button
                  className="phrase-pick"
                  key={c.id}
                  onClick={() => start([c.id])}
                >
                  <span className="reading-category">{c.category}</span>
                  <strong lang="kab-Latn">{c.latin}</strong>
                  <span>{c.french}</span>
                  <small>
                    {c.word_count} mots
                    {c.cefr_level ? " · " + c.cefr_level : ""} ·{" "}
                    {c.status === "validated" ? "Validé" : "À vérifier"}
                    {c.has_audio ? " · Avec audio" : ""}
                  </small>
                </button>
              ))}
            </div>
            {!catalog.items.length && (
              <p className="info-note">
                Aucune phrase pour ces filtres. Tu peux choisir un autre thème ;
                les imports seront ajoutés ici.
              </p>
            )}
            {catalog.total > 12 && (
              <div className="reading-pagination">
                <button
                  className="secondary"
                  disabled={!offset}
                  onClick={() => setOffset(Math.max(0, offset - 12))}
                >
                  Avant
                </button>
                <span>
                  {offset + 1}–{Math.min(offset + 12, catalog.total)} /{" "}
                  {catalog.total}
                </span>
                <button
                  className="secondary"
                  disabled={offset + 12 >= catalog.total}
                  onClick={() => setOffset(offset + 12)}
                >
                  Après
                </button>
              </div>
            )}
          </>
        )}
        <p className="tiny">
          La difficulté dépend ici de la longueur. Un niveau A1/A2 n’est affiché
          que s’il a été attribué dans l’administration.
        </p>
      </section>
    );
  if (finished)
    return (
      <section id="phrase-learning-session" className="phrase-session">
        <h2>Séance terminée !</h2>
        <p>{successes} réponse(s) correcte(s) enregistrée(s).</p>
        <button className="primary" onClick={exit}>
          Retour aux phrases
        </button>
      </section>
    );
  return (
    <section id="phrase-learning-session" className="phrase-session">
      <button className="back" onClick={exit} disabled={busy}>
        <ChevronLeft size={18} /> Retour aux phrases
      </button>
      <p className="eyebrow">
        PHRASE {position + 1} SUR {queue.length}
      </p>
      <div className="practice-modes">
        {(Object.keys(labels) as Mode[]).map((m) => (
          <button
            key={m}
            className={mode === m ? "active" : ""}
            disabled={
              busy ||
              (!!question &&
                ["dictation", "audio-choice"].includes(m) &&
                (!question.audios.length ||
                  (m === "audio-choice" && !question.options.length)))
            }
            onClick={() => setMode(m)}
          >
            {m === "dictation" || m === "audio-choice" ? (
              <Headphones size={16} />
            ) : (
              <BookOpen size={16} />
            )}{" "}
            {labels[m]}
          </button>
        ))}
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {loading && <p role="status">On prépare ta phrase…</p>}
      {question && (
        <>
          <p className="practice-meta">
            {question.category} ·{" "}
            {question.status === "validated" ? "Validé" : "À vérifier"}
            {question.cefr_level ? " · " + question.cefr_level : ""}
          </p>
          <h2>
            {mode === "flashcard"
              ? "Regarde. Écoute. Découvre."
              : mode === "order"
                ? "Remets les mots dans l’ordre."
                : mode === "dictation"
                  ? "Écoute et écris en kabyle."
                  : "Écoute et choisis la traduction."}
          </h2>
          {question.audios.length > 0 ? (
            <div className="phrase-audio">
              <Volume2 size={20} />
              <label>
                Voix enregistrée
                <audio
                  key={question.id + mode}
                  controls
                  preload="none"
                  src={question.audios[0].url}
                  onError={() => setAudioError(true)}
                  onPlay={() => setAudioError(false)}
                />
              </label>
              <small>
                {question.audios[0].author} · {question.audios[0].license}
              </small>
              {question.audios.length > 1 && (
                <details>
                  <summary>Autres voix ({question.audios.length - 1})</summary>
                  {question.audios.slice(1).map((a) => (
                    <label key={a.url}>
                      {a.author}
                      <audio
                        controls
                        preload="none"
                        src={a.url}
                        onError={() => setAudioError(true)}
                        onPlay={() => setAudioError(false)}
                      />
                      <small>{a.license}</small>
                    </label>
                  ))}
                </details>
              )}
              {audioError && (
                <p className="error">
                  Cet enregistrement ne se charge pas. Réessaie plus tard ou
                  choisis « Je construis ».
                </p>
              )}
            </div>
          ) : (
            <p className="tiny">
              Cette phrase n’a pas encore d’enregistrement. Tu peux découvrir la
              carte et construire la phrase.
            </p>
          )}
          {mode === "flashcard" ? (
            <>
              <div className="phrase-flashcard">
                <p lang="kab-Latn" className="interactive-sentence">
                  {question.latin.split(/(\s+)/).map((word, i) =>
                    /^\s+$/.test(word) ? (
                      word
                    ) : (
                      <button
                        key={i}
                        onClick={() => lookup(word)}
                        aria-label={"Voir le mot " + word}
                      >
                        {word}
                      </button>
                    ),
                  )}
                </p>
                <button
                  className="secondary"
                  onClick={() => setFlipped(!flipped)}
                >
                  {flipped ? "Cacher la traduction" : "Retourner la carte"}
                </button>
                {flipped && (
                  <p className="flash-translation">{question.french}</p>
                )}
                {question.grammar_note && (
                  <p className="info-note">{question.grammar_note}</p>
                )}
              </div>
              <p className="tiny">Touche un mot pour consulter le lexique.</p>
              <button className="primary" onClick={() => setMode("order")}>
                À moi de construire ! <ArrowRight size={18} />
              </button>
            </>
          ) : mode === "order" ? (
            <>
              <p className="exercise-french">{question.french}</p>
              <div className="assembled-phrase" aria-label="Ta phrase">
                {chips.length ? (
                  chips.map((n) => (
                    <button
                      disabled={busy || !!feedback}
                      key={n}
                      onClick={() => setChips(chips.filter((x) => x !== n))}
                    >
                      {question.tokens.find((t) => t.id === n)?.text}{" "}
                      <X size={13} />
                    </button>
                  ))
                ) : (
                  <span>Ta phrase apparaîtra ici.</span>
                )}
              </div>
              <div className="word-chips">
                {question.tokens.map((t) => (
                  <button
                    key={t.id}
                    disabled={busy || !!feedback || chips.includes(t.id)}
                    onClick={() => setChips([...chips, t.id])}
                  >
                    {t.text}
                  </button>
                ))}
              </div>
              <button
                className="primary"
                disabled={
                  busy || !!feedback || chips.length !== question.tokens.length
                }
                onClick={() =>
                  check(
                    chips
                      .map((n) => question.tokens.find((t) => t.id === n)!.text)
                      .join(" "),
                  )
                }
              >
                Vérifier ma phrase
              </button>
            </>
          ) : mode === "dictation" ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                check(answer);
              }}
            >
              <label>
                Ma dictée en kabyle
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={busy || !!feedback}
                  autoComplete="off"
                  spellCheck={false}
                  required
                />
              </label>
              <div className="character-keys">
                {Array.from(
                  new Set(
                    question.latin
                      .split("")
                      .filter((c) => c.charCodeAt(0) > 127),
                  ),
                ).map((c) => (
                  <button
                    key={c}
                    type="button"
                    disabled={busy || !!feedback}
                    onClick={() => setAnswer(answer + c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <button
                className="primary"
                disabled={busy || !!feedback || !answer.trim()}
              >
                Vérifier ma dictée
              </button>
            </form>
          ) : (
            <div className="audio-options">
              {question.options.map((o) => (
                <button
                  className="secondary"
                  key={o.id}
                  disabled={busy || !!feedback || audioError}
                  onClick={() => check(o.id)}
                >
                  {o.text}
                </button>
              ))}
            </div>
          )}
          {gloss && mode === "flashcard" && (
            <aside className="word-gloss" aria-live="polite">
              <h3>{gloss.token}</h3>
              {gloss.matches.length ? (
                gloss.matches.map((w) => (
                  <div key={w.id}>
                    <b>{w.latin}</b> — {w.french}
                    <small>
                      {w.status === "validated" ? "Validé" : "À vérifier"}
                    </small>
                    {w.french_variants?.length > 1 && (
                      <p>{w.french_variants.join(" · ")}</p>
                    )}
                  </div>
                ))
              ) : (
                <p>
                  Pas encore de traduction individuelle pour ce mot dans le
                  lexique.
                </p>
              )}
              <p className="tiny">{gloss.notice}</p>
            </aside>
          )}
          {feedback && (
            <div
              className={"feedback " + (feedback.correct ? "good" : "")}
              role="status"
            >
              <b>
                {feedback.correct
                  ? "Bien joué !"
                  : "Regarde la correction, puis réessaie."}
              </b>
              <p lang="kab-Latn">{feedback.expected}</p>
              <p>{feedback.french}</p>
              {feedback.correct ? (
                <button className="primary" onClick={next}>
                  {position + 1 < queue.length
                    ? "Phrase suivante"
                    : "Voir mon bilan"}{" "}
                  <ArrowRight size={18} />
                </button>
              ) : (
                <button className="primary" onClick={retry}>
                  <RotateCcw size={17} /> Je réessaie
                </button>
              )}
            </div>
          )}
          <details className="reading-sources">
            <summary>Sources et voix</summary>
            {question.sources.map((s, i) => (
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
            {question.audios.map((a) => (
              <a
                className="source"
                href={a.attribution_url || a.url}
                key={a.url}
                target="_blank"
                rel="noreferrer"
              >
                Voix : {a.author} · {a.license} ↗
              </a>
            ))}
          </details>
        </>
      )}
    </section>
  );
}
