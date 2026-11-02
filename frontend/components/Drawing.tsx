"use client";
import { useRef, useState } from "react";
import { PenLine, RotateCcw, Sparkles } from "lucide-react";
import type { Entry } from "../lib/types";
export default function Drawing({ letters }: { letters: Entry[] }) {
  const canvas = useRef<HTMLCanvasElement>(null),
    drawing = useRef(false),
    [selected, setSelected] = useState(0),
    [hasDrawn, setHasDrawn] = useState(false);
  function clear() {
    canvas.current?.getContext("2d")?.clearRect(0, 0, 600, 600);
    setHasDrawn(false);
  }
  return (
    <>
      <div className="draw-layout">
        <div className="draw-reference">
          <span className="eyebrow">VOTRE MODÈLE</span>
          <span className="model-glyph" lang="kab-Tfng">
            {letters[selected]?.tifinagh}
          </span>
          <b>{letters[selected]?.latin.toUpperCase()}</b>
          <p>{letters[selected]?.hint}</p>
          <div className="letter-picker">
            {letters.map((l, i) => (
              <button
                aria-label={`Tracer ${l.latin}`}
                className={selected === i ? "active" : ""}
                onClick={() => {
                  setSelected(i);
                  clear();
                }}
                key={l.id}
              >
                {l.tifinagh}
              </button>
            ))}
          </div>
        </div>
        <div className="draw-panel">
          <div className="draw-toolbar">
            <span>
              <PenLine size={16} /> Votre espace d’écriture
            </span>
            <button className="text-button" onClick={clear}>
              <RotateCcw size={15} /> Effacer
            </button>
          </div>
          <div className="canvas-wrap">
            <canvas
              ref={canvas}
              width={600}
              height={600}
              aria-label="Zone pour tracer une lettre"
              onPointerDown={(e) => {
                const c = canvas.current!,
                  ctx = c.getContext("2d")!,
                  rect = c.getBoundingClientRect();
                c.setPointerCapture(e.pointerId);
                drawing.current = true;
                ctx.beginPath();
                ctx.moveTo(
                  ((e.clientX - rect.left) * 600) / rect.width,
                  ((e.clientY - rect.top) * 600) / rect.height,
                );
                setHasDrawn(true);
              }}
              onPointerMove={(e) => {
                if (!drawing.current) return;
                const c = canvas.current!,
                  ctx = c.getContext("2d")!,
                  rect = c.getBoundingClientRect();
                ctx.lineWidth = 12;
                ctx.strokeStyle = "#31594a";
                ctx.lineCap = "round";
                ctx.lineJoin = "round";
                ctx.lineTo(
                  ((e.clientX - rect.left) * 600) / rect.width,
                  ((e.clientY - rect.top) * 600) / rect.height,
                );
                ctx.stroke();
              }}
              onPointerUp={() => (drawing.current = false)}
              onPointerCancel={() => (drawing.current = false)}
            />
            {!hasDrawn && (
              <span className="canvas-hint">
                Tracez ici avec la souris ou le doigt
              </span>
            )}
          </div>
          <div className="draw-bottom">
            <span>Un espace libre, sans pression.</span>
            <button
              className="secondary"
              disabled={!hasDrawn}
              onClick={() => {
                const a = document.createElement("a");
                a.href = canvas.current!.toDataURL();
                a.download = `tifin-${letters[selected]?.latin}.png`;
                a.click();
              }}
            >
              Enregistrer mon tracé
            </button>
          </div>
        </div>
      </div>
      <div className="info-note">
        <Sparkles size={20} />
        <span>
          <b>Reconnaissance IA indisponible.</b> Aucun modèle évalué n’est
          déployé. Comparez visuellement votre tracé au modèle ; aucune
          prédiction n’est simulée.
        </span>
      </div>
    </>
  );
}
