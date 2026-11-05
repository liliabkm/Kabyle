"use client";
import { useEffect, useRef, useState } from "react";
import { request } from "../lib/api";
import type { CoursePath } from "./LearningPath";

type Stats = { pending: number; indexed: number; content_total: number; lexemes: number; sentences: number; translations: number; recordings: number; sources: number; snapshots: number; lessons: number; version: string; notice: string; topics: {id: string; label: string}[] };
type Choice = {id: string; latin: string; french: string; status: string; kind: string; learning_role?: string; audios?: unknown[]};
type Activity = {content_id: string; kind: string; latin: string; french: string};

export default function DataStudio({ token }: {token: string}) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [path, setPath] = useState<CoursePath | null>(null);
  const [busy, setBusy] = useState(false);
  const stop = useRef(false);
  useEffect(() => () => { stop.current = true; }, []);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [level, setLevel] = useState("");
  const [unit, setUnit] = useState("");
  const [title, setTitle] = useState("");
  const [objective, setObjective] = useState("");
  const [topic, setTopic] = useState("salutations");
  const [status, setStatus] = useState("draft");
  const [editing, setEditing] = useState("");
  const [prerequisites, setPrerequisites] = useState<string[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [newLevelCode, setNewLevelCode] = useState("B1");
  const [newLevelTitle, setNewLevelTitle] = useState("");
  const [lexicon, setLexicon] = useState<{items: {id: string; lemma: string; forms: string[]; translations: string[]}[]; total: number} | null>(null);
  const [kind, setKind] = useState("word");
  const [query, setQuery] = useState("");
  const [choices, setChoices] = useState<Choice[]>([]);
  const headers = {Authorization: "Bearer " + token};
  async function load() {
    const data: Stats = await request("admin/data-structure", {headers});
    setStats(data);
    const courses = await request("courses");
    if (courses.length) {
      const tree = await request(`admin/courses/${courses[0].id}`, {headers});
      setPath(tree); if (!level) setLevel(tree.levels[0]?.id || "");
    }
  }
  async function action(work: () => Promise<void>) {
    setBusy(true); setError("");
    try { await work(); } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function organize() {
    stop.current = false;
    await action(async () => {
      let remaining = 1;
      while (remaining && !stop.current) {
        const result = await request("admin/data-structure/process", {method: "POST", headers, body: JSON.stringify({size: 500})});
        remaining = result.remaining;
        setMessage(`${result.job_processed || result.processed} fiches organisées · ${remaining} restantes. Les lots terminés sont enregistrés.`);
        setStats(await request("admin/data-structure", {headers}));
      }
    });
  }
  async function edit(id: string) {
    await action(async () => {
      const lesson = await request(`admin/course-lessons/${id}`, {headers});
      setEditing(id); setLevel(lesson.level_id); setUnit(lesson.unit_title); setTitle(lesson.title); setObjective(lesson.objective);
      setTopic(lesson.topic); setStatus(lesson.status); setPrerequisites(lesson.prerequisites); setActivities(lesson.activities);
    });
  }
  async function save() {
    await action(async () => {
      const body = {level_id: level, unit_title: unit, title, objective, topic, status, prerequisites,
        activities: activities.map(({content_id, kind}) => ({content_id, kind}))};
      const result = await request(editing ? `admin/course-lessons/${editing}` : "admin/course-lessons", {method: editing ? "PUT" : "POST", headers, body: JSON.stringify(body)});
      setEditing(result.id); setMessage(`Leçon enregistrée · version ${result.revision}.`); await load();
    });
  }
  async function exportPlan() {
    if (!path) return;
    await action(async () => {
      const data = await request(`admin/courses/${path.id}/export`, {headers});
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: "application/json"}));
      const anchor = document.createElement("a"); anchor.href = url; anchor.download = `${path.id}-parcours.json`; anchor.click(); URL.revokeObjectURL(url);
    });
  }
  return <section className="data-studio" aria-labelledby="data-studio-title">
    <h2 id="data-studio-title">Organiser les données et les parcours</h2>
    <p>Le corpus conserve les sources. Les leçons sélectionnent des contenus de ce corpus, dans un ordre choisi.</p>
    <button className="secondary" disabled={!token || busy} onClick={() => action(load)}>Charger le bilan et le parcours</button>
    {error && <p className="error" role="alert">{error}</p>}
    {message && <p role="status">{message}</p>}
    {stats && <>
      <div className="data-stats">{[["Fiches sources", stats.content_total], ["À organiser", stats.pending], ["Unités lexicales", stats.lexemes], ["Phrases distinctes", stats.sentences], ["Traductions", stats.translations], ["Audios référencés", stats.recordings]].map(([label, value]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
      <div className="admin-actions"><button className="primary" disabled={busy || !stats.pending} onClick={organize}>Organiser les fiches restantes</button>{busy && <button className="secondary" onClick={() => {stop.current = true;}}>Arrêter après ce lot</button>}</div>
      <details><summary>Comment fonctionne cette organisation ?</summary><p>{stats.notice}</p><p>{stats.sources} sources · {stats.snapshots} versions de sources · {stats.version}. Les mots sont regroupés par sens connu ; les variantes inconnues restent à relire.</p><p>Tu peux fermer cette page et reprendre plus tard. Pour un gros import, utilise aussi <code>bash scripts/organize_data.sh</code>.</p></details>
    </>}
    {stats && <details><summary>Voir le lexique organisé</summary>
      <button className="secondary" disabled={busy} onClick={() => action(async () => {setLexicon(await request("admin/structured-lexicon", {headers}));})}>Charger les 20 premières unités lexicales</button>
      {lexicon && <><p>{lexicon.total} unités lexicales avec des sources actives. Formes et sens proposés, à relire.</p><ul>{lexicon.items.map((l) => <li key={l.id}><strong>{l.lemma}</strong> — {l.translations.join(" / ")}<p>Formes : {l.forms.join(", ")}</p></li>)}</ul></>}
    </details>}
    {path && <details className="course-builder">
      <summary>Composer ou modifier une leçon par niveau</summary>
      <p>Les leçons à vérifier sont publiques. Les prérequis sont des conseils, sans verrouillage. Les niveaux CECRL restent à relire.</p>
      <details><summary>Ajouter un niveau au parcours</summary><label>Code du nouveau niveau<select value={newLevelCode} onChange={(e) => setNewLevelCode(e.target.value)}>{["A1","A2","B1","B2","C1","C2"].map((code) => <option key={code}>{code}</option>)}</select></label><label>Nom du nouveau niveau<input value={newLevelTitle} maxLength={160} onChange={(e) => setNewLevelTitle(e.target.value)} /></label><button className="secondary" disabled={busy || !newLevelTitle.trim()} onClick={() => action(async () => {await request("admin/course-levels", {method:"POST", headers, body:JSON.stringify({course_id:path.id, code:newLevelCode, title:newLevelTitle})}); setMessage("Niveau proposé ajouté."); await load();})}>Ajouter ce niveau</button></details>
      <div className="admin-actions"><button className="secondary" disabled={busy} onClick={() => {setEditing(""); setTitle(""); setObjective(""); setActivities([]); setPrerequisites([]); setStatus("draft");}}>Nouvelle leçon</button><button className="secondary" disabled={busy} onClick={exportPlan}>Exporter le parcours JSON</button></div>
      <label>Leçon existante<select value={editing} disabled={busy} onChange={(e) => e.target.value && edit(e.target.value)}><option value="">Nouvelle leçon</option>{path.levels.flatMap((l) => l.units.flatMap((u) => u.lessons.map((lesson) => <option value={lesson.id} key={lesson.id}>{l.code} · {u.title} · {lesson.title}</option>)))}</select></label>
      <div className="word-lab-fields">
        <label>Niveau proposé<select value={level} disabled={busy} onChange={(e) => setLevel(e.target.value)}>{path.levels.map((l) => <option value={l.id} key={l.id}>{l.code} · {l.title}</option>)}</select></label>
        <label>Unité<input list="course-unit-options" value={unit} disabled={busy} maxLength={160} onChange={(e) => { setUnit(e.target.value); const selected = path.levels.find((l) => l.id === level)?.units.find((u) => u.title === e.target.value); if (selected) setTopic(selected.topic); }} /><datalist id="course-unit-options">{path.levels.find((l) => l.id === level)?.units.map((u) => <option value={u.title} key={u.id} />)}</datalist></label>
      </div>
      <label>Titre de la leçon<input value={title} maxLength={160} disabled={busy} onChange={(e) => setTitle(e.target.value)} /></label>
      <label>Objectif pédagogique<input value={objective} maxLength={600} disabled={busy} onChange={(e) => setObjective(e.target.value)} /></label>
      <div className="word-lab-fields">
        <label>Thème de l’unité<select value={topic} disabled={busy} onChange={(e) => setTopic(e.target.value)}>{stats?.topics.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}</select></label>
        <label>Statut<select value={status} disabled={busy} onChange={(e) => setStatus(e.target.value)}><option value="draft">Publique · à vérifier</option><option value="validated">Validée après relecture</option><option value="rejected">Retirée du parcours public</option></select></label>
      </div>
      <label>Prérequis conseillés<select multiple value={prerequisites} disabled={busy} onChange={(e) => setPrerequisites(Array.from(e.target.selectedOptions, (x) => x.value))}>{path.levels.flatMap((l) => l.units.flatMap((u) => u.lessons.filter((x) => x.id !== editing).map((x) => <option key={x.id} value={x.id}>{l.code} · {x.title}</option>)))}</select></label>
      <h3>Choisir les contenus existants</h3>
      <div className="word-lab-fields"><label>Type de contenu<select value={kind} disabled={busy} onChange={(e) => setKind(e.target.value)}><option value="word">Mots</option><option value="phrase">Phrases</option></select></label><label>Recherche dans le corpus<input value={query} disabled={busy} onChange={(e) => setQuery(e.target.value)} placeholder="Ex. cheval" /></label></div>
      <button className="secondary" disabled={busy} onClick={() => action(async () => {const data = await request("admin/library?" + new URLSearchParams({kind, q: query, limit: "12"}), {headers}); setChoices(data.items.filter((c: Choice) => c.status !== "rejected"));})}>Chercher des contenus</button>
      <div className="course-bank">{choices.map((c) => <div key={c.id}><span><b>{c.latin}</b> — {c.french || "Traduction à compléter"}{["review", "fragment"].includes(c.learning_role || "") && " · Fiche à clarifier"}</span><button className="secondary" disabled={busy || activities.length >= 20 || !c.latin?.trim() || !c.french?.trim() || ["review", "fragment"].includes(c.learning_role || "")} onClick={() => setActivities([...activities, {content_id: c.id, kind: c.kind === "word" ? "recall" : "order", latin: c.latin, french: c.french}])}>Ajouter à la leçon</button></div>)}</div>
      <h3>{activities.length} activités dans l’ordre</h3>
      <ol className="course-editor-activities">{activities.map((a, i) => <li key={i}><p>{a.latin} — {a.french}</p><label>Exercice {i + 1}<select value={a.kind} disabled={busy} onChange={(e) => setActivities(activities.map((x,j) => j === i ? {...x, kind: e.target.value} : x))}><option value="recall">Écrire en kabyle</option><option value="order">Construire la phrase</option><option value="dictation">Dictée avec audio</option></select></label><div className="admin-actions"><button className="secondary" disabled={busy || i === 0} onClick={() => {const next = [...activities]; [next[i - 1], next[i]] = [next[i], next[i - 1]]; setActivities(next);}}>Monter</button><button className="secondary" disabled={busy || i === activities.length - 1} onClick={() => {const next = [...activities]; [next[i], next[i + 1]] = [next[i + 1], next[i]]; setActivities(next);}}>Descendre</button><button className="secondary" disabled={busy} onClick={() => setActivities(activities.filter((_,j) => i !== j))}>Retirer</button></div></li>)}</ol>
      <button className="primary" disabled={busy || !title.trim() || !unit.trim() || !objective.trim() || !activities.length} onClick={save}>Enregistrer la leçon</button>
    </details>}
  </section>;
}
