"use client";
import { useState } from "react";
import { Volume2 } from "lucide-react";

export type Recording = {
  url: string;
  author: string;
  license: string;
  attribution_url?: string;
};

function Clip({ recording, text, onAvailability }: {
  recording: Recording; text: string; onAvailability?: (available: boolean) => void;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <div className="phrase-recording">
      <audio
        controls
        preload="none"
        src={recording.url}
        aria-label={`Écouter la phrase : ${text}`}
        onPlay={(event) => {
          document.querySelectorAll("audio").forEach((audio) => {
            if (audio !== event.currentTarget) audio.pause();
          });
          setFailed(false);
          onAvailability?.(true);
        }}
        onError={() => { setFailed(true); onAvailability?.(false); }}
      />
      {failed && <p className="audio-load-error" role="status">L’audio ne se charge pas. <a href={recording.url} target="_blank" rel="noreferrer">Ouvrir l’enregistrement</a></p>}
      <details className="audio-credit">
        <summary>Crédit audio</summary>
        <p>{recording.author} · {recording.license}</p>
        {recording.attribution_url && /^https?:\/\//.test(recording.attribution_url) && (
          <a href={recording.attribution_url} target="_blank" rel="noreferrer">Source de l’enregistrement</a>
        )}
      </details>
    </div>
  );
}

export default function PhraseAudio({ audios, text, onAvailability }: {
  audios?: Recording[]; text: string; onAvailability?: (available: boolean) => void;
}) {
  const recordings = (audios || []).filter((audio) =>
    audio.author && audio.license &&
    (/^https?:\/\//.test(audio.url) || audio.url.startsWith("/api/media/")),
  );
  if (!recordings.length) return null;
  return (
    <div className="phrase-listen">
      <div className="phrase-listen-title"><Volume2 size={19} aria-hidden="true" /><span>Écouter la phrase</span></div>
      <Clip key={recordings[0].url} recording={recordings[0]} text={text} onAvailability={onAvailability} />
      {recordings.length > 1 && (
        <details className="audio-other-voices">
          <summary>Autres voix ({recordings.length - 1})</summary>
          {recordings.slice(1).map((audio) => <Clip key={audio.url} recording={audio} text={text} onAvailability={onAvailability} />)}
        </details>
      )}
    </div>
  );
}
