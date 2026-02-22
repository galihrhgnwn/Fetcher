import { Music, Video, FileAudio } from "lucide-react";
import type { VideoMetadata } from "@/lib/api";
import { AUDIO_FORMATS } from "@/lib/api";

interface Props {
  format: string;
  quality: string;
  isAudioOnly?: boolean;
  onChange: (format: string, quality: string) => void;
}

const VIDEO_FORMATS = [
  { value: "mp4",  label: "MP4",  icon: "🎬", desc: "Best compatibility" },
  { value: "webm", label: "WebM", icon: "🌐", desc: "Open format" },
  { value: "mkv",  label: "MKV",  icon: "📦", desc: "High quality" },
];

const AUDIO_FORMAT_LIST = [
  { value: "mp3",  label: "MP3",  icon: "🎵", desc: "Universal audio" },
  { value: "m4a",  label: "M4A",  icon: "🍎", desc: "Apple audio" },
  { value: "opus", label: "Opus", icon: "🔊", desc: "Efficient codec" },
  { value: "flac", label: "FLAC", icon: "💎", desc: "Lossless" },
  { value: "wav",  label: "WAV",  icon: "〰️", desc: "Uncompressed" },
];

const QUALITIES = [
  { value: "best",   label: "Best Available" },
  { value: "2160p",  label: "4K (2160p)" },
  { value: "1440p",  label: "2K (1440p)" },
  { value: "1080p",  label: "Full HD (1080p)" },
  { value: "720p",   label: "HD (720p)" },
  { value: "480p",   label: "SD (480p)" },
  { value: "360p",   label: "360p" },
  { value: "240p",   label: "240p" },
  { value: "144p",   label: "144p" },
];

export function FormatSelector({ format, quality, isAudioOnly, onChange }: Props) {
  const isAudio = AUDIO_FORMATS.includes(format);

  return (
    <div className="space-y-4">
      {/* Format type tabs */}
      <div>
        <div className="flex gap-2 mb-3">
          {!isAudioOnly && (
            <button
              onClick={() => onChange("mp4", quality)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                !isAudio
                  ? "bg-brand-600 text-white"
                  : "bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}
            >
              <Video size={12} /> Video
            </button>
          )}
          <button
            onClick={() => onChange("mp3", quality)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isAudio
                ? "bg-brand-600 text-white"
                : "bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            <Music size={12} /> Audio Only
          </button>
        </div>

        {/* Format grid */}
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
          {(isAudio ? AUDIO_FORMAT_LIST : VIDEO_FORMATS).map((f) => (
            <button
              key={f.value}
              onClick={() => onChange(f.value, quality)}
              className={`flex flex-col items-center gap-1 p-2.5 rounded-lg border text-xs transition-all ${
                format === f.value
                  ? "border-brand-500 bg-brand-900/30 text-brand-300"
                  : "border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:border-[var(--border-light)] hover:text-[var(--text-primary)]"
              }`}
            >
              <span className="text-base">{f.icon}</span>
              <span className="font-semibold">{f.label}</span>
              <span className="text-[10px] opacity-70 hidden sm:block">{f.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Quality selector (only for video) */}
      {!isAudio && (
        <div>
          <label className="text-xs text-[var(--text-muted)] mb-1.5 block">Quality</label>
          <select
            value={quality}
            onChange={(e) => onChange(format, e.target.value)}
            className="select-custom"
          >
            {QUALITIES.map((q) => (
              <option key={q.value} value={q.value}>{q.label}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
