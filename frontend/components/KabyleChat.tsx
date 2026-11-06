"use client";
import { FormEvent, useEffect, useState } from "react";
import { MessageCircle, Send } from "lucide-react";
import { request } from "../lib/api";
import PhraseAudio, { type Recording } from "./PhraseAudio";

type Reference = { number: number; id: string; latin: string; french: string; status: string; audios: Recording[] };
type Turn = { role: "user" | "assistant"; content: string; references?: Reference[] };
type Status = { available: boolean; model: string; adaptation: string; notice: string };

export default function KabyleChat() {
  const [status, setStatus] = useState<Status | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    try { setStatus(await request("chat/status") as Status); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Connexion impossible"); }
  }
  useEffect(() => { void refresh(); }, []);

  async function send(e: FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || busy) return;
    setBusy(true); setError("");
    try {
      const result = await request("chat", {
        method: "POST",
        body: JSON.stringify({
          message,
          history: turns.slice(-6).map(({ role, content }) => ({ role, content: content.slice(0, 2000) })),
        }),
      }) as { answer: string; references: Reference[] };
      setTurns(old => [...old, { role: "user", content: message }, {
        role: "assistant", content: result.answer, references: result.references,
      }]);
      setInput("");
    } catch (e) { setError(e instanceof Error ? e.message : "Réponse indisponible"); }
    finally { setBusy(false); }
  }

  return <section className="kabyle-chat">
    <div className="chat-header">
      <span className="chat-icon"><MessageCircle size={32} /></span>
      <div><h1>On parle kabyle ?</h1><p>Une question, une traduction, un petit échange.</p></div>
    </div>
    <div className="chat-connection">
      <strong>{status?.available
        ? status.adaptation === "lora_loaded" ? "Modèle adapté chargé" : "Modèle de base chargé"
        : "Modèle non connecté"}</strong>
      <p>{status?.notice || "Vérification de la connexion…"}</p>
      <button className="secondary" onClick={() => void refresh()}>Vérifier la connexion</button>
      {!status?.available && <details>
        <summary>Configurer le chatbot</summary>
        <p>Exporte le corpus, entraîne l’adaptateur dans Colab, puis démarre le serveur local.</p>
        <a href="https://github.com/liliabkm/Kabyle/blob/main/docs/chatbot-kabyle.md" target="_blank" rel="noreferrer">Guide d’installation</a>
      </details>}
    </div>
    <p className="chat-notice">Les réponses sont générées par un modèle et restent à vérifier.</p>
    <div aria-live="polite" aria-busy={busy}>
      {turns.map((turn, i) => <article key={i} className={`chat-bubble ${turn.role}`}>
        <strong>{turn.role === "user" ? "Toi" : "Compagnon kabyle · réponse générée"}</strong>
        <p className="chat-text">{turn.content}</p>
        {!!turn.references?.length && <details>
          <summary>Exemples du corpus fournis au modèle ({turn.references.length})</summary>
          <p>Ces exemples ne garantissent pas chaque affirmation de la réponse.</p>
          {turn.references.map(ref => <div key={ref.id} className="chat-reference">
            <strong>[{ref.number}] {ref.latin}</strong>
            <p>{ref.french} · {ref.status === "validated" ? "Validé" : "À vérifier"}</p>
            <PhraseAudio audios={ref.audios} text={ref.latin} />
          </div>)}
        </details>}
      </article>)}
    </div>
    <form onSubmit={send} className="chat-compose">
      <label htmlFor="chat-question">Ta question</label>
      <textarea id="chat-question" value={input} onChange={e => setInput(e.target.value)}
        maxLength={1200} rows={3} placeholder="Comment dit-on bonjour en kabyle ?" disabled={busy} />
      <div className="chat-actions">
        <button className="primary" disabled={busy || !status?.available || !input.trim()}>
          {busy ? "Le modèle réfléchit…" : <>Envoyer <Send size={16} /></>}
        </button>
        {turns.length > 0 && <button type="button" className="secondary" disabled={busy}
          onClick={() => setTurns([])}>Nouvelle conversation</button>}
      </div>
    </form>
    {error && <p role="alert" className="chat-error">{error}</p>}
  </section>;
}
