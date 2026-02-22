const BASE = "/api";

export interface ValidationResult {
  valid: boolean;
  url_type?: string;
  normalised?: string;
  error?: string;
}

export interface FormatOption {
  format_id: string;
  ext: string;
  quality?: string;
  resolution?: string;
  filesize?: number;
  note?: string;
}

export interface VideoMetadata {
  title: string;
  thumbnail?: string;
  duration?: number;
  uploader?: string;
  upload_date?: string;
  view_count?: number;
  description?: string;
  formats: FormatOption[];
  estimated_size?: number;
  is_audio_only: boolean;
  extractor?: string;
}

export interface MetadataResponse {
  metadata: VideoMetadata;
  url_type?: string;
}

export interface StartDownloadResponse {
  job_id: string;
  status: string;
}

export interface JobStatus {
  id: string;
  url: string;
  format: string;
  quality: string;
  status: string;
  progress: number;
  speed?: string;
  eta?: string;
  filename?: string;
  file_size?: number;
  error?: string;
  created_at: number;
  updated_at: number;
}

export interface SSEEvent {
  status: string;
  progress: number;
  message?: string;
  speed?: string;
  eta?: string;
  filename?: string;
  file_size?: number;
  error?: string;
}

export interface HistoryEntry {
  id: string;
  url: string;
  title: string;
  format: string;
  file_size?: number;
  thumbnail?: string;
  downloaded_at: number;
}

// ── API calls ──────────────────────────────────────────────────────────────

export async function validateUrl(url: string): Promise<ValidationResult> {
  const r = await fetch(`${BASE}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return r.json();
}

export async function fetchMetadata(url: string): Promise<MetadataResponse> {
  const r = await fetch(`${BASE}/metadata`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to fetch metadata");
  }
  return r.json();
}

export async function startDownload(
  url: string,
  format: string,
  quality: string
): Promise<StartDownloadResponse> {
  const r = await fetch(`${BASE}/download/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, format, quality }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Failed to start download");
  }
  return r.json();
}

export async function cancelDownload(jobId: string): Promise<void> {
  await fetch(`${BASE}/download/${jobId}/cancel`, { method: "POST" });
}

export async function getHistory(): Promise<HistoryEntry[]> {
  const r = await fetch(`${BASE}/history`);
  return r.json();
}

export function getFileUrl(jobId: string): string {
  return `${BASE}/download/${jobId}/file`;
}

export function getProgressUrl(jobId: string): string {
  return `${BASE}/download/${jobId}/progress`;
}

// ── Helpers ────────────────────────────────────────────────────────────────

export function formatBytes(bytes?: number): string {
  if (!bytes) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let v = bytes;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(1)} ${units[i]}`;
}

export function formatDuration(secs?: number): string {
  if (!secs) return "—";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function platformLabel(urlType?: string): string {
  const map: Record<string, string> = {
    youtube: "YouTube", tiktok: "TikTok", instagram: "Instagram",
    twitter: "Twitter/X", facebook: "Facebook", vimeo: "Vimeo",
    twitch: "Twitch", soundcloud: "SoundCloud", reddit: "Reddit",
    dailymotion: "Dailymotion", bilibili: "Bilibili", rumble: "Rumble",
    odysee: "Odysee", bandcamp: "Bandcamp", direct_file: "Direct File",
    generic_web: "Web",
  };
  return map[urlType || ""] || urlType || "Unknown";
}

export const AUDIO_FORMATS = ["mp3", "m4a", "opus", "flac", "wav", "aac"];
export const AUDIO_PLATFORMS = ["soundcloud", "bandcamp"];

export function recommendFormat(urlType?: string, isAudioOnly?: boolean): string {
  if (isAudioOnly || AUDIO_PLATFORMS.includes(urlType || "")) return "mp3";
  return "mp4";
}
