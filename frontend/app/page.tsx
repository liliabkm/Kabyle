"use client";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  ChevronLeft,
  ChevronRight,
  Compass,
  Headphones,
  LayoutGrid,
  Leaf,
  Menu,
  PenLine,
  RotateCcw,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import Mascot from "../components/Mascot";
import Matching from "../components/Matching";
import type { Entry, Progress } from "../lib/types";
import { request } from "../lib/api";
import PageTitle from "../components/PageTitle";
import Course from "../components/Course";
import Drawing from "../components/Drawing";
import Recorder from "../components/Recorder";
import Admin from "../components/Admin";
type View =
  | "learn"
  | "alphabet"
  | "words"
  | "draw"
  | "oral"
  | "progress"
  | "admin";
export default function Home() {
  const [matching, setMatching] = useState<Entry[] | null>(null);
  const [view, setView] = useState<View>("learn"),
    [entries, setEntries] = useState<Entry[]>([]),
    [progress, setProgress] = useState<Progress[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [active, setActive] = useState<Entry | null>(null),
    [quiz, setQuiz] = useState(false),
    [answer, setAnswer] = useState<string | null>(null),
    [feedback, setFeedback] = useState<boolean | null>(null),
    [busy, setBusy] = useState(false),
    [round, setRound] = useState(0),
    [mode, setMode] = useState<"choice" | "complete">("choice"),
    [review, setReview] = useState(false),
    [attempt, setAttempt] = useState(""),
    [mobile, setMobile] = useState(false);
  const letters = entries.filter((e) => e.kind === "letter"),
    words = entries.filter((e) => e.kind === "word");
  const done = progress.filter((p) => p.correct > 0).length;
  const due = progress
    .filter((p) => new Date(p.due) <= new Date())
    .map((p) => p.content_id);
  const refresh = () => request("progress").then(setProgress);
  useEffect(() => {
    Promise.all([request("content").then(setEntries), refresh()])
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [view, quiz, matching]);
  function navigate(v: View) {
    setMatching(null);
    setView(v);
    setActive(null);
    setQuiz(false);
    setMobile(false);
    setError("");
  }
  function begin(list: Entry[], revisions = false) {
    if (!list.length) return;
    setReview(revisions);
    setActive(list[0]);
    setQuiz(true);
    setRound(0);
    setAnswer(null);
    setFeedback(null);
    setAttempt(crypto.randomUUID());
  }
  async function submit(value: string) {
    if (!active || busy || feedback !== null) return;
    setBusy(true);
    setError("");
    try {
      const result = await request("answers", {
        method: "POST",
        body: JSON.stringify({
          content_id: active.id,
          answer: value,
          attempt_id: attempt,
        }),
      });
      setAnswer(value);
      setFeedback(result.correct);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function next() {
    const pool = (active?.kind === "word" ? words : letters).filter(
      (e) => !review || due.includes(e.id),
    );
    const index = pool.findIndex((e) => e.id === active?.id);
    if (index + 1 >= pool.length) {
      setQuiz(false);
      setActive(null);
      setView("progress");
      return;
    }
    setActive(pool[index + 1]);
    setRound(round + 1);
    setFeedback(null);
    setAnswer(null);
    setAttempt(crypto.randomUUID());
  }
  const nav = [
    { id: "learn", label: "Accueil", icon: Compass },
    { id: "alphabet", label: "Les lettres", icon: BookOpen },
    { id: "words", label: "Les mots", icon: LayoutGrid },
    { id: "draw", label: "Dessiner", icon: PenLine },
    { id: "oral", label: "Ma voix", icon: Headphones },
    { id: "progress", label: "Mes progrès", icon: Target },
  ] as const;
  return (
    <div className="shell">
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            navigate("learn");
          }}
        >
          <span className="brandmark">ⵣ</span>
          <span>
            tifin<span className="branddot">.</span>
            <small>LE KABYLE, PAS À PAS</small>
          </span>
        </a>
        <div className="workspace-label">À TOI DE JOUER</div>
        <nav>
          {nav.map((n) => (
            <button
              key={n.id}
              className={view === n.id ? "nav-item selected" : "nav-item"}
              aria-current={view === n.id ? "page" : undefined}
              onClick={() => navigate(n.id)}
            >
              <n.icon size={19} />
              {n.label}
              {n.id === "learn" && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <Sparkles size={24} />
          <b>Tu peux y arriver !</b>
          <p>Une lettre à la fois.</p>
        </div>
        <button className="admin-nav" onClick={() => navigate("admin")}>
          <Settings size={17} /> Gestion des contenus
        </button>
        <div className="guest">
          <div className="avatar">A</div>
          <div>
            Mon petit espace<small>Pas besoin de compte</small>
          </div>
          <Leaf size={17} />
        </div>
      </aside>
      <div className="body">
        <header>
          <button
            className="mobile-menu icon-button"
            aria-label="Ouvrir le menu"
            aria-expanded={mobile}
            onClick={() => setMobile(!mobile)}
          >
            <Menu />
          </button>
          <div className="breadcrumb">
            Mon espace <ChevronRight size={14} />
            <strong>
              {nav.find((n) => n.id === view)?.label || "Gestion des contenus"}
            </strong>
          </div>
          <div className="header-right">
            <span className="level">
              <span /> Je débute
            </span>
            <div className="header-divider" />
            <span className="header-avatar">A</span>
          </div>
        </header>
        <main>
          {error && (
            <div role="alert" className="error">
              {error}
              <button onClick={() => setError("")} aria-label="Fermer">
                <X size={16} />
              </button>
            </div>
          )}
          {loading ? (
            <div className="empty">
              <Sparkles /> On prépare les jeux…
            </div>
          ) : matching ? (
            <Matching
              entries={matching}
              onExit={() => setMatching(null)}
              onSaved={refresh}
            />
          ) : quiz && active ? (
            <section className="exercise">
              <button
                className="back"
                onClick={() => {
                  setQuiz(false);
                  setActive(null);
                }}
              >
                <ChevronLeft size={16} /> Quitter l’exercice
              </button>
              <div className="eyebrow">
                À VOUS DE JOUER · QUESTION {round + 1}
              </div>
              <h1>
                {active.kind === "word"
                  ? "Quel mot correspond à cette image ?"
                  : mode === "complete"
                    ? "Écris la lettre correspondante"
                    : "Quelle est cette lettre ?"}
              </h1>
              <p className="muted">Regarde la forme et trouve sa lettre.</p>
              <div
                className="quiz-glyph"
                lang={active.kind === "letter" ? "kab-Tfng" : undefined}
              >
                {active.kind === "word" && active.images?.[0] ? (
                  <img
                    src={active.images[0].url}
                    alt="Illustration du mot à retrouver"
                  />
                ) : (
                  active.tifinagh
                )}
              </div>
              <div className="exercise-switch">
                <button
                  className={mode === "choice" ? "active" : ""}
                  onClick={() => setMode("choice")}
                >
                  Je choisis
                </button>
                <button
                  className={mode === "complete" ? "active" : ""}
                  onClick={() => setMode("complete")}
                >
                  J’écris
                </button>
              </div>
              {mode === "choice" ? (
                <div className="answers">
                  {[
                    active,
                    ...(active.kind === "word" ? words : letters)
                      .filter((e) => e.id !== active.id)
                      .slice(round % 3, (round % 3) + 3),
                  ]
                    .sort((a, b) => a.latin.localeCompare(b.latin))
                    .map((e) => (
                      <button
                        disabled={busy || feedback !== null}
                        className={
                          answer === e.latin
                            ? feedback
                              ? "correct"
                              : "wrong"
                            : ""
                        }
                        key={e.id}
                        onClick={() => submit(e.latin)}
                      >
                        {e.latin}
                      </button>
                    ))}
                </div>
              ) : (
                <form
                  className="inline-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    submit(String(new FormData(e.currentTarget).get("answer")));
                  }}
                >
                  <input
                    key={active.id}
                    aria-label="Ta réponse"
                    name="answer"
                    autoComplete="off"
                    required
                    disabled={feedback !== null}
                  />
                  <button
                    className="primary"
                    disabled={busy || feedback !== null}
                  >
                    Vérifier
                  </button>
                </form>
              )}
              {feedback !== null && (
                <div
                  className={feedback ? "feedback good" : "feedback"}
                  role="status"
                >
                  <b>
                    {feedback
                      ? "Bravo, bien joué !"
                      : "Presque ! Voici la bonne lettre."}
                  </b>
                  <p>
                    {active.tifinagh} = {active.latin}
                  </p>
                  <button className="primary" onClick={next}>
                    La suite <ArrowRight size={16} />
                  </button>
                </div>
              )}
            </section>
          ) : view === "learn" ? (
            <>
              <div className="page-heading home-heading">
                <div>
                  <span className="hello-tag">
                    <Sparkles size={17} /> Apprendre en s’amusant
                  </span>
                  <h1>Le kabyle, c’est parti !</h1>
                  <p>Un petit jeu. Une nouvelle découverte.</p>
                </div>
              </div>
              <section className="hero">
                <div className="hero-content">
                  <span className="pill">TON PREMIER DÉFI</span>
                  <h2>
                    On joue avec
                    <br />
                    les lettres ?
                  </h2>
                  <p>Regarde la forme. Trouve la bonne lettre !</p>
                  <button
                    className="cream-button"
                    onClick={() => begin(letters)}
                  >
                    C’est parti ! <ArrowRight size={22} />
                  </button>
                  <div className="hero-meta">
                    <span>
                      <BookOpen size={17} /> 8 lettres à découvrir
                    </span>
                  </div>
                </div>
                <div className="hero-art">
                  <span className="letter-bubble bubble-a" lang="kab-Tfng">
                    ⴰ
                  </span>
                  <span className="letter-bubble bubble-m" lang="kab-Tfng">
                    ⵎ
                  </span>
                  <Mascot />
                </div>
              </section>
              <div className="discovery-progress">
                <span className="progress-star" aria-hidden="true">
                  ★
                </span>
                <div>
                  <b>
                    {done
                      ? `Bravo ! ${done} lettre${done > 1 ? "s" : ""} découverte${done > 1 ? "s" : ""}`
                      : "Ta première étoile t’attend !"}
                  </b>
                  <div
                    className="discovery-track"
                    role="progressbar"
                    aria-label="Lettres découvertes"
                    aria-valuenow={
                      progress.filter(
                        (p) =>
                          p.correct > 0 &&
                          letters.some((l) => l.id === p.content_id),
                      ).length
                    }
                    aria-valuemin={0}
                    aria-valuemax={letters.length || 8}
                  >
                    <span
                      style={{
                        width: `${Math.min(100, (progress.filter((p) => p.correct > 0 && letters.some((l) => l.id === p.content_id)).length / Math.max(1, letters.length)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
                <button onClick={() => navigate("progress")}>
                  Mes progrès <ArrowRight size={18} />
                </button>
              </div>
              <div className="section-heading">
                <h2>Choisis ton activité</h2>
                <span>À ton rythme !</span>
              </div>
              <div className="course-grid">
                <Course
                  color="sand"
                  symbol="ⴰ"
                  label="1"
                  title="Les lettres"
                  text="Regarde et reconnais."
                  footer="Je découvre"
                  onClick={() => navigate("alphabet")}
                />
                <Course
                  color="sage"
                  symbol="✎"
                  label="2"
                  title="Je dessine"
                  text="À toi de tracer !"
                  footer="Je prends mon crayon"
                  onClick={() => navigate("draw")}
                />
                <Course
                  color="rose"
                  symbol="♧"
                  label="3"
                  title="Les mots"
                  text={
                    words.length
                      ? "Des images et des mots."
                      : "De nouvelles aventures se préparent."
                  }
                  footer={words.length ? "Je découvre" : "Bientôt disponible"}
                  onClick={() => navigate("words")}
                  pending={!words.length}
                />
              </div>
              <div className="home-games">
                <div>
                  <span className="game-icon">
                    <LayoutGrid size={28} />
                  </span>
                  <div>
                    <h3>Le jeu des paires</h3>
                    <p>Retrouve les cartes qui vont ensemble.</p>
                  </div>
                  <button
                    className="secondary"
                    onClick={() => setMatching(letters)}
                  >
                    Jouer <ArrowRight size={19} />
                  </button>
                </div>
                {due.length > 0 && (
                  <div>
                    <span className="game-icon">
                      <RotateCcw size={27} />
                    </span>
                    <div>
                      <h3>On révise ?</h3>
                      <p>
                        {due.length} carte{due.length > 1 ? "s" : ""} à
                        retrouver.
                      </p>
                    </div>
                    <button
                      className="secondary"
                      onClick={() =>
                        begin(
                          entries.filter((e) => due.includes(e.id)),
                          true,
                        )
                      }
                    >
                      Réviser <ArrowRight size={19} />
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : view === "alphabet" ? (
            <>
              <PageTitle
                tag="JE DÉCOUVRE"
                title="Touche une lettre !"
                text="Regarde sa forme et découvre son nom."
              />
              <details className="parent-note">
                <summary>Pour les parents : alphabet et sources</summary>
                <p>
                  Ces 8 lettres utilisent les correspondances de base du
                  tifinagh Unicode. Les variantes kabyles et la spirantisation
                  ne sont pas encore enseignées. Les audios et les exemples de
                  mots ne sont pas disponibles. Les sources sont indiquées sur
                  les fiches.
                </p>
              </details>
              <div className="alphabet-grid">
                {letters.map((e) => (
                  <button
                    key={e.id}
                    className={
                      active?.id === e.id
                        ? "letter-card current"
                        : "letter-card"
                    }
                    onClick={() => setActive(e)}
                  >
                    <span className="letter-number">
                      {String(letters.indexOf(e) + 1).padStart(2, "0")}
                    </span>
                    <span lang="kab-Tfng">{e.tifinagh}</span>
                    <b>{e.latin}</b>
                    {progress.some(
                      (p) => p.content_id === e.id && p.correct > 0,
                    ) && <Check className="letter-check" size={18} />}
                  </button>
                ))}
              </div>
              {active && (
                <div className="detail-card">
                  <div className="detail-glyph" lang="kab-Tfng">
                    {active.tifinagh}
                  </div>
                  <div>
                    <div className="eyebrow">REGARDE BIEN</div>
                    <h2>
                      {active.latin.toUpperCase()} <small>{active.ipa}</small>
                    </h2>
                    <p>{active.hint}</p>
                    <p className="tiny">
                      Pas encore d’exemple de mot pour cette lettre.
                    </p>
                    <a
                      className="source"
                      href={active.sources[0]?.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Source : {active.sources[0]?.author} ↗
                    </a>
                  </div>
                  <button
                    className="secondary"
                    onClick={() => navigate("draw")}
                  >
                    <PenLine size={17} /> Tracer
                  </button>
                </div>
              )}
              <div className="action-bar">
                <p>
                  <Sparkles size={18} /> À toi de jouer !
                </p>
                <button
                  className="secondary"
                  onClick={() => setMatching(letters)}
                >
                  Jouer aux paires
                </button>
                <button className="primary" onClick={() => begin(letters)}>
                  Jouer avec les lettres <ArrowRight size={17} />
                </button>
              </div>
            </>
          ) : view === "words" ? (
            <>
              <PageTitle
                tag="03 · LE QUOTIDIEN"
                title="Les mots en images"
                text="Regarde l’image et trouve le mot."
              />
              <div className="themes">
                {[
                  "Tous les thèmes",
                  "Animaux",
                  "Fruits",
                  "Légumes",
                  "Famille",
                  "Maison",
                  "Vie quotidienne",
                ].map((t) => (
                  <span key={t}>{t}</span>
                ))}
              </div>
              {words.length ? (
                <>
                  <div className="course-grid">
                    {words.map((w) => (
                      <div className="word-card" key={w.id}>
                        {w.images?.[0] && (
                          <img alt={w.french} src={w.images[0].url} />
                        )}
                        <h2>{w.latin}</h2>
                        <span lang="kab-Tfng">{w.tifinagh}</span>
                        <p>{w.french}</p>
                        {[...w.sources, ...(w.images || [])].map((s) => (
                          <a
                            className="source"
                            key={s.url}
                            href={s.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {s.author} · {s.license} ↗
                          </a>
                        ))}
                      </div>
                    ))}
                  </div>
                  <button
                    className="secondary"
                    onClick={() => setMatching(words)}
                  >
                    Jouer aux paires
                  </button>
                  <button className="primary" onClick={() => begin(words)}>
                    Pratiquer les mots <ArrowRight size={17} />
                  </button>
                </>
              ) : (
                <div className="empty">
                  <div className="empty-art">♧</div>
                  <span className="pill light">À DÉCOUVRIR BIENTÔT</span>
                  <h2>Les mots arrivent bientôt !</h2>
                  <p>En attendant, viens jouer avec les lettres !</p>
                  <button
                    className="secondary"
                    onClick={() => navigate("alphabet")}
                  >
                    Découvrir les lettres <ArrowRight size={16} />
                  </button>
                </div>
              )}
            </>
          ) : view === "draw" ? (
            <>
              <PageTitle
                tag="MON ATELIER"
                title="À toi de dessiner !"
                text="Choisis une lettre, puis dessine-la avec ton doigt ou la souris."
              />
              <Drawing letters={letters} />
            </>
          ) : view === "oral" ? (
            <>
              <PageTitle
                tag="JE M’ÉCOUTE"
                title="À toi de parler !"
                text="Enregistre ta voix, puis écoute-toi."
              />
              <Recorder />
              <div className="info-note">
                <ShieldCheck size={20} />
                <span>
                  Ta voix reste sur cet appareil. Les audios à écouter et la
                  transcription automatique ne sont pas encore disponibles.
                </span>
              </div>
            </>
          ) : view === "progress" ? (
            <>
              <PageTitle
                tag="BRAVO POUR TES EFFORTS"
                title="Mes petites victoires"
                text="Chaque essai te fait avancer."
              />
              <div className="progress-summary">
                <div>
                  <strong>
                    {done}
                    <small>/{entries.length}</small>
                  </strong>
                  <p>lettres découvertes</p>
                </div>
                <div>
                  <strong>{progress.reduce((n, p) => n + p.correct, 0)}</strong>
                  <p>bonnes réponses</p>
                </div>
                <div>
                  <strong>{progress.reduce((n, p) => n + p.errors, 0)}</strong>
                  <p>essais à revoir</p>
                </div>
              </div>
              <div className="action-bar">
                <div>
                  <h2>On essaie encore ?</h2>
                  <p>
                    {due.length
                      ? `${due.length} fiche(s) vous attendent.`
                      : "Tout est révisé. Tu peux découvrir une autre lettre !"}
                  </p>
                </div>
                <button
                  className="primary"
                  disabled={!due.length}
                  onClick={() =>
                    begin(
                      entries.filter((e) => due.includes(e.id)),
                      true,
                    )
                  }
                >
                  Réviser <RotateCcw size={16} />
                </button>
              </div>
              <div className="progress-list">
                {progress.map((p) => (
                  <div key={p.content_id}>
                    <span className="mini-glyph">
                      {entries.find((e) => e.id === p.content_id)?.tifinagh}
                    </span>
                    <b>{entries.find((e) => e.id === p.content_id)?.latin}</b>
                    <span>
                      {p.correct} réussite(s) · {p.errors} erreur(s)
                    </span>
                    <small>
                      Révision : {new Date(p.due).toLocaleDateString("fr-FR")}
                    </small>
                  </div>
                ))}
              </div>
              {!progress.length && (
                <div className="empty">
                  <Leaf />
                  <h2>Ta première lettre t’attend !</h2>
                  <button
                    className="primary"
                    onClick={() => navigate("alphabet")}
                  >
                    Explorer l’alphabet
                  </button>
                </div>
              )}
              <p className="tiny">
                Tes progrès sont gardés dans ce navigateur. Reviens demain pour
                continuer !
              </p>
              <button
                className="text-button"
                onClick={async () => {
                  if (
                    confirm(
                      "Effacer toutes vos réponses et votre progression ?",
                    )
                  ) {
                    await request("progress", { method: "DELETE" });
                    await refresh();
                  }
                }}
              >
                Effacer ma progression
              </button>
            </>
          ) : (
            <>
              <PageTitle
                tag="ESPACE ÉDITORIAL"
                title="Des contenus de confiance."
                text="Importez, corrigez et validez les ressources avant leur publication."
              />
              <Admin onSaved={() => request("content").then(setEntries)} />
            </>
          )}
        </main>
        <footer>
          <span className="footer-brand">tifin.</span>
          <span>Un petit jeu chaque jour.</span>
          <span>
            Apprendre, jouer, recommencer <Leaf size={13} />
          </span>
        </footer>
      </div>
    </div>
  );
}
