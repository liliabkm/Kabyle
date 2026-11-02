"use client";
import { useRef, useState, useEffect } from "react";
import { Headphones } from "lucide-react";
import { request } from "../lib/api";
export default function Recorder() {
  const [url, setUrl] = useState(""),
    [recording, setRecording] = useState(false),
    [message, setMessage] = useState(""),
    [expected, setExpected] = useState(""),
    [observed, setObserved] = useState(""),
    [result, setResult] = useState<
      { operation: string; expected: string[]; observed: string[] }[]
    >([]);
  const rec = useRef<MediaRecorder | null>(null),
    stream = useRef<MediaStream | null>(null),
    urlRef = useRef("");
  useEffect(
    () => () => {
      rec.current?.state === "recording" && rec.current.stop();
      stream.current?.getTracks().forEach((t) => t.stop());
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    },
    [],
  );
  async function toggle() {
    if (recording) {
      rec.current?.stop();
      setRecording(false);
      return;
    }
    try {
      if (!navigator.mediaDevices || !window.MediaRecorder)
        throw Error(
          "L’enregistrement nécessite un navigateur compatible et un contexte HTTPS.",
        );
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      const recorder = new MediaRecorder(stream.current);
      rec.current = recorder;
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        if (urlRef.current) URL.revokeObjectURL(urlRef.current);
        urlRef.current = URL.createObjectURL(
          new Blob(chunks, { type: recorder.mimeType }),
        );
        setUrl(urlRef.current);
        stream.current?.getTracks().forEach((t) => t.stop());
      };
      recorder.start();
      setRecording(true);
      setMessage("");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <>
      <div className="oral-card">
        <span className="oral-symbol">
          <Headphones size={35} />
        </span>
        <h2>Écoutez votre propre voix.</h2>
        <p>
          Enregistrez un essai pour vous réécouter. La transcription automatique
          kabyle n’est pas disponible.
        </p>
        <button className="primary" onClick={toggle}>
          {recording
            ? "Arrêter l’enregistrement"
            : "Commencer un enregistrement"}
        </button>
        {recording && <p role="status">● Enregistrement en cours…</p>}
        {message && <p role="alert">{message}</p>}
        {url && (
          <div className="recording">
            <audio controls src={url} />
            <button
              className="text-button"
              onClick={() => {
                URL.revokeObjectURL(url);
                urlRef.current = "";
                setUrl("");
              }}
            >
              Supprimer
            </button>
          </div>
        )}
      </div>
      <details className="compare">
        <summary>Comparer deux textes manuellement</summary>
        <p>Un outil textuel d’appoint ; il n’évalue pas votre voix.</p>
        <label>
          Phrase attendue
          <input
            value={expected}
            onChange={(e) => setExpected(e.target.value)}
          />
        </label>
        <label>
          Texte à comparer
          <input
            value={observed}
            onChange={(e) => setObserved(e.target.value)}
          />
        </label>
        <button
          className="secondary"
          disabled={!expected || !observed}
          onClick={async () => {
            try {
              setResult(
                (
                  await request("practice/compare", {
                    method: "POST",
                    body: JSON.stringify({ expected, observed }),
                  })
                ).words,
              );
            } catch (e) {
              setMessage((e as Error).message);
            }
          }}
        >
          Comparer les mots
        </button>
        <div className="comparison">
          {result.map((r, i) => (
            <span
              className={r.operation === "equal" ? "match" : "difference"}
              key={i}
            >
              {r.operation === "equal"
                ? r.expected.join(" ")
                : `${r.expected.join(" ") || "∅"} → ${r.observed.join(" ") || "∅"}`}
            </span>
          ))}
        </div>
      </details>
    </>
  );
}
