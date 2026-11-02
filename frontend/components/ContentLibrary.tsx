"use client";
import { useEffect, useState } from "react";
import { BookOpen, Camera, Search, X } from "lucide-react";
import { request } from "../lib/api";
type PhotoData = {
  url: string;
  author: string;
  license: string;
  license_url: string;
  page_url: string;
  source_url: string;
  [key: string]: unknown;
};
type Photo = { id: string; label_fr: string; theme: string; data: PhotoData };
type Word = {
  id: string;
  kind: string;
  variety: string;
  script: string;
  theme: string;
  status: string;
  data: {
    latin: string;
    french: string;
    tifinagh?: string;
    images?: PhotoData[];
    publication_blockers?: string[];
    sources?: { url: string; author: string; license: string }[];
    [key: string]: unknown;
  };
};
export default function ContentLibrary({
  token,
  onSaved,
}: {
  token: string;
  onSaved: () => void;
}) {
  const [words, setWords] = useState<Word[]>([]),
    [photos, setPhotos] = useState<Photo[]>([]),
    [loaded, setLoaded] = useState(false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [tab, setTab] = useState<"words" | "photos">("words"),
    [search, setSearch] = useState(""),
    [selected, setSelected] = useState<Word | null>(null),
    [picked, setPicked] = useState("");
  useEffect(() => {
    setLoaded(false);
    setWords([]);
    setPhotos([]);
    setSelected(null);
    setMessage("");
  }, [token]);
  useEffect(() => {
    if (selected)
      document
        .getElementById("catalog-word-editor")
        ?.scrollIntoView({ block: "start" });
  }, [selected?.id]);
  const headers = { Authorization: "Bearer " + token };
  async function load() {
    setBusy(true);
    setMessage("");
    try {
      const [all, media] = await Promise.all([
        request("admin/content", { headers }),
        request("admin/media", { headers }),
      ]);
      setWords(all.filter((w: Word) => w.kind === "word"));
      setPhotos(media);
      setLoaded(true);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const normalize = (s: string) =>
    s
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("fr");
  const query = normalize(search);
  async function save() {
    if (!selected) return;
    setBusy(true);
    try {
      const photo = photos.find((p) => p.id === picked);
      const images = selected.data.images || [];
      const updated = {
        ...selected,
        status: "draft",
        data: {
          ...selected.data,
          images:
            photo && !images.some((i) => i.url === photo.data.url)
              ? [...images, { ...photo.data, asset_id: photo.id }]
              : images,
          validation_status: "editor_draft",
          edited_at: new Date().toISOString(),
        },
      };
      await request("admin/import", {
        method: "POST",
        headers,
        body: JSON.stringify([updated]),
      });
      setWords(words.map((w) => (w.id === updated.id ? updated : w)));
      setSelected(null);
      setPicked("");
      setMessage("Brouillon enregistré. Il reste exclu des leçons.");
      onSaved();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="content-library">
      <div className="library-heading">
        <div>
          <h2>Les mots et les photos</h2>
          <p>Préparez les fiches avant de les publier.</p>
        </div>
        <button className="secondary" disabled={!token || busy} onClick={load}>
          {busy
            ? "Chargement…"
            : loaded
              ? "Actualiser la bibliothèque"
              : "Ouvrir la bibliothèque"}
        </button>
      </div>
      {message && (
        <p className="info-note" role="status">
          {message}
        </p>
      )}
      {loaded && (
        <>
          <div className="library-tabs">
            <button
              className={tab === "words" ? "active" : ""}
              aria-pressed={tab === "words"}
              onClick={() => setTab("words")}
            >
              <BookOpen size={18} />
              {words.length} entrées kabyle–français
            </button>
            <button
              className={tab === "photos" ? "active" : ""}
              aria-pressed={tab === "photos"}
              onClick={() => setTab("photos")}
            >
              <Camera size={18} />
              {photos.length} photos
            </button>
          </div>
          <label className="library-search">
            <Search size={18} />
            <input
              aria-label="Rechercher dans la bibliothèque"
              placeholder="Chercher un mot, une photo ou un thème…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          {tab === "words" ? (
            <>
              <p className="tiny">
                Les mots importés ne sont pas encore validés. Le tifinagh est à
                compléter. La licence du cours doit être clarifiée avant
                publication ou usage commercial.
              </p>
              <div className="library-word-list">
                {words
                  .filter((w) =>
                    normalize(
                      [w.data.latin, w.data.french, w.theme].join(" "),
                    ).includes(query),
                  )
                  .map((w) => (
                    <button
                      key={w.id}
                      onClick={() => {
                        setSelected(structuredClone(w));
                        setPicked("");
                      }}
                    >
                      <span>
                        <b lang="kab-Latn">{w.data.latin}</b>
                        <span>{w.data.french}</span>
                      </span>
                      <span className="library-badge">
                        {w.status === "draft"
                          ? "À vérifier"
                          : w.status === "validated"
                            ? "Publié"
                            : "Rejeté"}
                      </span>
                    </button>
                  ))}
              </div>
            </>
          ) : (
            <div className="library-photo-grid">
              {photos
                .filter((p) =>
                  normalize(p.label_fr + " " + p.theme).includes(query),
                )
                .map((p) => (
                  <article className="library-photo" key={p.id}>
                    <img
                      src={p.data.url}
                      alt={p.label_fr}
                      width={100}
                      height={100}
                      loading="lazy"
                    />
                    <h3>{p.label_fr}</h3>
                    <p>{p.data.author}</p>
                    <a
                      href={p.data.license_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {p.data.license}
                    </a>
                    <a href={p.data.page_url} target="_blank" rel="noreferrer">
                      Photo d’origine ↗
                    </a>
                    <small>100 × 100 px · photo inchangée</small>
                  </article>
                ))}
            </div>
          )}
          {selected && (
            <form
              id="catalog-word-editor"
              className="library-editor"
              onSubmit={(e) => {
                e.preventDefault();
                save();
              }}
            >
              <div className="library-heading">
                <h3>Modifier « {selected.data.latin} »</h3>
                <button
                  type="button"
                  className="icon-button"
                  aria-label="Fermer la fiche"
                  onClick={() => setSelected(null)}
                >
                  <X size={21} />
                </button>
              </div>
              <label>
                Mot kabyle (latin)
                <input
                  required
                  maxLength={200}
                  value={selected.data.latin}
                  onChange={(e) =>
                    setSelected({
                      ...selected,
                      data: { ...selected.data, latin: e.target.value },
                    })
                  }
                />
              </label>
              <label>
                Traduction française
                <input
                  required
                  maxLength={200}
                  value={selected.data.french}
                  onChange={(e) =>
                    setSelected({
                      ...selected,
                      data: { ...selected.data, french: e.target.value },
                    })
                  }
                />
              </label>
              <label>
                Tifinagh — à faire vérifier
                <input
                  lang="kab-Tfng"
                  value={selected.data.tifinagh || ""}
                  onChange={(e) =>
                    setSelected({
                      ...selected,
                      data: { ...selected.data, tifinagh: e.target.value },
                    })
                  }
                />
              </label>
              <label>
                Ajouter une photo
                <select
                  aria-label="Ajouter une photo"
                  value={picked}
                  onChange={(e) => setPicked(e.target.value)}
                >
                  <option value="">Aucune nouvelle photo</option>
                  {photos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label_fr} · {p.data.license}
                    </option>
                  ))}
                </select>
              </label>
              {picked && (
                <img
                  className="library-picked-photo"
                  src={photos.find((p) => p.id === picked)?.data.url}
                  alt={photos.find((p) => p.id === picked)?.label_fr}
                />
              )}
              {selected.data.images?.length ? (
                <p className="tiny">
                  {selected.data.images.length} photo(s) déjà associée(s). Le
                  nouvel ajout conserve les photos existantes et leurs crédits.
                </p>
              ) : null}
              <details>
                <summary>Sources et points à vérifier</summary>
                <ul>
                  {selected.data.publication_blockers?.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
                {selected.data.sources?.map((s, i) => (
                  <a
                    className="source"
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {s.author} · {s.license} ↗
                  </a>
                ))}
              </details>
              <p className="tiny">
                L’association d’une image ne valide ni la traduction, ni le
                nombre grammatical, ni la transcription. L’enregistrement
                conserve les blocages et remet la fiche en brouillon.
              </p>
              <button className="primary" disabled={busy} type="submit">
                {busy ? "Enregistrement…" : "Enregistrer en brouillon"}
              </button>
            </form>
          )}
        </>
      )}
    </section>
  );
}
