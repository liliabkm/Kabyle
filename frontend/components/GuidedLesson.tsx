"use client";
import { useRef, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  ChevronLeft,
  Eye,
  PenLine,
  RotateCcw,
  Star,
} from "lucide-react";
import type { Entry } from "../lib/types";
import { request } from "../lib/api";
import Mascot from "./Mascot";
export default function GuidedLesson({
  letters,
  number,
  total,
  onExit,
  onSaved,
  onNext,
  onDraw,
}: {
  letters: Entry[];
  number: number;
  total: number;
  onExit: () => void;
  onSaved: () => Promise<void>;
  onNext: () => void;
  onDraw: () => void;
}) {
  const [phase, setPhase] = useState<
      "intro" | "discover" | "practice" | "finished"
    >("intro"),
    [index, setIndex] = useState(0),
    [revealed, setRevealed] = useState(true),
    [feedback, setFeedback] = useState<boolean | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [mistakes, setMistakes] = useState(0);
  const attempt = useRef<string | null>(null);
  const entry = letters[index];
  const [options, setOptions] = useState(() =>
    [...letters].sort((a, b) => a.latin.localeCompare(b.latin)),
  );
  function prepare(i: number) {
    setIndex(i);
    setFeedback(null);
    setError("");
    attempt.current = null;
    setOptions(
      [...letters].sort((a, b) => {
        const k = i % letters.length;
        return (
          ((letters.indexOf(a) + k) % letters.length) -
          ((letters.indexOf(b) + k) % letters.length)
        );
      }),
    );
  }
  async function answer(value: string) {
    if (busy || feedback !== null) return;
    setBusy(true);
    setError("");
    try {
      attempt.current ??= crypto.randomUUID();
      const result = await request("answers", {
        method: "POST",
        body: JSON.stringify({
          content_id: entry.id,
          answer: value,
          attempt_id: attempt.current,
        }),
      });
      setFeedback(result.correct);
      if (!result.correct) setMistakes((v) => v + 1);
      await onSaved().catch(() =>
        setError(
          "Ta réponse est enregistrée. Le résumé des progrès ne peut pas être actualisé pour le moment.",
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function nextQuestion() {
    if (index + 1 === letters.length) {
      setPhase("finished");
      setIndex(0);
    } else prepare(index + 1);
  }
  return (
    <section className="guided-lesson">
      <button className="back" disabled={busy} onClick={onExit}>
        <ChevronLeft size={18} /> Mes leçons
      </button>
      <div className="lesson-topline">
        <span>
          LEÇON {number} / {total}
        </span>
        <span>{letters.length} lettres · à ton rythme</span>
      </div>
      <ol className="lesson-steps" aria-label="Étapes de la leçon">
        {[
          { id: "discover", name: "Je découvre", icon: BookOpen },
          { id: "practice", name: "Je m’entraîne", icon: RotateCcw },
          { id: "finished", name: "Je réussis", icon: Star },
        ].map((s) => (
          <li
            key={s.id}
            aria-current={
              (phase === "intro" ? "discover" : phase) === s.id
                ? "step"
                : undefined
            }
          >
            <s.icon size={18} />
            {s.name}
          </li>
        ))}
      </ol>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {phase === "intro" ? (
        <div className="lesson-intro">
          <div className="lesson-buddy">
            <Mascot />
          </div>
          <div className="eyebrow">UN PETIT OBJECTIF</div>
          <h1>Je reconnais {letters.length} lettres.</h1>
          <p>On les découvre ensemble. Ensuite, c’est à toi de jouer !</p>
          <div className="lesson-preview">
            {letters.map((l) => (
              <span key={l.id} lang="kab-Tfng">
                {l.tifinagh}
              </span>
            ))}
          </div>
          <button
            className="primary"
            onClick={() => {
              setPhase("discover");
              setIndex(0);
            }}
          >
            Découvrir les lettres <ArrowRight size={20} />
          </button>
        </div>
      ) : phase === "discover" ? (
        <div className="lesson-stage">
          <div className="eyebrow">
            LETTRE {index + 1} SUR {letters.length}
          </div>
          <h1>Regarde bien cette forme.</h1>
          <div className="letter-pair">
            <div>
              <span className="pair-label">TIFINAGH</span>
              <span lang="kab-Tfng">{entry.tifinagh}</span>
            </div>
            <span className="pair-equals">=</span>
            <div>
              <span className="pair-label">LATIN</span>
              <span>{revealed ? entry.latin : "?"}</span>
            </div>
          </div>
          <p className="lesson-hint">
            {revealed
              ? `Cette forme correspond à « ${entry.latin} ».`
              : "Quelle lettre se cache ici ?"}
          </p>
          <button
            className="text-button recall-button"
            onClick={() => setRevealed(!revealed)}
          >
            <Eye size={18} />
            {revealed ? "Je cache la réponse" : "Je regarde la réponse"}
          </button>
          <div className="lesson-controls">
            <button
              className="secondary"
              disabled={index === 0}
              onClick={() => {
                setIndex(index - 1);
                setRevealed(true);
              }}
            >
              <ChevronLeft size={18} /> Avant
            </button>
            <button
              className="primary"
              onClick={() => {
                setRevealed(true);
                if (index + 1 === letters.length) {
                  setPhase("practice");
                  prepare(0);
                } else setIndex(index + 1);
              }}
            >
              {index + 1 === letters.length
                ? "À moi de jouer !"
                : "Lettre suivante"}{" "}
              <ArrowRight size={18} />
            </button>
          </div>
          <details className="parent-note">
            <summary>Pour les parents</summary>
            <p>
              Cette activité enseigne la correspondance graphique
              tifinagh–latin. Aucun audio ni score de prononciation n’est
              disponible.
            </p>
            {entry.sources.map((s) => (
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
          </details>
        </div>
      ) : phase === "practice" ? (
        <div className="lesson-stage">
          <div className="eyebrow">
            DÉFI {index + 1} SUR {letters.length}
          </div>
          <h1>Quelle lettre as-tu reconnue ?</h1>
          <p>Choisis la lettre latine qui correspond.</p>
          <div className="quiz-glyph" lang="kab-Tfng">
            {entry.tifinagh}
          </div>
          <div className="answers lesson-answers">
            {options.map((o) => (
              <button
                disabled={busy || feedback !== null}
                key={o.id}
                onClick={() => answer(o.latin)}
              >
                {o.latin}
              </button>
            ))}
          </div>
          {feedback !== null && (
            <div
              className={feedback ? "feedback good" : "feedback"}
              role="status"
            >
              <b>{feedback ? "Bien joué !" : "Regarde, puis essaie encore."}</b>
              <p>
                <span lang="kab-Tfng">{entry.tifinagh}</span> = {entry.latin}
              </p>
              <button
                className="primary"
                disabled={busy}
                onClick={() => {
                  if (feedback) nextQuestion();
                  else {
                    setFeedback(null);
                    attempt.current = null;
                    setError("");
                  }
                }}
              >
                {feedback
                  ? index + 1 === letters.length
                    ? "Voir ma réussite"
                    : "Défi suivant"
                  : "Je réessaie"}{" "}
                <ArrowRight size={18} />
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="lesson-finished">
          <div className="lesson-award" aria-hidden="true">
            <Star size={48} fill="currentColor" />
          </div>
          <h1>Bravo, tu les as reconnues !</h1>
          <p>
            {letters.length} lettres, {letters.length} réponses trouvées.{" "}
            {mistakes
              ? "Tu as continué après tes erreurs. Bien joué !"
              : "Un joli début !"}
          </p>
          <div className="lesson-results">
            {letters.map((l) => (
              <span key={l.id}>
                <span lang="kab-Tfng">{l.tifinagh}</span>
                <b>{l.latin}</b>
                <Check size={18} />
              </span>
            ))}
          </div>
          <p className="lesson-saved">
            <Check size={17} /> Tes réponses sont enregistrées pour les
            révisions.
          </p>
          <div className="lesson-controls">
            <button className="secondary" onClick={onDraw}>
              <PenLine size={18} /> Je dessine ces lettres
            </button>
            <button className="primary" onClick={onNext}>
              {number < total ? "Leçon suivante" : "Voir mes progrès"}{" "}
              <ArrowRight size={18} />
            </button>
          </div>
          <button
            className="text-button"
            onClick={() => {
              setPhase("practice");
              setMistakes(0);
              prepare(0);
            }}
          >
            Rejouer cette leçon
          </button>
        </div>
      )}
    </section>
  );
}
