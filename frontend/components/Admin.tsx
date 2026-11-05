"use client";
import { useState } from "react";
import { LockKeyhole, ArrowRight } from "lucide-react";
import ContentLibrary from "./ContentLibrary";
import WordLaboratory from "./WordLaboratory";
import DataStudio from "./DataStudio";
import { request } from "../lib/api";
export default function Admin({ onSaved }: { onSaved: () => void }) {
  const [token, setToken] = useState(""),
    [json, setJson] = useState(
      '[\n  {\n    "id": "word-example",\n    "kind": "word",\n    "variety": "kab",\n    "script": "Tfng",\n    "theme": "animaux",\n    "status": "draft",\n    "data": { "latin": "À renseigner", "sources": [] }\n  }\n]',
    ),
    [message, setMessage] = useState(""),
    [connected, setConnected] = useState(false);
  const headers = { Authorization: "Bearer " + token };
  async function load() {
    try {
      setJson(
        JSON.stringify(
          (await request("admin/content", { headers })).slice(0, 500),
          null,
          2,
        ),
      );
      setConnected(true);
      setMessage(
        "Premières fiches chargées. Pour rechercher dans toute la base, utilise la bibliothèque.",
      );
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <div className="admin-panel">
      <div className="info-note">
        <LockKeyhole size={19} />
        <span>
          Administration protégée par le jeton du serveur. Le jeton saisi reste
          en mémoire dans cet onglet.
        </span>
      </div>
      <label>
        Jeton administrateur
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          autoComplete="off"
          placeholder="ADMIN_TOKEN"
        />
      </label>
      <DataStudio key={"structure-" + token} token={token} />
      <WordLaboratory key={token} token={token} onSaved={onSaved} />
      <ContentLibrary token={token} onSaved={onSaved} />
      <details className="advanced-editor">
        <summary>Édition avancée et import JSON</summary>
        <button className="secondary" onClick={load} disabled={!token}>
          Charger les 500 premières fiches
        </button>
        <label>
          Contenus JSON (liste d’entrées)
          <textarea
            spellCheck={false}
            rows={22}
            value={json}
            onChange={(e) => setJson(e.target.value)}
          />
        </label>
        <div className="admin-actions">
          <button
            className="primary"
            disabled={!token}
            onClick={async () => {
              try {
                const data = JSON.parse(json);
                if (!Array.isArray(data))
                  throw Error("Une liste JSON est requise.");
                const result = await request("admin/import", {
                  method: "POST",
                  headers,
                  body: JSON.stringify(data),
                });
                setMessage(`${result.imported} entrée(s) enregistrée(s).`);
                onSaved();
              } catch (e) {
                setMessage((e as Error).message);
              }
            }}
          >
            Enregistrer / importer <ArrowRight size={16} />
          </button>
          <label className="file-import">
            Ouvrir un fichier JSON
            <input
              type="file"
              accept="application/json"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (f) setJson(await f.text());
              }}
            />
          </label>
        </div>
      </details>
      {message && (
        <p role="status" className="info-note">
          {message}
        </p>
      )}
      <p className="tiny">
        Tous les contenus à vérifier sont publics. Le bouton « Valider »
        confirme ta relecture du mot ou de la phrase.
      </p>
    </div>
  );
}
