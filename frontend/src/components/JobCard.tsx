import { useEffect, useState } from "react";
import { Download, X, CheckCircle, AlertCircle, Loader2, Zap, Clock } from "lucide-react";
import { useSSE } from "@/hooks/useSSE";
import { cancelDownload, getFileUrl, formatBytes, type SSEEvent } from "@/lib/api";
import { useStore, type DownloadJob } from "@/store/useStore";

interface Props {
  job: DownloadJob;
}

const STATUS_LABELS: Record<string, string> = {
  queued:            "Queued",
  fetching_metadata: "Fetching info...",
  downloading:       "Downloading",
  converting:        "Converting",
  done:              "Complete",
  error:             "Failed",
  cancelled:         "Cancelled",
};

export function JobCard({ job }: Props) {
  const updateJob = useStore((s) => s.updateJob);
  const removeJob = useStore((s) => s.removeJob);
  const [sseActive, setSseActive] = useState(
    !["done", "error", "cancelled"].includes(job.status)
  );

  useSSE(
    sseActive ? job.id : null,
    (event: SSEEvent) => {
      updateJob(job.id, {
        status:    event.status,
        progress:  event.progress,
        speed:     event.speed,
        eta:       event.eta,
        filename:  event.filename ?? job.filename,
        file_size: event.file_size ?? job.file_size,
        error:     event.error,
      });
    },
    () => setSseActive(false)
  );

  const isDone      = job.status === "done";
  const isError     = job.status === "error";
  const isCancelled = job.status === "cancelled";
  const isActive    = !isDone && !isError && !isCancelled;

  const handleCancel = async () => {
    await cancelDownload(job.id);
    updateJob(job.id, { status: "cancelled" });
    setSseActive(false);
  };

  const handleDownload = () => {
    const a = document.createElement("a");
    a.href = getFileUrl(job.id);
    a.download = job.filename || "download";
    a.click();
  };

  const statusColor = isDone ? "text-emerald-400"
    : isError ? "text-red-400"
    : isCancelled ? "text-gray-500"
    : "text-brand-400";

  return (
    <div className={`card p-4 animate-slide-up transition-all ${isError ? "border-red-900/50" : isDone ? "border-emerald-900/30" : ""}`}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className={`mt-0.5 flex-shrink-0 ${statusColor}`}>
          {isDone ? <CheckCircle size={16} /> :
           isError ? <AlertCircle size={16} /> :
           isCancelled ? <X size={16} className="text-gray-500" /> :
           <Loader2 size={16} className="animate-spin" />}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-[var(--text-primary)] truncate">
            {job.title || job.url}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-xs ${statusColor}`}>
              {STATUS_LABELS[job.status] || job.status}
            </span>
            <span className="badge-gray text-[10px]">{job.format.toUpperCase()}</span>
            {job.quality !== "best" && (
              <span className="badge-gray text-[10px]">{job.quality}</span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {isDone && (
            <button onClick={handleDownload} className="btn-primary py-1.5 px-3 text-xs">
              <Download size={12} /> Save
            </button>
          )}
          {isActive && (
            <button onClick={handleCancel} className="btn-ghost text-xs text-red-400 hover:text-red-300">
              <X size={12} /> Cancel
            </button>
          )}
          {(isDone || isError || isCancelled) && (
            <button onClick={() => removeJob(job.id)} className="btn-ghost text-xs">
              <X size={12} />
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {isActive && (
        <div className="space-y-1.5">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${Math.min(job.progress, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-[var(--text-subtle)]">
            <span>{job.progress.toFixed(1)}%</span>
            <div className="flex items-center gap-3">
              {job.speed && (
                <span className="flex items-center gap-1">
                  <Zap size={9} /> {job.speed}
                </span>
              )}
              {job.eta && (
                <span className="flex items-center gap-1">
                  <Clock size={9} /> {job.eta}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Done info */}
      {isDone && job.file_size && (
        <p className="text-xs text-[var(--text-muted)] mt-1">
          {job.filename} · {formatBytes(job.file_size)}
        </p>
      )}

      {/* Error */}
      {isError && job.error && (
        <p className="text-xs text-red-400 mt-1 bg-red-950/30 rounded-lg px-3 py-2">
          {job.error}
        </p>
      )}
    </div>
  );
}
