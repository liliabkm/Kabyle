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
          <span className="eyebrow">REGARDE CETTE LETTRE</span>
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
              <PenLine size={16} /> Ton dessin
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
            {!hasDrawn && <span className="canvas-hint">Dessine ici !</span>}
          </div>
          <div className="draw-bottom">
            <span>Prends ton temps.</span>
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
              Garder mon dessin
            </button>
          </div>
        </div>
      </div>
      <div className="info-note">
        <Sparkles size={20} />
        <span>
          <b>Ton dessin n’est pas noté.</b> Compare-le à la lettre. La
          reconnaissance automatique n’est pas encore disponible.
        </span>
      </div>
    </>
  );
}
