"use client";
import { useRef, useState } from "react";
import { Play, Pause, Volume2, LoaderCircle } from "lucide-react";

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
  const [playing, setPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const player = useRef<HTMLAudioElement>(null);
  const time = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
  async function toggle() {
    const audio = player.current;
    if (!audio) return;
    if (!audio.paused) { audio.pause(); return; }
    setFailed(false);
    setLoading(true);
    try { await audio.play(); }
    catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setFailed(true);
      onAvailability?.(false);
    } finally { setLoading(false); }
  }
  return (
    <div className="phrase-recording">
      <audio
        ref={player}
        hidden
        aria-hidden="true"
        preload="none"
        src={recording.url}
        aria-label={`Écouter la phrase : ${text}`}
        onPlay={(event) => {
          document.querySelectorAll("audio").forEach((audio) => {
            if (audio !== event.currentTarget) audio.pause();
          });
          setPlaying(true);
          setFailed(false);
          onAvailability?.(true);
        }}
        onPlaying={() => setLoading(false)}
        onWaiting={() => setLoading(true)}
        onPause={() => { setPlaying(false); setLoading(false); }}
        onEnded={() => { setPlaying(false); setLoading(false); }}
        onLoadedMetadata={(event) => setDuration(Number.isFinite(event.currentTarget.duration) ? event.currentTarget.duration : 0)}
        onTimeUpdate={(event) => setPosition(event.currentTarget.currentTime)}
        onError={() => { setFailed(true); setLoading(false); setPlaying(false); onAvailability?.(false); }}
      />
      <div className="audio-controls">
        <button type="button" className="audio-play-button" onClick={toggle}
          aria-label={`${playing ? "Mettre en pause" : "Lire la phrase"} : ${text}`}>
          {loading ? <LoaderCircle size={20} className="audio-spinner" aria-hidden="true" /> : playing ? <Pause size={20} fill="currentColor" aria-hidden="true" /> : <Play size={20} fill="currentColor" aria-hidden="true" />}
        </button>
        <div className="audio-timeline">
          <input type="range" min={0} max={duration || 1} step={0.01}
            value={Math.min(position, duration || 1)} disabled={!duration}
            aria-label={`Position audio : ${text}`} aria-valuetext={`${time(position)} sur ${time(duration)}`}
            onChange={(event) => {
              if (player.current) player.current.currentTime = Number(event.target.value);
              setPosition(Number(event.target.value));
            }} />
          <span className="audio-time">{time(position)} <span>/ {time(duration)}</span></span>
        </div>
      </div>
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
