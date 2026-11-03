"use client";
import { useState } from "react";
import { request } from "../lib/api";
type Preview = {
  upload_id: string;
  sample: { line: number; cells: string[] }[];
  kab_column: number | null;
  fr_column: number | null;
  has_header: boolean;
};
export default function TsvImport({
  token,
  onDone,
}: {
  token: string;
  onDone: () => void;
}) {
  const [preview, setPreview] = useState<Preview | null>(null),
    [kab, setKab] = useState(1),
    [fr, setFr] = useState(2),
    [header, setHeader] = useState(false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const headers = { Authorization: "Bearer " + token };
  function received(p: Preview) {
    setPreview(p);
    setKab(p.kab_column || 1);
    setFr(p.fr_column || 2);
    setHeader(p.has_header);
    setMessage("Vérifie les colonnes ci-dessous, puis lance l’import.");
  }
  async function upload(file: File) {
    setBusy(true);
    setMessage("");
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await fetch("/api/admin/import-tsv/preview", {
        method: "POST",
        headers,
        body: form,
      });
      const data = await r.json();
      if (!r.ok) throw Error(data.detail || "Échec du téléversement");
      received(data);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function download() {
    setBusy(true);
    try {
      received(
        await request("admin/import-tsv/from-url", { method: "POST", headers }),
      );
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
      const r = await request("admin/import-tsv/commit", {
        method: "POST",
        headers,
        body: JSON.stringify({
          upload_id: preview.upload_id,
          kab_column: kab,
          fr_column: fr,
          has_header: header,
        }),
      });
      setMessage(
        `${r.inserted} phrases ajoutées · ${r.duplicates} doublons · ${r.invalid_rows} lignes incomplètes. Les phrases sont publiques, classées et à vérifier.`,
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
      <summary>Importer les phrases Kabyle–Français (Sifal)</summary>
      <p>
        Les phrases importées seront visibles dans la bibliothèque. Tu pourras
        corriger leur catégorie et les valider.
      </p>
      <a
        href="https://huggingface.co/datasets/Sifal/Kabyle-French/tree/main"
        target="_blank"
        rel="noreferrer"
      >
        Ouvrir le jeu de données ↗
      </a>
      <p>
        <button
          className="secondary"
          disabled={busy || !token}
          onClick={download}
        >
          Télécharger depuis Hugging Face
        </button>
      </p>
      <label>
        Choisir le fichier TSV{" "}
        <input
          type="file"
          accept=".tsv,text/tab-separated-values"
          disabled={busy || !token}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload(file);
          }}
        />
      </label>
      {message && <p role="status">{message}</p>}
      {busy && <p role="status">Import en cours…</p>}
      {preview && (
        <>
          <div className="tsv-sample">
            <table>
              <thead>
                <tr>
                  {preview.sample[0].cells.map((_, i) => (
                    <th key={i}>Colonne {i + 1}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.sample.map((r) => (
                  <tr key={r.line}>
                    {r.cells.map((c, i) => (
                      <td key={i}>{c}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <label>
            Colonne kabyle{" "}
            <input
              type="number"
              min={1}
              max={30}
              value={kab}
              onChange={(e) => setKab(Number(e.target.value))}
            />
          </label>
          <label>
            Colonne français{" "}
            <input
              type="number"
              min={1}
              max={30}
              value={fr}
              onChange={(e) => setFr(Number(e.target.value))}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={header}
              onChange={(e) => setHeader(e.target.checked)}
            />{" "}
            La première ligne contient les titres
          </label>
          <button
            className="primary"
            disabled={busy || kab === fr}
            onClick={commit}
          >
            Importer et rendre public
          </button>
        </>
      )}
    </details>
  );
}
