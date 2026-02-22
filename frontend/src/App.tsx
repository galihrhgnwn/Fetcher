import { useState, useCallback, useRef } from "react";
import {
  Download, Plus, Trash2, Loader2, Sun, Moon, Search,
  History, Cookie, Zap, AlertCircle, ClipboardPaste, X
} from "lucide-react";
import { Toaster, toast } from "sonner";
import { useStore } from "@/store/useStore";
import { useClipboardPaste } from "@/hooks/useClipboard";
import { MetadataCard } from "@/components/MetadataCard";
import { FormatSelector } from "@/components/FormatSelector";
import { JobCard } from "@/components/JobCard";
import { DownloadHistory } from "@/components/DownloadHistory";
import { CookiesPanel } from "@/components/CookiesPanel";
import {
  validateUrl, fetchMetadata, startDownload,
  recommendFormat, platformLabel,
  type VideoMetadata,
} from "@/lib/api";

interface UrlEntry {
  url: string;
  format: string;
  quality: string;
  loading: boolean;
  error?: string;
  meta?: VideoMetadata;
  urlType?: string;
  validated: boolean;
}

function createEntry(url = ""): UrlEntry {
  return { url, format: "mp4", quality: "best", loading: false, validated: false };
}

export default function App() {
  const { theme, toggleTheme, jobs, addJob, activeTab, setActiveTab } = useStore();
  const [entries, setEntries] = useState<UrlEntry[]>([createEntry()]);
  const [batchLoading, setBatchLoading] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // ── Clipboard auto-paste ─────────────────────────────────────────────────
  useClipboardPaste((url) => {
    const first = entries[0];
    if (!first.url && !first.validated) {
      updateEntry(0, { url });
      toast.info("URL pasted from clipboard", { duration: 2000 });
    }
  });

  // ── Entry helpers ─────────────────────────────────────────────────────────
  const updateEntry = (i: number, patch: Partial<UrlEntry>) => {
    setEntries((prev) => prev.map((e, idx) => idx === i ? { ...e, ...patch } : e));
  };

  const addEntry = () => {
    setEntries((prev) => [...prev, createEntry()]);
    setTimeout(() => inputRefs.current[entries.length]?.focus(), 50);
  };

  const removeEntry = (i: number) => {
    if (entries.length === 1) {
      setEntries([createEntry()]);
    } else {
      setEntries((prev) => prev.filter((_, idx) => idx !== i));
    }
  };

  // ── Validate + fetch metadata ─────────────────────────────────────────────
  const handleFetchMeta = async (i: number) => {
    const entry = entries[i];
    if (!entry.url.trim()) return;

    updateEntry(i, { loading: true, error: undefined, meta: undefined, validated: false });

    try {
      const val = await validateUrl(entry.url);
      if (!val.valid) {
        updateEntry(i, { loading: false, error: val.error || "Invalid URL" });
        return;
      }

      const { metadata, url_type } = await fetchMetadata(val.normalised!);
      const recommended = recommendFormat(url_type, metadata.is_audio_only);

      updateEntry(i, {
        loading:   false,
        meta:      metadata,
        urlType:   url_type,
        url:       val.normalised!,
        format:    recommended,
        validated: true,
        error:     undefined,
      });
    } catch (err: any) {
      updateEntry(i, { loading: false, error: err.message || "Failed to fetch metadata" });
    }
  };

  // ── Start download(s) ─────────────────────────────────────────────────────
  const handleDownloadAll = async () => {
    const valid = entries.filter((e) => e.validated && e.url);
    if (valid.length === 0) {
      toast.error("Please fetch metadata for at least one URL first.");
      return;
    }

    setBatchLoading(true);
    let started = 0;

    for (const entry of valid) {
      try {
        const { job_id } = await startDownload(entry.url, entry.format, entry.quality);
        addJob({
          id:       job_id,
          url:      entry.url,
          title:    entry.meta?.title || entry.url,
          format:   entry.format,
          quality:  entry.quality,
          status:   "queued",
          progress: 0,
          thumbnail: entry.meta?.thumbnail,
        });
        started++;
      } catch (err: any) {
        toast.error(`Failed to start: ${err.message}`);
      }
    }

    if (started > 0) {
      toast.success(`${started} download${started > 1 ? "s" : ""} started`);
      setEntries([createEntry()]);
      setActiveTab("download");
    }
    setBatchLoading(false);
  };

  const handleDownloadSingle = async (i: number) => {
    const entry = entries[i];
    if (!entry.validated) {
      await handleFetchMeta(i);
      return;
    }
    try {
      const { job_id } = await startDownload(entry.url, entry.format, entry.quality);
      addJob({
        id:       job_id,
        url:      entry.url,
        title:    entry.meta?.title || entry.url,
        format:   entry.format,
        quality:  entry.quality,
        status:   "queued",
        progress: 0,
        thumbnail: entry.meta?.thumbnail,
      });
      toast.success("Download started");
      removeEntry(i);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const activeJobs = jobs.filter((j) => !["done", "error", "cancelled"].includes(j.status));
  const doneJobs   = jobs.filter((j) => ["done", "error", "cancelled"].includes(j.status));

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] font-sans">
      <Toaster position="top-right" theme={theme} richColors />

      {/* ── Header ───────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--bg-primary)]/90 backdrop-blur-md">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
              <Download size={14} className="text-white" />
            </div>
            <span className="font-bold text-[var(--text-primary)] tracking-tight">
              Fetcher <span className="text-brand-400 font-normal text-sm">v3</span>
            </span>
          </div>

          <div className="flex items-center gap-1">
            {/* Tab nav */}
            {(["download", "history", "cookies"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`btn-ghost text-xs capitalize flex items-center gap-1.5 ${
                  activeTab === tab ? "text-[var(--text-primary)] bg-[var(--bg-elevated)]" : ""
                }`}
              >
                {tab === "download" && <Zap size={12} />}
                {tab === "history"  && <History size={12} />}
                {tab === "cookies"  && <Cookie size={12} />}
                {tab}
                {tab === "download" && activeJobs.length > 0 && (
                  <span className="ml-0.5 px-1.5 py-0.5 rounded-full bg-brand-600 text-white text-[10px] font-bold leading-none">
                    {activeJobs.length}
                  </span>
                )}
              </button>
            ))}

            {/* Theme toggle */}
            <button onClick={toggleTheme} className="btn-ghost p-2 ml-1">
              {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Main ─────────────────────────────────────────────────────────── */}
      <main className="max-w-3xl mx-auto px-4 py-8">

        {/* ── Download Tab ─────────────────────────────────────────────── */}
        {activeTab === "download" && (
          <div className="space-y-6">
            {/* Hero */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gradient mb-2">
                Download Anything
              </h1>
              <p className="text-sm text-[var(--text-muted)]">
                YouTube · TikTok · Instagram · Twitter · Vimeo · SoundCloud · 1000+ sites
              </p>
            </div>

            {/* URL inputs */}
            <div className="space-y-3">
              {entries.map((entry, i) => (
                <div key={i} className="card p-4 space-y-4 animate-fade-in">
                  {/* URL row */}
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        ref={(el) => { inputRefs.current[i] = el; }}
                        type="url"
                        value={entry.url}
                        onChange={(e) => updateEntry(i, { url: e.target.value, validated: false, meta: undefined, error: undefined })}
                        onKeyDown={(e) => e.key === "Enter" && handleFetchMeta(i)}
                        placeholder="Paste URL here... (auto-detect from clipboard)"
                        className="input pr-10"
                        disabled={entry.loading}
                      />
                      {entry.url && (
                        <button
                          onClick={() => updateEntry(i, { url: "", validated: false, meta: undefined, error: undefined })}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-subtle)] hover:text-[var(--text-muted)]"
                        >
                          <X size={14} />
                        </button>
                      )}
                    </div>

                    {/* Fetch meta button */}
                    <button
                      onClick={() => handleFetchMeta(i)}
                      disabled={!entry.url.trim() || entry.loading}
                      className="btn-secondary flex-shrink-0"
                      title="Fetch metadata"
                    >
                      {entry.loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                    </button>

                    {/* Remove entry */}
                    {entries.length > 1 && (
                      <button onClick={() => removeEntry(i)} className="btn-ghost p-2 text-red-400 hover:text-red-300 flex-shrink-0">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>

                  {/* Error */}
                  {entry.error && (
                    <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/30 rounded-lg px-3 py-2">
                      <AlertCircle size={12} />
                      {entry.error}
                    </div>
                  )}

                  {/* Platform badge */}
                  {entry.urlType && !entry.error && (
                    <div className="flex items-center gap-2">
                      <span className="badge-purple text-xs">{platformLabel(entry.urlType)}</span>
                    </div>
                  )}

                  {/* Metadata preview */}
                  {entry.meta && (
                    <MetadataCard meta={entry.meta} urlType={entry.urlType} />
                  )}

                  {/* Format selector */}
                  {entry.validated && (
                    <FormatSelector
                      format={entry.format}
                      quality={entry.quality}
                      isAudioOnly={entry.meta?.is_audio_only}
                      onChange={(fmt, qual) => updateEntry(i, { format: fmt, quality: qual })}
                    />
                  )}

                  {/* Single download button */}
                  {entry.validated && (
                    <button
                      onClick={() => handleDownloadSingle(i)}
                      className="btn-primary w-full justify-center"
                    >
                      <Download size={14} />
                      Download as {entry.format.toUpperCase()}
                      {entry.quality !== "best" && ` (${entry.quality})`}
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Batch controls */}
            <div className="flex gap-2">
              <button onClick={addEntry} className="btn-secondary flex-1">
                <Plus size={14} /> Add URL
              </button>
              {entries.some((e) => e.validated) && entries.length > 1 && (
                <button
                  onClick={handleDownloadAll}
                  disabled={batchLoading}
                  className="btn-primary flex-1"
                >
                  {batchLoading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                  Download All ({entries.filter((e) => e.validated).length})
                </button>
              )}
            </div>

            {/* Active jobs */}
            {activeJobs.length > 0 && (
              <div className="space-y-2">
                <h2 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                  Active Downloads
                </h2>
                {activeJobs.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            )}

            {/* Completed jobs */}
            {doneJobs.length > 0 && (
              <div className="space-y-2">
                <h2 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                  Completed
                </h2>
                {doneJobs.map((job) => (
                  <JobCard key={job.id} job={job} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── History Tab ──────────────────────────────────────────────── */}
        {activeTab === "history" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Download History</h2>
            <DownloadHistory />
          </div>
        )}

        {/* ── Cookies Tab ──────────────────────────────────────────────── */}
        {activeTab === "cookies" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Cookie Files</h2>
            <CookiesPanel />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border)] mt-16 py-6 text-center text-xs text-[var(--text-subtle)]">
        Fetcher v3.0 · Python + React · For personal use only · Respect copyright laws
      </footer>
    </div>
  );
}
