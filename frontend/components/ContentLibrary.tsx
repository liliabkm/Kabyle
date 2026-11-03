"use client";
import { useEffect, useState, useRef } from "react";
import { Search, X } from "lucide-react";
import OrganizationAudit from "./OrganizationAudit";
import TatoebaImport from "./TatoebaImport";
import TsvImport from "./TsvImport";
import ReadingLibrary from "./ReadingLibrary";
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
type Item = {
  id: string;
  kind: "letter" | "word" | "phrase";
  variety: string;
  script: string;
  theme: string;
  status: string;
  data: {
    alternative_versions?: string[];
    synonyms?: string[];
    french_variants?: string[];
    latin: string;
    french?: string;
    tifinagh?: string;
    images?: PhotoData[];
    publication_blockers?: string[];
    source_issues?: string[];
    sources?: { url: string; author: string; license: string }[];
    [key: string]: unknown;
  };
};
type Category = { id: string; label: string };
export default function ContentLibrary({
  token,
  onSaved,
}: {
  token: string;
  onSaved: () => void;
}) {
  const [reading, setReading] = useState(false);
  const [offset, setOffset] = useState(0),
    [total, setTotal] = useState(0),
    [counts, setCounts] = useState<Record<string, number>>({}),
    [refresh, setRefresh] = useState(0);
  const [items, setItems] = useState<Item[]>([]),
    [photos, setPhotos] = useState<Photo[]>([]),
    [categories, setCategories] = useState<Category[]>([]),
    [loaded, setLoaded] = useState(false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [tab, setTab] = useState<"word" | "phrase" | "letter" | "photos">("word"),
    [search, setSearch] = useState(""),
    [category, setCategory] = useState(""),
    [status, setStatus] = useState(""),
    [selected, setSelected] = useState<Item | null>(null),
    [picked, setPicked] = useState("");
  const loadVersion = useRef(0);
  const headers = { Authorization: "Bearer " + token };
  useEffect(() => {
    loadVersion.current++;
    setLoaded(false);
    setBusy(false);
    setItems([]);
    setPhotos([]);
    setCategories([]);
    setSelected(null);
    setMessage("");
  }, [token]);
  useEffect(() => {
    if (selected)
      document
        .getElementById("catalog-word-editor")
        ?.scrollIntoView({ block: "start" });
  }, [selected?.id]);
  async function load() {
    const version = ++loadVersion.current;
    setBusy(true);
    setMessage("");
    try {
      const [content, media, cats] = await Promise.all([
        request(
          "admin/library?" +
            new URLSearchParams({
              kind: tab === "photos" ? "word" : tab,
              category,
              q: search,
              status,
              offset: String(offset),
              limit: "24",
            }),
          { headers },
        ),
        request("admin/media", { headers }),
        request("admin/categories", { headers }),
      ]);
      if (version !== loadVersion.current) return;
      setItems(
        content.items.map(
          ({
            id,
            kind,
            variety,
            script,
            theme,
            status,
            ...data
          }: Omit<Item, "data"> & Item["data"]) => ({
            id,
            kind,
            theme,
            status,
            variety,
            script,
            data,
          }),
        ),
      );
      setTotal(content.total);
      setCounts(content.counts);
      setPhotos(media);
      setCategories(cats);
      setLoaded(true);
    } catch (e) {
      if (version === loadVersion.current) setMessage((e as Error).message);
    } finally {
      if (version === loadVersion.current) setBusy(false);
    }
  }
  const fold = (s: string) =>
    s
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("fr");
  const query = fold(search);
  const label = (theme: string) =>
    categories.find((c) => c.id === theme)?.label || theme;
  const matches = items;
  useEffect(() => {
    if (loaded) load();
  }, [tab, category, search, status, offset, refresh]);
  async function validate(id: string) {
    setBusy(true);
    try {
      await request(`admin/content/${id}/validate`, {
        method: "POST",
        headers,
      });
      setRefresh((n) => n + 1);
      setMessage("Fiche validée.");
      onSaved();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    if (!selected) return;
    setBusy(true);
    try {
      const photo = photos.find((p) => p.id === picked),
        images = selected.data.images || [];
      const categoryChanged =
        items.find((i) => i.id === selected.id)?.theme !== selected.theme;
      const updated = {
        ...selected,
        status: "draft",
        data: {
          ...selected.data,
          ...(categoryChanged
            ? {
                category_reviewed_at: new Date().toISOString(),
                category_status: "editorial",
              }
            : {}),
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
      setItems(items.map((i) => (i.id === updated.id ? updated : i)));
      setSelected(null);
      setPicked("");
      setMessage(
        "Modifications enregistrées. La fiche est visible et à vérifier.",
      );
      onSaved();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function classify() {
    if (!selected) return;
    setBusy(true);
    try {
      const result = await request(`admin/content/${selected.id}/category`, {
        method: "PATCH",
        headers,
        body: JSON.stringify({ theme: selected.theme }),
      });
      setItems(
        items.map((i) =>
          i.id === selected.id ? { ...i, theme: result.theme } : i,
        ),
      );
      setMessage(
        "Catégorie enregistrée. Le texte et le statut de publication sont conservés.",
      );
      onSaved();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (reading)
    return <ReadingLibrary token={token} onExit={() => setReading(false)} />;
  return (
    <section className="content-library">
      <div className="library-heading">
        <div>
          <h2>Tous les contenus</h2>
          <p>Lettres, mots, phrases et photos, classés par catégorie.</p>
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
        <p role="status" className="info-note">
          {message}
        </p>
      )}
      <OrganizationAudit token={token} />
      <TatoebaImport
        token={token}
        onDone={() => {
          setOffset(0);
          setRefresh((n) => n + 1);
          onSaved();
        }}
      />
      <TsvImport
        token={token}
        onDone={() => {
          setOffset(0);
          setRefresh((n) => n + 1);
          onSaved();
        }}
      />
      {loaded && (
        <>
          <button className="secondary" onClick={() => setReading(true)}>
            Vue lecture
          </button>
          <div className="library-tabs">
            {(
              [
                { id: "letter", label: "Lettres" },
                { id: "word", label: "Mots" },
                { id: "phrase", label: "Phrases" },
                { id: "photos", label: "Photos" },
              ] as const
            ).map((t) => (
              <button
                key={t.id}
                className={tab === t.id ? "active" : ""}
                aria-pressed={tab === t.id}
                onClick={() => {
                  setTab(t.id);
                  setOffset(0);
                  setSelected(null);
                  setCategory("");
                  setStatus("");
                  setSearch("");
                }}
              >
                {t.label} (
                {t.id === "photos" ? photos.length : (counts[t.id] ?? 0)})
              </button>
            ))}
          </div>
          <div className="admin-library-filters">
            <label className="library-search">
              <Search size={18} />
              <input
                aria-label="Rechercher dans la bibliothèque"
                placeholder="Chercher en kabyle ou en français…"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setOffset(0);
                }}
              />
            </label>
            <label>
              Catégorie
              <select
                aria-label="Filtrer la catégorie"
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setOffset(0);
                }}
              >
                <option value="">Toutes les catégories</option>
                {categories.map((c) => (
                  <option value={c.id} key={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            {tab !== "photos" && (
              <label>
                Statut
                <select
                  aria-label="Filtrer le statut"
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">Tous les statuts</option>
                  <option value="draft">À vérifier</option>
                  <option value="validated">Validé</option>
                  <option value="rejected">Rejeté</option>
                </select>
              </label>
            )}
          </div>
          {tab === "photos" ? (
            <div className="library-photo-grid">
              {photos
                .filter(
                  (p) =>
                    (!category || p.theme === category) &&
                    fold(p.label_fr + " " + label(p.theme)).includes(query),
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
                    <span className="reading-category">{label(p.theme)}</span>
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
          ) : (
            <>
              <p className="tiny" role="status">
                {total} fiche(s). Les fiches à vérifier sont publiques. Valide
                une fiche après avoir relu son texte et sa traduction.
              </p>
              <div className="library-word-list">
                {matches.map((i) => (
                  <div className="catalog-row" key={i.id}>
                    <button
                      className="catalog-open"
                      onClick={() => {
                        setSelected(structuredClone(i));
                        setPicked("");
                      }}
                    >
                      <span>
                        <b lang={i.kind === "letter" ? "kab-Tfng" : "kab-Latn"}>
                          {i.kind === "letter"
                            ? `${i.data.tifinagh} · ${i.data.latin}`
                            : i.data.latin}
                        </b>
                        <span>{i.data.french}</span>
                        <small>{label(i.theme)}</small>
                      </span>
                      <span className="library-badge">
                        {i.status === "draft"
                          ? "À vérifier"
                          : i.status === "validated"
                            ? "Validé"
                            : "Rejeté"}
                      </span>
                    </button>
                    <button
                      className="secondary"
                      disabled={busy || i.status === "validated"}
                      onClick={() => validate(i.id)}
                    >
                      {i.status === "validated" ? "Validé" : "Valider"}
                    </button>
                  </div>
                ))}
              </div>
              {!matches.length && (
                <p className="info-note">
                  Aucune fiche ne correspond à ces filtres.
                </p>
              )}
            </>
          )}
          {tab !== "photos" && total > 24 && (
            <div className="reading-pagination">
              <button
                className="secondary"
                disabled={busy || offset === 0}
                onClick={() => setOffset(Math.max(0, offset - 24))}
              >
                Avant
              </button>
              <span>
                {offset + 1}–{Math.min(offset + 24, total)} / {total}
              </span>
              <button
                className="secondary"
                disabled={busy || offset + 24 >= total}
                onClick={() => setOffset(offset + 24)}
              >
                Après
              </button>
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
              <div className="category-edit">
                <label>
                  Catégorie de la fiche
                  <select
                    aria-label="Catégorie de la fiche"
                    value={selected.theme}
                    onChange={(e) =>
                      setSelected({ ...selected, theme: e.target.value })
                    }
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={classify}
                >
                  Enregistrer uniquement la catégorie
                </button>
                <p className="tiny">
                  Cette action conserve le texte et son statut actuel.
                </p>
              </div>
              <label>
                {selected.kind === "phrase"
                  ? "Phrase kabyle (latin)"
                  : "Mot ou lettre (latin)"}
                <input
                  required
                  maxLength={2000}
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
                  maxLength={2000}
                  value={selected.data.french || ""}
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
              {selected.kind === "word" && (
                <>
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
                </>
              )}
              {selected.data.source_issues?.map((issue, n) => (
                <p className="info-note" key={n}>
                  {issue}
                </p>
              ))}
              {selected.kind === "phrase" && (
                <>
                  <label>
                    Niveau CECR attribué
                    <select
                      aria-label="Niveau CECR attribué"
                      value={String(selected.data.cefr_level || "")}
                      onChange={(e) =>
                        setSelected({
                          ...selected,
                          data: {
                            ...selected.data,
                            cefr_level: e.target.value,
                          },
                        })
                      }
                    >
                      <option value="">Non évalué</option>
                      {["A1", "A2", "B1", "B2", "C1", "C2"].map((level) => (
                        <option key={level}>{level}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Note grammaticale
                    <textarea
                      maxLength={4000}
                      value={String(selected.data.grammar_note || "")}
                      onChange={(e) =>
                        setSelected({
                          ...selected,
                          data: {
                            ...selected.data,
                            grammar_note: e.target.value,
                          },
                        })
                      }
                      placeholder="Une explication relue pour cette phrase"
                    />
                  </label>
                </>
              )}
              <details>
                <summary>Sources et points à vérifier</summary>
                {(
                  selected.data.alternative_versions ||
                  selected.data.synonyms ||
                  []
                ).length > 0 && (
                  <>
                    <p>Variantes attestées :</p>
                    <ul>
                      {(
                        selected.data.alternative_versions ||
                        selected.data.synonyms ||
                        []
                      ).map((v, i) => (
                        <li key={i} lang="kab-Latn">
                          {v}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
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
                Modifier le texte ou une image demande une relecture.
                L’enregistrement ci-dessous remet la fiche à vérifier et la
                garde visible.
              </p>
              <button className="primary" disabled={busy} type="submit">
                {busy ? "Enregistrement…" : "Enregistrer les modifications"}
              </button>
            </form>
          )}
        </>
      )}
    </section>
  );
}
