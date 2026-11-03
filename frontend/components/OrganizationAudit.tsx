"use client";
import { useState } from "react";
import { request } from "../lib/api";
type Report = {
  roles: Record<string, number>;
  topics: {
    id: string;
    title: string;
    word_count: number;
    phrase_count: number;
  }[];
  issues: { id: string; latin: string; french: string; reason: string }[];
};
export default function OrganizationAudit({ token }: { token: string }) {
  const [report, setReport] = useState<Report | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function load() {
    setBusy(true);
    setError("");
    try {
      setReport(
        await request("admin/organization", {
          headers: { Authorization: "Bearer " + token },
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="tsv-import">
      <summary>Classement des données et fiches à clarifier</summary>
      <p>
        Les fiches d’apprentissage sont regroupées par sens français. Les
        variantes restent conservées. Les chapitres des fichiers source ne
        servent plus de catégories automatiques.
      </p>
      <button className="secondary" disabled={!token || busy} onClick={load}>
        {busy ? "Chargement…" : "Voir le bilan du classement"}
      </button>
      {error && <p className="error">{error}</p>}
      {report && (
        <>
          <p>
            {report.roles.word || 0} formes lexicales ·{" "}
            {report.roles.function || 0} petits mots · {report.roles.name || 0}{" "}
            noms propres ·{" "}
            {(report.roles.review || 0) +
              (report.roles.fragment || 0) +
              (report.roles.unclassified || 0)}{" "}
            éléments à clarifier.
          </p>
          <h3>À corriger dans la source</h3>
          {report.issues.map((i) => (
            <article className="organization-issue" key={i.id}>
              <b>{i.latin}</b> → {i.french}
              <p>{i.reason}</p>
              <small>
                Ouvre cette fiche dans la bibliothèque pour corriger sa
                transcription ou sa traduction. La validation linguistique n’est
                pas modifiée par le classement.
              </small>
            </article>
          ))}
        </>
      )}
    </details>
  );
}
