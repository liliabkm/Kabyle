"use client";
import { useState } from "react";
import { ArrowRight, ChevronLeft } from "lucide-react";
import type { Entry } from "../lib/types";
import { request } from "../lib/api";
export default function Matching({
  entries,
  onExit,
  onSaved,
}: {
  entries: Entry[];
  onExit: () => void;
  onSaved: () => void;
}) {
  const cards = entries.slice(0, 4);
  const [selected, setSelected] = useState<Entry | null>(null),
    [matched, setMatched] = useState<string[]>([]),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function match(right: Entry) {
    if (!selected || busy) return;
    setBusy(true);
    try {
      const result = await request("answers", {
        method: "POST",
        body: JSON.stringify({
          content_id: selected.id,
          answer: right.latin,
          attempt_id: crypto.randomUUID(),
        }),
      });
      if (result.correct) {
        setMatched([...matched, selected.id]);
        setMessage("Bravo, une paire trouvée !");
        setSelected(null);
      } else {
        setMessage("Pas cette carte. Essaie une autre !");
      }
      onSaved();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="exercise">
      <button className="back" onClick={onExit}>
        <ChevronLeft size={16} /> Retour aux fiches
      </button>
      <div className="eyebrow">LE JEU DES PAIRES</div>
      <h1>Trouve les bonnes paires !</h1>
      <p className="muted">
        Touche une forme à gauche, puis sa lettre à droite.
      </p>
      <div className="matching">
        <div>
          {cards.map((c) => (
            <button
              disabled={matched.includes(c.id) || busy}
              className={selected?.id === c.id ? "selected" : ""}
              key={c.id}
              onClick={() => setSelected(c)}
            >
              {c.kind === "word" && c.images?.[0] ? (
                <img src={c.images[0].url} alt="Mot à retrouver" />
              ) : (
                <span lang="kab-Tfng">{c.tifinagh}</span>
              )}
            </button>
          ))}
        </div>
        <div>
          {[...cards].reverse().map((c) => (
            <button
              key={c.id}
              disabled={matched.includes(c.id) || !selected || busy}
              onClick={() => match(c)}
            >
              {c.latin}
            </button>
          ))}
        </div>
      </div>
      <p role="status" className="muted">
        {message}
      </p>
      {matched.length === cards.length && (
        <div className="feedback good">
          <b>Toutes les paires sont réunies !</b>
          <p>Bravo, tu as tout trouvé !</p>
          <button className="primary" onClick={onExit}>
            Continuer <ArrowRight size={16} />
          </button>
        </div>
      )}
    </section>
  );
}
