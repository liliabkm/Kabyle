"use client";
import { useState } from "react";
import { Plus, Search, Save, Trash2 } from "lucide-react";
import { request } from "../lib/api";
import PhraseAudio, { type Recording } from "./PhraseAudio";

type Pair = { latin: string; french: string };
type Linked = Pair & { id: string; audios?: Recording[]; highlight?: { before: string; text: string; after: string } | null };
type Matches = { items: Linked[]; total: number };
type Report = {
  classification: { theme: string; label: string; reason: string; confidence: string; candidates: string[] };
  existing_phrases: Matches;
  provided_phrases: (Pair & { matches: boolean })[];
  categories: { id: string; label: string }[];
  notice: string;
  word_id?: string;
  word_created?: boolean;
  theme?: string;
  status?: string;
  phrases_added?: number;
  phrase_duplicates?: number;
  related_phrases?: Matches;
};

export default function WordLaboratory({ token, onSaved }: { token: string; onSaved: () => void }) {
  const [latin, setLatin] = useState("");
  const [french, setFrench] = useState("");
  const [variants, setVariants] = useState("");
  const [category, setCategory] = useState("");
  const [pairs, setPairs] = useState<Pair[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [categories, setCategories] = useState<Report["categories"]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [offset, setOffset] = useState(0);
  const [links, setLinks] = useState<Matches | null>(null);
  const headers = { Authorization: "Bearer " + token };
  function changed() { setReport(null); setLinks(null); setOffset(0); setError(""); }
  function body() {
    const phrases = pairs.filter((p) => p.latin.trim() || p.french.trim());
    if (phrases.some((p) => !p.latin.trim() || !p.french.trim())) throw Error("Chaque phrase doit avoir son texte kabyle et sa traduction française.");
    return { latin, french, synonyms: variants.split(",").map((s) => s.trim()).filter(Boolean), category, phrases };
  }
  async function submit(save: boolean) {
    setBusy(true); setError("");
    try {
      const result: Report = await request(`admin/word-laboratory/${save ? "save" : "preview"}`, { method: "POST", headers, body: JSON.stringify(body()) });
      setReport(result); setCategories(result.categories); setOffset(0);
      setLinks(result.related_phrases || result.existing_phrases);
      if (save) onSaved();
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function page(next: number) {
    if (!report?.word_id) return;
    setBusy(true); setError("");
    try {
      setLinks(await request(`words/${encodeURIComponent(report.word_id)}/phrases?offset=${next}`));
      setOffset(next);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  return (
    <section className="word-laboratory" aria-labelledby="word-lab-title">
      <h2 id="word-lab-title">Ajouter un mot et tester ses associations</h2>
      <p>Renseigne le mot et sa traduction. L’aperçu cherche dans toute la base, sans rien enregistrer.</p>
      <div className="word-lab-fields">
        <label>Mot kabyle<input value={latin} maxLength={200} disabled={busy} onChange={(e) => { setLatin(e.target.value); changed(); }} placeholder="Ex. agmar" /></label>
        <label>Traduction française<input value={french} maxLength={200} disabled={busy} onChange={(e) => { setFrench(e.target.value); changed(); }} placeholder="Ex. cheval" /></label>
      </div>
      <label>Variantes ou pluriels kabyles (facultatif)<input value={variants} disabled={busy} onChange={(e) => { setVariants(e.target.value); changed(); }} placeholder="Sépare les formes par une virgule" /></label>
      {!!categories.length && <label>Catégorie<select value={category} disabled={busy} onChange={(e) => { setCategory(e.target.value); changed(); }}>
        <option value="">Classement automatique</option>
        {categories.map((c) => <option key={c.id} value={c.id}>{c.label}</option>)}
      </select></label>}
      <h3>Phrases supplémentaires (facultatif)</h3>
      {pairs.map((pair, index) => (
        <div className="word-lab-pair" key={index}>
          <label>Phrase kabyle {index + 1}<input maxLength={1000} value={pair.latin} disabled={busy} onChange={(e) => { setPairs(pairs.map((p, i) => i === index ? { ...p, latin: e.target.value } : p)); changed(); }} /></label>
          <label>Traduction de la phrase {index + 1}<input maxLength={1000} value={pair.french} disabled={busy} onChange={(e) => { setPairs(pairs.map((p, i) => i === index ? { ...p, french: e.target.value } : p)); changed(); }} /></label>
          <button className="secondary" disabled={busy} aria-label={`Supprimer la phrase ${index + 1}`} onClick={() => { setPairs(pairs.filter((_, i) => i !== index)); changed(); }}><Trash2 size={17} /></button>
        </div>
      ))}
      <button className="secondary" disabled={busy || pairs.length >= 20} onClick={() => { setPairs([...pairs, { latin: "", french: "" }]); changed(); }}><Plus size={17} /> Ajouter une phrase</button>
      <div className="admin-actions">
        <button className="primary" disabled={busy || !token || !latin.trim() || !french.trim()} onClick={() => submit(false)}><Search size={17} /> {busy ? "Traitement…" : "Tester sans enregistrer"}</button>
        <button className="secondary" disabled={busy || !token || !report || !!report.word_id || report.provided_phrases.some((p) => !p.matches)} onClick={() => submit(true)}><Save size={17} /> Enregistrer dans la base</button>
      </div>
      {!token && <p>Renseigne ton jeton administrateur pour lancer l’essai.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {report && <div className="word-lab-report">
        <h3>{report.word_id ? "Résultat enregistré" : "Aperçu du classement"}</h3>
        <p><strong>{report.classification.label}</strong> · {report.classification.reason}</p>
        {report.classification.candidates.length > 1 && <p>Catégories possibles : {report.classification.candidates.map((id) => report.categories.find((c) => c.id === id)?.label || id).join(", ")}</p>}
        {report.classification.confidence === "uncertain" && <p className="info-note">Le classement demande une vérification. Tu peux choisir une catégorie ci-dessus, puis refaire l’essai.</p>}
        {report.word_id && <p role="status">{report.word_created ? "Mot ajouté et public, à vérifier." : "Ce mot existe déjà : sa fiche a été conservée."} {report.phrases_added} phrase(s) ajoutée(s), {report.phrase_duplicates} doublon(s) ignoré(s).</p>}
        {report.provided_phrases.map((p, i) => <p key={i}>{p.matches ? "✓" : "À corriger :"} {p.latin} — {p.french}{!p.matches && " · Le mot ou sa traduction n’a pas été retrouvé dans cette phrase."}</p>)}
        <h3>{links?.total || 0} phrase(s) {report.word_id ? "associée(s) dans la base" : "déjà présente(s) dans la base"}</h3>
        <p className="tiny">{report.notice}</p>
        {!report.word_id && links && links.total > 12 && <p className="tiny">Aperçu des 12 premières correspondances. Après enregistrement, toutes les pages seront accessibles.</p>}
        {!links?.total && <p>Aucune correspondance trouvée. Les variantes inconnues ne sont pas devinées.</p>}
        <div className="topic-phrase-grid">
          {links?.items.map((p) => <article className="topic-phrase-card" key={p.id}>
            <p lang="kab-Latn">{p.highlight ? <>{p.highlight.before}<mark>{p.highlight.text}</mark>{p.highlight.after}</> : p.latin}</p>
            <p>{p.french}</p>
            <PhraseAudio audios={p.audios} text={p.latin} />
          </article>)}
        </div>
        {report.word_id && links && links.total > 12 && <div className="reading-pagination">
          <button className="secondary" disabled={busy || !offset} onClick={() => page(Math.max(0, offset - 12))}>Avant</button>
          <span>{offset + 1}–{Math.min(offset + 12, links.total)} / {links.total}</span>
          <button className="secondary" disabled={busy || offset + 12 >= links.total} onClick={() => page(offset + 12)}>Après</button>
        </div>}
      </div>}
    </section>
  );
}
