"use client";
import { useEffect, useState } from "react";
import { BookOpen, Search, ChevronLeft, ChevronRight } from "lucide-react";
import ThemeLearning from "./ThemeLearning";
import PhrasePractice from "./PhrasePractice";
import PhraseAudio from "./PhraseAudio";
import { request } from "../lib/api";
type Kind = "letter" | "word" | "phrase";
type Citation = {
  url: string;
  author: string;
  license: string;
  license_url?: string;
};
type Card = {
  id: string;
  kind: Kind;
  status: string;
  alternative_versions?: string[];
  synonyms?: string[];
  theme: string;
  category_label: string;
  latin: string;
  french?: string;
  tifinagh?: string;
  hint?: string;
  source_issues?: string[];
  sources?: Citation[];
  images?: Citation[];
  audios?: Citation[];
};
type Result = {
  items: Card[];
  counts: Record<Kind, number>;
  categories: { id: string; label: string; count: number }[];
  total: number;
  offset: number;
  limit: number;
};
const allowed = (url: string) =>
  /^https?:\/\//.test(url) || url.startsWith("/api/media/");
function EditorialReadingLibrary({
  token,
  onExit,
}: { token?: string; onExit?: () => void } = {}) {
  const [practiceId, setPracticeId] = useState<string | null>(null);
  const [kind, setKind] = useState<Kind>(token ? "word" : "letter"),
    [category, setCategory] = useState(""),
    [query, setQuery] = useState(""),
    [offset, setOffset] = useState(0),
    [result, setResult] = useState<Result | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setResult(null);
    setError("");
    request(
      (token ? "admin/library?" : "library?") +
        new URLSearchParams({
          kind,
          category,
          q: query,
          offset: String(offset),
          limit: "24",
        }),
      {
        signal: controller.signal,
        headers: token ? { Authorization: "Bearer " + token } : {},
      },
    )
      .then((data) => {
        if (active) setResult(data);
      })
      .catch((e) => {
        if (active && e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [kind, category, query, offset, token]);
  if (practiceId)
    return (
      <PhrasePractice
        initialId={practiceId}
        onExit={() => setPracticeId(null)}
      />
    );
  return (
    <section className="reading-library">
      {onExit && (
        <button className="back" onClick={onExit}>
          <ChevronLeft size={17} /> Retour à la gestion
        </button>
      )}
      {token && (
        <p className="info-note">
          Vue administrateur : toutes les fiches, avec leur état de validation.
        </p>
      )}
      <div className="page-heading">
        <div>
          <div className="eyebrow">JE LIS À MON RYTHME</div>
          <h1>Ma bibliothèque</h1>
          <p>Les lettres, les mots et les phrases. Pas besoin de jouer !</p>
        </div>
      </div>
      <div className="reading-tabs" aria-label="Type de fiches">
        {(
          [
            { id: "letter", label: "Lettres" },
            { id: "word", label: "Mots" },
            { id: "phrase", label: "Phrases" },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            aria-pressed={kind === t.id}
            className={kind === t.id ? "active" : ""}
            onClick={() => {
              setKind(t.id);
              setCategory("");
              setQuery("");
              setOffset(0);
            }}
          >
            {t.label}
            <span>{result?.counts[t.id] ?? 0}</span>
          </button>
        ))}
      </div>
      <div className="reading-filters">
        <label className="library-search">
          <Search size={19} />
          <input
            aria-label="Rechercher une fiche"
            placeholder="Cherche en kabyle ou en français…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <label className="category-select">
          Catégorie
          <select
            aria-label="Catégorie des fiches"
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Toutes les catégories</option>
            {result?.categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label} ({c.count})
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {loading ? (
        <p className="info-note" role="status">
          On ouvre les fiches…
        </p>
      ) : (
        <>
          <p className="reading-count" role="status">
            {result?.total ?? 0} fiche(s) à consulter
          </p>
          {result?.items.length ? (
            <div
              className={
                "reading-grid " +
                (kind === "phrase" ? "phrase-reading-grid" : "")
              }
            >
              {result.items.map((c) => (
                <article
                  key={c.id}
                  data-content-id={c.id}
                  className={"reading-card reading-" + c.kind}
                >
                  <span className="reading-category">{c.category_label}</span>
                  {
                    <span className="library-badge">
                      {c.status === "validated"
                        ? "Validé"
                        : c.status === "draft"
                          ? "À vérifier"
                          : "Rejeté"}
                    </span>
                  }
                  {c.kind === "letter" ? (
                    <div className="reading-letter" lang="kab-Tfng">
                      {c.tifinagh}
                    </div>
                  ) : c.images?.[0] && allowed(c.images[0].url) ? (
                    <img
                      className="reading-photo"
                      src={c.images[0].url}
                      alt={c.french || "Illustration du mot"}
                      loading="lazy"
                    />
                  ) : null}
                  <h2 lang="kab-Latn">{c.latin}</h2>
                  {c.kind !== "letter" && c.tifinagh && (
                    <p className="reading-tifinagh" lang="kab-Tfng">
                      {c.tifinagh}
                    </p>
                  )}
                  {c.source_issues?.map((issue, n) => (
                    <p className="info-note" key={n}>
                      {issue}
                    </p>
                  ))}
                  <p className="reading-french">
                    {c.french || "Traduction non disponible"}
                  </p>
                  <PhraseAudio audios={c.audios} text={c.latin} />
                  {c.images?.[0] && (
                    <small className="reading-image-credit">
                      Image : {c.images[0].author} · {c.images[0].license}
                    </small>
                  )}
                  {c.kind === "phrase" && (
                    <button
                      className="secondary"
                      onClick={() => setPracticeId(c.id)}
                    >
                      M’entraîner avec cette phrase
                    </button>
                  )}
                  <details className="reading-sources">
                    <summary>En savoir plus et sources</summary>
                    {(c.alternative_versions || c.synonyms || []).length >
                      0 && (
                      <>
                        <p>Variantes attestées dans la source :</p>
                        <ul>
                          {(c.alternative_versions || c.synonyms || [])
                            .filter((v) => typeof v === "string")
                            .map((v, i) => (
                              <li key={i} lang="kab-Latn">
                                {v}
                              </li>
                            ))}
                        </ul>
                      </>
                    )}
                    {c.hint && <p>{c.hint}</p>}
                    {c.sources
                      ?.filter((s) => allowed(s.url))
                      .map((s, i) => (
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
                </article>
              ))}
            </div>
          ) : (
            <div className="empty">
              <BookOpen size={32} />
              <h2>
                {kind === "letter"
                  ? "Aucune lettre trouvée."
                  : kind === "word"
                    ? "Les mots se préparent."
                    : "Les phrases se préparent."}
              </h2>
              <p>
                {query || category
                  ? "Essaie une autre recherche ou une autre catégorie."
                  : "Les nouvelles fiches apparaîtront ici après vérification. Tu peux déjà découvrir les lettres."}
              </p>
              {kind !== "letter" && !query && !category && (
                <button
                  className="secondary"
                  onClick={() => {
                    setKind("letter");
                    setCategory("");
                  }}
                >
                  Voir les lettres
                </button>
              )}
            </div>
          )}
          {result && result.total > result.limit && (
            <div className="reading-pagination">
              <button
                className="secondary"
                disabled={offset === 0}
                onClick={() => {
                  setOffset(Math.max(0, offset - 24));
                  window.scrollTo(0, 0);
                }}
              >
                <ChevronLeft size={17} /> Avant
              </button>
              <span>
                {offset + 1}–{Math.min(offset + 24, result.total)} /{" "}
                {result.total}
              </span>
              <button
                className="secondary"
                disabled={offset + 24 >= result.total}
                onClick={() => {
                  setOffset(offset + 24);
                  window.scrollTo(0, 0);
                }}
              >
                Après <ChevronRight size={17} />
              </button>
            </div>
          )}
        </>
      )}
      <p className="tiny">
        La consultation ne compte pas comme un exercice réussi. Les fiches à
        vérifier sont aussi accessibles. La validation est indiquée sur chaque
        fiche.
      </p>
    </section>
  );
}

export default function ReadingLibrary(
  props: { token?: string; onExit?: () => void } = {},
) {
  return props.token ? (
    <EditorialReadingLibrary {...props} />
  ) : (
    <ThemeLearning showAlphabet title="Ma bibliothèque" />
  );
}
