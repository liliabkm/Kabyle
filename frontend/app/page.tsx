"use client";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  ChevronLeft,
  ChevronRight,
  Compass,
  Flame,
  Flower2,
  Headphones,
  LayoutGrid,
  Leaf,
  LockKeyhole,
  Menu,
  PenLine,
  RotateCcw,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  Volume2,
  X,
} from "lucide-react";
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
    { id: "learn", label: "Mon parcours", icon: Compass },
    { id: "alphabet", label: "Alphabet tifinagh", icon: BookOpen },
    { id: "words", label: "Les mots du quotidien", icon: LayoutGrid },
    { id: "draw", label: "Atelier d’écriture", icon: PenLine },
    { id: "oral", label: "Pratique orale", icon: Headphones },
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
        <div className="workspace-label">MON ESPACE D’APPRENTISSAGE</div>
        <nav>
          {nav.map((n) => (
            <button
              key={n.id}
              className={view === n.id ? "nav-item selected" : "nav-item"}
              onClick={() => navigate(n.id)}
            >
              <n.icon size={19} />
              {n.label}
              {n.id === "learn" && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <Flower2 size={28} />
          <b>
            Une langue se transmet.
            <br />
            Un peu chaque jour.
          </b>
          <p>Chaque lettre est un nouveau lien avec la culture kabyle.</p>
          <span>ⴰ ⵣ ⵓ ⵍ</span>
        </div>
        <button className="admin-nav" onClick={() => navigate("admin")}>
          <Settings size={17} /> Gestion des contenus
        </button>
        <div className="guest">
          <div className="avatar">A</div>
          <div>
            Apprenant curieux<small>Parcours sans compte</small>
          </div>
          <Leaf size={17} />
        </div>
      </aside>
      <div className="body">
        <header>
          <button
            className="mobile-menu icon-button"
            aria-label="Ouvrir le menu"
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
              <span /> Niveau découverte
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
              <Sparkles /> Chargement de votre parcours…
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
                    ? "Complétez la transcription"
                    : "Quelle transcription correspond ?"}
              </h1>
              <p className="muted">
                Observez, puis retrouvez la transcription latine correspondante.
              </p>
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
                  Choisir une réponse
                </button>
                <button
                  className={mode === "complete" ? "active" : ""}
                  onClick={() => setMode("complete")}
                >
                  Écrire la réponse
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
                    aria-label="Transcription latine"
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
                  <b>{feedback ? "Très bien !" : "Continuons à apprendre."}</b>
                  <p>
                    {active.tifinagh} correspond à « {active.latin} ».{" "}
                    {active.hint}
                  </p>
                  <button className="primary" onClick={next}>
                    Continuer <ArrowRight size={16} />
                  </button>
                </div>
              )}
            </section>
          ) : view === "learn" ? (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    LE PLAISIR D’APPRENDRE · À VOTRE RYTHME
                  </div>
                  <h1>
                    Un petit pas, un nouveau lien<span>.</span>
                  </h1>
                  <p>
                    Découvrez le kabyle à votre rythme. Votre voyage commence
                    ici.
                  </p>
                </div>
                <span className="welcome-symbol">✳︎</span>
              </div>
              <section className="hero">
                <div className="hero-content">
                  <span className="pill">
                    <span /> VOTRE PREMIÈRE AVENTURE
                  </span>
                  <h2>
                    Et si tout commençait
                    <br />
                    par une lettre ?
                  </h2>
                  <p>
                    Faites connaissance avec le tifinagh.
                    <br />
                    Des formes, des sons, et une culture à découvrir.
                  </p>
                  <button
                    className="cream-button"
                    onClick={() => {
                      navigate("alphabet");
                      setActive(letters[0] || null);
                    }}
                  >
                    Découvrir l’alphabet <ArrowRight size={18} />
                  </button>
                  <div className="hero-meta">
                    <span>
                      <BookOpen size={14} /> 8 lettres pour commencer
                    </span>
                    <span>≈ 5 minutes</span>
                  </div>
                </div>
                <div className="hero-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="art-glyph g1">ⴰ</div>
                  <div className="art-glyph g2">ⵎ</div>
                  <div className="art-glyph g3">ⵣ</div>
                  <div className="art-star">✳︎</div>
                  <span className="art-dot dot1" />
                  <span className="art-dot dot2" />
                  <svg className="hill" viewBox="0 0 600 220">
                    <path
                      d="M0 185 Q100 35 210 150 T440 110 T600 170 L600 220 L0 220Z"
                      fill="#537665"
                    />
                    <path
                      d="M0 220 Q140 105 260 180 T600 150 L600 220Z"
                      fill="#638673"
                    />
                  </svg>
                </div>
              </section>
              <section className="stats-row">
                <div>
                  <span className="stat-icon peach">
                    <Flame size={20} />
                  </span>
                  <div>
                    <b>
                      {done}{" "}
                      <small>
                        lettre{done > 1 ? "s" : ""} explorée
                        {done > 1 ? "s" : ""}
                      </small>
                    </b>
                    <p>Chaque découverte compte</p>
                  </div>
                </div>
                <div>
                  <span className="stat-icon sage">
                    <Target size={20} />
                  </span>
                  <div>
                    <b>
                      {due.length}{" "}
                      <small>révision{due.length > 1 ? "s" : ""} à faire</small>
                    </b>
                    <p>Pour ancrer vos connaissances</p>
                  </div>
                </div>
                <div>
                  <span className="stat-icon lilac">
                    <Leaf size={20} />
                  </span>
                  <div>
                    <b>À votre rythme</b>
                    <p>Aucune course, juste le plaisir</p>
                  </div>
                </div>
              </section>
              <div className="section-heading">
                <div>
                  <h2>Votre chemin de découverte</h2>
                  <p>Un peu de curiosité, beaucoup de possibilités.</p>
                </div>
                <span className="section-label">LES PREMIERS PAS</span>
              </div>
              <div className="course-grid">
                <Course
                  color="sand"
                  symbol="ⴰ"
                  label="01 · LES FONDATIONS"
                  title="Lire les premières lettres"
                  text="Apprivoisez 8 lettres tifinaghes et leurs équivalents latins."
                  footer="8 fiches · Exercices de reconnaissance"
                  onClick={() => navigate("alphabet")}
                />
                <Course
                  color="sage"
                  symbol="✎"
                  label="02 · LE GESTE"
                  title="Donner forme aux lettres"
                  text="Prenez un crayon virtuel et laissez votre main apprendre."
                  footer="Atelier libre · Souris ou doigt"
                  onClick={() => navigate("draw")}
                />
                <Course
                  color="rose"
                  symbol="♧"
                  label="03 · LE QUOTIDIEN"
                  title="Des mots, tout un monde"
                  text="Animaux, fruits, famille… Un vocabulaire qui prend vie."
                  footer={
                    words.length
                      ? `${words.length} mots disponibles`
                      : "Contenus en cours de validation"
                  }
                  onClick={() => navigate("words")}
                  pending={!words.length}
                />
              </div>
              <div className="bottom-note">
                <span>ⵣ</span>
                <div>
                  <b>
                    Apprendre une langue, c’est aussi rencontrer une culture.
                  </b>
                  <p>
                    Nous construisons ce parcours avec soin : les contenus
                    lexicaux sont publiés après validation de leurs sources.
                  </p>
                </div>
                <Leaf size={23} />
              </div>
            </>
          ) : view === "alphabet" ? (
            <>
              <PageTitle
                tag="01 · LES FONDATIONS"
                title="L’alphabet, lettre par lettre."
                text="Huit formes à reconnaître. Le premier chapitre de votre découverte."
              />
              <div className="info-note">
                <BookOpen size={19} />
                <span>
                  Convention d’initiation : correspondances de base communes au
                  tifinagh Unicode. Les variantes et la spirantisation kabyles
                  ne sont pas encore enseignées. Aucun audio n’est disponible
                  pour ces fiches.
                </span>
              </div>
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
                    <div className="eyebrow">UNE LETTRE À DÉCOUVRIR</div>
                    <h2>
                      {active.latin.toUpperCase()} <small>{active.ipa}</small>
                    </h2>
                    <p>{active.hint}</p>
                    <p className="tiny">
                      Correspondance graphique vérifiée dans Unicode ; exemples
                      de mots en attente de validation.
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
                  <Sparkles size={18} /> Prêt à reconnaître ces formes ?
                </p>
                <button
                  className="secondary"
                  onClick={() => setMatching(letters)}
                >
                  Associer les cartes
                </button>
                <button className="primary" onClick={() => begin(letters)}>
                  Commencer les exercices <ArrowRight size={17} />
                </button>
              </div>
            </>
          ) : view === "words" ? (
            <>
              <PageTitle
                tag="03 · LE QUOTIDIEN"
                title="Un monde de mots."
                text="Des images pour découvrir, des exercices pour mémoriser."
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
                    Associer les cartes
                  </button>
                  <button className="primary" onClick={() => begin(words)}>
                    Pratiquer les mots <ArrowRight size={17} />
                  </button>
                </>
              ) : (
                <div className="empty">
                  <div className="empty-art">♧</div>
                  <span className="pill light">
                    LA QUALITÉ AVANT LA QUANTITÉ
                  </span>
                  <h2>Les premiers mots se préparent.</h2>
                  <p>
                    Les traductions, transcriptions tifinaghes et droits des
                    images doivent être vérifiés avant publication. Aucun mot
                    non validé n’est présenté comme une leçon.
                  </p>
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
                tag="02 · LE GESTE"
                title="À vous de tracer."
                text="Observez une lettre et redessinez-la. Prenez tout votre temps."
              />
              <Drawing letters={letters} />
            </>
          ) : view === "oral" ? (
            <>
              <PageTitle
                tag="LA LANGUE SE VIT AUSSI À L’ORAL"
                title="Écouter. Essayer. Recommencer."
                text="Un espace de pratique, sans note de prononciation."
              />
              <Recorder />
              <div className="info-note">
                <ShieldCheck size={20} />
                <span>
                  Aucun audio pédagogique n’a encore été importé : une paire
                  audio–texte doit être vérifiée. L’enregistrement personnel
                  reste sur votre appareil et n’est jamais envoyé
                  automatiquement.
                </span>
              </div>
            </>
          ) : view === "progress" ? (
            <>
              <PageTitle
                tag="CHAQUE PETIT PAS COMPTE"
                title="Votre parcours prend forme."
                text="Vos réponses sont sauvegardées sans compte, dans cet espace personnel."
              />
              <div className="progress-summary">
                <div>
                  <strong>
                    {done}
                    <small>/{entries.length}</small>
                  </strong>
                  <p>fiches pratiquées avec succès</p>
                </div>
                <div>
                  <strong>{progress.reduce((n, p) => n + p.correct, 0)}</strong>
                  <p>bonnes réponses</p>
                </div>
                <div>
                  <strong>{progress.reduce((n, p) => n + p.errors, 0)}</strong>
                  <p>occasions de réviser</p>
                </div>
              </div>
              <div className="action-bar">
                <div>
                  <h2>Votre prochaine révision</h2>
                  <p>
                    {due.length
                      ? `${due.length} fiche(s) vous attendent.`
                      : "Aucune révision en attente. Découvrez de nouvelles lettres !"}
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
                  <h2>Votre première lettre vous attend.</h2>
                  <button
                    className="primary"
                    onClick={() => navigate("alphabet")}
                  >
                    Explorer l’alphabet
                  </button>
                </div>
              )}
              <p className="tiny">
                Conservez les cookies de ce navigateur pour retrouver votre
                progression. Les révisions s’espacent après chaque réussite ;
                une erreur remet la fiche à réviser aujourd’hui.
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
          <span>Une lettre après l’autre. Un lien qui grandit.</span>
          <span>
            Fait pour les esprits curieux <Leaf size={13} />
          </span>
        </footer>
      </div>
    </div>
  );
}
