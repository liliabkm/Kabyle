import {
  Apple,
  BookOpen,
  Carrot,
  GraduationCap,
  House,
  Shirt,
  Sun,
  Mountain,
  Users,
  Utensils,
  CupSoda,
  Coffee,
  Milk,
  Droplet,
  Wine,
  Beer,
  PawPrint,
  Briefcase,
  Music,
  Heart,
  MessageCircle,
  Paintbrush,
  Footprints,
  ShoppingBasket,
  HelpCircle,
  Leaf,
  Glasses,
  Flame,
  Stethoscope,
  Wheat,
} from "lucide-react";
import WordVisual from "./WordVisual";
const icons: Record<string, typeof Apple> = {
  fruits: Apple,
  legumes: Carrot,
  alimentation: Utensils,
  boissons: CupSoda,
  vetements: Shirt,
  nature: Mountain,
  famille: Users,
  ecole: GraduationCap,
  maison: House,
  metiers: Briefcase,
  description: Paintbrush,
  couleurs: Paintbrush,
  actions: Footprints,
  salutations: MessageCircle,
  questions: HelpCircle,
  grammaire: BookOpen,
  etats: Heart,
  sante: Heart,
  musique: Music,
  achats: ShoppingBasket,
  voyages: Mountain,
  jours: Sun,
  prenoms: Users,
};
export function TopicArt({ topic }: { topic: string }) {
  if (topic === "animaux")
    return (
      <div
        className="topic-art animal-scene"
        role="img"
        aria-label="Illustrations d’un chien et d’un cheval"
      >
        <WordVisual media={{ illustration: "dog" }} label="Chien" />
        <WordVisual media={{ illustration: "horse" }} label="Cheval" />
      </div>
    );
  if (topic === "alphabet")
    return (
      <div
        className="topic-art alphabet-scene"
        role="img"
        aria-label="Lettres tifinaghes"
      >
        <span>ⴰ</span>
        <span>ⴱ</span>
        <span>ⴷ</span>
      </div>
    );
  if (topic === "nombres")
    return (
      <div
        className="topic-art number-scene"
        role="img"
        aria-label="Les nombres 1, 2 et 3"
      >
        <span>1</span>
        <span>2</span>
        <span>3</span>
      </div>
    );
  const Icon = icons[topic] || BookOpen;
  return (
    <svg
      className="topic-art"
      viewBox="0 0 280 160"
      role="img"
      aria-label="Illustration du thème"
    >
      <circle cx="220" cy="35" r="18" fill="#ffe0a6" />
      <ellipse cx="140" cy="139" rx="105" ry="9" fill="#d6e5e0" />
      <path
        d="M28 127Q37 79 58 125M234 128q6-38 23-10"
        fill="none"
        stroke="#83bba1"
        strokeWidth="7"
        strokeLinecap="round"
      />
      <Icon
        x={84}
        y={30}
        width={100}
        height={100}
        stroke="#5a568a"
        fill="#eee7fb"
        strokeWidth={1.5}
      />
      <Leaf
        x={48}
        y={66}
        width={33}
        height={33}
        stroke="#549874"
        fill="#bce7cc"
      />
      {topic === "fruits" ? (
        <>
          <circle cx="214" cy="105" r="12" fill="#9664b1" />
          <circle cx="199" cy="88" r="12" fill="#ac76c3" />
          <circle cx="224" cy="84" r="12" fill="#ac76c3" />
          <circle cx="211" cy="65" r="12" fill="#c28cd4" />
        </>
      ) : (
        <circle cx="212" cy="99" r="17" fill="#ffcfa9" />
      )}
    </svg>
  );
}
const photos: Record<string, string> = {
  fraise: "fraise",
  figue: "figue",
  raisin: "raisin",
  pomme: "pomme",
  banane: "banane",
  orange: "orange",
  poire: "poire",
  cerise: "cerise",
  carotte: "carotte",
  tomate: "tomate",
  oignon: "oignon",
  "pomme-de-terre": "pomme-de-terre",
};
export function WordArt({ art, label }: { art?: string; label: string }) {
  if (art && photos[art])
    return (
      <div className="topic-word-art photo-word-art">
        <img
          src={"/api/media/fruits360/" + photos[art] + ".jpg"}
          alt={label}
          width={100}
          height={100}
          loading="lazy"
        />
      </div>
    );
  if (art === "chien" || art === "cheval")
    return (
      <div className="topic-word-art">
        <WordVisual
          media={{ illustration: art === "chien" ? "dog" : "horse" }}
          label={label}
        />
      </div>
    );
  const colors: Record<string, string> = {
    vert: "#69aa73",
    rouge: "#df6c6b",
    bleu: "#6b9dcc",
    blanc: "#ffffff",
    gris: "#a7acb8",
    roux: "#ae7250",
  };
  if (art && colors[art])
    return (
      <div className="topic-word-art" role="img" aria-label={label}>
        <svg viewBox="0 0 140 100" width="140" height="100">
          <path
            d="M30 25Q75-5 107 26t-4 57q-37 24-69-2T30 25"
            fill={colors[art]}
            stroke="#d6d4e2"
            strokeWidth="2"
          />
          <ellipse cx="56" cy="27" rx="16" ry="7" fill="white" opacity=".45" />
        </svg>
      </div>
    );
  if (art?.startsWith("number:"))
    return (
      <div className="topic-word-art numeral-art" role="img" aria-label={label}>
        {art.split(":")[1]}
      </div>
    );
  if (
    art &&
    [
      "chat",
      "ours",
      "lion",
      "souris",
      "elephant",
      "ane",
      "canard",
      "poisson",
    ].includes(art)
  ) {
    const color =
      art === "chat"
        ? "#edb16e"
        : art === "ours"
          ? "#b78a68"
          : art === "lion"
            ? "#edba54"
            : "#bdc5d8";
    return (
      <svg
        className="topic-word-art"
        viewBox="0 0 180 140"
        role="img"
        aria-label={label}
      >
        <ellipse cx="90" cy="126" rx="59" ry="6" fill="#e2ddeb" />
        {art === "poisson" ? (
          <>
            <path d="m122 62 37-26v61l-37-24" fill="#edb96f" />
            <ellipse cx="79" cy="68" rx="54" ry="37" fill="#f4c777" />
            <circle cx="51" cy="59" r="5" fill="#303654" />
            <path
              d="m86 49-15 22 15 19"
              fill="none"
              stroke="#d6954c"
              strokeWidth="5"
            />
          </>
        ) : art === "canard" ? (
          <>
            <ellipse cx="88" cy="93" rx="57" ry="30" fill="#f6cf69" />
            <circle cx="69" cy="52" r="27" fill="#f6cf69" />
            <path d="M44 51 16 63l32 10" fill="#ec9756" />
            <circle cx="64" cy="47" r="4" fill="#303654" />
            <path
              d="M88 82q49-11 20 22"
              stroke="#dfb84a"
              strokeWidth="5"
              fill="none"
            />
          </>
        ) : (
          <>
            {art === "lion" && <circle cx="90" cy="70" r="57" fill="#bc7946" />}
            {art === "chat" ? (
              <>
                <path d="m47 57-3-40 36 22m22 0 34-22-3 40" fill={color} />
                <path d="m51 40-2-14 13 13m58 0 11-13-1 16" fill="#e69c99" />
              </>
            ) : art === "ane" ? (
              <>
                <ellipse cx="65" cy="30" rx="10" ry="27" fill={color} />
                <ellipse cx="115" cy="30" rx="10" ry="27" fill={color} />
              </>
            ) : (
              <>
                <circle
                  cx="48"
                  cy="39"
                  r={art === "elephant" ? 33 : art === "souris" ? 27 : 20}
                  fill={color}
                />
                <circle
                  cx="132"
                  cy="39"
                  r={art === "elephant" ? 33 : art === "souris" ? 27 : 20}
                  fill={color}
                />
              </>
            )}
            <rect x="44" y="32" width="92" height="85" rx="39" fill={color} />
            <circle cx="68" cy="67" r="6" fill="#303654" />
            <circle cx="112" cy="67" r="6" fill="#303654" />
            {art === "elephant" ? (
              <path
                d="M90 80v31q0 23 24 8"
                stroke={color}
                strokeWidth="22"
                fill="none"
                strokeLinecap="round"
              />
            ) : (
              <>
                <ellipse cx="90" cy="92" rx="27" ry="20" fill="#f8eadc" />
                <path
                  d="m82 85 16 0-8 9z"
                  fill={art === "souris" ? "#df9d9e" : "#49536c"}
                />
                <path
                  d="M80 101q10 10 20 0"
                  fill="none"
                  stroke="#6a6272"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                {art === "chat" && (
                  <path
                    d="m38 85 29 5m-27 9 28-4m45-5 29-5m-28 10 28 4"
                    stroke="#7a6b67"
                    strokeWidth="2"
                  />
                )}
              </>
            )}
          </>
        )}
      </svg>
    );
  }
  const map: Record<string, typeof Apple> = {
    eau: Droplet,
    lait: Milk,
    cafe: Coffee,
    the: Coffee,
    biere: Beer,
    vin: Wine,
    patte: PawPrint,
    animal: PawPrint,
    lunettes: Glasses,
    tshirt: Shirt,
    chemise: Shirt,
    soleil: Sun,
    montagne: Mountain,
    jardin: Leaf,
    feu: Flame,
    docteur: Stethoscope,
    fermier: Wheat,
    ecole: GraduationCap,
    lettre: BookOpen,
    chanson: Music,
    maison: House,
  };
  const Icon = map[art || ""];
  return (
    <div className="topic-word-art simple-word-art">
      {Icon ? (
        <Icon size={70} strokeWidth={1.6} />
      ) : (
        <span aria-hidden="true">{label.slice(0, 1).toUpperCase()}</span>
      )}
    </div>
  );
}
export function PhotoCredit({ art }: { art?: string }) {
  return art && photos[art] ? (
    <small className="topic-photo-credit">
      Photo : Mihai Oltean · CC BY-SA 4.0
    </small>
  ) : null;
}
