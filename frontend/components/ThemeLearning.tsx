"use client";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Check,
  RefreshCw,
} from "lucide-react";
import { cachedLibrary, peekLibrary, libraryVersion, invalidateLibraryCache } from "../lib/api";
import { TopicArt, WordArt, PhotoCredit } from "./TopicArt";
import PhrasePractice from "./PhrasePractice";
import PhraseAudio, { type Recording } from "./PhraseAudio";
import AlphabetExplorer, { type AlphabetLetter } from "./AlphabetExplorer";
type Topic = {
  id: string;
  title: string;
  description: string;
  word_count: number;
  phrase_count: number;
  resource: boolean;
};
type Form = {
  id: string;
  latin: string;
  french: string;
  status: string;
  synonyms: string[];
};
type Word = {
  id: string;
  concept: string | null;
  latin: string;
  french: string;
  label: string;
  art?: string;
  status: string;
  role: string;
  forms: Form[];
  issue?: string;
  image?: { url: string; author: string; license: string };
  sources: { url: string; author: string; license: string }[];
};
type Words = {
  items: Word[];
  total: number;
  title: string;
  description: string;
};
type Phrase = {
  id: string;
  latin: string;
  french: string;
  status: string;
  has_audio: boolean;
  audios?: Recording[];
  highlight: {
    start: number;
    end: number;
    text: string;
    before: string;
    after: string;
  } | null;
};
type Phrases = { items: Phrase[]; total: number };
type Catalog = {topics: Topic[]; letter_count: number};
type Browsing = {generation: number; topic: Topic | null; stage: "words" | "phrases"; selected: Word | null; wordOffset: number; phraseOffset: number; audioOnly: boolean};
const browsing = new Map<string, Browsing>();
type LibraryPage = Words | Phrases | {items: AlphabetLetter[]};
function pagePath(topic: Topic, stage: "words" | "phrases", selected: Word | null, wordOffset: number, phraseOffset: number, audioOnly: boolean) {
  if (topic.id === "alphabet") return "library?kind=letter&limit=72";
  if (stage === "words") return `topics/${topic.id}/words?offset=${wordOffset}`;
  return (selected ? `words/${encodeURIComponent(selected.id)}/phrases?` : `topics/${topic.id}/phrases?`) + new URLSearchParams({word: selected?.concept || "", offset: String(phraseOffset), audio_only: String(audioOnly)});
}


