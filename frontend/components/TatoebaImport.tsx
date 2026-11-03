"use client";
import { useState } from "react";
import { request } from "../lib/api";
type Preview = {
  upload_id: string;
  pairs: number;
  audio_records: number;
  pairs_with_audio: number;
  invalid_pairs: number;
  invalid_audio_rows: number;
  audio_without_credits: number;
  sample: { kab_id: number; fr_id: number; latin: string; french: string }[];
};
export default function TatoebaImport({
  token,
  onDone,
}: {
  token: string;
  onDone: () => void;
}) {
  const [pairs, setPairs] = useState<File | null>(null),
    [audio, setAudio] = useState<File | null>(null),
    [preview, setPreview] = useState<Preview | null>(null),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  async function prepare() {
    if (!pairs) return;
    setBusy(true);
    setMessage("");
    setPreview(null);
    try {
      const form = new FormData();
      form.append("pairs", pairs);
      if (audio) form.append("audio", audio);
      const r = await fetch("/api/admin/tatoeba/preview", {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
        body: form,
      });
      const data = await r.json();
      if (!r.ok)
        throw Error(
          typeof data.detail === "string" ? data.detail : "Fichier non reconnu",
        );
      setPreview(data);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function commit() {
    if (!preview) return;
    setBusy(true);
    try {
      const r = await request("admin/tatoeba/import", {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
        body: JSON.stringify({ upload_id: preview.upload_id }),
      });
      setMessage(
        `${r.inserted} phrases ajoutées · ${r.duplicates} doublons · ${r.enriched} fiches enrichies. Les phrases sont publiques et à vérifier.`,
      );
      setPreview(null);
      onDone();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="tsv-import">
      <summary>Importer Tatoeba : phrases et enregistrements</summary>
      <p>
        Depuis{" "}
        <a
          href="https://tatoeba.org/en/downloads"
          target="_blank"
          rel="noreferrer"
        >
          les téléchargements Tatoeba ↗
        </a>
        , exporte les paires kab → fra avec les quatre colonnes : identifiant
        kabyle, texte kabyle, identifiant français, texte français.
      </p>
      <label>
        Paires Tatoeba{" "}
        <input
          type="file"
          accept=".tsv,.csv,.bz2,.gz"
          disabled={busy}
          onChange={(e) => {
            setPairs(e.target.files?.[0] || null);
            setPreview(null);
          }}
        />
      </label>
      <label>
        Métadonnées audio Tatoeba (facultatif){" "}
        <input
          type="file"
          accept=".tsv,.csv,.bz2,.gz"
          disabled={busy}
          onChange={(e) => {
            setAudio(e.target.files?.[0] || null);
            setPreview(null);
          }}
        />
      </label>
      <p className="tiny">
        Fichier sentences_with_audio : identifiant phrase, identifiant audio,
        auteur, licence, lien d’attribution. Les archives .tar.bz2 sont
        acceptées. Maximum 128 Mo au total ; les gros exports de phrases et de
        liens passent par le script documenté dans le README.
      </p>
      <button
        className="secondary"
        disabled={!token || !pairs || busy}
        onClick={prepare}
      >
        Préparer et voir l’aperçu
      </button>
      {busy && <p role="status">Traitement des fichiers…</p>}
      {message && <p role="status">{message}</p>}
      {preview && (
        <>
          <p role="status">
            {preview.pairs} paires alignées · {preview.audio_records}{" "}
            enregistrements associés · {preview.pairs_with_audio} paires avec
            audio.
          </p>
          {!!(
            preview.invalid_pairs +
            preview.invalid_audio_rows +
            preview.audio_without_credits
          ) && (
            <p>
              {preview.invalid_pairs} paires incomplètes ·{" "}
              {preview.invalid_audio_rows} lignes audio non reconnues ·{" "}
              {preview.audio_without_credits} enregistrements sans crédits
              complets.
            </p>
          )}
          <div className="tsv-sample">
            <table>
              <thead>
                <tr>
                  <th>Phrase kabyle</th>
                  <th>Traduction française</th>
                  <th>Identifiants</th>
                </tr>
              </thead>
              <tbody>
                {preview.sample.map((r) => (
                  <tr key={`${r.kab_id}-${r.fr_id}`}>
                    <td lang="kab-Latn">{r.latin}</td>
                    <td>{r.french}</td>
                    <td>
                      {r.kab_id} → {r.fr_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="primary" disabled={busy} onClick={commit}>
            Importer Tatoeba et rendre public
          </button>
        </>
      )}
    </details>
  );
}
