"use client";
import { useEffect, useState } from "react";
import { ArrowRight, ChevronLeft, Check, BookOpen } from "lucide-react";
import { request } from "../lib/api";
import { TopicArt } from "./TopicArt";
import PhraseAudio, { type Recording } from "./PhraseAudio";

export type PathLesson = { id: string; title: string; objective: string; status: string; completed: boolean; available: boolean; reason: string; activity_count: number; prerequisites: string[]; revision: number };
export type CoursePath = { id: string; title: string; notice: string; levels: {id: string; code: string; title: string; review_status: string; units: {id: string; title: string; objective: string; topic: string; lessons: PathLesson[]}[]}[] };
type Lesson = { id: string; title: string; objective: string; contents: {id: string; latin: string; french: string; kind: string; audios: Recording[]; sources: {url: string; author: string}[]}[] };
type Question = { id: string; kind: string; french: string; audios: Recording[]; tokens: {id: number; text: string}[] };
type Run = {run_id: string; questions: Question[]};
type Feedback = {correct: boolean; expected: string; passed: boolean; completed_activities: number; total_activities: number};

export default function LearningPath() {
  const [path, setPath] = useState<CoursePath | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [run, setRun] = useState<Run | null>(null);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [chosen, setChosen] = useState<number[]>([]);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState("");
  const [level, setLevel] = useState("");
  async function refresh() {
    const courses = await request("courses");
    if (courses.length) setPath(await request(`courses/${courses[0].id}`));
  }
  useEffect(() => { refresh().catch((e) => setError(e.message)); }, []);
  async function open(id: string) {
    setBusy(true); setError("");
    try { setLesson(await request(`course-lessons/${id}`)); setRun(null); setFeedback(null); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function start() {
    if (!lesson) return;
    setBusy(true); setError("");
    try {
      setRun(await request(`course-lessons/${lesson.id}/start`, {method: "POST"}));
      setIndex(0); setChosen([]); setAnswer(""); setFeedback(null); setAttempt(crypto.randomUUID());
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  const question = run?.questions[index];
  async function check() {
    if (!run || !question) return;
    setBusy(true); setError("");
    const value = question.kind === "order" ? chosen.map((id) => question.tokens.find((t) => t.id === id)!.text).join(" ") : answer;
    try { setFeedback(await request(`course-runs/${run.run_id}/answer`, {method: "POST", body: JSON.stringify({activity_id: question.id, answer: value, attempt_id: attempt})})); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function back() {
    setLesson(null); setRun(null); setError(""); setFeedback(null);
    try { await refresh(); } catch (e) { setError((e as Error).message); }
  }
  function next() {
    setIndex(index + 1); setChosen([]); setAnswer(""); setFeedback(null); setAttempt(crypto.randomUUID());
  }
  if (lesson) return (
    <section className="course-player">
      <button className="secondary" onClick={back}><ChevronLeft size={17} /> Retour au parcours</button>
      <h1>{lesson.title}</h1><p>{lesson.objective}</p>
      {error && <p className="error" role="alert">{error}</p>}
      {!run ? <>
        <h2>D’abord, je découvre</h2>
        <div className="topic-word-grid">{lesson.contents.map((c) => <article className="topic-word-card" key={c.id}>
          <h3 lang="kab-Latn">{c.latin}</h3><p>{c.french}</p>
          <PhraseAudio audios={c.audios} text={c.latin} />
          <details><summary>Source</summary>{!c.sources.length && <p>Source à renseigner. Contenu à vérifier.</p>}{c.sources.map((source, i) => /^https?:\/\//.test(source.url) && <p key={i}><a href={source.url} target="_blank" rel="noreferrer">{source.author}</a></p>)}</details>
        </article>)}</div>
        <button className="primary" disabled={busy} onClick={start}>Commencer les exercices <ArrowRight size={17} /></button>
      </> : feedback?.passed ? <div className="course-finished" role="status">
        <Check size={36} /><h2>Leçon terminée !</h2><p>Toutes les activités ont été réussies. Tu peux la refaire quand tu veux.</p>
        <button className="primary" onClick={back}>Revenir au parcours</button>
      </div> : question && <>
        <p className="course-step">Activité {index + 1} / {run.questions.length}</p>
        <progress value={index} max={run.questions.length} aria-label="Progression dans la leçon" />
        <h2>{question.kind === "order" ? "Construis la phrase en kabyle" : question.kind === "dictation" ? "Écoute et écris en kabyle" : "Comment dit-on en kabyle ?"}</h2>
        {question.kind !== "dictation" && <p className="course-prompt">{question.french}</p>}
        <PhraseAudio audios={question.audios} text={question.french} />
        {question.kind === "order" ? <>
          <div className="course-answer" aria-label="Ma phrase">{chosen.map((id) => <button className="secondary" key={id} disabled={busy || !!feedback} onClick={() => setChosen(chosen.filter((x) => x !== id))}>{question.tokens.find((t) => t.id === id)?.text}</button>)}</div>
          <div className="word-chips">{question.tokens.map((t) => <button key={t.id} disabled={busy || !!feedback || chosen.includes(t.id)} onClick={() => setChosen([...chosen, t.id])}>{t.text}</button>)}</div>
        </> : <>
          <label>Ma réponse en kabyle<input value={answer} autoComplete="off" disabled={busy || !!feedback} onChange={(e) => setAnswer(e.target.value)} /></label>
          <div className="word-chips">{"ɛɣḍḥṛṣṭẓčǧ".split("").map((c) => <button key={c} disabled={busy || !!feedback} onClick={() => setAnswer(answer + c)}>{c}</button>)}</div>
        </>}
        {!feedback && <button className="primary" disabled={busy || (question.kind === "order" ? !chosen.length : !answer.trim())} onClick={check}>Vérifier ma réponse</button>}
        {feedback && <div className={"feedback " + (feedback.correct ? "ok" : "retry")} role="status">
          <p>{feedback.correct ? "Bien joué !" : `La réponse attendue est : ${feedback.expected}`}</p>
          {feedback.correct ? <button className="primary" onClick={next}>Continuer <ArrowRight size={17} /></button> : <button className="secondary" onClick={() => { setFeedback(null); setAttempt(crypto.randomUUID()); }}>Réessayer</button>}
        </div>}
      </>}
    </section>
  );
  const levels = path?.levels || [];
  const current = levels.find((l) => l.id === level) || levels[0];
  return <section className="learning-path">
    <div className="eyebrow">MON PARCOURS</div><h1>{path?.title || "Le kabyle, pas à pas"}</h1>
    <p>De petites leçons, dans un ordre qui t’aide à avancer.</p>
    {error && <p className="error" role="alert">{error}</p>}
    {!path && !error && <p role="status">On prépare ton parcours…</p>}
    <div className="course-levels" role="group" aria-label="Choisir un niveau">{levels.map((l) => <button className={current?.id === l.id ? "primary" : "secondary"} key={l.id} onClick={() => setLevel(l.id)} aria-pressed={current?.id === l.id}>{l.code} · {l.title}</button>)}</div>
    {current?.units.map((u, i) => <section className="course-unit" key={u.id}>
      <div className="course-unit-heading"><TopicArt topic={u.topic} /><div><span className="eyebrow">UNITÉ {i + 1}</span><h2>{u.title}</h2><p>{u.objective}</p></div></div>
      {!u.lessons.length && <p>Les leçons de cette unité sont à préparer.</p>}
      <div className="course-lesson-grid">{u.lessons.map((l) => <button className="course-lesson-card" key={l.id} disabled={busy || !l.available} onClick={() => open(l.id)}>
        {l.completed ? <Check size={25} /> : <BookOpen size={25} />}<strong>{l.title}</strong>
        <span>{l.activity_count} activités{l.completed ? " · Terminée" : ""}</span>
        {!l.available && <small>{l.reason}</small>}
        {!!l.prerequisites.length && <small>Une leçon précédente est conseillée ; celle-ci reste accessible.</small>}
        <span>Je commence <ArrowRight size={16} /></span>
      </button>)}</div>
    </section>)}
    {path && <details><summary>À propos des niveaux</summary><p>{path.notice}</p></details>}
  </section>;
}