export default function ThemeLearning({
  showAlphabet = false,
  title = "Choisis ton thème",
}: { showAlphabet?: boolean; title?: string } = {}) {
  const scope = showAlphabet ? "library" : "vocabulary";
  const remembered = browsing.get(scope);
  const saved = remembered?.generation === libraryVersion() ? remembered : undefined;
  const [revision, setRevision] = useState(libraryVersion());
  const [topics, setTopics] = useState<Topic[]>(() => peekLibrary<Catalog>("topics")?.topics || []),
    [letterCount, setLetterCount] = useState(() => peekLibrary<Catalog>("topics")?.letter_count || 0),
    [topic, setTopic] = useState<Topic | null>(saved?.topic || null),
    [stage, setStage] = useState<"words" | "phrases">(saved?.stage || "words"),
    [selected, setSelected] = useState<Word | null>(saved?.selected || null),
    [wordData, setWordData] = useState<Words | null>(() => saved?.topic && saved.topic.id !== "alphabet" && saved.stage === "words" ? peekLibrary<Words>(pagePath(saved.topic, saved.stage, saved.selected, saved.wordOffset, saved.phraseOffset, saved.audioOnly)) || null : null),
    [phraseData, setPhraseData] = useState<Phrases | null>(() => saved?.topic && saved.topic.id !== "alphabet" && saved.stage === "phrases" ? peekLibrary<Phrases>(pagePath(saved.topic, saved.stage, saved.selected, saved.wordOffset, saved.phraseOffset, saved.audioOnly)) || null : null),
    [wordOffset, setWordOffset] = useState(saved?.wordOffset || 0),
    [phraseOffset, setPhraseOffset] = useState(saved?.phraseOffset || 0),
    [audioOnly, setAudioOnly] = useState(saved?.audioOnly || false),
    [exercise, setExercise] = useState<string | null>(null),
    [letters, setLetters] = useState<AlphabetLetter[]>(() => peekLibrary<{items: AlphabetLetter[]}>("library?kind=letter&limit=72")?.items || []),
    [loading, setLoading] = useState(() => saved?.topic ? !peekLibrary(pagePath(saved.topic, saved.stage, saved.selected, saved.wordOffset, saved.phraseOffset, saved.audioOnly)) : !peekLibrary<Catalog>("topics")),
    [error, setError] = useState("");
  useEffect(() => {
    const refresh = () => setRevision((value) => value + 1);
    window.addEventListener("library-data-changed", refresh);
    return () => window.removeEventListener("library-data-changed", refresh);
  }, []);
  useEffect(() => {
    browsing.set(scope, {generation: libraryVersion(), topic, stage, selected, wordOffset, phraseOffset, audioOnly});
  }, [scope, topic, stage, selected, wordOffset, phraseOffset, audioOnly, revision]);
  useEffect(() => {
    let active = true;
    setError("");
    const apply = (r: Catalog) => { setTopics(r.topics); setLetterCount(r.letter_count); };
    const cached = peekLibrary<Catalog>("topics");
    if (cached) { apply(cached); if (!topic) setLoading(false); }
    else {
      if (!topic) setLoading(true);
      cachedLibrary<Catalog>("topics").then((r) => { if (active) apply(r); })
        .catch((e) => { if (active) setError(e.message); })
        .finally(() => { if (active && !topic) setLoading(false); });
    }
    return () => { active = false; };
  }, [revision]);
  useEffect(() => {
    if (!topic) return;
    let active = true;
    setError("");
    const path = pagePath(topic, stage, selected, wordOffset, phraseOffset, audioOnly);
    const apply = (r: LibraryPage) => {
      if (topic.id === "alphabet") setLetters((r as {items: AlphabetLetter[]}).items);
      else if (stage === "words") setWordData(r as Words);
      else setPhraseData(r as Phrases);
    };
    const cached = peekLibrary<LibraryPage>(path);
    if (cached) { apply(cached); setLoading(false); }
    else {
      setLoading(true);
      cachedLibrary<LibraryPage>(path).then((r) => { if (active) apply(r); })
        .catch((e) => { if (active) setError(e.message); })
        .finally(() => { if (active) setLoading(false); });
    }
    return () => { active = false; };
  }, [topic?.id, stage, selected?.concept, wordOffset, phraseOffset, audioOnly, selected?.id, revision]);
  function hydrate(t: Topic, nextStage: "words" | "phrases", w: Word | null, wo: number, po: number, audio: boolean) {
    const cached = peekLibrary<LibraryPage>(pagePath(t, nextStage, w, wo, po, audio));
    setLoading(!cached);
    if (!cached && topic && pagePath(topic, stage, selected, wordOffset, phraseOffset, audioOnly) === pagePath(t, nextStage, w, wo, po, audio)) {
      setRevision((value) => value + 1);
    }
    if (t.id === "alphabet") setLetters((cached as {items: AlphabetLetter[]} | undefined)?.items || []);
    else if (nextStage === "words") setWordData(cached as Words || null);
    else setPhraseData(cached as Phrases || null);
  }
  function open(t: Topic) {
    setTopic(t);
    setAudioOnly(false);
    setStage(t.word_count ? "words" : "phrases");
    setSelected(null);
    setWordOffset(0);
    setPhraseOffset(0);
    hydrate(t, t.word_count ? "words" : "phrases", null, 0, 0, false);
    window.scrollTo(0, 0);
  }
  function contexts(w: Word | null) {
    setSelected(w);
    setStage("phrases");
    setPhraseOffset(0);
    if (topic) hydrate(topic, "phrases", w, wordOffset, 0, audioOnly);
    window.scrollTo(0, 0);
  }
  function back() {
    setLoading(false);
    setTopic(null);
    setSelected(null);
    setExercise(null);
    setError("");
    window.scrollTo(0, 0);
  }
  function page(kind: "words" | "phrases", direction: number) {
    const wo = kind === "words" ? Math.max(0, wordOffset + direction * 24) : wordOffset;
    const po = kind === "phrases" ? Math.max(0, phraseOffset + direction * 12) : phraseOffset;
    if (topic) hydrate(topic, kind, selected, wo, po, audioOnly);
    setWordOffset(wo); setPhraseOffset(po);
    window.scrollTo(0, 0);
  }
  const badge = (status: string) => (
    <span
      className={"topic-status " + (status === "validated" ? "checked" : "")}
    >
      {status === "validated" ? (
        <>
          <Check size={12} /> Validé
        </>
      ) : (
        "À vérifier"
      )}
    </span>
  );
  if (exercise)
    return (
      <div className="topic-training">
        <p className="topic-breadcrumb">
          {topic?.title}
          {selected ? " / " + selected.label : ""} / À moi de jouer
        </p>
        <PhrasePractice
          initialId={exercise}
          initialMode="order"
          onExit={() => setExercise(null)}
        />
      </div>
    );
  if (!topic)
    return (
      <section className="theme-learning">
        <div className="page-heading">
          <div>
            <div className="eyebrow">UN MONDE À LA FOIS</div>
            <h1>{title}</h1>
            <p>Une image, des mots, puis des petites phrases.</p>
          </div>
          <button className="secondary" onClick={invalidateLibraryCache} disabled={loading}>
            <RefreshCw size={16} /> Actualiser
          </button>
        </div>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {loading ? (
          <p role="status">On prépare tes thèmes…</p>
        ) : (
          <>
            <div className="topic-gallery">
              {showAlphabet && letterCount > 0 && (
                <button
                  className="topic-tile"
                  data-topic="alphabet"
                  onClick={() =>
                    open({
                      id: "alphabet",
                      title: "Les lettres",
                      description:
                        "Les lettres, tranquillement, sans jeu obligatoire.",
                      word_count: 0,
                      phrase_count: 0,
                      resource: false,
                    })
                  }
                >
                  <TopicArt topic="alphabet" />
                  <div className="topic-tile-copy">
                    <h2>Les lettres</h2>
                    <p>{letterCount} lettres à découvrir</p>
                    <span>
                      Je découvre <ArrowRight size={17} />
                    </span>
                  </div>
                </button>
              )}
              {topics
                .filter((t) => !t.resource)
                .map((t) => (
                  <button
                    className={"topic-tile theme-" + t.id}
                    data-topic={t.id}
                    key={t.id}
                    aria-label={"Ouvrir le thème " + t.title}
                    onClick={() => open(t)}
                  >
                    <TopicArt topic={t.id} />
                    <div className="topic-tile-copy">
                      <h2>{t.title}</h2>
                      <p>
                        {t.word_count} mots · {t.phrase_count} phrases
                      </p>
                      <span>
                        J’explore <ArrowRight size={17} />
                      </span>
                    </div>
                  </button>
                ))}
            </div>
            {topics.some((t) => t.resource) && (
              <details className="topic-resources">
                <summary>Le coin du dictionnaire</summary>
                <p>
                  Les noms des personnages et les éléments de source à clarifier
                  sont rangés à part.
                </p>
                <div className="topic-gallery">
                  {topics
                    .filter((t) => t.resource)
                    .map((t) => (
                      <button
                        className="topic-tile resource-tile"
                        data-topic={t.id}
                        key={t.id}
                        onClick={() => open(t)}
                      >
                        <TopicArt topic={t.id} />
                        <div className="topic-tile-copy">
                          <h2>{t.title}</h2>
                          <p>
                            {t.word_count} fiches · {t.phrase_count} phrases
                          </p>
                        </div>
                      </button>
                    ))}
                </div>
              </details>
            )}
          </>
        )}
      </section>
    );
  return (
    <section className="theme-learning topic-detail">
      <button className="back" onClick={back}>
        <ChevronLeft size={18} /> Tous les thèmes
      </button>
      <div className="topic-hero">
        <TopicArt topic={topic.id} />
        <div>
          <div className="eyebrow">MON THÈME</div>
          <h1>{topic.title}</h1>
          <p>{topic.description}</p>
        </div>
      </div>
      {topic.id !== "alphabet" && !topic.resource && (
        <ol className="topic-steps">
          <li aria-current={stage === "words" ? "step" : undefined}>
            <button
              onClick={() => {
                setStage("words");
                setSelected(null);
                hydrate(topic, "words", null, wordOffset, phraseOffset, audioOnly);
              }}
            >
              1 <span>Les mots</span>
            </button>
          </li>
          <li aria-current={stage === "phrases" ? "step" : undefined}>
            <button onClick={() => contexts(null)}>
              2 <span>Les phrases</span>
            </button>
          </li>
          <li>
            3 <span>À moi de jouer</span>
          </li>
        </ol>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {loading ? (
        <p role="status">On ouvre les fiches…</p>
      ) : topic.id === "alphabet" ? (
        <AlphabetExplorer letters={letters} />
      ) : stage === "words" ? (
        <>
          <div className="topic-section-title">
            <h2>
              {topic.resource
                ? "Les fiches de la source"
                : "D’abord, je découvre les mots."}
            </h2>
            {!topic.resource && (
              <button className="secondary" onClick={() => contexts(null)}>
                Voir les phrases du thème <ArrowRight size={17} />
              </button>
            )}
          </div>
          <div className="topic-word-grid">
            {wordData?.items.map((w) => (
              <article
                className={
                  "topic-word-card " + (topic.resource ? "source-card" : "")
                }
                data-concept={w.concept || w.id}
                key={w.id}
              >
                {!topic.resource &&
                  (w.image &&
                  (w.image.url.startsWith("https://") ||
                    w.image.url.startsWith("/api/media/")) ? (
                    <div className="topic-word-art">
                      <img src={w.image.url} alt={w.label} />
                    </div>
                  ) : (
                    <WordArt art={w.art} label={w.label} />
                  ))}
                <h2 lang="kab-Latn">{w.latin}</h2>
                <p className="word-meaning">{w.label}</p>
                {badge(w.status)}
                {w.issue && (
                  <p className="topic-source-issue">
                    {w.issue}. La traduction d’origine est conservée : «{" "}
                    {w.french} ».
                  </p>
                )}
                {!topic.resource && w.concept && (
                  <button className="primary" onClick={() => contexts(w)}>
                    Utiliser ce mot <ArrowRight size={16} />
                  </button>
                )}
                {(w.forms.length > 1 ||
                  w.forms.some((f) => f.synonyms?.length)) && (
                  <details className="word-forms">
                    <summary>Formes et expressions de la source</summary>
                    {w.forms.map((f) => (
                      <p key={f.id}>
                        <b lang="kab-Latn">{f.latin}</b>
                        <span>{f.french}</span>
                        {!!f.synonyms?.length && (
                          <small>Également : {f.synonyms.join(" · ")}</small>
                        )}
                      </p>
                    ))}
                  </details>
                )}
                <details className="word-sources">
                  <summary>Sources</summary>
                  {w.image ? (
                    <small>
                      Image : {w.image.author} · {w.image.license}
                    </small>
                  ) : (
                    <PhotoCredit art={w.art} />
                  )}
                  {w.sources.map((s, i) => (
                    <a href={s.url} key={i} target="_blank" rel="noreferrer">
                      {s.author} · {s.license} ↗
                    </a>
                  ))}
                </details>
              </article>
            ))}
          </div>
          {wordData && !wordData.total && (
            <p className="info-note">
              Il n’y a pas encore de mot isolé pour ce thème. Tu peux déjà
              découvrir ses phrases.
            </p>
          )}
          {wordData && wordData.total > 24 && (
            <div className="reading-pagination">
              <button
                className="secondary"
                disabled={!wordOffset}
                onClick={() => page("words", -1)}
              >
                Avant
              </button>
              <span>
                {wordOffset + 1}–{Math.min(wordOffset + 24, wordData.total)} /{" "}
                {wordData.total}
              </span>
              <button
                className="secondary"
                disabled={wordOffset + 24 >= wordData.total}
                onClick={() => page("words", 1)}
              >
                Après
              </button>
            </div>
          )}
        </>
      ) : (
        <>
          <div className="topic-section-title">
            <div>
              <h2>
                {selected
                  ? "Je fais des phrases avec « " +
                    selected.label.toLocaleLowerCase("fr") +
                    " »."
                  : "Les mots dans des phrases."}
              </h2>
              {selected && (
                <p>
                  Le mot ou une forme attestée est surligné dans chaque phrase.
                </p>
              )}
            </div>
            <button
              className="secondary"
              onClick={() => {
                setStage("words");
                setSelected(null);
                hydrate(topic, "words", null, wordOffset, phraseOffset, audioOnly);
              }}
            >
              <ChevronLeft size={16} /> Revoir les mots
            </button>
          </div>
          {selected && (
            <div className="selected-topic-word">
              <WordArt art={selected.art} label={selected.label} />
              <div>
                <b lang="kab-Latn">{selected.latin}</b>
                <span>{selected.label}</span>
              </div>
              <button className="text-button" onClick={() => contexts(null)}>
                Toutes les phrases du thème
              </button>
            </div>
          )}
          <div className="phrase-filter-bar">
            <label className={"audio-only-toggle" + (audioOnly ? " active" : "")}>
              <input type="checkbox" checked={audioOnly} onChange={(event) => {
                setAudioOnly(event.target.checked);
                setPhraseOffset(0);
                hydrate(topic, "phrases", selected, wordOffset, 0, event.target.checked);
              }} />
              Avec audio uniquement
            </label>
            {phraseData && <span>{phraseData.total} phrase{phraseData.total !== 1 ? "s" : ""}</span>}
          </div>
          <div className="topic-phrase-grid">
            {phraseData?.items.map((p) => (
              <article
                className="topic-phrase-card"
                data-phrase={p.id}
                key={p.id}
              >
                <p className="topic-phrase-latin" lang="kab-Latn">
                  {p.highlight ? (
                    <>
                      {p.highlight.before}
                      <mark>{p.highlight.text}</mark>
                      {p.highlight.after}
                    </>
                  ) : (
                    p.latin
                  )}
                </p>
                <p>{p.french}</p>
                {badge(p.status)}
                <PhraseAudio audios={p.audios} text={p.latin} />
                <button
                  className="primary"
                  onClick={() => {
                    setExercise(p.id);
                    window.scrollTo(0, 0);
                  }}
                >
                  Construire cette phrase <ArrowRight size={17} />
                </button>
              </article>
            ))}
          </div>
          {phraseData && !phraseData.total && (
            <div className="topic-empty">
              <BookOpen size={34} />
              <h3>{audioOnly ? "Pas encore d’audio pour ces phrases." : "Pas encore de phrase attestée pour ce mot."}</h3>
              <p>{audioOnly ? "Tu peux consulter les phrases sans enregistrement." : "Tu peux déjà découvrir les autres phrases de ce thème."}</p>
              <button className="secondary" onClick={() => {
                if (audioOnly) { setAudioOnly(false); setPhraseOffset(0); hydrate(topic, "phrases", selected, wordOffset, 0, false); }
                else contexts(null);
              }}>
                {audioOnly ? "Afficher toutes les phrases" : "Voir les phrases du thème"}
              </button>
            </div>
          )}
          {phraseData && phraseData.total > 12 && (
            <div className="reading-pagination">
              <button
                className="secondary"
                disabled={!phraseOffset}
                onClick={() => page("phrases", -1)}
              >
                Avant
              </button>
              <span>
                {phraseOffset + 1}–
                {Math.min(phraseOffset + 12, phraseData.total)} /{" "}
                {phraseData.total}
              </span>
              <button
                className="secondary"
                disabled={phraseOffset + 12 >= phraseData.total}
                onClick={() => page("phrases", 1)}
              >
                Après
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
