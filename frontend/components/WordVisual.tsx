export type WordMedia = {
  illustration?: string;
  url?: string;
  repeat?: number;
  author?: string;
  license?: string;
  license_url?: string;
  page_url?: string;
  presentation?: string;
};
export default function WordVisual({
  media,
  label,
}: {
  media: WordMedia;
  label: string;
}) {
  if (media.url)
    return (
      <div className="word-photo-cluster" role="img" aria-label={label}>
        {Array.from(
          { length: Math.max(1, Math.min(4, media.repeat || 1)) },
          (_, i) => (
            <img key={i} src={media.url} alt="" width={100} height={100} />
          ),
        )}
      </div>
    );
  if (!["dog", "horse"].includes(media.illustration || ""))
    return (
      <div className="word-picture-unavailable">Illustration à ajouter</div>
    );
  return (
    <svg
      className="animal-visual"
      viewBox="0 0 220 180"
      role="img"
      aria-label={label}
    >
      {media.illustration === "dog" ? (
        <>
          <ellipse cx="110" cy="162" rx="65" ry="9" fill="#d9d0ed" />
          <path
            d="M60 58Q13 30 30 125q7 20 35-4m95-63q47-28 30 67-7 20-35-4"
            fill="#a27551"
          />
          <rect x="53" y="40" width="114" height="119" rx="49" fill="#f5ddb8" />
          <path d="M80 48q30-18 60 0l-9 38H89z" fill="#fff7e6" />
          <ellipse cx="110" cy="124" rx="34" ry="28" fill="#fff7e6" />
          <circle cx="81" cy="96" r="8" fill="#303654" />
          <circle cx="139" cy="96" r="8" fill="#303654" />
          <path d="M100 118q10-8 20 0l-10 10z" fill="#303654" />
          <path d="M102 139q8 15 16 0v-10h-16z" fill="#eb8f8b" />
        </>
      ) : (
        <>
          <ellipse cx="111" cy="163" rx="65" ry="9" fill="#d9d0ed" />
          <path
            d="m80 65-5-43q4-10 16 9l11 29m36 1 5-39q6-8 12 13l3 43"
            fill="#a96e50"
          />
          <path
            d="M84 46q48-20 65 25l20 58q8 34-34 35H90q-38-1-25-38z"
            fill="#c99569"
          />
          <path
            d="M76 66q16-43 46-28l19 26-18-5-15 19-10-12-18 20z"
            fill="#6c4b4a"
          />
          <ellipse cx="116" cy="139" rx="50" ry="26" fill="#f4d9b4" />
          <circle cx="92" cy="101" r="7" fill="#303654" />
          <circle cx="139" cy="101" r="7" fill="#303654" />
          <circle cx="92" cy="138" r="5" fill="#a77757" />
          <circle cx="141" cy="138" r="5" fill="#a77757" />
          <path
            d="M104 150q12 8 24 0"
            stroke="#925c48"
            strokeWidth="4"
            fill="none"
            strokeLinecap="round"
          />
        </>
      )}
    </svg>
  );
}
