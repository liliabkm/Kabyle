"use client";
import { useEffect, useRef, useState } from "react";
import { ChevronLeft } from "lucide-react";

export type AlphabetLetter = {
  id: string;
  latin: string;
  tifinagh: string;
  french?: string;
  hint?: string;
  examples?: {
    content_id: string;
    kind: string;
    latin: string;
    french: string;
    tifinagh: string;
    sources: { url: string; author: string }[];
  }[];
};

export default function AlphabetExplorer({ letters }: { letters: AlphabetLetter[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const grid = useRef<HTMLDivElement>(null);
  const selected = letters.find((letter) => letter.id === selectedId);
  useEffect(() => {
    if (selectedId) heading.current?.focus();
  }, [selectedId]);

  function back() {
    const id = selectedId;
    setSelectedId(null);
    requestAnimationFrame(() => {
      grid.current?.querySelector<HTMLButtonElement>(`[data-letter-id="${id}"]`)?.focus();
    });
  }

  if (!selected) {
    return (
      <div ref={grid}>
        <p>Choisis une lettre pour découvrir les mots qui commencent par elle.</p>
        <div className="alphabet-grid">
          {letters.map((letter) => (
            <button
              className="alphabet-letter"
              data-letter-id={letter.id}
              key={letter.id}
              aria-label={`Découvrir la lettre ${letter.latin}`}
              onClick={() => setSelectedId(letter.id)}
            >
              <span className="topic-glyph" lang="kab-Tfng">{letter.tifinagh}</span>
              <span lang="kab-Latn">{letter.latin}</span>
            </button>
          ))}
        </div>
        <details>
          <summary>À propos de cet alphabet</summary>
          <p>33 lettres de base. Le signe ʷ / ⵯ accompagne certaines consonnes. Convention : e → ⴻ, h → ⵀ ; d’autres usages existent.</p>
        </details>
      </div>
    );
  }

  // Guard against older seeded data as well as manually edited examples.
  const initial = selected.latin.normalize("NFC").toLocaleLowerCase("kab");
  const examples = (selected.examples || []).filter((example) =>
    example.kind === "word" &&
    example.latin.trim().normalize("NFC").toLocaleLowerCase("kab").startsWith(initial),
  );

  return (
    <section className="alphabet-detail" aria-labelledby="alphabet-heading">
      <button className="secondary" onClick={back}><ChevronLeft size={18} /> Toutes les lettres</button>
      <h2 id="alphabet-heading" ref={heading} tabIndex={-1}>
        <span className="topic-glyph" lang="kab-Tfng">{selected.tifinagh}</span>
        Les mots qui commencent par <span lang="kab-Latn">{selected.latin}</span>
      </h2>
      {examples.length ? (
        <>
          <p>Lis le mot en tifinagh, puis découvre sa traduction.</p>
          <div className="topic-word-grid">
            {examples.map((example) => (
              <article className="topic-word-card alphabet-example" key={example.content_id}>
                <p className="reading-tifinagh" lang="kab-Tfng">{example.tifinagh}</p>
                <h3 lang="kab-Latn">{example.latin}</h3>
                <p>{example.french}</p>
                <details>
                  <summary>Source et écriture</summary>
                  <p>Le tifinagh est généré depuis le texte latin et reste à vérifier.</p>
                  {example.sources[0] && /^https?:\/\//.test(example.sources[0].url) && (
                    <a href={example.sources[0].url} target="_blank" rel="noreferrer">Voir la source du mot</a>
                  )}
                </details>
              </article>
            ))}
          </div>
        </>
      ) : (
        <p role="status">Il n’y a pas encore de mot commençant par « {selected.latin} » dans les exemples disponibles.</p>
      )}
      <details>
        <summary>En savoir plus sur cette lettre</summary>
        <p>{selected.hint}</p>
      </details>
    </section>
  );
}
